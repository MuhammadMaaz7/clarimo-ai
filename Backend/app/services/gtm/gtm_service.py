"""
Module 6: GTM Strategy Generator – Core Service
Hybrid expert system: heuristic layer → LLM hyper-contextualization → fallback.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple

from app.db.models.gtm_model import (
    GTMRequest, GTMResponse, GTMInDB,
    ChannelRecommendation, MessagingGuide, CampaignMilestone, BusinessModel
)
from app.db.database import (
    gtm_strategies_collection,
    validation_results_collection,
    competitor_analyses_collection,
    user_inputs_collection,
    launch_plans_collection
)
from app.core.logging import logger
from app.services.gtm.gtm_llm_synthesizer import GTMLLMSynthesizer
from app.services.gtm.gtm_data import (
    CHANNEL_LIBRARY, DOMAIN_CHANNEL_MAP, CAMPAIGN_PHASES, TONE_MAP
)


class GTMService:
    """
    Go-to-Market Strategy Generator.

    Pipeline:
    1. Gather context from previous modules (optional).
    2. Detect domain/business model for channel selection.
    3. Heuristic channel recommendation (scored + ranked).
    4. Heuristic messaging guide (tone + structure).
    5. Heuristic campaign roadmap (phase-gated timeline).
    6. LLM hyper-contextualization (refine all outputs).
    7. Merge LLM output with heuristics (fallback-safe).
    8. Persist to MongoDB and return response.
    """

    def __init__(self):
        self.synthesizer = GTMLLMSynthesizer()

    async def create_strategy(self, request: GTMRequest) -> GTMResponse:
        gtm_id = str(uuid.uuid4())

        # 1. Context from prior modules
        context = await self._gather_context(request)

        # 2. Domain detection
        domain = self._detect_domain(request.startup_description, request.business_model)

        # 3. Heuristic channels
        heuristic_channels = self._select_channels(domain, request.budget, context)

        # 4. Heuristic messaging
        heuristic_messaging = self._build_messaging_guide(request, context)

        # 5. Heuristic roadmap
        heuristic_roadmap = self._build_campaign_roadmap(request)

        # 6. LLM synthesis
        llm_data = await self.synthesizer.synthesize(
            request_details=request.dict(),
            heuristic_channels=[c.dict() for c in heuristic_channels],
            heuristic_roadmap=[m.dict() for m in heuristic_roadmap],
            context=context
        )

        # 7. Merge: prefer LLM output, fall back to heuristics
        final_channels = self._merge_channels(heuristic_channels, llm_data.get("refined_channels", []))
        final_roadmap = self._merge_roadmap(heuristic_roadmap, llm_data.get("refined_roadmap", []))
        final_messaging = self._merge_messaging(heuristic_messaging, llm_data.get("messaging_guide", {}))

        response = GTMResponse(
            gtm_id=gtm_id,
            user_id=request.user_id or "anonymous",
            executive_summary=llm_data.get("executive_summary") or self._fallback_summary(request),
            channel_recommendations=final_channels,
            messaging_guide=final_messaging,
            campaign_roadmap=final_roadmap,
            positioning_statement=llm_data.get("positioning_statement") or self._fallback_positioning(request),
            target_segment_analysis=llm_data.get("target_segment_analysis") or f"Primary segment: {request.target_audience}.",
            competitive_differentiation=llm_data.get("competitive_differentiation") or "Differentiation analysis pending.",
            risk_factors=llm_data.get("risk_factors") or ["Market timing risk", "Channel saturation", "Budget constraints"],
            success_metrics=llm_data.get("success_metrics") or ["Monthly active users", "CAC < LTV/3", "30-day retention > 40%"],
            created_at=datetime.utcnow()
        )

        # 8. Persist
        doc = GTMInDB(
            **response.dict(),
            inputs=request,
            domain_detected=domain,
            updated_at=datetime.utcnow()
        ).dict()
        gtm_strategies_collection.insert_one(doc)

        return response

    # ── Context Gathering ────────────────────────────────────────────────────

    async def _gather_context(self, request: GTMRequest) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "validation_score": 3.0,
            "competitor_count": 5,
            "pain_points": [],
            "competitor_channels": [],
            "launch_plan_stage": None
        }

        if request.problem_discovery_id:
            doc = user_inputs_collection.find_one({"input_id": request.problem_discovery_id})
            if doc:
                context["pain_points"] = doc.get("extracted_pain_points", [])

        if request.validation_id:
            doc = validation_results_collection.find_one({"validation_id": request.validation_id})
            if doc:
                context["validation_score"] = doc.get("overall_score", 3.0)

        if request.competitor_analysis_id:
            doc = competitor_analyses_collection.find_one({"analysis_id": request.competitor_analysis_id})
            if doc:
                context["competitor_count"] = len(doc.get("competitors", []))
                # Extract any channel hints from competitor insights
                insights = doc.get("insights", {})
                recs = insights.get("recommendations", [])
                context["competitor_channels"] = recs[:3]

        if request.launch_plan_id:
            doc = launch_plans_collection.find_one({"plan_id": request.launch_plan_id})
            if doc:
                context["launch_plan_stage"] = doc.get("inputs", {}).get("product_stage")

        return context

    # ── Domain Detection ─────────────────────────────────────────────────────

    def _detect_domain(self, description: str, business_model: BusinessModel) -> str:
        """Maps business model enum directly; uses keyword fallback for saas."""
        model_map = {
            BusinessModel.B2B: "b2b",
            BusinessModel.B2C: "b2c",
            BusinessModel.B2B2C: "b2b2c",
            BusinessModel.MARKETPLACE: "marketplace",
            BusinessModel.ECOMMERCE: "ecommerce",
            BusinessModel.SAAS: "saas"
        }
        return model_map.get(business_model, "saas")

    # ── Heuristic Channel Selection ──────────────────────────────────────────

    def _select_channels(
        self, domain: str, budget: float, context: Dict[str, Any]
    ) -> List[ChannelRecommendation]:
        """
        Selects top 5 channels for the domain, adjusts priority based on budget.
        Low budget (<$2k) deprioritizes paid channels.
        """
        ordered_keys = DOMAIN_CHANNEL_MAP.get(domain, DOMAIN_CHANNEL_MAP["saas"])
        channels: List[ChannelRecommendation] = []

        for i, key in enumerate(ordered_keys[:6]):
            data = CHANNEL_LIBRARY.get(key)
            if not data:
                continue

            # Budget-aware priority adjustment
            if budget < 2000 and data["category"] == "paid":
                priority = "low"
            elif i == 0:
                priority = "high"
            elif i <= 2:
                priority = "high" if budget >= 3000 else "medium"
            else:
                priority = "medium" if budget >= 1500 else "low"

            channels.append(ChannelRecommendation(
                channel=key,
                category=data["category"],
                priority=priority,
                rationale=f"Strong fit for {domain} businesses targeting {data['best_for']}.",
                estimated_reach=data["reach"],
                estimated_cost=data["cost"],
                tactics=data["tactics"]
            ))

        return channels

    # ── Heuristic Messaging Guide ────────────────────────────────────────────

    def _build_messaging_guide(self, request: GTMRequest, context: Dict[str, Any]) -> MessagingGuide:
        tone = TONE_MAP.get(request.business_model, "Clear and benefit-focused")
        pain_points = context.get("pain_points", [])[:3] or [
            f"Challenges faced by {request.target_audience}",
            "Inefficiency in current solutions",
            "High cost of alternatives"
        ]

        return MessagingGuide(
            headline=f"The smarter way for {request.target_audience} to solve their biggest challenge",
            tagline="Built for results. Designed for you.",
            elevator_pitch=(
                f"We help {request.target_audience} overcome their core challenges "
                f"through {request.startup_description[:80]}. "
                f"Unlike existing solutions, we deliver measurable outcomes faster."
            ),
            tone=tone,
            key_messages=[
                f"Purpose-built for {request.target_audience}",
                "Faster time-to-value than alternatives",
                "Proven ROI from day one",
                "Backed by real user research"
            ],
            differentiators=[
                request.unique_value_proposition or "Unique approach to the problem",
                "Superior user experience",
                "Transparent pricing with no lock-in"
            ],
            pain_points_addressed=pain_points,
            call_to_action="Start your free trial — no credit card required"
        )

    # ── Heuristic Campaign Roadmap ───────────────────────────────────────────

    def _build_campaign_roadmap(self, request: GTMRequest) -> List[CampaignMilestone]:
        """Scales phase durations to the user's launch_date_weeks."""
        total_weeks = max(request.launch_date_weeks, 4)
        milestones: List[CampaignMilestone] = []
        current_week = 1

        for phase in CAMPAIGN_PHASES:
            duration = max(1, int(total_weeks * phase["ratio"]))
            week_end = current_week + duration - 1

            milestones.append(CampaignMilestone(
                phase=phase["phase"],
                week_start=current_week,
                week_end=week_end,
                objective=phase["objective"],
                activities=phase["activities"],
                kpis=phase["kpis"],
                budget_allocation_pct=phase["budget_pct"]
            ))
            current_week = week_end + 1

        return milestones

    # ── Merge Helpers ────────────────────────────────────────────────────────

    def _merge_channels(
        self, heuristic: List[ChannelRecommendation], llm_refined: List[Dict]
    ) -> List[ChannelRecommendation]:
        if not llm_refined:
            return heuristic
        try:
            return [ChannelRecommendation(**c) for c in llm_refined]
        except Exception:
            return heuristic

    def _merge_roadmap(
        self, heuristic: List[CampaignMilestone], llm_refined: List[Dict]
    ) -> List[CampaignMilestone]:
        if not llm_refined:
            return heuristic
        try:
            return [CampaignMilestone(**m) for m in llm_refined]
        except Exception:
            return heuristic

    def _merge_messaging(self, heuristic: MessagingGuide, llm_data: Dict) -> MessagingGuide:
        if not llm_data:
            return heuristic
        try:
            return MessagingGuide(**llm_data)
        except Exception:
            return heuristic

    # ── Fallback Text ────────────────────────────────────────────────────────

    def _fallback_summary(self, request: GTMRequest) -> str:
        return (
            f"This GTM strategy targets {request.target_audience} with a "
            f"{request.business_model.value} approach. "
            f"With a ${request.budget:,.0f} budget over {request.launch_date_weeks} weeks, "
            f"the plan prioritizes high-ROI channels and a phased launch approach."
        )

    def _fallback_positioning(self, request: GTMRequest) -> str:
        return (
            f"For {request.target_audience} who need a better solution, "
            f"our product delivers {request.unique_value_proposition or 'unique value'} "
            f"unlike any existing alternative."
        )
