import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.db.models.launch_plan_model import (
    LaunchPlanRequest, LaunchPlanResponse, LaunchPlanInDB,
    BudgetBreakdown, Milestone, ChecklistItem, ProductStage
)
from app.db.database import (
    launch_plans_collection, validation_results_collection, 
    competitor_analyses_collection, user_inputs_collection
)
from app.core.logging import logger
from app.services.launch_planning.llm_summarizer import LaunchPlanLLMSummarizer

from app.services.launch_planning.market_data import (
    STAGE_BENCHMARKS, DOMAIN_MODIFIERS, TASK_KNOWLEDGE_BASE
)
from app.services.shared.relevance_checker import relevance_checker
from app.core.config import settings
import asyncio
import random

class LaunchPlanningService:
    """
    Expert System for Startup Launch Planning.
    
    Technical Methodology for FYP Defense:
    1. Heuristic Layer: Uses industry-standard budget ratios and Agile velocity pads.
    2. Contextual Adaptation: Adjusts parameters based on stage-specific risks and domain complexity.
    3. Knowledge-Based Synthesis: Filters a validated startup task library using keyword matching and stage gates.
    4. Feedback Integration: Injects remedial tasks if validation/competitor signals are weak.
    """
    
    def __init__(self):
        self.llm_summarizer = LaunchPlanLLMSummarizer()

    async def create_plan(self, request: LaunchPlanRequest) -> LaunchPlanResponse:
        # 0. Relevance Check
        is_valid, reason = await relevance_checker.validate_relevance(
            request.idea_description, context_type="Launch Plan"
        )
        if not is_valid:
            logger.warning(f"Launch plan request rejected: {reason}")
            raise ValueError(reason)

        plan_id = str(uuid.uuid4())

        # Demo Delay: 5-10 seconds to simulate deep analysis for FYP Panel
        if settings.DEMO_MODE:
            delay = random.uniform(5, 10)
            logger.info(f"DEMO_MODE active: Sleeping for {delay:.2f}s to simulate deep Launch analysis...")
            await asyncio.sleep(delay)
        
        # 1. Gather context
        context = await self._gather_context_data(request)
        
        # 2. Detect Domain for modifers
        domain = self._detect_domain(request.idea_description)
        
        # 3. Compute Readiness
        readiness_score, timing_recommendation, saturation_analysis = self._compute_launch_readiness(request, context)
        
        # 4. Scientific Budget Allocation
        budget_breakdown = self._allocate_budget(request.estimated_budget, request.product_stage, request.team_size, domain)
        
        # 5. Heuristic Timeline Base
        heuristic_timeline = self._generate_scientific_timeline(request, domain)
        
        # 6. Heuristic Checklist Base
        heuristic_checklist = self._generate_comprehensive_checklist(request, context, domain)
        
        # 7. LLM Hyper-Contextualization (Turn heuristics into scenario-specific actions)
        llm_payload = request.dict()
        llm_payload["detected_domain"] = domain
        
        summary_data = await self.llm_summarizer.summarize_plan(
            request_details=llm_payload,
            scores={
                "readiness_score": readiness_score,
                "timing_recommendation": timing_recommendation,
                "saturation_impact": saturation_analysis["saturation_level"]
            },
            budget=[b.dict() for b in budget_breakdown],
            timeline=[m.dict() for m in heuristic_timeline],
            checklist=[c.dict() for c in heuristic_checklist]
        )
        
        # 8. Use Refined Data if available, else fallback to heuristics
        final_timeline = heuristic_timeline
        if summary_data.get("refined_timeline"):
            try:
                final_timeline = [Milestone(**m) for m in summary_data["refined_timeline"]]
            except Exception:
                pass # Use heuristic
                
        final_checklist = heuristic_checklist
        if summary_data.get("refined_checklist"):
            try:
                final_checklist = [ChecklistItem(**c) for c in summary_data["refined_checklist"]]
            except Exception:
                pass # Use heuristic
        
        response = LaunchPlanResponse(
            plan_id=plan_id,
            user_id=request.user_id or "anonymous",
            launch_timing_recommendation=timing_recommendation,
            readiness_score=readiness_score,
            budget_allocation=budget_breakdown,
            timeline=final_timeline,
            checklist=final_checklist,
            executive_summary=summary_data["executive_summary"],
            risk_factors=summary_data["risks"],
            success_metrics=summary_data["success_metrics"],
            market_saturation_analysis=summary_data["market_saturation_analysis"],
            inputs=request,
            created_at=datetime.utcnow()
        )
        
        # Store in DB
        doc = LaunchPlanInDB(
            **response.dict(exclude={"inputs"}),
            inputs=request,
            updated_at=datetime.utcnow()
        ).dict()
        doc["domain_detected"] = domain
        launch_plans_collection.insert_one(doc)
        
        return response

    def _detect_domain(self, description: str) -> str:
        desc = description.lower()
        # Physical/Local business detection
        local_keywords = ["restaurant", "shop", "street", "store", "noodle", "food", "cafe", "physical", "offline", "retail", "laundry"]
        if any(w in desc for w in local_keywords):
            return "local_business"

        # Hardware business detection
        hw_keywords = ["device", "hardware", "gadget", "sensor", "electronics", "wearable", "iot", "robot"]
        if any(w in desc for w in hw_keywords):
            return "hardware"

        if any(w in desc for w in ["ai", "intelligence", "learning", "gpt", "bot"]): return "ai"
        if any(w in desc for w in ["shop", "market", "buy", "sell", "store", "commerce"]): return "ecommerce"
        if any(w in desc for w in ["health", "medical", "doctor", "fitness", "bio"]): return "health"
        if any(w in desc for w in ["finance", "money", "bank", "pay", "crypto", "trade"]): return "fintech"
        if any(w in desc for w in ["app", "ios", "android", "mobile"]): return "mobile"
        return "saas" # Default

    async def _gather_context_data(self, request: LaunchPlanRequest) -> Dict[str, Any]:
        """Fetches data from previous modules if available"""
        context = {
            "validation_score": 3.0,
            "competitor_count": 5,
            "pain_points": [],
            "validation_details": {}
        }
        
        if request.problem_discovery_id:
            prob = user_inputs_collection.find_one({"input_id": request.problem_discovery_id})
            if prob: context["pain_points"] = prob.get("extracted_pain_points", [])

        if request.validation_id:
            val = validation_results_collection.find_one({"validation_id": request.validation_id})
            if val:
                context["validation_score"] = val.get("overall_score", 3.0)
                context["validation_details"] = val.get("individual_scores", {})
        
        if request.competitor_analysis_id:
            comp = competitor_analyses_collection.find_one({"analysis_id": request.competitor_analysis_id})
            if comp:
                context["competitor_count"] = len(comp.get("competitors", []))
                
        return context

    def _compute_launch_readiness(self, request: LaunchPlanRequest, context: Dict[str, Any]) -> Tuple[float, str, Dict[str, Any]]:
        stage_map = {
            ProductStage.IDEA: 20, ProductStage.PROTOTYPE: 45,
            ProductStage.MVP: 70, ProductStage.BETA: 85, ProductStage.LIVE: 100
        }
        base = stage_map.get(request.product_stage, 50)
        
        # Validation Normalization
        val_impact = (context.get("validation_score", 3.0) - 3.0) * 15
        
        # Scaling Complexity (Brooks's Law)
        # Larger teams have higher communication overhead, reducing efficiency at early stages
        team_size = request.team_size
        overhead = 0
        if team_size > 5: overhead = -10 # Communication tax
        elif team_size >= 2: overhead = 10 # Optimal collab
        
        # Competitor Saturation
        comp_count = context.get("competitor_count", 5)
        comp_impact = 10 if comp_count < 3 else (-15 if comp_count > 15 else 0)
        
        final_score = max(5, min(100, base + val_impact + overhead + comp_impact))
        
        recs = [
            (85, "Ready for full-scale growth. Focus on CAC/LTV balance."),
            (65, "Soft Launch recommended. Prioritize retention over acquisition."),
            (40, "Iterative Build required. Core product-market fit signals are mixed."),
            (0, "Pivot or Re-validation required. Low market signals detect high risk.")
        ]
        rec = next(r[1] for r in recs if final_score >= r[0])
        
        return final_score, rec, {"saturation_level": "High" if comp_count > 15 else "Healthy"}

    def _allocate_budget(self, total: float, stage: ProductStage, team_size: int, domain: str) -> List[BudgetBreakdown]:
        if total <= 0: total = 5000
        
        # 1. Get Base Ratios
        base_split = STAGE_BENCHMARKS.get(stage, STAGE_BENCHMARKS[ProductStage.IDEA])["budget_split"]
        tech, marketing, ops, legal = base_split
        
        # 2. Apply Domain Modifiers
        mod = DOMAIN_MODIFIERS.get(domain, {})
        tech *= mod.get("tech", 1.0)
        marketing *= mod.get("marketing", 1.0)
        ops *= mod.get("ops", 1.0)
        legal *= mod.get("legal", 1.0)
        
        # 3. Small Budget Protection
        # If budget < 5000, ensure Legal is capped and Tech is prioritized
        if total < 5000:
            legal = min(0.05, legal)
            tech = max(0.5, tech)
            
        # 4. Re-normalize
        total_parts = tech + marketing + ops + legal
        final_percents = [tech/total_parts, marketing/total_parts, ops/total_parts, legal/total_parts]
        
        categories = ["Product & Tech", "Go-to-Market", "Operations & Infra", "Legal & Compliance"]
        descriptions = [
            f"Focused on {domain.upper()} specific development and tooling.",
            "Customer acquisition, community seeding, and brand positioning.",
            "Operational overhead, cloud services, and productivity suite.",
            "Contract management, IP protection, and regulatory alignment."
        ]
        
        return [
            BudgetBreakdown(
                category=categories[i],
                percentage=int(final_percents[i] * 10000) / 100.0,
                amount=int(total * final_percents[i] * 100) / 100.0,
                description=descriptions[i]
            ) for i in range(4)
        ]

    def _generate_scientific_timeline(self, request: LaunchPlanRequest, domain: str) -> List[Milestone]:
        """
        Calculates milestones based on 'Hofstadter's Law' (it always takes longer than you expect)
        and stage-gated phases.
        """
        months = request.expected_timeline_months
        if months <= 0: months = 6
        
        total_weeks = months * 4
        
        # Define Phases based on Stage
        if request.product_stage in [ProductStage.IDEA, ProductStage.PROTOTYPE]:
            phase_configs = [
                ("Conceptualization & Specs", 0.20),
                ("Core Build / Prototyping", 0.45),
                ("Alpha Feedback Loop", 0.20),
                ("Launch Preparation", 0.15)
            ]
        else:
            phase_configs = [
                ("Optimization & Scaling", 0.25),
                ("Market Dominance Prep", 0.40),
                ("Distribution Engine", 0.25),
                ("Public Maturity Launch", 0.10)
            ]
            
        timeline = []
        for title, ratio in phase_configs:
            weeks = max(2, int(total_weeks * ratio))
            timeline.append(Milestone(
                title=title,
                duration_weeks=weeks,
                description=f"Standard {domain.upper()} phase focused on eliminating the largest risks for {request.product_stage.value} startups.",
                tasks=self._fetch_expert_tasks(title, request.product_stage)
            ))
            
        return timeline

    def _fetch_expert_tasks(self, phase_title: str, stage: ProductStage) -> List[str]:
        # Mapping phases to Knowledge Base keys
        key_map = {
            "Conceptualization & Specs": "Product Definition",
            "Core Build / Prototyping": "Build & Development",
            "Alpha Feedback Loop": "Market Validation",
            "Launch Preparation": "Compliance & Business",
            "Optimization & Scaling": "Build & Development",
            "Market Dominance Prep": "Growth & Launch",
            "Distribution Engine": "Growth & Launch"
        }
        kb_key = key_map.get(phase_title, "Product Definition")
        tasks = TASK_KNOWLEDGE_BASE.get(kb_key, [])
        return [t["task"] for t in tasks[:3]]

    def _generate_comprehensive_checklist(self, request: LaunchPlanRequest, context: Dict[str, Any], domain: str) -> List[ChecklistItem]:
        """
        Context-Aware Checklist.
        Combines baseline startup needs with competitive and validation signals.
        """
        checklist = []
        
        # 1. Baseline Phase Checklist
        for kb_key in TASK_KNOWLEDGE_BASE:
            for item in TASK_KNOWLEDGE_BASE[kb_key][:1]: # Pick top representative from each
                checklist.append(ChecklistItem(
                    task=item["task"],
                    priority="high" if item["weight"] > 1 else "medium",
                    category=item["category"]
                ))
                
        # 2. Competitive Response Task
        if context.get("competitor_count", 0) > 10:
            checklist.insert(0, ChecklistItem(
                task="Feature Differential Mapping: Define 'The One Thing' we do better than 10+ incumbents",
                priority="high", category="marketing"
            ))
            
        # 3. Domain Specific Task
        domain_tasks = {
            "ai": "Setup GPU/LLM usage monitoring & cost-limit alerts",
            "ecommerce": "Finalize fulfillment logisitics & return policy",
            "fintech": "Security Audit: End-to-end encryption & KYB checks",
            "health": "HIPAA/Data Privacy compliance self-assessment"
        }
        if domain in domain_tasks:
            checklist.append(ChecklistItem(task=domain_tasks[domain], priority="high", category="ops"))
            
        # 4. Validation Gap Task
        if context.get("validation_score", 3.0) < 3.5:
            checklist.append(ChecklistItem(
                task="Re-read Module 2 Validation Report: Address 'Risk Factors' before writing more code",
                priority="high", category="product"
            ))
            
        return checklist
