"""
Tools for the Risk Assessment & Governance Agent.

Includes:
- Subagents (called as tools): regulatory research, GRC database analyst, risk assessor
- Direct tools: SQL database access for the orchestrator's own queries
"""

import os
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLDatabaseTool,
)
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from langchain_core.tools import tool


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "risk_governance.db")


def _extract_text(content):
    """Extract text from message content that may be a string, list of strings, or list of dicts."""
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, str):
                parts.append(c)
            elif isinstance(c, dict) and c.get("type") == "text":
                parts.append(c["text"])
        return "\n".join(parts) if parts else str(content)
    return content if isinstance(content, str) else str(content)


def _get_db():
    return SQLDatabase.from_uri(f"sqlite:///{DB_PATH}", sample_rows_in_table_info=3)


def _get_sql_tools():
    db = _get_db()
    return [
        ListSQLDatabaseTool(db=db),
        InfoSQLDatabaseTool(db=db),
        QuerySQLDatabaseTool(db=db),
    ]


# ---------------------------------------------------------------------------
# Subagent: Regulatory Research Agent
# ---------------------------------------------------------------------------

REGULATORY_RESEARCH_PROMPT = """You are a Regulatory Research Specialist focused on AI governance frameworks.

Your job is to search the internet for current, authoritative information about AI regulations \
and compliance requirements. Focus on these frameworks:

- **EU AI Act**: The EU's comprehensive AI regulation classifying AI systems by risk level
- **AICM (AI Compliance Management)**: Framework for managing AI compliance throughout the lifecycle
- **AIEU (AI Ethics in the EU)**: EU guidelines for trustworthy AI (transparency, fairness, human oversight)

When researching:
- Prioritize official EU sources, regulatory bodies, and reputable legal/compliance firms
- Include specific article references (e.g., "AI Act Art. 14 - Human Oversight")
- Note enforcement dates, penalties, and practical compliance steps
- Compare requirements across frameworks where relevant

Return a structured summary with specific regulatory requirements relevant to the query."""


def create_regulatory_research_subagent(llm):
    """Create the regulatory research subagent with Tavily search."""
    search = TavilySearch(
        max_results=5,
        topic="general",
        search_depth="advanced",
    )
    return create_agent(llm, [search], system_prompt=REGULATORY_RESEARCH_PROMPT)


# ---------------------------------------------------------------------------
# Subagent: GRC Database Analyst Agent
# ---------------------------------------------------------------------------

GRC_ANALYST_PROMPT = """You are a GRC Database Analyst. You query the organization's Governance, Risk, \
and Compliance database to find relevant controls, risks, audit findings, and compliance status.

The database contains these tables:
- **regulatory_frameworks**: Includes EU AI Act, AICM, AIEU, GDPR, SOX, HIPAA, ISO 27001, PCI DSS, NIST CSF, CCPA
- **policies**: Organizational governance policies with owners and status
- **controls**: Control measures linked to policies with effectiveness ratings
- **risks**: Risk register with likelihood, impact, risk scores (1-25), and risk levels (Critical/High/Medium/Low)
- **risk_mitigations**: Mitigation strategies linked to risks and controls
- **audit_findings**: Audit results with severity and remediation status
- **compliance_mappings**: How controls map to regulatory framework requirements

ALWAYS start by listing tables and checking schema before writing queries. \
Focus on AI governance controls, AI Act/AICM/AIEU compliance mappings, and related risks \
when the query involves AI systems. Return specific data with names, statuses, and scores — \
not just counts."""


def create_grc_analyst_subagent(llm):
    """Create the GRC database analyst subagent with SQL tools."""
    sql_tools = _get_sql_tools()
    return create_agent(llm, sql_tools, system_prompt=GRC_ANALYST_PROMPT)


# ---------------------------------------------------------------------------
# Subagent: Risk Assessor Agent
# ---------------------------------------------------------------------------

RISK_ASSESSOR_PROMPT = """You are a Risk Assessment Specialist. Given information about a proposed AI \
initiative, regulatory requirements, and the organization's current GRC posture, you produce a \
structured risk assessment.

Your assessment must include:

1. **AI Act Risk Classification**: Classify the proposed system as Unacceptable / High / Limited / Minimal risk \
per the EU AI Act, with justification

2. **Regulatory Requirements Summary**: What specific obligations apply from:
   - EU AI Act (specific articles)
   - AICM (lifecycle compliance requirements)
   - AIEU (ethics and trustworthiness requirements)

3. **Risk Identification**: List specific risks with:
   - Risk title and description
   - Category (AI Regulatory, AI Governance, Data Privacy, Cybersecurity, etc.)
   - Likelihood (1-5) and Impact (1-5) scores with reasoning
   - Risk level (Critical / High / Medium / Low)

4. **Control Gap Analysis**: Based on the organization's existing controls:
   - Which existing controls apply and their current effectiveness
   - What controls are missing or insufficient
   - Priority gaps that must be addressed before deployment

5. **Recommendations**: Prioritized list of actions to achieve compliance, ordered by:
   - Must-have (blocking deployment)
   - Should-have (required within 6 months)
   - Nice-to-have (best practice improvements)

Be specific and actionable. Reference specific AI Act articles, AICM requirements, and AIEU principles."""


def create_risk_assessor_subagent(llm):
    """Create the risk assessor subagent (no tools — it synthesizes from provided context)."""
    return create_agent(llm, [], system_prompt=RISK_ASSESSOR_PROMPT)


# ---------------------------------------------------------------------------
# Wrap subagents as tools for the orchestrator
# ---------------------------------------------------------------------------

def create_subagent_tools(llm):
    """Create subagent tools that the orchestrator can call."""

    regulatory_agent = create_regulatory_research_subagent(llm)
    grc_agent = create_grc_analyst_subagent(llm)
    risk_agent = create_risk_assessor_subagent(llm)

    @tool
    def regulatory_research(query: str) -> str:
        """Search the internet for current AI regulatory requirements, guidance, and compliance
        information related to the EU AI Act, AICM, and AIEU frameworks. Use this when you need
        to understand what regulations apply to a proposed AI system or initiative."""
        result = regulatory_agent.invoke(
            {"messages": [{"role": "user", "content": query}]}
        )
        final = result["messages"][-1]
        content = final.content if hasattr(final, "content") else str(final)
        return _extract_text(content)

    @tool
    def grc_database_analysis(query: str) -> str:
        """Query the organization's GRC database to find relevant controls, risks, audit findings,
        compliance status, and policy information. Use this to understand the organization's current
        governance posture, existing AI controls, and compliance gaps against AI Act/AICM/AIEU."""
        result = grc_agent.invoke(
            {"messages": [{"role": "user", "content": query}]}
        )
        final = result["messages"][-1]
        content = final.content if hasattr(final, "content") else str(final)
        return _extract_text(content)

    @tool
    def risk_assessment(context: str) -> str:
        """Produce a structured risk assessment for a proposed AI initiative. Pass in a comprehensive
        description including: what the AI system does, regulatory research findings, and the
        organization's current GRC posture. Returns a formal risk assessment with AI Act classification,
        regulatory requirements, risk identification, control gap analysis, and recommendations."""
        result = risk_agent.invoke(
            {"messages": [{"role": "user", "content": context}]}
        )
        final = result["messages"][-1]
        content = final.content if hasattr(final, "content") else str(final)
        return _extract_text(content)

    return [regulatory_research, grc_database_analysis, risk_assessment]


def get_all_tools(llm):
    """Return all tools for the orchestrator agent."""
    return create_subagent_tools(llm)
