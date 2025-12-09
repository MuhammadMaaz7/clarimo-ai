"""
Intelligent Competitor Analysis Service
Hybrid approach: Local NLP analysis + LLM for final insights
"""

import logging
from typing import Dict, Any, List, Optional
from collections import Counter
import numpy as np
from .nlp_analysis_engine import NLPAnalysisEngine

logger = logging.getLogger(__name__)


class HybridAnalysisEngine:
    """
    Hybrid analysis approach:
    1. Local NLP/ML analysis on ALL competitors (free, uses all data)
    2. Generate condensed summary
    3. Send summary + top competitors to LLM (efficient token usage)
    """
    
    @staticmethod
    async def analyze_competitors(
        product_info: Dict[str, Any],
        competitors: List[Dict[str, Any]],
        max_competitors_for_llm: int = 15,
        use_local_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Hybrid analysis pipeline
        
        Args:
            product_info: User's product information
            competitors: List of ALL competitors
            max_competitors_for_llm: Max competitors to send to LLM
            use_local_analysis: Whether to use local NLP analysis
            
        Returns:
            Prepared data for LLM analysis with local insights
        """
        logger.info(f"Starting hybrid analysis of {len(competitors)} competitors")
        
        # Step 1: Local Analysis on ALL competitors (free, no API calls)
        local_insights = None
        if use_local_analysis and len(competitors) > 0:
            logger.info("Running local NLP analysis on ALL competitors...")
            local_insights = await NLPAnalysisEngine.analyze_all_competitors(
                product_info=product_info,
                competitors=competitors
            )
            logger.info("Local analysis complete")
        
        # Step 2: Basic Statistics
        stats = HybridAnalysisEngine._get_statistics(competitors)
        
        # Step 3: Rank & Filter Top Competitors for detailed LLM analysis
        top_competitors = HybridAnalysisEngine._rank_and_filter(
            competitors,
            max_competitors_for_llm
        )
        
        # Step 4: Aggregate Features & Pricing
        all_features = HybridAnalysisEngine._aggregate_features(competitors)
        pricing_info = HybridAnalysisEngine._aggregate_pricing(competitors)
        
        logger.info(f"Prepared: Local insights from {len(competitors)} competitors + Top {len(top_competitors)} for LLM")
        
        return {
            "statistics": stats,
            "local_insights": local_insights,  # Comprehensive local analysis
            "all_features": all_features,
            "pricing_info": pricing_info,
            "top_competitors": top_competitors,
            "total_competitors": len(competitors)
        }
    
    @staticmethod
    def _get_statistics(competitors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get basic statistics - domain agnostic
        """
        total = len(competitors)
        
        # Source distribution
        sources = Counter(c.get('source', 'unknown') for c in competitors)
        
        # Data quality stats
        with_description = sum(1 for c in competitors if c.get('description'))
        with_features = sum(1 for c in competitors if c.get('features'))
        with_pricing = sum(1 for c in competitors if c.get('pricing'))
        
        return {
            "total_competitors": total,
            "sources": dict(sources),
            "data_quality": {
                "with_description": with_description,
                "with_features": with_features,
                "with_pricing": with_pricing
            }
        }
    
    @staticmethod
    def _aggregate_features(competitors: List[Dict[str, Any]]) -> List[str]:
        """
        Collect all features from all competitors (for LLM context)
        """
        all_features = []
        for comp in competitors:
            features = comp.get('features', [])
            if features:
                all_features.extend(features)
        
        # Return unique features with frequency
        feature_freq = Counter(all_features)
        return [{"feature": f, "count": c} for f, c in feature_freq.most_common(50)]
    
    @staticmethod
    def _aggregate_pricing(competitors: List[Dict[str, Any]]) -> List[str]:
        """
        Collect all pricing information (for LLM context)
        """
        pricing_list = []
        for comp in competitors:
            pricing = comp.get('pricing')
            if pricing:
                pricing_list.append({
                    "competitor": comp.get('name'),
                    "pricing": str(pricing)
                })
        
        return pricing_list[:20]  # Top 20 for context
    
    @staticmethod
    def _rank_and_filter(
        competitors: List[Dict[str, Any]],
        max_count: int
    ) -> List[Dict[str, Any]]:
        """
        Rank competitors by data quality and filter top N
        """
        scored_competitors = []
        
        for comp in competitors:
            score = 0
            
            # Score based on data completeness
            if comp.get('description'):
                score += 3
            
            if comp.get('features'):
                score += min(len(comp.get('features', [])), 5)
            
            if comp.get('pricing'):
                score += 2
            
            if comp.get('url'):
                score += 1
            
            # Existing relevance score
            if comp.get('relevance_score'):
                score += comp['relevance_score']
            
            scored_competitors.append({
                **comp,
                'quality_score': score
            })
        
        # Sort by score and return top N
        sorted_comps = sorted(scored_competitors, key=lambda x: x['quality_score'], reverse=True)
        return sorted_comps[:max_count]
