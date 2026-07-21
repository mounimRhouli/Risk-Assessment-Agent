"""
Offline evaluations for the Risk Assessment & Governance Agent.

Evaluators:
  1. subagent_delegation_quality  — LLM judge (trajectory): correct subagent tool selection
  2. risk_classification_accuracy — LLM judge (single step): EU AI Act risk level correctness
  3. regulatory_framework_coverage      — custom code: expected frameworks cited in response
  4. assessment_structure_completeness  — custom code: required assessment sections present

Runs 4 experiments, each with a different model:
  - gpt-4.1-mini
  - gpt-4.1
  - claude-sonnet-4-20250514
  - gemini-2.5-flash

Usage: uv run python offline_evals.py
"""

from typing import TypedDict

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from langsmith import Client

from agent import SYSTEM_PROMPT
from tools import get_all_tools

load_dotenv()

ls_client = Client()

DATASET_NAME = "Risk Assessment Agent Evaluations"

# ── Models to evaluate ───────────────────────────────────────────────────────

MODEL_CONFIGS = [
    {"model": "openai:gpt-4.1-mini", "temperature": 0, "label": "gpt-4.1-mini"},
    {"model": "openai:gpt-4.1", "temperature": 0, "label": "gpt-4.1"},
    {"model": "anthropic:claude-sonnet-4-20250514", "temperature": 0, "label": "claude-sonnet-4"},
    {"model": "google_genai:gemini-2.5-flash", "temperature": 0, "label": "gemini-2.5-flash"},
]

# Agent tool definitions — populated into metadata so LangSmith UI shows them
AGENT_TOOLS = [
    {
        "name": "regulatory_research",
        "description": "Search for current AI regulatory requirements (EU AI Act, AICM, AIEU)",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "grc_database_analysis",
        "description": "Query the GRC database for controls, risks, audit findings, compliance status",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "risk_assessment",
        "description": "Produce a structured risk assessment for a proposed AI initiative",
        "parameters": {
            "type": "object",
            "properties": {"context": {"type": "string"}},
            "required": ["context"],
        },
    },
]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _extract_text(content):
    """Extract text from message content (string, list of strings, or list of dicts)."""
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, str):
                parts.append(c)
            elif isinstance(c, dict) and c.get("type") == "text":
                parts.append(c["text"])
        return "\n".join(parts) if parts else str(content)
    return content if isinstance(content, str) else str(content)


def _extract_trajectory(messages):
    """Extract tool call names from the agent's message history."""
    tool_names = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_names.append(tc["name"])
    return tool_names


# ── Run function factory ─────────────────────────────────────────────────────


def make_run_fn(model_name: str, temperature: float = 0):
    """Create a run function that invokes the agent with a specific model.

    Each call builds a fresh agent (orchestrator + subagents) so the model
    under test is used end-to-end.
    """
    llm = init_chat_model(model_name, temperature=temperature)
    tools = get_all_tools(llm)
    agent = create_agent(llm, tools, system_prompt=SYSTEM_PROMPT)

    def run_fn(inputs: dict) -> dict:
        query = inputs["query"]
        # The agent is conversational and will ask clarifying questions by default.
        # For evaluation, append a directive so it proceeds with tool calls directly.
        eval_query = (
            f"{query}\n\n"
            "I've given you all the details I have. Please proceed directly with the "
            "full assessment — research the regulations, check the GRC database, and "
            "produce the risk assessment now."
        )
        result = agent.invoke({"messages": [{"role": "user", "content": eval_query}]})
        messages = result["messages"]

        # Final response text
        final = messages[-1]
        response = _extract_text(
            final.content if hasattr(final, "content") else str(final)
        )

        # Trajectory: which subagent tools the orchestrator called
        trajectory = _extract_trajectory(messages)

        return {"response": response, "trajectory": trajectory}

    return run_fn


# ── Evaluators ───────────────────────────────────────────────────────────────

# ---------- 1. LLM Judge — Subagent Delegation Quality (trajectory) ----------


class DelegationGrade(TypedDict):
    reasoning: str
    is_correct: bool


