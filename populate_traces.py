"""
Pre-populate LangSmith with realistic multi-turn traces using simulated users.

Uses openevals' run_multiturn_simulation to generate diverse conversations
where a simulated user describes AI initiatives and the agent assesses risks.

Usage: python populate_traces.py
"""

import uuid
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from openevals.simulators import run_multiturn_simulation, create_llm_simulated_user
from rich.console import Console
from rich.panel import Panel
from agent import create_risk_agent

load_dotenv()

console = Console()

# Each scenario defines a simulated user persona and their opening message
SCENARIOS = [
    {
        "name": "AI Credit Scoring System",
        "user_system": (
            "You are a VP of Engineering at a financial services company. You want to build "
            "an AI credit scoring system for lending decisions in the EU. It uses historical "
            "loan data, income, employment history, and credit bureau data. Loan officers will "
            "use it but it can also auto-reject applications below a threshold. You want to "
            "deploy in 6 months. Answer the agent's questions with specific details about your "
            "system. When the agent asks if you want a full assessment, say yes."
        ),
        "first_message": "I want to build an AI-powered credit scoring system for our EU lending operations. Can you help me understand the risks?",
        "max_turns": 4,
    },
    {
        "name": "AI Hiring Screening Tool",
        "user_system": (
            "You are an HR Director planning to deploy an AI tool that screens job applications "
            "for EU offices. It parses resumes, scores candidates on skills, and auto-rejects "
            "those below a minimum. It processes names, work history, education, and skills. "
            "HR recruiters review the shortlist but won't see rejected candidates. You need it "
            "live in 3 months. Be direct and provide details when asked. Push for the assessment."
        ),
        "first_message": "We're planning an AI hiring screening tool for our EU recruitment. What compliance requirements should we be aware of?",
        "max_turns": 4,
    },
    {
        "name": "Customer Service Chatbot",
        "user_system": (
            "You are a Product Manager building a customer service chatbot for an EU-facing "
            "e-commerce website. It answers product questions, handles return requests, and "
            "escalates complex issues to humans. It uses your product catalog and FAQ knowledge "
            "base. No financial data — just order history and customer names. You're curious "
            "whether this even falls under the AI Act. Be conversational and ask follow-up questions."
        ),
        "first_message": "We want to deploy an AI chatbot for customer service on our EU website. Does the AI Act even apply to something like this?",
        "max_turns": 4,
    },
    {
        "name": "Fraud Detection System",
        "user_system": (
            "You are a Chief Risk Officer building an AI fraud detection system for a payment "
            "processing platform. It monitors transactions in real-time and flags suspicious "
            "activity. It processes transaction amounts, merchant info, location data, and "
            "behavioral patterns. Flagged transactions go to manual review — no auto-blocking. "
            "You serve EU customers. You're knowledgeable about risk but want the AI-specific "
            "regulatory perspective."
        ),
        "first_message": "I need a risk assessment for our AI fraud detection system. We process payments for EU customers and I want to understand our AI Act obligations.",
        "max_turns": 4,
    },
    {
        "name": "AI Medical Triage Assistant",
        "user_system": (
            "You are a CTO at a healthtech company developing an AI assistant that helps ER "
            "staff prioritize patients based on symptoms and vital signs. It will be deployed in "
            "hospitals across Germany and France. It processes patient symptoms, vitals, medical "
            "history summaries, and age. Doctors make all final decisions — AI just suggests "
            "triage priority. Targeting 12-month deployment. You're very concerned about "
            "regulatory compliance and patient safety."
        ),
        "first_message": "We're developing an AI triage assistant for emergency rooms in Germany and France. This is healthcare so I imagine the regulatory bar is very high — what do we need to know?",
        "max_turns": 5,
    },
    {
        "name": "Compliance Status Review",
        "user_system": (
            "You are a Compliance Officer doing a quarterly review. You want to understand "
            "your organization's current compliance gaps against the EU AI Act, AICM, and AIEU. "
            "Ask specific follow-up questions about the worst gaps and what remediation timelines "
            "look like."
        ),
        "first_message": "Can you pull up our current compliance status against the EU AI Act, AICM, and AIEU? I need to understand where our biggest gaps are.",
        "max_turns": 3,
    },
    {
        "name": "AI Content Moderation System",
        "user_system": (
            "You are a Trust & Safety Director at a social media platform with 50M EU users. "
            "You're building an AI system that automatically moderates user-generated content — "
            "flagging and auto-removing hate speech, misinformation, and graphic violence. It "
            "processes text posts, image captions, and video transcripts. Clear violations are "
            "auto-removed, borderline cases go to human review. You're worried about both "
            "the AI Act and the Digital Services Act implications."
        ),
        "first_message": "We need to assess our AI content moderation system — it auto-removes policy violations from our platform with 50M EU users. What are the regulatory risks?",
        "max_turns": 4,
    },
    {
        "name": "Open Risk Register Review",
        "user_system": (
            "You are a CISO doing a risk review. You want to see all high and critical open "
            "risks, especially AI governance risks. Ask about mitigation status and timelines "
            "for the worst items. Be brief and executive in tone."
        ),
        "first_message": "Give me a rundown of our highest-severity open risks — anything High or Critical, especially AI governance related.",
        "max_turns": 3,
    },
]


