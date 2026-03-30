"""
Module 6: GTM Strategy Generator – Static Knowledge Base
Contains channel benchmarks, domain modifiers, and campaign phase templates.
"""

from app.db.models.gtm_model import BusinessModel

# ── Channel Knowledge Base ───────────────────────────────────────────────────
# Each entry: priority weight, category, reach estimate, cost estimate, tactics

CHANNEL_LIBRARY = {
    "LinkedIn Ads": {
        "category": "paid",
        "best_for": ["b2b", "saas"],
        "reach": "5k–50k impressions/month",
        "cost": "$500–$2,000/month",
        "tactics": [
            "Sponsored InMail to decision-makers",
            "Lead Gen Forms targeting job titles",
            "Thought leadership content promotion"
        ]
    },
    "Google Search Ads": {
        "category": "paid",
        "best_for": ["b2b", "b2c", "saas", "ecommerce"],
        "reach": "10k–100k impressions/month",
        "cost": "$300–$3,000/month",
        "tactics": [
            "Competitor keyword bidding",
            "Problem-aware search terms",
            "Retargeting warm audiences"
        ]
    },
    "Content Marketing / SEO": {
        "category": "organic",
        "best_for": ["b2b", "saas", "b2c"],
        "reach": "Compounding – 1k–50k visits/month at 6 months",
        "cost": "$200–$800/month (tools + time)",
        "tactics": [
            "Long-tail keyword blog posts targeting pain points",
            "Comparison pages (vs. Competitor X)",
            "Free tools / calculators for lead capture"
        ]
    },
    "Product Hunt Launch": {
        "category": "community",
        "best_for": ["saas", "b2b", "b2c"],
        "reach": "500–5,000 upvotes potential",
        "cost": "Free",
        "tactics": [
            "Build hunter network 4 weeks before launch",
            "Prepare launch day email sequence to early adopters",
            "Offer exclusive PH discount code"
        ]
    },
    "Reddit / Niche Communities": {
        "category": "community",
        "best_for": ["b2c", "saas", "marketplace"],
        "reach": "1k–20k engaged users per subreddit",
        "cost": "Free (time investment)",
        "tactics": [
            "Provide value in r/[niche] before promoting",
            "Share 'I built this' posts with demo",
            "Answer questions where your product solves the problem"
        ]
    },
    "Email Marketing": {
        "category": "owned",
        "best_for": ["b2b", "b2c", "saas", "ecommerce"],
        "reach": "Depends on list size – 20–40% open rate",
        "cost": "$0–$100/month (Mailchimp/Brevo free tier)",
        "tactics": [
            "Waitlist nurture sequence (5-email drip)",
            "Weekly value newsletter to build authority",
            "Behavioral trigger emails (onboarding, churn risk)"
        ]
    },
    "Instagram / TikTok Organic": {
        "category": "organic",
        "best_for": ["b2c", "ecommerce", "marketplace"],
        "reach": "500–50,000 followers in 3 months",
        "cost": "Free (content creation time)",
        "tactics": [
            "Behind-the-scenes build-in-public content",
            "Short-form demo videos (15–30 seconds)",
            "User-generated content campaigns"
        ]
    },
    "Partnership / Integrations": {
        "category": "partnership",
        "best_for": ["saas", "b2b", "b2b2c"],
        "reach": "Access to partner's existing user base",
        "cost": "Revenue share or co-marketing budget",
        "tactics": [
            "Identify complementary tools (non-competing)",
            "Co-host webinars or joint content",
            "Marketplace listing (Zapier, Shopify App Store)"
        ]
    },
    "Cold Outreach (Email/LinkedIn)": {
        "category": "outbound",
        "best_for": ["b2b", "saas"],
        "reach": "50–200 qualified prospects/week",
        "cost": "$50–$200/month (tools)",
        "tactics": [
            "Hyper-personalized 3-step email sequence",
            "LinkedIn connection + value message",
            "Case study-led outreach after first customers"
        ]
    },
    "Influencer / Creator Marketing": {
        "category": "paid",
        "best_for": ["b2c", "ecommerce", "marketplace"],
        "reach": "10k–500k per campaign",
        "cost": "$200–$5,000 per creator",
        "tactics": [
            "Micro-influencers (10k–100k) for higher engagement",
            "Affiliate commission model to reduce upfront cost",
            "Product seeding to niche creators"
        ]
    }
}