delegation_judge = ChatOpenAI(model="gpt-4.1", temperature=0).with_structured_output(
    DelegationGrade, method="json_schema", strict=True
)


def subagent_delegation_quality(run, example):
    """LLM judge — did the agent delegate to the correct subagents for this query?

    Evaluates the full trajectory of tool calls against expected tool usage.
    For system assessments, expects regulatory_research + grc_database_analysis +
    risk_assessment. For compliance queries, expects grc_database_analysis.
    """
    run_outputs = run.outputs if hasattr(run, "outputs") else run.get("outputs", {}) or {}
    example_outputs = example.outputs if hasattr(example, "outputs") else example.get("outputs", {}) or {}
    example_inputs = example.inputs if hasattr(example, "inputs") else example.get("inputs", {}) or {}

    trajectory = run_outputs.get("trajectory", [])
    expected_tools = example_outputs.get("expected_tools", [])
    query = example_inputs.get("query", "")

    grade = delegation_judge.invoke(
        [
            {
                "role": "user",
                "content": (
                    f"A risk assessment agent received this query:\n\n"
                    f"Query: {query}\n\n"
                    f"The agent called these tools (in order): {trajectory}\n\n"
                    f"The expected tools were: {expected_tools}\n\n"
                    f"Available tools:\n"
                    f"- regulatory_research: Search for AI regulatory requirements\n"
                    f"- grc_database_analysis: Query the GRC database for controls, risks, "
                    f"audit findings\n"
                    f"- risk_assessment: Produce a structured risk assessment\n\n"
                    f"Judge whether the agent delegated to the correct subagents for this "
                    f"query. For a full AI system risk assessment, the agent should use all "
                    f"three tools. For a compliance or risk register query, "
                    f"grc_database_analysis is essential. Tool order matters less than "
                    f"having the right coverage. Was the tool delegation correct?"
                ),
            }
        ]
    )

    return {"score": 1 if grade["is_correct"] else 0, "comment": grade["reasoning"]}


# ------- 2. LLM Judge — Risk Classification Accuracy (single step) ----------


class ClassificationGrade(TypedDict):
    reasoning: str
    is_accurate: bool


classification_judge = ChatOpenAI(model="gpt-4.1", temperature=0).with_structured_output(
    ClassificationGrade, method="json_schema", strict=True
)


def risk_classification_accuracy(run, example):
    """LLM judge — is the EU AI Act risk classification correct for this system?

    Checks whether the agent assigned the right risk level (Unacceptable / High /
    Limited / Minimal) under the EU AI Act given the described AI system.
    """
    run_outputs = run.outputs if hasattr(run, "outputs") else run.get("outputs", {}) or {}
    example_outputs = example.outputs if hasattr(example, "outputs") else example.get("outputs", {}) or {}
    example_inputs = example.inputs if hasattr(example, "inputs") else example.get("inputs", {}) or {}

    response = run_outputs.get("response", "")
    expected_level = example_outputs.get("expected_risk_level", "")
    query = example_inputs.get("query", "")

    # Skip if no risk classification expected (e.g., compliance status queries)
    if not expected_level:
        return {"score": 1, "comment": "No risk classification expected for this query type"}

    grade = classification_judge.invoke(
        [
            {
                "role": "user",
                "content": (
                    f"An AI system was described as follows:\n\n{query}\n\n"
                    f"The expected EU AI Act risk classification is: {expected_level}\n\n"
                    f"The agent's full response is below. Find the risk classification "
                    f"in it.\n\n"
                    f"Agent response (first 3000 chars):\n{response[:3000]}\n\n"
                    f"EU AI Act risk levels for reference:\n"
                    f"- Unacceptable: Banned (social scoring, real-time biometric ID in "
                    f"public)\n"
                    f"- High: Annex III systems (credit scoring, hiring, medical devices, "
                    f"law enforcement, critical infrastructure)\n"
                    f"- Limited: Chatbots, emotion recognition, deep fakes (transparency "
                    f"obligations only)\n"
                    f"- Minimal: Spam filters, AI video games, recommendation systems "
                    f"(no obligations)\n\n"
                    f"Did the agent correctly classify this system as {expected_level} risk?"
                ),
            }
        ]
    )

    return {"score": 1 if grade["is_accurate"] else 0, "comment": grade["reasoning"]}


