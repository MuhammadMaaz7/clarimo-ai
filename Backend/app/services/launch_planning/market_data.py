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
DOMAIN_MODIFIERS = {
    "ai": {"tech": 1.2, "ops": 1.2, "marketing": 0.8},
    "saas": {"tech": 1.0, "marketing": 1.1},
    "ecommerce": {"tech": 0.8, "marketing": 1.3, "ops": 1.2},
    "health": {"legal": 1.5, "tech": 1.1},
    "fintech": {"legal": 1.8, "tech": 1.1},
    "mobile": {"tech": 1.1, "marketing": 1.2},
    "local_business": {"tech": 0.5, "marketing": 1.2, "ops": 1.5, "legal": 1.3},
    "hardware": {"tech": 1.4, "marketing": 0.8, "ops": 1.3, "legal": 1.5}
}

# Extensive library of tasks used to build the roadmap and checklist
TASK_KNOWLEDGE_BASE = {
    "Product Definition": [
        {"task": "MVP Scope Definition & Feature Prioritization (MoSCoW Method)", "weight": 2, "category": "product"},
        {"task": "User Journey Mapping & Information Architecture (Figma/Whimsical)", "weight": 1, "category": "product"},
        {"task": "Physical Location Sourcing & Foot Traffic Analysis", "weight": 2, "category": "ops"},
        {"task": "Menu/Service Offering Design & Initial Pricing Strategy", "weight": 1, "category": "product"},
        {"task": "Technical Stack Selection & Backend Schema Design", "weight": 2, "category": "technical"}
    ],
    "Build & Development": [
        {"task": "Development Environment Setup & CI/CD Pipeline Implementation", "weight": 2, "category": "technical"},
        {"task": "Shop front/Interior Design & Renovation Planning", "weight": 3, "category": "ops"},
        {"task": "POS System selection & Inventory Management setup", "weight": 2, "category": "technical"},
        {"task": "Staff Recruitment, Training & Shift Scheduling", "weight": 2, "category": "ops"},
        {"task": "Hardware Prototyping (CAD Design, 3D Printing, PCB Layout)", "weight": 4, "category": "technical"},
        {"task": "Manufacturing Partner Selection & Supply Chain Sourcing", "weight": 3, "category": "ops"}
    ],
    "Market Validation": [
        {"task": "High-Conversion Landing Page & Waitlist Management Setup", "weight": 1, "category": "marketing"},
        {"task": "Google Business Profile Optimization & Local Maps SEO", "weight": 1, "category": "marketing"},
        {"task": "Local Community Outreach (Facebook Groups, Neighborhood Apps)", "weight": 2, "category": "marketing"},
        {"task": "Early Adopter Recruitment (User Interviews & Surveys)", "weight": 2, "category": "ops"}
    ],
    "Growth & Launch": [
        {"task": "Product Hunt & Social Media Launch Campaign Prep", "weight": 3, "category": "marketing"},
        {"task": "Grand Opening Event Planning & Physical Flyer Blitz", "weight": 2, "category": "marketing"},
        {"task": "Local Influencer/Blogger Visit & Review Campaign", "weight": 2, "category": "marketing"},
        {"task": "Analytics Mastery: Funnel Analysis & Cohort Retention Tracking", "weight": 2, "category": "product"}
    ],
    "Compliance & Business": [
        {"task": "Health & Safety Permits, Food Licenses & Local Regulations", "weight": 3, "category": "legal"},
        {"task": "Business Insurance (Liability, Property) & Local Tax Registration", "weight": 2, "category": "legal"},
        {"task": "Trademark Registration & Intellectual Property Strategy", "weight": 3, "category": "legal"},
        {"task": "Hardware Safety & Compliance Certification (FCC, CE, RoHS)", "weight": 4, "category": "legal"}
    ]
}