# ── Domain → Channel Priority Mapping ────────────────────────────────────────
# Maps detected domain to top channel keys (ordered by priority)

DOMAIN_CHANNEL_MAP = {
    "saas": [
        "Content Marketing / SEO",
        "Product Hunt Launch",
        "Cold Outreach (Email/LinkedIn)",
        "LinkedIn Ads",
        "Email Marketing",
        "Reddit / Niche Communities"
    ],
    "b2b": [
        "LinkedIn Ads",
        "Cold Outreach (Email/LinkedIn)",
        "Content Marketing / SEO",
        "Partnership / Integrations",
        "Email Marketing"
    ],
    "b2c": [
        "Instagram / TikTok Organic",
        "Google Search Ads",
        "Email Marketing",
        "Reddit / Niche Communities",
        "Influencer / Creator Marketing"
    ],
    "ecommerce": [
        "Google Search Ads",
        "Instagram / TikTok Organic",
        "Influencer / Creator Marketing",
        "Email Marketing",
        "Reddit / Niche Communities"
    ],
    "marketplace": [
        "Content Marketing / SEO",
        "Reddit / Niche Communities",
        "Partnership / Integrations",
        "Google Search Ads",
        "Email Marketing"
    ],
    "b2b2c": [
        "LinkedIn Ads",
        "Partnership / Integrations",
        "Content Marketing / SEO",
        "Email Marketing",
        "Cold Outreach (Email/LinkedIn)"
    ]
}

# ── Campaign Phase Templates ──────────────────────────────────────────────────
# Phases are scaled to the user's launch_date_weeks

CAMPAIGN_PHASES = [
    {
        "phase": "Pre-Launch Awareness",
        "ratio": 0.30,           # 30% of total timeline
        "objective": "Build brand awareness and grow a warm audience before launch day.",
        "activities": [
            "Publish teaser content and landing page with waitlist",
            "Begin SEO content publishing (3 posts/week)",
            "Seed communities (Reddit, Slack groups, Discord)",
            "Reach out to 20 potential beta users for feedback"
        ],
        "kpis": ["Waitlist signups", "Landing page conversion rate", "Social followers"],
        "budget_pct": 0.20
    },
    {
        "phase": "Beta & Validation Sprint",
        "ratio": 0.25,
        "objective": "Onboard first users, collect feedback, and refine messaging.",
        "activities": [
            "Invite waitlist to closed beta",
            "Run 10 user interviews to validate messaging",
            "A/B test landing page headlines",
            "Set up analytics (Mixpanel / PostHog)"
        ],
        "kpis": ["Beta activation rate", "NPS score", "Feature usage heatmap"],
        "budget_pct": 0.15
    },
    {
        "phase": "Launch Day Blitz",
        "ratio": 0.10,
        "objective": "Maximize visibility and first-day signups across all channels simultaneously.",
        "activities": [
            "Product Hunt / Hacker News launch",
            "Email blast to full waitlist",
            "Paid ad campaigns go live",
            "Founder posts on LinkedIn/Twitter with story"
        ],
        "kpis": ["Day-1 signups", "Product Hunt ranking", "Press mentions"],
        "budget_pct": 0.30
    },
    {
        "phase": "Post-Launch Growth Engine",
        "ratio": 0.35,
        "objective": "Convert launch momentum into sustainable acquisition and retention.",
        "activities": [
            "Optimize paid channels based on launch data",
            "Publish case studies from beta users",
            "Launch referral / affiliate program",
            "Double down on top-performing organic channel"
        ],
        "kpis": ["CAC", "MoM user growth", "Churn rate", "LTV:CAC ratio"],
        "budget_pct": 0.35
    }
]

# ── Tone Map by Business Model ────────────────────────────────────────────────
TONE_MAP = {
    BusinessModel.B2B: "Professional, data-driven, and ROI-focused",
    BusinessModel.B2C: "Friendly, relatable, and benefit-led",
    BusinessModel.SAAS: "Clear, technical-yet-accessible, and outcome-focused",
    BusinessModel.ECOMMERCE: "Aspirational, visual, and urgency-driven",
    BusinessModel.MARKETPLACE: "Trust-building, community-first, and transparent",
    BusinessModel.B2B2C: "Dual-tone: professional for partners, friendly for end users"
}
