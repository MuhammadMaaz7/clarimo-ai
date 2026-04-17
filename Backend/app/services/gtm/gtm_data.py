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
    },
    "Google Maps / Local SEO": {
        "category": "organic",
        "best_for": ["local_business"],
        "reach": "100–1,000 local views/week",
        "cost": "Free",
        "tactics": [
            "Optimize Google Business Profile with high-res photos",
            "Encourage 5-star reviews from first customers",
            "Update location-based keywords in business description"
        ]
    },
    "Physical Marketing (Flyers/Signage)": {
        "category": "traditional",
        "best_for": ["local_business"],
        "reach": "Depends on foot traffic and distribution area",
        "cost": "$50–$300 (printing)",
        "tactics": [
            "In-store signage for initial attraction",
            "Door-to-door flyers in the immediate neighborhood",
            "QR codes on tables/window for digital menu/loyalty"
        ]
    },
    "Hyper-local Social Media": {
        "category": "paid",
        "best_for": ["local_business", "b2c"],
        "reach": "2k–10k local residents",
        "cost": "$100–$500/month",
        "tactics": [
            "Facebook Ads targeting a 2-5 mile radius",
            "Instagram ads with 'Get Directions' CTA",
            "Nextdoor community sponsorship"
        ]
    },
    "Local Partnerships": {
        "category": "partnership",
        "best_for": ["local_business"],
        "reach": "Partner's customer foot traffic",
        "cost": "Free / Barter",
        "tactics": [
            "Cross-promotion vouchers with nearby non-competing shops",
            "Supply products as wholesale to local cafes",
            "Joint local event / street pop-up"
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
    "hardware": [
        "Influencer / Creator Marketing",
        "Reddit / Niche Communities",
        "Google Search Ads",
        "Physical Marketing (Flyers/Signage)",
        "Partnership / Integrations"
    ],
    "b2b2c": [
        "LinkedIn Ads",
        "Partnership / Integrations",
        "Content Marketing / SEO",
        "Email Marketing",
        "Cold Outreach (Email/LinkedIn)"
    ],
    "local_business": [
        "Google Maps / Local SEO",
        "Physical Marketing (Flyers/Signage)",
        "Hyper-local Social Media",
        "Local Partnerships",
        "Instagram / TikTok Organic"
    ]
}

# ── Campaign Phase Templates ──────────────────────────────────────────────────
# Phases are scaled to the user's launch_date_weeks

CAMPAIGN_PHASES = [
    {
        "phase": "Pre-Launch Awareness",
        "ratio": 0.30,
        "objective": "Build brand awareness and local presence.",
        "activities": [
            "Establish digital presence (GMB, Social profiles)",
            "Begin organic content publishing (3 posts/week)",
            "Analyze local competitor foot traffic and pricing",
            "Engage in local community groups / neighborhoods"
        ],
        "kpis": ["Initial followers", "Local brand recall", "Digital profile views"],
        "budget_pct": 0.20
    },
    {
        "phase": "Soft Opening / Beta Test",
        "ratio": 0.25,
        "objective": "Test operations with a small group and gather initial feedback.",
        "activities": [
            "Invite friends, family, and nearby residents for a soft opening",
            "Collect direct feedback on product/service quality",
            "A/B test core offering combinations",
            "Refine operational workflow (delivery, serving, or setup)"
        ],
        "kpis": ["Feedback positivity score", "Return intent", "Operational efficiency"],
        "budget_pct": 0.15
    },
    {
        "phase": "Grand Launch Event",
        "ratio": 0.10,
        "objective": "Create a massive local splash and drive maximum first-day traffic.",
        "activities": [
            "Grand opening event with special offers/discounts",
            "Heavy local signage and physical flyer distribution",
            "Influencer/local blogger visit and review",
            "Social media 'now open' blitz with local hashtags"
        ],
        "kpis": ["First-day foot traffic/orders", "Grand opening revenue", "Social mentions"],
        "budget_pct": 0.30
    },
    {
        "phase": "Sustainable Growth",
        "ratio": 0.35,
        "objective": "Build loyalty and expand local footprint.",
        "activities": [
            "Launch local loyalty / referral program",
            "Optimize local ad spend ( radius targeting)",
            "Forge partnerships with nearby businesses",
            "Encourage and manage online reviews for trust"
        ],
        "kpis": ["Repeat customer rate", "Average transaction value", "Local search ranking"],
        "budget_pct": 0.35
    }
]

LOCAL_CAMPAIGN_PHASES = [
    {
        "phase": "Local Setup & Awareness",
        "ratio": 0.30,
        "objective": "Prepare the physical location and generate local buzz.",
        "activities": [
            "Set up 'Coming Soon' signage at the location",
            "Claim and optimize Google Business Profile",
            "Distribute flyers in the 1-mile radius",
            "Connect with neighboring business owners"
        ],
        "kpis": ["Inquiries", "GMB Profile Views", "Local Group mentions"],
        "budget_pct": 0.25
    },
    {
        "phase": "Soft Opening Sprint",
        "ratio": 0.25,
        "objective": "Test food/service quality with limited local audience.",
        "activities": [
            "Host invite-only tasting/demo sessions",
            "Collect feedback on menu/pricing",
            "Refine kitchen/service workflow",
            "Capture high-quality photos for social media"
        ],
        "kpis": ["Customer Satisfaction", "Dish/Product popularity", "Wait times"],
        "budget_pct": 0.10
    },
    {
        "phase": "Grand Opening Blitz",
        "ratio": 0.10,
        "objective": "Maximize neighborhood foot traffic on launch day.",
        "activities": [
            "Launch Day event with BOGO offers",
            "Banner/Balloon installation at shop front",
            "Nextdoor and Local Facebook Ads go live",
            "Live music or local personality appearance"
        ],
        "kpis": ["Foot traffic count", "Opening day sales", "Google Reviews"],
        "budget_pct": 0.40
    },
    {
        "phase": "Neighborhood Dominance",
        "ratio": 0.35,
        "objective": "Convert one-time visitors into local regulars.",
        "activities": [
            "Implement physical loyalty punch-cards",
            "Weekly 'Neighbor Specials' promotions",
            "Sponsor local school/community events",
            "Optimized hyper-local social ads"
        ],
        "kpis": ["Returning customer rate", "Mouth-to-mouth referrals", "Review score"],
        "budget_pct": 0.25
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
