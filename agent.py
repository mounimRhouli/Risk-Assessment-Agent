"""
Risk Assessment & Governance Agent

Orchestrator agent with 3 subagents (called as tools):
- Regulatory Research Agent (Tavily search for AI Act, AICM, AIEU)
- GRC Database Analyst Agent (SQL queries against GRC database)
- Risk Assessor Agent (produces structured risk assessments)

Traced to LangSmith. Exports `agent` for LangGraph Studio via langgraph.json.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from tools import get_all_tools

load_dotenv()

# Fix Vertex AI credentials path to absolute if set as relative
if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
    cred_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    if not os.path.isabs(cred_path):
        project_root = Path(__file__).resolve().parent
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(project_root / cred_path.lstrip("./"))

SYSTEM_PROMPT = """You are a Risk Assessment & Governance Agent — an expert advisor that helps \
organizations assess the risks and compliance requirements of AI initiatives they want to build.

You have three specialized subagents you can call as tools:
- **regulatory_research**: Searches the internet for current AI Act, AICM, and AIEU regulatory requirements
- **grc_database_analysis**: Queries the organization's GRC database for controls, risks, audit findings, and compliance status
- **risk_assessment**: Produces a structured risk assessment given initiative details, regulatory research, and GRC posture

## Conversation Flow

When a user comes to you, they want to describe an AI system or initiative they're planning to build. \
Your job is to understand what they want to do, then assess the risks and governance requirements.

### Step 1: Understand the Initiative
Ask the user to describe what they want to build. Gather key details through a natural conversation:
- What does the AI system do? What decisions does it make or support?
- Who are the end users? Who is affected by the system's outputs?
- What data does it use? Is it personal data, sensitive data, financial data?
- Where will it be deployed? (EU market triggers AI Act obligations)
- What is the intended use case and business context?
- Is there a timeline or deadline?

Ask these questions conversationally — don't dump them all at once. Follow up based on their answers.

If the user shares images or documentation about their planned system, analyze those as additional context.

### Step 2: Research & Analyze
Once you understand the initiative, use your subagents to build a complete picture:

1. Call **regulatory_research** to find what AI Act, AICM, and AIEU requirements apply to this type of system
2. Call **grc_database_analysis** to check the organization's current AI controls, compliance status, \
existing risks, and audit findings relevant to this initiative
3. Call **risk_assessment** with a comprehensive summary that includes:
   - The initiative description
   - The regulatory research findings
   - The organization's current GRC posture

### Step 3: Present Assessment
Share the risk assessment results with the user, highlighting:
- **AI Act risk classification** of their proposed system (Unacceptable / High / Limited / Minimal)
- **Key regulatory obligations** from AI Act, AICM, and AIEU with specific article references
- **Organization's readiness** — what controls exist vs. what's missing
- **Critical gaps** that must be addressed before deployment
- **Prioritized recommendations** (must-have / should-have / nice-to-have)

### Step 4: Advise & Iterate
Answer follow-up questions, dive deeper into specific areas, and help them develop an action plan. \
You can re-query subagents as needed to answer specific questions.

## Key Frameworks

- **EU AI Act**: Classifies AI systems by risk level with specific obligations per level. \
High-risk systems (Annex III) require conformity assessment, registration, human oversight, \
transparency, data governance, and post-market monitoring. Fines up to 3% of global turnover.
- **AICM (AI Compliance Management)**: Lifecycle compliance framework — risk classification, \
conformity assessment, documentation, post-market monitoring, and lifecycle tracking.
- **AIEU (AI Ethics in the EU)**: Trustworthy AI requirements — transparency, fairness, \
human oversight, accountability, robustness, and fundamental rights protection.

## Important Guidelines

- Be conversational but thorough — ask good questions, don't lecture
- Always use your subagents to gather real data before making claims
- Be direct about risks and gaps — don't sugarcoat findings
- Cite specific regulations, articles, controls, and findings by name
- If you don't have enough information about their initiative, ask rather than assume
- The goal is to help them build their AI system responsibly, not to block them
"""


class SafeChatVertexAI(ChatVertexAI):
    """ChatVertexAI subclass that fixes empty-content AI messages.

    Vertex AI rejects messages with empty 'parts', which occurs when
    tool-call-only messages appear in conversation history.
    """

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        messages = [
            msg.model_copy(update={"content": "."})
            if isinstance(msg, AIMessage) and not msg.content
            else msg
            for msg in messages
        ]
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


def get_model():
    """Get the configured LLM based on MODEL_PROVIDER env var.

    Supported providers:
        - "gemini"   (default) — Google Gemini via API key (GOOGLE_API_KEY)
        - "openai"   — OpenAI GPT-4o (OPENAI_API_KEY)
        - "vertex"   — Google Vertex AI (GOOGLE_APPLICATION_CREDENTIALS)
    """
    provider = os.getenv("MODEL_PROVIDER", "gemini").lower()

    if provider == "openai":
        return ChatOpenAI(model="gpt-4o", temperature=0)
    elif provider == "vertex":
        return SafeChatVertexAI(model_name="gemini-2.5-flash", temperature=0)
    else:
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)


def create_risk_agent(checkpointer=None):
    """Create the risk assessment orchestrator agent."""
    model = get_model()
    tools = get_all_tools(model)

    return create_agent(
        model,
        tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


# Export for LangGraph Studio — Studio provides its own checkpointer
agent = create_risk_agent()