def create_app(agent, thread_id):
    """Create an app function compatible with run_multiturn_simulation."""
    config = {"configurable": {"thread_id": thread_id}}

    def app(inputs, *, thread_id: str, **kwargs):
        content = inputs.get("content", "") if isinstance(inputs, dict) else str(inputs)
        result = agent.invoke(
            {"messages": [{"role": "user", "content": content}]},
            config=config,
        )
        final = result["messages"][-1]
        response_content = final.content if hasattr(final, "content") else str(final)
        if isinstance(response_content, list):
            parts = []
            for c in response_content:
                if isinstance(c, str):
                    parts.append(c)
                elif isinstance(c, dict) and c.get("type") == "text":
                    parts.append(c["text"])
            response_content = "\n".join(parts) if parts else str(response_content)
        return {"role": "assistant", "content": response_content}

    return app


def run_scenario(agent, scenario):
    """Run a single simulation scenario."""
    thread_id = str(uuid.uuid4())

    console.print(Panel(
        f"[bold cyan]{scenario['name']}[/bold cyan]\n"
        f"[dim]Thread: {thread_id} | max {scenario['max_turns']} turns[/dim]",
        border_style="cyan",
    ))

    app = create_app(agent, thread_id)

    user = create_llm_simulated_user(
        system=scenario["user_system"],
        model="openai:gpt-4o-mini",
        fixed_responses=[{"role": "user", "content": scenario["first_message"]}],
    )

    result = run_multiturn_simulation(
        app=app,
        user=user,
        max_turns=scenario["max_turns"],
    )

    trajectory = result.get("trajectory", [])
    console.print(f"  [green]Completed:[/green] {len(trajectory)} messages in trajectory")

    # Show last assistant message snippet
    for msg in reversed(trajectory):
        if msg.get("role") == "assistant":
            snippet = msg["content"][:200].replace("\n", " ")
            console.print(f"  [blue]Last response:[/blue] {snippet}...")
            break

    console.print()
    return thread_id


def main():
    console.print(Panel(
        f"[bold]Pre-populating LangSmith with Simulated Conversations[/bold]\n\n"
        f"Running {len(SCENARIOS)} scenarios using openevals multi-turn simulation.\n"
        f"Each scenario uses a simulated user persona that interacts naturally with the agent.",
        border_style="green",
        title="Trace Population",
    ))
    console.print()

    checkpointer = MemorySaver()
    agent = create_risk_agent(checkpointer=checkpointer)

    threads = []
    for i, scenario in enumerate(SCENARIOS, 1):
        console.print(f"[bold]Scenario {i}/{len(SCENARIOS)}[/bold]")
        try:
            thread_id = run_scenario(agent, scenario)
            threads.append((scenario["name"], thread_id, "success"))
        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]\n")
            threads.append((scenario["name"], None, f"error: {e}"))

    # Summary
    succeeded = sum(1 for _, _, s in threads if s == "success")
    console.print(Panel(
        "\n".join(
            f"  {'[green]OK[/green]' if status == 'success' else '[red]FAIL[/red]'} "
            f"{name} ({tid[:8] if tid else 'N/A'}...)"
            for name, tid, status in threads
        ),
        title=f"Results: {succeeded}/{len(threads)} succeeded",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
