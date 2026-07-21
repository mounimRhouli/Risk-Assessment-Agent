"""
Seed script to create and populate a synthetic GRC (Governance, Risk, Compliance) SQLite database.

Run once: python seed_db.py
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "risk_governance.db")


def create_tables(cursor):
    cursor.executescript("""
        DROP TABLE IF EXISTS compliance_mappings;
        DROP TABLE IF EXISTS audit_findings;
        DROP TABLE IF EXISTS risk_mitigations;
        DROP TABLE IF EXISTS risks;
        DROP TABLE IF EXISTS controls;
        DROP TABLE IF EXISTS policies;
        DROP TABLE IF EXISTS regulatory_frameworks;

        CREATE TABLE regulatory_frameworks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            abbreviation TEXT NOT NULL,
            description TEXT,
            jurisdiction TEXT,
            last_updated DATE
        );

        CREATE TABLE policies (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            owner TEXT NOT NULL,
            effective_date DATE,
            review_date DATE,
            status TEXT NOT NULL CHECK(status IN ('Active', 'Draft', 'Under Review', 'Retired'))
        );

        CREATE TABLE controls (
            id INTEGER PRIMARY KEY,
            policy_id INTEGER NOT NULL REFERENCES policies(id),
            name TEXT NOT NULL,
            description TEXT,
            control_type TEXT NOT NULL CHECK(control_type IN ('Preventive', 'Detective', 'Corrective', 'Compensating')),
            implementation_status TEXT NOT NULL CHECK(implementation_status IN ('Implemented', 'Partially Implemented', 'Planned', 'Not Implemented')),
            effectiveness TEXT CHECK(effectiveness IN ('Effective', 'Partially Effective', 'Ineffective', 'Not Assessed')),
            owner TEXT NOT NULL,
            last_tested DATE
        );

        CREATE TABLE risks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            likelihood INTEGER NOT NULL CHECK(likelihood BETWEEN 1 AND 5),
            impact INTEGER NOT NULL CHECK(impact BETWEEN 1 AND 5),
            risk_score INTEGER GENERATED ALWAYS AS (likelihood * impact) STORED,
            risk_level TEXT GENERATED ALWAYS AS (
                CASE
                    WHEN likelihood * impact >= 20 THEN 'Critical'
                    WHEN likelihood * impact >= 12 THEN 'High'
                    WHEN likelihood * impact >= 6 THEN 'Medium'
                    ELSE 'Low'
                END
            ) STORED,
            status TEXT NOT NULL CHECK(status IN ('Open', 'Mitigated', 'Accepted', 'Transferred', 'Closed')),
            owner TEXT NOT NULL,
            identified_date DATE,
            last_reviewed DATE
        );

        CREATE TABLE risk_mitigations (
            id INTEGER PRIMARY KEY,
            risk_id INTEGER NOT NULL REFERENCES risks(id),
            control_id INTEGER REFERENCES controls(id),
            strategy TEXT NOT NULL CHECK(strategy IN ('Avoid', 'Mitigate', 'Transfer', 'Accept')),
            description TEXT,
            status TEXT NOT NULL CHECK(status IN ('Planned', 'In Progress', 'Completed', 'Overdue')),
            due_date DATE,
            completed_date DATE
        );

        CREATE TABLE audit_findings (
            id INTEGER PRIMARY KEY,
            control_id INTEGER NOT NULL REFERENCES controls(id),
            finding TEXT NOT NULL,
            severity TEXT NOT NULL CHECK(severity IN ('Critical', 'High', 'Medium', 'Low', 'Informational')),
            status TEXT NOT NULL CHECK(status IN ('Open', 'In Remediation', 'Closed', 'Risk Accepted')),
            identified_date DATE,
            remediation_due DATE,
            remediation_owner TEXT,
            notes TEXT
        );

        CREATE TABLE compliance_mappings (
            id INTEGER PRIMARY KEY,
            control_id INTEGER NOT NULL REFERENCES controls(id),
            framework_id INTEGER NOT NULL REFERENCES regulatory_frameworks(id),
            requirement_ref TEXT NOT NULL,
            compliance_status TEXT NOT NULL CHECK(compliance_status IN ('Compliant', 'Partially Compliant', 'Non-Compliant', 'Not Assessed')),
            last_assessed DATE,
            evidence_location TEXT
        );
    """)


def seed_data(cursor):
    # Regulatory frameworks
    cursor.executemany(
        "INSERT INTO regulatory_frameworks (name, abbreviation, description, jurisdiction, last_updated) VALUES (?, ?, ?, ?, ?)",
        [
            ("General Data Protection Regulation", "GDPR", "EU regulation on data protection and privacy", "European Union", "2024-03-15"),
            ("Sarbanes-Oxley Act", "SOX", "US federal law on financial reporting and corporate governance", "United States", "2024-01-10"),
            ("Health Insurance Portability and Accountability Act", "HIPAA", "US regulation protecting sensitive patient health information", "United States", "2024-06-01"),
            ("ISO/IEC 27001:2022", "ISO 27001", "International standard for information security management systems", "International", "2024-04-20"),
            ("Payment Card Industry Data Security Standard", "PCI DSS", "Security standard for organizations handling credit card data", "International", "2024-03-31"),
            ("NIST Cybersecurity Framework", "NIST CSF", "Framework for improving critical infrastructure cybersecurity", "United States", "2024-02-26"),
            ("California Consumer Privacy Act", "CCPA", "California state law on consumer data privacy rights", "California, US", "2024-01-01"),
            ("EU Artificial Intelligence Act", "AI Act", "EU regulation establishing harmonized rules on artificial intelligence, classifying AI systems by risk level (unacceptable, high, limited, minimal) with corresponding obligations", "European Union", "2025-02-02"),
            ("AI Compliance Management", "AICM", "Framework for managing compliance of AI systems throughout their lifecycle, covering risk assessment, documentation, monitoring, and conformity assessment procedures", "International", "2025-01-15"),
            ("AI Ethics in the EU", "AIEU", "EU guidelines and requirements for trustworthy AI addressing transparency, accountability, fairness, human oversight, robustness, and fundamental rights protection", "European Union", "2025-03-01"),
        ],
    )

    # Policies
    cursor.executemany(
        "INSERT INTO policies (name, category, description, owner, effective_date, review_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("Data Protection & Privacy Policy", "Data Privacy", "Defines requirements for collecting, processing, and storing personal data", "Chief Privacy Officer", "2024-01-15", "2025-01-15", "Active"),
            ("Information Security Policy", "Security", "Establishes the framework for protecting information assets", "CISO", "2024-02-01", "2025-02-01", "Active"),
            ("Access Control Policy", "Security", "Governs user access to systems and data based on least privilege", "CISO", "2024-03-01", "2025-03-01", "Active"),
            ("Incident Response Policy", "Security", "Defines procedures for detecting, responding to, and recovering from security incidents", "CISO", "2024-01-20", "2025-01-20", "Active"),
            ("Third-Party Risk Management Policy", "Vendor Management", "Requirements for assessing and managing risks from third-party vendors", "VP of Procurement", "2024-04-01", "2025-04-01", "Active"),
            ("Business Continuity Policy", "Operations", "Ensures critical business functions can continue during and after a disaster", "COO", "2024-02-15", "2025-02-15", "Active"),
            ("Data Retention & Disposal Policy", "Data Management", "Defines how long data is retained and how it is securely disposed of", "Chief Data Officer", "2024-05-01", "2025-05-01", "Active"),
            ("Acceptable Use Policy", "Human Resources", "Defines acceptable use of company IT resources by employees", "VP of HR", "2024-01-01", "2025-01-01", "Active"),
            ("Change Management Policy", "Operations", "Governs how changes to IT systems are requested, approved, and implemented", "VP of Engineering", "2024-03-15", "2025-03-15", "Active"),
            ("Financial Reporting Controls Policy", "Finance", "Internal controls over financial reporting processes to ensure accuracy", "CFO", "2024-01-10", "2025-01-10", "Active"),
            ("Cloud Security Policy", "Security", "Security requirements for cloud infrastructure and services", "CISO", "2024-06-01", "2025-06-01", "Draft"),
            ("AI Governance Policy", "Technology", "Governs the ethical development and deployment of AI systems", "CTO", "2024-07-01", "2025-07-01", "Under Review"),
        ],
    )

    # Controls
    cursor.executemany(
        "INSERT INTO controls (policy_id, name, description, control_type, implementation_status, effectiveness, owner, last_tested) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            # Data Protection controls
            (1, "Data Classification", "All data assets are classified by sensitivity level (Public, Internal, Confidential, Restricted)", "Preventive", "Implemented", "Effective", "Data Governance Team", "2024-11-15"),
            (1, "Data Encryption at Rest", "All sensitive data encrypted using AES-256 at rest", "Preventive", "Implemented", "Effective", "Platform Engineering", "2024-12-01"),
            (1, "Data Encryption in Transit", "All data in transit encrypted using TLS 1.2+", "Preventive", "Implemented", "Effective", "Platform Engineering", "2024-12-01"),
            (1, "Consent Management", "Consent collected and tracked for all personal data processing activities", "Preventive", "Partially Implemented", "Partially Effective", "Privacy Team", "2024-10-20"),
            (1, "Data Subject Access Request Process", "Process to handle DSAR within 30 days", "Corrective", "Implemented", "Effective", "Privacy Team", "2024-11-01"),
            # Access Control controls
            (3, "Multi-Factor Authentication", "MFA required for all user accounts accessing production systems", "Preventive", "Implemented", "Effective", "Identity Team", "2024-12-15"),
            (3, "Role-Based Access Control", "Access granted based on job role with least privilege principle", "Preventive", "Implemented", "Partially Effective", "Identity Team", "2024-11-20"),
            (3, "Quarterly Access Reviews", "All user access reviewed and certified quarterly by managers", "Detective", "Implemented", "Effective", "Identity Team", "2024-12-31"),
            (3, "Privileged Access Management", "Privileged accounts managed through PAM solution with session recording", "Preventive", "Partially Implemented", "Partially Effective", "Identity Team", "2024-10-15"),
            # Incident Response controls
            (4, "Security Event Monitoring", "24/7 SIEM monitoring with automated alerting", "Detective", "Implemented", "Effective", "SOC Team", "2024-12-20"),
            (4, "Incident Response Playbooks", "Documented playbooks for top 10 incident types", "Corrective", "Implemented", "Effective", "SOC Team", "2024-11-30"),
            (4, "Incident Post-Mortem Process", "Post-mortem conducted within 5 business days of incident closure", "Corrective", "Implemented", "Partially Effective", "SOC Team", "2024-12-10"),
            # Third-Party Risk
            (5, "Vendor Security Assessment", "Security questionnaire and assessment before onboarding new vendors", "Preventive", "Implemented", "Effective", "Vendor Risk Team", "2024-11-15"),
            (5, "Vendor Continuous Monitoring", "Ongoing monitoring of vendor security posture via automated scanning", "Detective", "Planned", "Not Assessed", "Vendor Risk Team", None),
            (5, "Contractual Security Requirements", "Security and data protection clauses in all vendor contracts", "Preventive", "Implemented", "Effective", "Legal", "2024-10-01"),
            # Business Continuity
            (6, "Disaster Recovery Plan", "Documented DR plan with RPO < 4 hours, RTO < 8 hours", "Corrective", "Implemented", "Effective", "Infrastructure Team", "2024-12-01"),
            (6, "Annual DR Testing", "Full DR failover test conducted annually", "Detective", "Implemented", "Partially Effective", "Infrastructure Team", "2024-09-15"),
            (6, "Backup Verification", "Weekly verification that backups complete successfully and can be restored", "Detective", "Implemented", "Effective", "Infrastructure Team", "2024-12-20"),
            # Change Management
            (9, "Change Advisory Board", "All significant changes reviewed by CAB before implementation", "Preventive", "Implemented", "Effective", "Change Management Team", "2024-12-15"),
            (9, "Automated Deployment Pipeline", "CI/CD pipeline with automated testing gates before production deployment", "Preventive", "Implemented", "Effective", "DevOps Team", "2024-12-20"),
            # Financial Reporting
            (10, "Segregation of Duties", "No single individual can initiate, approve, and record financial transactions", "Preventive", "Implemented", "Effective", "Finance Operations", "2024-12-01"),
            (10, "Financial Close Reconciliation", "All accounts reconciled within 5 business days of period close", "Detective", "Implemented", "Effective", "Finance Operations", "2024-12-31"),
            (10, "Journal Entry Approval", "All manual journal entries require manager approval before posting", "Preventive", "Implemented", "Effective", "Finance Operations", "2024-12-15"),
            # AI Governance (policy_id=12)
            (12, "AI Model Risk Assessment", "All AI models undergo risk assessment classifying system risk level (unacceptable/high/limited/minimal) per EU AI Act before production deployment", "Preventive", "Planned", "Not Assessed", "AI Ethics Board", None),
            (12, "AI Bias Testing", "Bias and fairness testing on all customer-facing AI models per AIEU trustworthy AI requirements", "Detective", "Planned", "Not Assessed", "ML Engineering", None),
            (12, "AI System Registration", "High-risk AI systems registered in EU database per AI Act Art. 71 before market placement", "Preventive", "Not Implemented", "Not Assessed", "AI Ethics Board", None),
            (12, "AI Transparency & Explainability", "AI systems provide meaningful explanations of decisions to affected individuals per AIEU transparency requirements", "Preventive", "Partially Implemented", "Partially Effective", "ML Engineering", "2025-01-15"),
            (12, "AI Human Oversight Mechanism", "Human oversight controls for high-risk AI systems ensuring ability to override, interrupt, or shut down per AI Act Art. 14", "Preventive", "Partially Implemented", "Not Assessed", "AI Ethics Board", None),
            (12, "AI Data Governance", "Training data quality, relevance, and representativeness assessed per AI Act Art. 10 and AICM data governance requirements", "Preventive", "Planned", "Not Assessed", "Data Governance Team", None),
            (12, "AI Conformity Assessment", "Conformity assessment procedures completed for high-risk AI systems per AI Act Art. 43 and AICM lifecycle requirements", "Preventive", "Not Implemented", "Not Assessed", "AI Ethics Board", None),
            (12, "AI Incident Reporting", "Serious incidents involving AI systems reported to authorities within 15 days per AI Act Art. 62", "Corrective", "Not Implemented", "Not Assessed", "SOC Team", None),
            (12, "AI Technical Documentation", "Technical documentation maintained for all AI systems per AI Act Annex IV including design, development, and monitoring details", "Preventive", "Partially Implemented", "Partially Effective", "ML Engineering", "2025-02-01"),
            (12, "AI Fundamental Rights Impact Assessment", "Impact assessment on fundamental rights conducted before deploying high-risk AI per AIEU requirements", "Preventive", "Not Implemented", "Not Assessed", "AI Ethics Board", None),
            (12, "AI Post-Market Monitoring", "Continuous monitoring of AI system performance, drift, and compliance throughout operational lifecycle per AICM monitoring requirements", "Detective", "Planned", "Not Assessed", "ML Engineering", None),
            (12, "AI Lifecycle Compliance Tracking", "End-to-end compliance tracking from development through decommissioning per AICM lifecycle management framework", "Detective", "Not Implemented", "Not Assessed", "AI Ethics Board", None),
        ],
    )

    # Risks
    cursor.executemany(
        "INSERT INTO risks (title, description, category, likelihood, impact, status, owner, identified_date, last_reviewed) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("Data Breach via Third-Party Vendor", "Unauthorized access to customer data through compromised vendor systems", "Third-Party", 3, 5, "Open", "CISO", "2024-06-15", "2024-12-20"),
            ("Ransomware Attack", "Ransomware encryption of critical business systems leading to operational disruption", "Cybersecurity", 3, 5, "Mitigated", "CISO", "2024-03-10", "2024-12-15"),
            ("GDPR Non-Compliance Fine", "Regulatory fine for failure to comply with GDPR data processing requirements", "Regulatory", 2, 5, "Open", "Chief Privacy Officer", "2024-04-20", "2024-12-10"),
            ("SOX Material Weakness", "Identified weakness in internal controls over financial reporting", "Financial", 2, 4, "Open", "CFO", "2024-07-01", "2024-12-20"),
            ("Insider Threat - Data Exfiltration", "Malicious or negligent employee exfiltrating sensitive data", "Cybersecurity", 3, 4, "Open", "CISO", "2024-05-15", "2024-12-01"),
            ("Cloud Service Provider Outage", "Extended outage of primary cloud provider impacting business operations", "Operations", 2, 4, "Mitigated", "CTO", "2024-02-01", "2024-11-30"),
            ("Phishing Campaign Targeting Executives", "Sophisticated spear phishing targeting C-suite for credential theft", "Cybersecurity", 4, 4, "Open", "CISO", "2024-08-10", "2024-12-20"),
            ("Regulatory Change Impact", "New regulations requiring significant changes to data handling practices", "Regulatory", 3, 3, "Accepted", "Chief Privacy Officer", "2024-09-01", "2024-12-15"),
            ("Privileged Access Abuse", "Misuse of admin-level access to modify financial records or access restricted data", "Cybersecurity", 2, 5, "Open", "CISO", "2024-10-05", "2024-12-10"),
            ("Business Continuity Plan Failure", "DR plan fails during actual disaster scenario due to untested components", "Operations", 2, 5, "Open", "COO", "2024-04-15", "2024-11-20"),
            ("AI Model Bias in Lending Decisions", "AI model produces biased outcomes in credit scoring affecting protected groups", "Technology", 3, 5, "Open", "CTO", "2024-11-01", "2024-12-20"),
            ("Supply Chain Software Vulnerability", "Critical vulnerability in widely-used open source dependency", "Cybersecurity", 4, 3, "Open", "VP of Engineering", "2024-07-20", "2024-12-15"),
            ("Employee Data Privacy Violation", "Unauthorized access to employee personal data by HR systems", "Data Privacy", 2, 3, "Mitigated", "VP of HR", "2024-06-01", "2024-12-01"),
            ("Incomplete Audit Trail", "Gaps in logging make it impossible to reconstruct events during investigation", "Compliance", 3, 3, "Open", "CISO", "2024-08-15", "2024-12-10"),
            ("Third-Party API Data Leakage", "Sensitive data exposed through improperly secured API integrations with partners", "Third-Party", 3, 4, "Open", "VP of Engineering", "2024-09-20", "2024-12-15"),
            ("AI Act Non-Compliance - High-Risk System", "Deploying AI system classified as high-risk under EU AI Act without completing conformity assessment, risking fines up to 3% of global turnover", "AI Regulatory", 4, 5, "Open", "CTO", "2025-01-15", "2025-03-01"),
            ("AI System Lack of Human Oversight", "AI systems making consequential decisions without adequate human oversight mechanisms, violating AI Act Art. 14", "AI Governance", 3, 5, "Open", "AI Ethics Board", "2025-01-20", "2025-03-01"),
            ("AI Training Data Bias & Quality", "AI models trained on biased, incomplete, or non-representative data leading to discriminatory outcomes and AIEU violations", "AI Governance", 4, 4, "Open", "ML Engineering", "2025-02-01", "2025-03-15"),
            ("AI Transparency Failure", "Inability to explain AI-driven decisions to regulators or affected individuals, violating AIEU transparency and AI Act Art. 13 requirements", "AI Governance", 3, 4, "Open", "ML Engineering", "2025-02-10", "2025-03-15"),
            ("AI Lifecycle Compliance Gap", "No end-to-end compliance tracking for AI systems from development through decommissioning per AICM framework", "AI Regulatory", 4, 4, "Open", "AI Ethics Board", "2025-02-15", "2025-03-20"),
            ("Unregistered High-Risk AI System", "High-risk AI system deployed without registration in EU database per AI Act Art. 71", "AI Regulatory", 3, 4, "Open", "AI Ethics Board", "2025-03-01", "2025-03-20"),
            ("AI Fundamental Rights Violation", "AI system negatively impacting fundamental rights (privacy, non-discrimination, due process) without prior impact assessment per AIEU", "AI Governance", 3, 5, "Open", "Chief Privacy Officer", "2025-02-20", "2025-03-15"),
        ],
    )

    # Risk mitigations
    cursor.executemany(
        "INSERT INTO risk_mitigations (risk_id, control_id, strategy, description, status, due_date, completed_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (1, 13, "Mitigate", "Implement vendor security assessment program for all critical vendors", "Completed", "2024-09-01", "2024-08-25"),
            (1, 14, "Mitigate", "Deploy continuous vendor security monitoring", "Planned", "2025-03-01", None),
            (2, 16, "Mitigate", "Implement immutable backups and DR plan", "Completed", "2024-06-01", "2024-05-20"),
            (2, 10, "Mitigate", "Deploy advanced endpoint detection and 24/7 SIEM monitoring", "Completed", "2024-07-01", "2024-06-28"),
            (3, 4, "Mitigate", "Complete consent management implementation across all data processing activities", "In Progress", "2025-02-01", None),
            (3, 5, "Mitigate", "Automate DSAR handling to ensure 30-day SLA", "Completed", "2024-10-01", "2024-09-28"),
            (4, 21, "Mitigate", "Strengthen segregation of duties controls and quarterly testing", "Completed", "2024-09-01", "2024-08-30"),
            (5, 6, "Mitigate", "Enforce MFA and implement user behavior analytics", "In Progress", "2025-01-15", None),
            (5, 9, "Mitigate", "Deploy privileged access management with session recording", "In Progress", "2025-02-01", None),
            (6, 16, "Mitigate", "Multi-region DR with automated failover", "Completed", "2024-06-01", "2024-05-15"),
            (7, 6, "Mitigate", "Phishing-resistant MFA for all executive accounts", "Completed", "2024-10-01", "2024-09-20"),
            (7, None, "Mitigate", "Quarterly executive security awareness training", "In Progress", "2025-03-01", None),
            (9, 9, "Mitigate", "Complete PAM rollout with just-in-time access", "In Progress", "2025-02-01", None),
            (10, 17, "Mitigate", "Expand DR testing to cover all critical systems quarterly", "In Progress", "2025-06-01", None),
            (11, 24, "Mitigate", "Implement AI model risk assessment framework", "Planned", "2025-06-01", None),
            (11, 25, "Mitigate", "Deploy bias testing pipeline for all customer-facing models", "Planned", "2025-06-01", None),
            (12, 20, "Mitigate", "Implement software composition analysis in CI/CD pipeline", "In Progress", "2025-01-15", None),
            # AI-specific mitigations (risk_ids 16-22, control_ids 24-35)
            (16, 30, "Mitigate", "Implement conformity assessment procedures for all high-risk AI systems", "Planned", "2025-09-01", None),
            (16, 26, "Mitigate", "Complete AI system registration in EU database before deployment", "Planned", "2025-06-01", None),
            (17, 28, "Mitigate", "Deploy human oversight mechanisms for all high-risk AI systems", "In Progress", "2025-06-01", None),
            (18, 29, "Mitigate", "Implement AI data governance framework per AI Act requirements", "Planned", "2025-07-01", None),
            (18, 25, "Mitigate", "Deploy bias testing across all AI models", "Planned", "2025-06-01", None),
            (19, 27, "Mitigate", "Implement explainability layer for all customer-facing AI", "In Progress", "2025-06-01", None),
            (19, 32, "Mitigate", "Develop technical documentation per AI Act Annex IV", "In Progress", "2025-07-01", None),
            (20, 35, "Mitigate", "Deploy AI lifecycle compliance tracking system per AICM", "Planned", "2025-09-01", None),
            (20, 34, "Mitigate", "Implement AI post-market monitoring per AICM requirements", "Planned", "2025-08-01", None),
            (21, 26, "Mitigate", "Register all high-risk AI systems in EU database", "Planned", "2025-06-01", None),
            (22, 33, "Mitigate", "Conduct fundamental rights impact assessment for all AI systems", "Planned", "2025-07-01", None),
        ],
    )

    # Audit findings
    cursor.executemany(
        "INSERT INTO audit_findings (control_id, finding, severity, status, identified_date, remediation_due, remediation_owner, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (4, "Consent records missing for 12% of EU customer accounts processed before Q2 2024", "High", "In Remediation", "2024-10-15", "2025-02-01", "Privacy Team", "Retroactive consent campaign underway"),
            (7, "15 dormant accounts with elevated privileges found during quarterly access review", "High", "In Remediation", "2024-12-31", "2025-02-15", "Identity Team", "Accounts disabled, root cause analysis in progress"),
            (9, "PAM solution not covering 3 legacy database admin accounts", "Critical", "Open", "2024-11-20", "2025-01-31", "Identity Team", "Legacy systems require PAM agent update"),
            (12, "Post-mortem reports completed for only 60% of P1 incidents in Q4", "Medium", "In Remediation", "2024-12-15", "2025-03-01", "SOC Team", "Process improvement initiative started"),
            (14, "No continuous monitoring in place for 8 critical SaaS vendors", "High", "Open", "2024-11-01", "2025-03-01", "Vendor Risk Team", "RFP for vendor risk monitoring tool in progress"),
            (17, "Last full DR failover test did not include payment processing systems", "High", "In Remediation", "2024-10-01", "2025-03-15", "Infrastructure Team", "Payment system DR test scheduled for Q1 2025"),
            (8, "Quarterly access review for finance systems completed 2 weeks late", "Medium", "Closed", "2024-09-30", "2024-11-15", "Identity Team", "Process automated to prevent recurrence"),
            (21, "Two instances of same-person initiating and approving journal entries found", "Critical", "In Remediation", "2024-12-01", "2025-01-31", "Finance Operations", "System controls being added to enforce separation"),
            (20, "Emergency changes bypassing CI/CD pipeline increased 40% in Q4", "Medium", "Open", "2024-12-20", "2025-03-01", "DevOps Team", "Reviewing emergency change process"),
            (1, "23 data assets in data warehouse not yet classified per policy", "Medium", "In Remediation", "2024-11-15", "2025-02-01", "Data Governance Team", "Classification sprint planned for January"),
            (24, "No AI model risk assessment framework exists despite 3 models in production", "High", "Open", "2024-12-10", "2025-06-01", "AI Ethics Board", "Framework development starting Q1 2025"),
            (26, "No AI system registration process exists for EU AI Act compliance", "Critical", "Open", "2025-02-15", "2025-06-01", "AI Ethics Board", "Registration process design starting Q2 2025"),
            (27, "AI-powered customer service chatbot provides no explanation for escalation decisions", "High", "Open", "2025-01-20", "2025-06-01", "ML Engineering", "Explainability module in design phase"),
            (28, "Human override capability not available for AI-driven credit scoring system", "Critical", "Open", "2025-02-01", "2025-05-01", "AI Ethics Board", "Override mechanism being designed"),
            (29, "Training data for fraud detection AI not assessed for bias or representativeness", "High", "Open", "2025-02-15", "2025-07-01", "Data Governance Team", "Data audit planned for Q2 2025"),
            (30, "No conformity assessment completed for any AI system despite EU AI Act enforcement", "Critical", "Open", "2025-03-01", "2025-09-01", "AI Ethics Board", "Assessment framework being developed"),
            (33, "No fundamental rights impact assessment conducted for AI hiring tool", "High", "Open", "2025-03-10", "2025-07-01", "AI Ethics Board", "FRIA template being created"),
            (35, "No lifecycle compliance tracking for 5 AI systems in production", "High", "Open", "2025-03-15", "2025-09-01", "AI Ethics Board", "AICM tracking tool evaluation underway"),
        ],
    )

    # Compliance mappings
    cursor.executemany(
        "INSERT INTO compliance_mappings (control_id, framework_id, requirement_ref, compliance_status, last_assessed, evidence_location) VALUES (?, ?, ?, ?, ?, ?)",
        [
            # GDPR mappings
            (1, 1, "Art. 5(1)(f) - Data Integrity & Confidentiality", "Compliant", "2024-12-01", "SharePoint/GRC/GDPR/Art5"),
            (2, 1, "Art. 32 - Security of Processing", "Compliant", "2024-12-01", "SharePoint/GRC/GDPR/Art32"),
            (3, 1, "Art. 32 - Security of Processing", "Compliant", "2024-12-01", "SharePoint/GRC/GDPR/Art32"),
            (4, 1, "Art. 6 & 7 - Lawfulness & Consent", "Partially Compliant", "2024-10-20", "SharePoint/GRC/GDPR/Art6"),
            (5, 1, "Art. 15-22 - Data Subject Rights", "Compliant", "2024-11-01", "SharePoint/GRC/GDPR/Art15"),
            # SOX mappings
            (21, 2, "Section 302 - Corporate Responsibility", "Compliant", "2024-12-01", "SharePoint/GRC/SOX/Sec302"),
            (22, 2, "Section 404 - Internal Controls Assessment", "Compliant", "2024-12-31", "SharePoint/GRC/SOX/Sec404"),
            (23, 2, "Section 404 - Internal Controls Assessment", "Compliant", "2024-12-15", "SharePoint/GRC/SOX/Sec404"),
            (8, 2, "Section 404 - Access Control over Financial Systems", "Compliant", "2024-12-31", "SharePoint/GRC/SOX/Sec404-Access"),
            # HIPAA mappings
            (2, 3, "164.312(a)(2)(iv) - Encryption at Rest", "Compliant", "2024-12-01", "SharePoint/GRC/HIPAA/Encryption"),
            (3, 3, "164.312(e)(1) - Transmission Security", "Compliant", "2024-12-01", "SharePoint/GRC/HIPAA/Transmission"),
            (6, 3, "164.312(d) - Person Authentication", "Compliant", "2024-12-15", "SharePoint/GRC/HIPAA/Auth"),
            (10, 3, "164.308(a)(6) - Security Incident Procedures", "Compliant", "2024-12-20", "SharePoint/GRC/HIPAA/Incident"),
            # ISO 27001 mappings
            (6, 4, "A.8.5 - Secure Authentication", "Compliant", "2024-12-15", "SharePoint/GRC/ISO27001/A8"),
            (7, 4, "A.5.15 - Access Control", "Partially Compliant", "2024-11-20", "SharePoint/GRC/ISO27001/A5"),
            (10, 4, "A.5.24 - Information Security Incident Management", "Compliant", "2024-12-20", "SharePoint/GRC/ISO27001/A5"),
            (16, 4, "A.5.30 - ICT Readiness for Business Continuity", "Compliant", "2024-12-01", "SharePoint/GRC/ISO27001/A5"),
            (19, 4, "A.8.32 - Change Management", "Compliant", "2024-12-15", "SharePoint/GRC/ISO27001/A8"),
            # PCI DSS mappings
            (2, 5, "Req 3.5 - Protect Stored Account Data", "Compliant", "2024-12-01", "SharePoint/GRC/PCI/Req3"),
            (3, 5, "Req 4.1 - Strong Cryptography in Transit", "Compliant", "2024-12-01", "SharePoint/GRC/PCI/Req4"),
            (6, 5, "Req 8.3 - MFA for Access to CDE", "Compliant", "2024-12-15", "SharePoint/GRC/PCI/Req8"),
            (10, 5, "Req 10.6 - Log Monitoring", "Compliant", "2024-12-20", "SharePoint/GRC/PCI/Req10"),
            # NIST CSF mappings
            (10, 6, "DE.CM - Security Continuous Monitoring", "Compliant", "2024-12-20", "SharePoint/GRC/NIST/DE-CM"),
            (11, 6, "RS.RP - Response Planning", "Compliant", "2024-11-30", "SharePoint/GRC/NIST/RS-RP"),
            (16, 6, "RC.RP - Recovery Planning", "Compliant", "2024-12-01", "SharePoint/GRC/NIST/RC-RP"),
            (13, 6, "ID.SC - Supply Chain Risk Management", "Compliant", "2024-11-15", "SharePoint/GRC/NIST/ID-SC"),
            # EU AI Act mappings (framework_id=8)
            (24, 8, "Art. 9 - Risk Management System", "Non-Compliant", "2025-03-01", None),
            (26, 8, "Art. 71 - EU Database Registration", "Non-Compliant", "2025-03-01", None),
            (27, 8, "Art. 13 - Transparency & Information", "Partially Compliant", "2025-01-15", "SharePoint/GRC/AIAct/Art13"),
            (28, 8, "Art. 14 - Human Oversight", "Partially Compliant", "2025-02-01", None),
            (29, 8, "Art. 10 - Data & Data Governance", "Non-Compliant", "2025-02-15", None),
            (30, 8, "Art. 43 - Conformity Assessment", "Non-Compliant", "2025-03-01", None),
            (31, 8, "Art. 62 - Serious Incident Reporting", "Non-Compliant", "2025-03-01", None),
            (32, 8, "Annex IV - Technical Documentation", "Partially Compliant", "2025-02-01", "SharePoint/GRC/AIAct/AnnexIV"),
            (25, 8, "Art. 10(2)(f) - Bias Examination", "Non-Compliant", "2025-03-01", None),
            (33, 8, "Art. 27 - Fundamental Rights Impact Assessment", "Non-Compliant", "2025-03-10", None),
            # AICM mappings (framework_id=9)
            (24, 9, "AICM-RM-01 - AI Risk Classification", "Non-Compliant", "2025-03-01", None),
            (30, 9, "AICM-CA-01 - Conformity Assessment Procedures", "Non-Compliant", "2025-03-01", None),
            (34, 9, "AICM-PM-01 - Post-Market Monitoring", "Non-Compliant", "2025-03-01", None),
            (35, 9, "AICM-LC-01 - Lifecycle Compliance Tracking", "Non-Compliant", "2025-03-15", None),
            (32, 9, "AICM-DOC-01 - Documentation Requirements", "Partially Compliant", "2025-02-01", "SharePoint/GRC/AICM/DOC"),
            (29, 9, "AICM-DG-01 - Data Governance", "Non-Compliant", "2025-02-15", None),
            # AIEU mappings (framework_id=10)
            (27, 10, "AIEU-TR-01 - Transparency & Explainability", "Partially Compliant", "2025-01-15", "SharePoint/GRC/AIEU/TR"),
            (25, 10, "AIEU-FA-01 - Fairness & Non-Discrimination", "Non-Compliant", "2025-03-01", None),
            (28, 10, "AIEU-HO-01 - Human Oversight & Autonomy", "Partially Compliant", "2025-02-01", None),
            (33, 10, "AIEU-FR-01 - Fundamental Rights Protection", "Non-Compliant", "2025-03-10", None),
            (24, 10, "AIEU-AC-01 - Accountability & Governance", "Non-Compliant", "2025-03-01", None),
            (32, 10, "AIEU-RO-01 - Robustness & Safety", "Partially Compliant", "2025-02-01", "SharePoint/GRC/AIEU/RO"),
        ],
    )


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    create_tables(cursor)
    seed_data(cursor)

    conn.commit()

    # Print summary
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("GRC Database created successfully!")
    print(f"Location: {DB_PATH}\n")
    for (table_name,) in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"  {table_name}: {count} rows")

    conn.close()


if __name__ == "__main__":
    main()