# ----------- 3. Custom Code — Regulatory Framework Coverage ------------------


def regulatory_framework_coverage(run, example):
    """Custom code — are the expected regulatory frameworks cited in the response?

    Checks that the agent's response references the expected frameworks
    (e.g., AI Act, AICM, AIEU) relevant to the query. Returns a 0-1 score
    based on the fraction of expected frameworks found.
    """
    run_outputs = run.outputs if hasattr(run, "outputs") else run.get("outputs", {}) or {}
    example_outputs = example.outputs if hasattr(example, "outputs") else example.get("outputs", {}) or {}

    response = run_outputs.get("response", "").lower()
    expected_frameworks = example_outputs.get("expected_frameworks", [])

    if not expected_frameworks:
        return {"score": 1, "comment": "No frameworks expected"}

    found = []
    missing = []
    for fw in expected_frameworks:
        if fw.lower() in response:
            found.append(fw)
        else:
            missing.append(fw)

    score = len(found) / len(expected_frameworks)
    comment = f"Found {len(found)}/{len(expected_frameworks)} frameworks."
    if missing:
        comment += f" Missing: {', '.join(missing)}"

    return {"score": score, "comment": comment}


# ---------- 4. Custom Code — Assessment Structure Completeness ---------------


def assessment_structure_completeness(run, example):
    """Custom code — does the response contain all expected assessment sections?

    Checks that the agent's output includes required sections like risk
    classification, regulatory requirements, control gap analysis, and
    recommendations. Returns a 0-1 score based on the fraction found.
    """
    run_outputs = run.outputs if hasattr(run, "outputs") else run.get("outputs", {}) or {}
    example_outputs = example.outputs if hasattr(example, "outputs") else example.get("outputs", {}) or {}

    response = run_outputs.get("response", "").lower()
    expected_sections = example_outputs.get("expected_sections", [])

    if not expected_sections:
        return {"score": 1, "comment": "No sections expected"}

    found = []
    missing = []
    for section in expected_sections:
        if section.lower() in response:
            found.append(section)
        else:
            missing.append(section)

    score = len(found) / len(expected_sections)
    comment = f"Found {len(found)}/{len(expected_sections)} sections."
    if missing:
        comment += f" Missing: {', '.join(missing)}"

    return {"score": score, "comment": comment}


# ── Experiment runner ────────────────────────────────────────────────────────

EVALUATORS = [
    subagent_delegation_quality,
    risk_classification_accuracy,
    regulatory_framework_coverage,
    assessment_structure_completeness,
]


def run_experiments():
    """Run 4 experiments — one per model — against the evaluation dataset."""
    for config in MODEL_CONFIGS:
        model_name = config["model"]
        label = config["label"]
        temperature = config["temperature"]

        print(f"\n{'=' * 60}")
        print(f"Running experiment: {label}")
        print(f"{'=' * 60}")

        run_fn = make_run_fn(model_name, temperature=temperature)

        # Metadata to populate model/prompt/tool columns in LangSmith UI
        EXPERIMENT_METADATA = {
            "models": [
                model_name,
                {
                    "id": ["langchain", "chat_models", "init_chat_model"],
                    "lc": 1,
                    "type": "constructor",
                    "kwargs": {"model": model_name, "temperature": temperature},
                },
            ],
            "prompts": ["risk-assessment-agent:system-prompt"],
            "tools": AGENT_TOOLS,
        }

        results = ls_client.evaluate(
            run_fn,
            data=DATASET_NAME,
            evaluators=EVALUATORS,
            experiment_prefix=f"{label}, risk-assessment",
            description=f"Risk assessment agent evaluation using {label}",
            max_concurrency=2,
            metadata=EXPERIMENT_METADATA,
        )

        print(f"Experiment '{label}' complete: {results}")


if __name__ == "__main__":
    run_experiments()
