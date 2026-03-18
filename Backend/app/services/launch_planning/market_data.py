from app.db.models.launch_plan_model import ProductStage

# Industry benchmarks for budget allocation by stage
# Format: [Product/Tech, Marketing, Ops, Legal]
STAGE_BENCHMARKS = {
    ProductStage.IDEA: {
        "budget_split": [0.60, 0.20, 0.10, 0.10],
        "focus": "Research & Conceptualization",
        "primary_risk": "Market Validation"
    },
    ProductStage.PROTOTYPE: {
        "budget_split": [0.55, 0.25, 0.10, 0.10],
        "focus": "UI/UX & Core Logic",
        "primary_risk": "Technical Feasibility"
    },
    ProductStage.MVP: {
        "budget_split": [0.45, 0.35, 0.10, 0.10],
        "focus": "User Feedback & Stability",
        "primary_risk": "Product-Market Fit"
    },
    ProductStage.BETA: {
        "budget_split": [0.30, 0.50, 0.10, 0.10],
        "focus": "Growth & Distribution",
        "primary_risk": "Scalability"
    },
    ProductStage.LIVE: {
        "budget_split": [0.20, 0.60, 0.15, 0.05],
        "focus": "Retention & Optimization",
        "primary_risk": "Unit Economics"
    }
}

# Domain-specific multipliers to adjust the budget
# Example: AI startups need more infra, Legal startups need more legal budget
DOMAIN_MODIFIERS = {
    "ai": {"tech": 1.2, "ops": 1.2, "marketing": 0.8},
    "saas": {"tech": 1.0, "marketing": 1.1},
    "ecommerce": {"tech": 0.8, "marketing": 1.3, "ops": 1.2},
    "health": {"legal": 1.5, "tech": 1.1},
    "fintech": {"legal": 1.8, "tech": 1.1},
    "mobile": {"tech": 1.1, "marketing": 1.2}
}

# Extensive library of tasks used to build the roadmap and checklist
# Each task has a "weight" representing complexity/duration
TASK_KNOWLEDGE_BASE = {
    "Product Definition": [
        {"task": "MVP Scope Definition & Feature Prioritization (MoSCoW Method)", "weight": 2, "category": "product"},
        {"task": "User Journey Mapping & Information Architecture (Figma/Whimsical)", "weight": 1, "category": "product"},
        {"task": "Technical Stack Selection & Backend Schema Design", "weight": 2, "category": "technical"},
        {"task": "Success Metrics (KPI) Definition & Benchmarking", "weight": 1, "category": "ops"},
        {"task": "Competitor Feature Gap Analysis & Positioning", "weight": 2, "category": "marketing"}
    ],
    "Build & Development": [
        {"task": "Development Environment Setup & CI/CD Pipeline Implementation", "weight": 2, "category": "technical"},
        {"task": "Core Auth, Database Schema & Security Layer Implementation", "weight": 3, "category": "technical"},
        {"task": "Primary User Workflow & UI Component Development", "weight": 5, "category": "technical"},
        {"task": "Third-party Integration (Payments, Communication, AI APIs)", "weight": 2, "category": "technical"},
        {"task": "Internal API Documentation & Unit Testing (Jest/PyTest)", "weight": 2, "category": "technical"},
        {"task": "End-to-End User Testing & Bug Scrubbing", "weight": 2, "category": "technical"}
    ],
    "Market Validation": [
        {"task": "High-Conversion Landing Page & Waitlist Management Setup", "weight": 1, "category": "marketing"},
        {"task": "Reddit, IndieHackers & Community Outreach Strategy", "weight": 2, "category": "marketing"},
        {"task": "Early Adopter Recruitment (User Interviews & Surveys)", "weight": 2, "category": "ops"},
        {"task": "Initial Feedback Synthesis & Product Pivot Assessment", "weight": 1, "category": "product"},
        {"task": "Content Marketing Calendar & SEO Keyword Research", "weight": 2, "category": "marketing"}
    ],
    "Growth & Launch": [
        {"task": "Product Hunt, Hacker News & Social Media Launch Campaign Prep", "weight": 3, "category": "marketing"},
        {"task": "Performance Marketing Strategy & Paid Ad Funnel Setup", "weight": 2, "category": "marketing"},
        {"task": "Scalability & Load Testing (JMeter/K6)", "weight": 2, "category": "technical"},
        {"task": "Customer Support Workflow & Support Ticket Tooling (Zendesk/Intercom)", "weight": 1, "category": "ops"},
        {"task": "Analytics Mastery: Funnel Analysis & Cohort Retention Tracking", "weight": 2, "category": "product"}
    ],
    "Compliance & Business": [
        {"task": "General Data Protection (GDPR/CCPA) & Privacy Policy Review", "weight": 2, "category": "legal"},
        {"task": "Trademark Registration & Intellectual Property Strategy", "weight": 3, "category": "legal"},
        {"task": "Company Formation, Cap Table & Stakeholder Agreement Setup", "weight": 1, "category": "legal"},
        {"task": "Post-Launch Financial Modeling & Runway Projections", "weight": 1, "category": "ops"}
    ]
}
