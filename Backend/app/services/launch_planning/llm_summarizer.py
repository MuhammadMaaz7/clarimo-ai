import json
from typing import Dict, Any, List
from app.services.shared.llm_service import get_llm_service_for_module5
from app.core.logging import logger

class LaunchPlanLLMSummarizer:
    def __init__(self):
        self.llm_service = get_llm_service_for_module5()
        self.temperature = 0.4 # Slightly higher for more creative/specific task generation
        self.max_tokens = 2000

    async def summarize_plan(
        self, 
        request_details: Dict[str, Any],
        scores: Dict[str, Any],
        budget: List[Dict[str, Any]],
        timeline: List[Dict[str, Any]],
        checklist: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Uses LLM to hyper-contextualize the plan, turning generic tasks into scenario-specific actions.
        """
        # Prepare serializable data
        def to_dict(obj):
            if isinstance(obj, dict): return obj
            if hasattr(obj, 'dict'): return obj.dict()
            if hasattr(obj, 'model_dump'): return obj.model_dump()
            return str(obj)

        budget_data = [to_dict(b) for b in budget]
        timeline_data = [to_dict(m) for m in timeline]
        checklist_data = [to_dict(c) for c in checklist]

        prompt = self._create_hyper_context_prompt(request_details, scores, budget_data, timeline_data, checklist_data)
        
        try:
            response = await self.llm_service.call_llm(
                prompt=prompt,
                response_format="json",
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            result = json.loads(response)
            return {
                "executive_summary": result.get("executive_summary", "Strategic launch plan generated."),
                "risks": result.get("risks", []),
                "success_metrics": result.get("success_metrics", []),
                "market_saturation_analysis": result.get("market_saturation_analysis", "Market analysis based on competitor data."),
                "refined_timeline": result.get("refined_timeline", []),
                "refined_checklist": result.get("refined_checklist", [])
            }
        except Exception as e:
            logger.error(f"LLM Hyper-Contextualization failed: {str(e)}")
            return {
                "executive_summary": "Heuristic plan generated. Advanced synthesis unavailable.",
                "risks": ["Resource constraints", "Market timing risks"],
                "success_metrics": ["User growth", "Conversion rate"],
                "market_saturation_analysis": "Basic analysis suggests moderate competition."
            }

    def _create_hyper_context_prompt(
        self, 
        details: Dict[str, Any], 
        scores: Dict[str, Any], 
        budget: List[Dict[str, Any]], 
        timeline: List[Dict[str, Any]],
        checklist: List[Dict[str, Any]]
    ) -> str:
        return f"""You are an elite Startup Launch Architect. Your goal is to transform a generic launch plan into a hyper-specific, scenario-aware execution roadmap.

SCENARIO DATA:
- Startup Idea: {details.get('idea_description')}
- Target Audience: {details.get('target_audience', 'N/A')}
- Product Stage: {details.get('product_stage')}
- Budget: ${details.get('estimated_budget')}
- Team Size: {details.get('team_size')}
- Validation Signal: {scores.get('readiness_score')}/100 
- Detected Domain Type: {details.get('detected_domain', 'Standard Digital')}

HEURISTIC DATA (Structure to follow):
TL;DR BUDGET: {json.dumps(budget[:2], indent=1)}
TL;DR TIMELINE: {json.dumps(timeline, indent=1)}
TL;DR CHECKLIST: {json.dumps(checklist[:5], indent=1)}

YOUR TASK (DO NOT BE GENERIC):
1. EXECUTIVE SUMMARY: Write 3-4 professional sentences. Connect their specific budget to their specific idea.
   - IF THE IDEA IS A PHYSICAL OR LOCAL BUSINESS (like a restaurant, noodle shop): Focus on location, physical assets, foot traffic, local marketing, and regulatory permits. 
   - IF THE IDEA IS HARDWARE: Focus on R&D, manufacturing, supply chain, and physical distribution.
   - IF THE IDEA IS SOFTWARE/SAAS: Focus on digital channels, user acquisition, and cloud infrastructure.
2. REFINED TIMELINE: Rewrite the milestone 'tasks' and 'description' to be hyper-specific to the IDEA description. 
   - Example: Instead of "MVP Build", write "Build the [Specific Feature Name] using [Industry Standard Stack]".
   - For physical businesses, tasks must involve physical setup (e.g., "Lease negotiation", "Interior renovation", "Kitchen equipment procurement").
3. REFINED CHECKLIST: Rewrite the 'task' names to be direct actions for this idea. 
   - Handle Edge Cases: If it's a regulated industry (Health/Fintech), add compliance specific tasks. If it's a physical business, add local licensing/permit tasks.
4. RISKS & METRICS: Identify 3 risks and 3 KPIs that ONLY apply to this specific business model.

OUTPUT JSON FORMAT:
{{
  "executive_summary": "...",
  "risks": ["...", "...", "..."],
  "success_metrics": ["...", "...", "..."],
  "market_saturation_analysis": "...",
  "refined_timeline": [
      {{
          "title": "Phase Title",
          "duration_weeks": 4,
          "description": "Scenario-specific description...",
          "tasks": ["Specific Task A", "Specific Task B"]
      }}
  ],
  "refined_checklist": [
      {{
          "task": "Hyper-specific task name",
          "priority": "high/medium/low",
          "category": "marketing/ops/tech/legal"
      }}
  ]
}}
"""
