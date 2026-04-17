"""
Module 6: GTM LLM Synthesizer
Uses the shared UnifiedLLMService to hyper-contextualize heuristic GTM outputs.
"""

import json
from typing import Dict, Any, List
from app.services.shared.llm_service import UnifiedLLMService
from app.core.logging import logger


def get_llm_service_for_module6() -> UnifiedLLMService:
    """GTM module uses Groq first for speed, then OpenRouter as fallback."""
    return UnifiedLLMService(provider_order=["groq", "openrouter", "huggingface"])


class GTMLLMSynthesizer:
    """
    Transforms heuristic GTM data into scenario-specific, human-readable strategy.
    The LLM refines messaging, personalizes channel tactics, and writes the executive summary.
    """

    def __init__(self):
        self.llm = get_llm_service_for_module6()
        self.temperature = 0.4
        self.max_tokens = 2500

    async def synthesize(
        self,
        request_details: Dict[str, Any],
        heuristic_channels: List[Dict],
        heuristic_roadmap: List[Dict],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main synthesis call. Returns refined GTM data from LLM.
        Falls back to heuristic data on any failure.
        """
        # Prepare serializable data
        def to_dict(obj):
            if isinstance(obj, dict): return obj
            if hasattr(obj, 'dict'): return obj.dict()
            if hasattr(obj, 'model_dump'): return obj.model_dump()
            return str(obj)

        channels_data = [to_dict(c) for c in heuristic_channels]
        roadmap_data = [to_dict(m) for m in heuristic_roadmap]

        prompt = self._build_prompt(request_details, channels_data, roadmap_data, context)

        try:
            raw = await self.llm.call_llm(
                prompt=prompt,
                response_format="json",
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            result = json.loads(raw)
            return {
                "executive_summary": result.get("executive_summary", ""),
                "positioning_statement": result.get("positioning_statement", ""),
                "target_segment_analysis": result.get("target_segment_analysis", ""),
                "competitive_differentiation": result.get("competitive_differentiation", ""),
                "messaging_guide": result.get("messaging_guide", {}),
                "refined_channels": result.get("refined_channels", []),
                "refined_roadmap": result.get("refined_roadmap", []),
                "risk_factors": result.get("risk_factors", []),
                "success_metrics": result.get("success_metrics", [])
            }
        except Exception as e:
            logger.error(f"[Module 6] LLM synthesis failed: {e}")
            return {}  # Caller will fall back to heuristics

    def _build_prompt(
        self,
        details: Dict[str, Any],
        channels: List[Dict],
        roadmap: List[Dict],
        context: Dict[str, Any]
    ) -> str:
        return f"""You are an elite Go-to-Market Strategist. Transform the heuristic GTM plan below into a hyper-specific, scenario-aware strategy for this exact startup.

STARTUP CONTEXT:
- Description: {details.get('startup_description')}
- Target Audience: {details.get('target_audience')}
- Unique Value Proposition: {details.get('unique_value_proposition', 'Not specified')}
- Business Model: {details.get('business_model')}
- Budget: ${details.get('budget')}
- Weeks to Launch: {details.get('launch_date_weeks')}
- Validation Score: {context.get('validation_score', 'N/A')}/5
- Competitor Count: {context.get('competitor_count', 'Unknown')}
- Key Pain Points: {', '.join(context.get('pain_points', [])[:3]) or 'Not provided'}
- Detected Domain Type: {details.get('detected_domain', 'Standard Digital')}

HEURISTIC CHANNELS (refine tactics to be idea-specific):
{json.dumps(channels[:4], indent=1)}

HEURISTIC ROADMAP (rewrite activities to be scenario-specific):
{json.dumps(roadmap, indent=1)}

YOUR TASKS (be specific, not generic):
1. EXECUTIVE SUMMARY: 3-4 sentences connecting their budget, audience, and business model.
   - IF THE IDEA IS A PHYSICAL OR LOCAL BUSINESS (e.g. restaurant, gym, retail): STICK RIGIDLY TO PHYSICAL REALITY. UNLEARN software-only patterns. Focus on foot traffic, signage, local permits, community engagement, and regional competition. Do NOT suggest "SaaS", "Subscription", or "Viral Digital Growth" unless it's a hybrid model.
   - IF THE IDEA IS HARDWARE: Focus on product-market fit via physical distribution, manufacturing, and hardware-specific sales cycles.
2. POSITIONING STATEMENT: "For [target audience] who [pain point], [product] is the [category] that [key benefit], unlike [competitor] which [limitation]."
3. TARGET SEGMENT ANALYSIS: 2-3 sentences on who the ideal first 100 customers are and where to find them. (For local businesses, focus on the immediate neighborhood/city/radius).
4. COMPETITIVE DIFFERENTIATION: 2 sentences on the single strongest differentiator.
5. MESSAGING GUIDE: Write a headline, tagline, elevator pitch, tone, 4 key messages, 3 differentiators, 3 pain points addressed, and a CTA — all specific to this startup.
6. REFINED CHANNELS: Rewrite the 'tactics' for each channel to be specific to this startup. 
   - For local businesses, use physical channels: local SEO (Google Maps), flyers, local partnerships, community events, local newspaper/radio if budget allowed.
7. REFINED ROADMAP: Rewrite 'activities' in each phase to be concrete actions for this startup.
   - For local businesses, phases MUST include "Lease/Permit acquisition", "Physical Setup", "Grand Opening", "Local Engagement".
8. RISKS: 3 GTM-specific risks for this business model and market (e.g. supply chain, local competition, zoning).
9. SUCCESS METRICS: 3 KPIs with target values relevant to this startup (e.g. foot traffic, local search rank, average order size).

OUTPUT JSON FORMAT (strict):
{{
  "executive_summary": "...",
  "positioning_statement": "...",
  "target_segment_analysis": "...",
  "competitive_differentiation": "...",
  "messaging_guide": {{
    "headline": "...",
    "tagline": "...",
    "elevator_pitch": "...",
    "tone": "...",
    "key_messages": ["...", "...", "...", "..."],
    "differentiators": ["...", "...", "..."],
    "pain_points_addressed": ["...", "...", "..."],
    "call_to_action": "..."
  }},
  "refined_channels": [
    {{
      "channel": "...",
      "category": "...",
      "priority": "high/medium/low",
      "rationale": "...",
      "estimated_reach": "...",
      "estimated_cost": "...",
      "tactics": ["...", "...", "..."]
    }}
  ],
  "refined_roadmap": [
    {{
      "phase": "...",
      "week_start": 1,
      "week_end": 4,
      "objective": "...",
      "activities": ["...", "...", "..."],
      "kpis": ["...", "..."],
      "budget_allocation_pct": 0.20
    }}
  ],
  "risk_factors": ["...", "...", "..."],
  "success_metrics": ["...", "...", "..."]
}}"""
