"""
Synthetic evaluation dataset for the Risk Assessment & Governance Agent.

Creates a dataset of diverse AI system scenarios with expected outputs
(risk classification, tool usage, regulatory frameworks, assessment sections)
and uploads to LangSmith for running offline evaluations.

Usage: uv run python eval_dataset.py
"""

from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

client = Client()

DATASET_NAME = "Risk Assessment Agent Evaluations"
DATASET_DESCRIPTION = (
    "Synthetic dataset for evaluating the Risk Assessment & Governance Agent. "
    "Each example describes an AI system or governance query with expected risk "
    "classification, tool usage, regulatory framework references, and assessment sections."
)

EXAMPLES = [
    {
        "inputs": {
            "query": (
                "I want to build an AI-powered credit scoring system for our EU lending "
                "operations. It uses historical loan data, income, employment history, and "
                "credit bureau data. Loan officers will use it but it also auto-rejects "
                "applications below a threshold. We want to deploy in 6 months."
            ),
        },
        "outputs": {
            "expected_risk_level": "High",
            "expected_tools": [
                "regulatory_research",
                "grc_database_analysis",
                "risk_assessment",
            ],
            "expected_frameworks": ["AI Act", "AICM", "AIEU"],
            "expected_sections": [
                "risk classification",
                "regulatory requirements",
                "control gap",
                "recommendations",
            ],
        },
    },
    {
        "inputs": {
            "query": (
                "We're planning to deploy an AI hiring screening tool for our EU offices. "
                "It parses resumes, scores candidates on skills match, and auto-rejects "
                "candidates below a minimum threshold. HR recruiters review the shortlist "
                "but won't see rejected candidates. It processes names, work history, "
                "education, and skills. We need it live in 3 months."
            ),
        },
        "outputs": {
            "expected_risk_level": "High",
            "expected_tools": [
                "regulatory_research",
                "grc_database_analysis",
                "risk_assessment",
            ],
            "expected_frameworks": ["AI Act", "AICM", "AIEU"],
            "expected_sections": [
                "risk classification",
                "regulatory requirements",
                "control gap",
                "recommendations",
            ],
        },
    },
    {
        "inputs": {
            "query": (
                "We want to deploy an AI customer service chatbot on our EU e-commerce "
                "website. It answers product questions, handles return requests, and "
                "escalates complex issues to human agents. It uses our product catalog "
                "and FAQ knowledge base. No financial data, just order history and "
                "customer names."
            ),
        },
        "outputs": {
            "expected_risk_level": "Limited",
            "expected_tools": [
                "regulatory_research",
                "grc_database_analysis",
                "risk_assessment",
            ],
            "expected_frameworks": ["AI Act", "AICM", "AIEU"],
            "expected_sections": [
                "risk classification",
                "regulatory requirements",
                "recommendations",
            ],
        },
    },
    {
        "inputs": {
            "query": (
                "I need a risk assessment for our AI fraud detection system. We process "
                "payments for EU customers. The system monitors transactions in real-time "
                "and flags suspicious activity based on transaction amounts, merchant info, "
                "location data, and behavioral patterns. Flagged transactions go to manual "
                "review — no auto-blocking."
            ),
        },
        "outputs": {
            "expected_risk_level": "High",
            "expected_tools": [
                "regulatory_research",
                "grc_database_analysis",
                "risk_assessment",
            ],
            "expected_frameworks": ["AI Act", "AICM", "AIEU"],
            "expected_sections": [
                "risk classification",
                "regulatory requirements",
                "control gap",
                "recommendations",
            ],
        },
    },
    {
        "inputs": {
            "query": (
                "We're developing an AI triage assistant for emergency rooms in Germany "
                "and France. It helps ER staff prioritize patients based on symptoms and "
                "vital signs. It processes patient symptoms, vitals, medical history "
                "summaries, and age. Doctors make all final decisions — AI just suggests "
                "triage priority. Targeting a 12-month deployment."
            ),
        },
        "outputs": {
            "expected_risk_level": "High",
            "expected_tools": [
                "regulatory_research",
                "grc_database_analysis",
                "risk_assessment",
            ],
            "expected_frameworks": ["AI Act", "AICM", "AIEU"],
            "expected_sections": [
                "risk classification",
                "regulatory requirements",
                "control gap",
                "recommendations",
            ],
        },
    },
    {
        "inputs": {
            "query": (
                "We need to assess our AI content moderation system. It automatically "
                "moderates user-generated content on our social media platform with 50M "
                "EU users — flagging and auto-removing hate speech, misinformation, and "
                "graphic violence. It processes text posts, image captions, and video "
                "transcripts. Clear violations are auto-removed, borderline cases go to "
                "human review."
            ),
        },
        "outputs": {
            "expected_risk_level": "High",
            "expected_tools": [
                "regulatory_research",
                "grc_database_analysis",
                "risk_assessment",
            ],
            "expected_frameworks": ["AI Act", "AICM", "AIEU"],
            "expected_sections": [
                "risk classification",
                "regulatory requirements",
                "control gap",
                "recommendations",
            ],
        },
    },
    {
        "inputs": {
            "query": (
                "Can you pull up our current compliance status against the EU AI Act, "
                "AICM, and AIEU? I need to understand where our biggest gaps are for "
                "the quarterly compliance review."
            ),
        },
        "outputs": {
            "expected_risk_level": "",
            "expected_tools": ["grc_database_analysis"],
            "expected_frameworks": ["AI Act", "AICM", "AIEU"],
            "expected_sections": [
                "compliance",
                "gaps",
            ],
        },
    },
    {
        "inputs": {
            "query": (
                "We're building an AI predictive maintenance system for our manufacturing "
                "plants in the EU. It analyzes sensor data from industrial equipment — "
                "temperature, vibration, pressure readings — to predict when machinery "
                "needs maintenance. No personal data involved. Maintenance technicians "
                "use the predictions to schedule repairs. We want to deploy in 4 months."
            ),
        },
        "outputs": {
            "expected_risk_level": "Minimal",
            "expected_tools": [
                "regulatory_research",
                "grc_database_analysis",
                "risk_assessment",
            ],
            "expected_frameworks": ["AI Act"],
            "expected_sections": [
                "risk classification",
                "recommendations",
            ],
        },
    },
]


def main():
    # Delete existing dataset if it exists
    datasets = list(client.list_datasets(dataset_name=DATASET_NAME))
    if datasets:
        print(f"Deleting existing dataset: {DATASET_NAME}")
        client.delete_dataset(dataset_id=datasets[0].id)

    # Create dataset
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description=DATASET_DESCRIPTION,
    )
    print(f"Created dataset: {DATASET_NAME} (id: {dataset.id})")

    # Add examples
    client.create_examples(
        inputs=[e["inputs"] for e in EXAMPLES],
        outputs=[e["outputs"] for e in EXAMPLES],
        dataset_id=dataset.id,
    )
    print(f"Added {len(EXAMPLES)} examples to dataset")

    # Print summary
    print(f"\nDataset summary:")
    for i, ex in enumerate(EXAMPLES, 1):
        query = ex["inputs"]["query"][:80]
        risk = ex["outputs"]["expected_risk_level"] or "N/A"
        tools = ", ".join(ex["outputs"]["expected_tools"])
        print(f"  {i}. [{risk:>7}] {query}... (tools: {tools})")


if __name__ == "__main__":
    main()
