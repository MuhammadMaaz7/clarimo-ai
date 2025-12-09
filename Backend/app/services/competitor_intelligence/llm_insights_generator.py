"""
LLM-Based Competitor Analysis Service
Receives pre-processed data and generates insights using LLM
"""

import logging
import os
import json
import re
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class LLMInsightsGenerator:
    """
    Uses LLM to generate competitive analysis insights from pre-processed data
    """
    
    @staticmethod
    def _get_groq_keys() -> List[str]:
        """Get Groq API keys with fallback"""
        keys = []
        primary_key = os.getenv("GROQ_API_KEY")
        if primary_key and "your-api-key" not in primary_key.lower():
            keys.append(primary_key)
        
        for i in range(2, 11):  # Support up to 10 keys
            key = os.getenv(f"GROQ_API_KEY_{i}")
            if key and "your-api-key" not in key.lower():
                keys.append(key)
        
        return keys
    
    @staticmethod
    def _get_openrouter_keys() -> List[str]:
        """Get OpenRouter API keys as fallback"""
        keys = []
        primary_key = os.getenv("OPENROUTER_API_KEY")
        if primary_key and "your-api-key" not in primary_key.lower():
            keys.append(primary_key)
        
        for i in range(2, 6):
            key = os.getenv(f"OPENROUTER_API_KEY_{i}")
            if key and "your-api-key" not in key.lower():
                keys.append(key)
        
        return keys
    
    @staticmethod
    async def generate_competitive_analysis(
        product_info: Dict[str, Any],
        preprocessed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive competitive analysis using LLM with automatic fallback
        NEVER shows API failures to users - always returns a result
        
        Args:
            product_info: User's product information
            preprocessed_data: Pre-processed competitor data from intelligent analysis
            
        Returns:
            Comprehensive analysis with insights (always succeeds)
        """
        logger.info("Generating LLM-based competitive analysis with fallback chain")
        
        try:
            from app.services.shared.llm_service import get_llm_service_for_module3
            
            # Build optimized prompt
            prompt = LLMInsightsGenerator._build_analysis_prompt(product_info, preprocessed_data)
            
            system_prompt = """You are a brutally honest competitive intelligence analyst. Your job is to give REAL, UNBIASED analysis - not to make the user feel good. If their market is saturated, say so. If they have no unique advantages, say so. Use ONLY the data provided. Be specific and factual. Return valid JSON only."""
            
            # Define fallback handler
            def fallback_handler():
                return LLMInsightsGenerator._fallback_analysis(preprocessed_data)
            
            # Call LLM with automatic fallback chain
            llm_service = get_llm_service_for_module3()
            result = await llm_service.call_llm_with_fallback(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=2500,
                response_format="json",
                fallback_handler=fallback_handler
            )
            
            if result["success"]:
                analysis = result["content"]
                analysis['analysis_method'] = result['provider']
                
                if 'note' in result:
                    analysis['note'] = result['note']
                
                logger.info(f"✓ Analysis generated using {result['provider']}")
                return analysis
            else:
                # This should rarely happen due to fallback_handler
                logger.warning("All providers failed, using rule-based fallback")
                return LLMInsightsGenerator._fallback_analysis(preprocessed_data)
            
        except Exception as e:
            logger.error(f"Analysis generation failed: {str(e)}")
            # Always return something - never fail
            return LLMInsightsGenerator._fallback_analysis(preprocessed_data)
    
    @staticmethod
    def _build_analysis_prompt(
        product_info: Dict[str, Any],
        preprocessed_data: Dict[str, Any]
    ) -> str:
        """
        Build domain-agnostic prompt using local insights + top competitors
        """
        stats = preprocessed_data.get('statistics', {})
        top_competitors = preprocessed_data.get('top_competitors', [])[:15]
        all_features = preprocessed_data.get('all_features', [])[:30]
        pricing_info = preprocessed_data.get('pricing_info', [])[:15]
        local_insights = preprocessed_data.get('local_insights', {})
        
        # Build prompt with local analysis summary
        prompt_parts = [
            "You are a competitive intelligence analyst. Analyze the competitive landscape based on the data provided.",
            "",
            "# USER'S PRODUCT",
            f"Name: {product_info.get('name')}",
            f"Description: {product_info.get('description')}",
            f"Features: {json.dumps(product_info.get('features', []))}",
            f"Pricing: {product_info.get('pricing', 'Not specified')}",
            "",
            "# COMPREHENSIVE MARKET ANALYSIS (Local NLP Analysis of ALL Competitors)",
        ]
        
        # Add local insights summary if available
        if local_insights and local_insights.get('summary'):
            prompt_parts.append(local_insights['summary'])
            prompt_parts.append("")
            
            # Add topic insights
            if local_insights.get('topics'):
                prompt_parts.append("DISCOVERED MARKET THEMES:")
                for topic in local_insights['topics']:
                    prompt_parts.append(f"  - {topic['theme']}: {', '.join(topic['keywords'][:5])}")
                prompt_parts.append("")
            
            # Add clustering insights
            clusters = local_insights.get('clusters', {})
            if clusters.get('high_similarity'):
                high_sim = clusters['high_similarity'][:5]
                prompt_parts.append(f"DIRECT COMPETITORS (High Similarity): {', '.join([c['name'] for c in high_sim])}")
            if clusters.get('medium_similarity'):
                med_sim = clusters['medium_similarity'][:5]
                prompt_parts.append(f"INDIRECT COMPETITORS (Medium Similarity): {', '.join([c['name'] for c in med_sim])}")
            prompt_parts.append("")
        else:
            prompt_parts.append(f"Total Competitors Found: {stats.get('total_competitors')}")
            prompt_parts.append(f"Data Sources: {json.dumps(stats.get('sources', {}))}")
            prompt_parts.append("")
        
        # Add top competitors for detailed analysis
        prompt_parts.extend([
            "# TOP COMPETITORS (Detailed Data)",
            LLMInsightsGenerator._format_competitors(top_competitors),
            ""
        ])
        
        # Add feature and pricing data if available
        if all_features:
            prompt_parts.append("# MARKET FEATURES")
            prompt_parts.append(json.dumps(all_features[:20], indent=2))
            prompt_parts.append("")
        
        if pricing_info:
            prompt_parts.append("# MARKET PRICING")
            prompt_parts.append(json.dumps(pricing_info[:10], indent=2))
            prompt_parts.append("")
        
        prompt_parts.extend([
            "# CRITICAL INSTRUCTIONS - BE HONEST AND FACTUAL",
            "",
            "1. USE ONLY DATA PROVIDED - Do NOT invent competitors, features, or information",
            "2. BE HONEST - If the market is saturated, say so. If user's product isn't unique, say so.",
            "3. NO BIAS - Don't make the user feel special if they're not. Give real analysis.",
            "4. BE SPECIFIC - Use actual competitor names and features from the data above",
            "5. IF DATA IS LIMITED - Say 'Limited data available' instead of guessing",
            "6. REAL GAPS ONLY - Only mention opportunities if they're actually missing from competitors",
            "",
            "# REQUIRED ANALYSIS FORMAT",
            "Return ONLY valid JSON with honest, factual analysis:",
            "",
            "{",
            '    "market_position": "Honest assessment: Is this a saturated market? Are there many competitors? Be specific about the competitive landscape.",',
            '    "key_competitors": [',
            '        {"name": "Actual competitor name from data", "description": "What they actually do", "threat_level": "high/medium/low"}',
            '    ],',
            '    "competitive_advantages": [',
            '        "ONLY list advantages if user actually has them based on data. If none, return empty array []"',
            '    ],',
            '    "competitive_threats": [',
            '        "Real threats from actual competitors. Be specific about what makes them strong."',
            '    ],',
            '    "feature_comparison": {',
            '        "unique_features": ["Features ONLY user has - if none, empty array"],',
            '        "missing_features": ["Features competitors have but user lacks - be honest"],',
            '        "common_features": ["Features everyone has"]',
            '    },',
            '    "gap_analysis": {',
            '        "opportunities": [',
            '            "REAL gaps in market based on data. If market is saturated, say: Market appears saturated with established players"',
            '        ],',
            '        "underserved_segments": ["Only if you see actual gaps in the data"]',
            '    },',
            '    "differentiation_strategy": "Honest advice: What would actually make user competitive? If they need major changes, say so.",',
            '    "pricing_strategy": "Based on actual competitor pricing from data",',
            '    "target_audience_insights": "Based on actual competitor target audiences",',
            '    "opportunity_score": {',
            '        "score": 1-10,',
            '        "justification": "Honest score. 1-3 = saturated market, hard to compete. 4-6 = moderate opportunity. 7-10 = good opportunity with clear gaps"',
            '    }',
            "}",
            "",
            "REMEMBER: Be honest. Users need real analysis, not feel-good fluff."
        ])
        
        prompt = '\n'.join(prompt_parts)
        return prompt
    
    @staticmethod
    def _format_competitors(competitors: List[Dict[str, Any]]) -> str:
        """Format competitors for prompt - show actual data"""
        formatted = []
        for i, comp in enumerate(competitors, 1):
            features = comp.get('features', [])
            topics = comp.get('topics', [])
            
            comp_info = [
                f"{i}. **{comp.get('name')}** (Source: {comp.get('source')})"
            ]
            
            # Description
            desc = comp.get('description', '')
            if desc:
                comp_info.append(f"   Description: {desc[:200]}")
            
            # URL
            url = comp.get('url', '')
            if url:
                comp_info.append(f"   URL: {url}")
            
            # Features (if available)
            if features:
                comp_info.append(f"   Features: {', '.join(features[:5])}")
            
            # Topics/Categories (if available)
            if topics:
                comp_info.append(f"   Categories: {', '.join(topics)}")
            
            # Pricing (if available)
            pricing = comp.get('pricing')
            if pricing:
                comp_info.append(f"   Pricing: {pricing}")
            
            # Votes/Stars (if available)
            if comp.get('votes'):
                comp_info.append(f"   Votes: {comp.get('votes')}")
            if comp.get('stars'):
                comp_info.append(f"   Stars: {comp.get('stars')}")
            if comp.get('rating'):
                comp_info.append(f"   Rating: {comp.get('rating')}")
            
            formatted.append('\n'.join(comp_info))
        
        return '\n\n'.join(formatted)
    
    @staticmethod
    def _call_groq(api_key: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Call Groq API (fast and high quality)
        """
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.3-70b-versatile"  # Best balance of speed and quality
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a brutally honest competitive intelligence analyst. Your job is to give REAL, UNBIASED analysis - not to make the user feel good. If their market is saturated, say so. If they have no unique advantages, say so. Use ONLY the data provided. Be specific and factual. Return valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # Very low for factual, unbiased responses
            "max_tokens": 2500
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        output = response.json()["choices"][0]["message"]["content"].strip()
        
        return LLMInsightsGenerator._parse_json_response(output)
    
    @staticmethod
    def _call_openrouter(api_key: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Call OpenRouter API (fallback)
        """
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        model = "google/gemini-2.0-flash-exp:free"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a brutally honest competitive intelligence analyst. Give REAL, UNBIASED analysis based ONLY on provided data. If market is saturated, say so. If user has no advantages, say so. Be specific and factual. Return valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # Very low for factual responses
            "max_tokens": 3000
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        output = response.json()["choices"][0]["message"]["content"].strip()
        
        return LLMInsightsGenerator._parse_json_response(output)
    
    @staticmethod
    def _parse_json_response(output: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response
        """
        try:
            # Remove markdown code blocks if present
            output = re.sub(r'```json\s*', '', output)
            output = re.sub(r'```\s*$', '', output)
            
            data = json.loads(output)
            return data
            
        except json.JSONDecodeError:
            # Try to extract JSON from output
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data
            
            raise Exception("Failed to parse JSON from LLM response")
    
    @staticmethod
    def _assess_analysis_quality(analysis: Dict[str, Any]) -> int:
        """
        Assess the quality of generated analysis (0-10 scale)
        
        Checks:
        - Completeness of required fields
        - Depth of insights (not generic)
        - Specificity (mentions actual competitors/features)
        - Actionability
        
        Returns:
            Quality score (0-10)
        """
        score = 0
        
        # Check 1: Required fields present (2 points)
        required_fields = ['market_position', 'key_competitors', 'competitive_advantages', 
                          'gap_analysis', 'differentiation_strategy']
        present_fields = sum(1 for field in required_fields if analysis.get(field))
        score += (present_fields / len(required_fields)) * 2
        
        # Check 2: Key competitors have details (2 points)
        key_comps = analysis.get('key_competitors', [])
        if key_comps and len(key_comps) >= 2:
            score += 1
            # Check if competitors have descriptions
            if all(comp.get('description') for comp in key_comps[:3]):
                score += 1
        
        # Check 3: Competitive advantages are specific (2 points)
        advantages = analysis.get('competitive_advantages', [])
        if advantages and len(advantages) >= 2:
            score += 1
            # Check if not generic
            generic_terms = ['unique', 'innovative', 'better', 'improved', 'enhanced']
            specific_advantages = [adv for adv in advantages 
                                  if not any(term in adv.lower() for term in generic_terms)]
            if len(specific_advantages) >= 1:
                score += 1
        
        # Check 4: Gap analysis has opportunities (2 points)
        gap = analysis.get('gap_analysis', {})
        opportunities = gap.get('opportunities', [])
        if opportunities and len(opportunities) >= 2:
            score += 1
            # Check if opportunities are specific
            if any(len(opp) > 50 for opp in opportunities):  # Detailed opportunities
                score += 1
        
        # Check 5: Market position is detailed (2 points)
        market_pos = analysis.get('market_position', '')
        if market_pos and len(market_pos) > 100:
            score += 1
            # Check if mentions specific competitors or numbers
            if any(char.isdigit() for char in market_pos):
                score += 1
        
        return min(score, 10)
    
    @staticmethod
    def _fallback_analysis(preprocessed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate basic analysis without LLM
        """
        stats = preprocessed_data.get('statistics', {})
        top_comps = preprocessed_data.get('top_competitors', [])[:5]
        
        return {
            "market_position": f"Operating in a market with {stats.get('total_competitors', 0)} identified competitors across {len(stats.get('sources', {}))} sources.",
            "key_competitors": [
                {
                    "name": comp.get('name', 'Unknown'),
                    "description": comp.get('description', 'No description')[:100],
                    "threat_level": "medium"
                }
                for comp in top_comps[:3]
            ],
            "competitive_advantages": [
                "Unique product positioning",
                "Innovative feature set",
                "Targeted approach"
            ],
            "competitive_threats": [
                f"{stats.get('total_competitors', 0)} competitors in the market",
                "Established market players with user base",
                "Feature parity challenges"
            ],
            "feature_comparison": {
                "unique_features": [],
                "missing_features": [],
                "common_features": []
            },
            "gap_analysis": {
                "opportunities": ["Market research needed for detailed gap analysis"],
                "underserved_segments": ["Further analysis required"]
            },
            "differentiation_strategy": "Focus on unique value proposition and target underserved market segments. Detailed LLM analysis recommended.",
            "pricing_strategy": "Competitive pricing based on market standards. Detailed analysis recommended.",
            "target_audience_insights": "Target users seeking alternatives to existing solutions with better value proposition.",
            "opportunity_score": {
                "score": 6,
                "justification": "Market has competitors but opportunities exist. Detailed LLM analysis recommended for accurate assessment."
            },
            "analysis_method": "fallback",
            "note": "This is a basic analysis. Configure API keys for detailed LLM-powered insights."
        }
