"""
HuggingFace Local LLM Service
Runs small LLMs locally on CPU (no GPU required)
Perfect for demos on laptops
"""

import logging
import json
import re
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class HuggingFaceLLMService:
    """
    Local LLM using HuggingFace Transformers (CPU-friendly)
    
    Recommended models for CPU (no GPU):
    - google/flan-t5-small (80MB) - Very fast, good quality
    - google/flan-t5-base (250MB) - Better quality, still fast
    - facebook/opt-350m (350MB) - Good for generation
    """
    
    _pipeline = None
    _model_name = None
    
    @staticmethod
    def is_available() -> bool:
        """Check if transformers is installed"""
        try:
            import transformers
            return True
        except ImportError:
            return False
    
    @staticmethod
    def load_model(model_name: Optional[str] = None):
        """
        Load HuggingFace model (lazy loading)
        """
        if HuggingFaceLLMService._pipeline is not None:
            return HuggingFaceLLMService._pipeline
        
        if not HuggingFaceLLMService.is_available():
            logger.error("transformers not installed. Run: pip install transformers torch")
            return None
        
        try:
            from transformers import pipeline
            import torch
            
            # Default to small, fast model
            model_name = model_name or os.getenv("HF_MODEL", "google/flan-t5-small")
            
            logger.info(f"Loading HuggingFace model: {model_name}")
            
            # Use CPU explicitly
            device = -1  # CPU
            
            # Load pipeline
            HuggingFaceLLMService._pipeline = pipeline(
                "text2text-generation",
                model=model_name,
                device=device,
                max_length=512,
                do_sample=True,
                temperature=0.3
            )
            
            HuggingFaceLLMService._model_name = model_name
            logger.info(f"Model loaded successfully: {model_name}")
            
            return HuggingFaceLLMService._pipeline
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return None
    
    @staticmethod
    async def generate_competitive_analysis(
        product_info: Dict[str, Any],
        preprocessed_data: Dict[str, Any],
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate competitive analysis using HuggingFace model
        
        Args:
            product_info: User's product information
            preprocessed_data: Pre-processed competitor data
            model_name: HuggingFace model to use
            
        Returns:
            Comprehensive analysis
        """
        pipeline = HuggingFaceLLMService.load_model(model_name)
        
        if pipeline is None:
            logger.warning("HuggingFace model not available")
            return None
        
        try:
            logger.info("Generating analysis with HuggingFace model...")
            
            # Build prompts (smaller chunks for CPU models)
            analysis = {}
            
            # 1. Market Position
            market_prompt = HuggingFaceLLMService._build_market_position_prompt(
                product_info, preprocessed_data
            )
            analysis['market_position'] = HuggingFaceLLMService._generate(
                pipeline, market_prompt
            )
            
            # 2. Key Competitors
            analysis['key_competitors'] = HuggingFaceLLMService._extract_key_competitors(
                preprocessed_data
            )
            
            # 3. Competitive Advantages
            advantages_prompt = HuggingFaceLLMService._build_advantages_prompt(
                product_info, preprocessed_data
            )
            advantages_text = HuggingFaceLLMService._generate(pipeline, advantages_prompt)
            analysis['competitive_advantages'] = HuggingFaceLLMService._parse_list(advantages_text)
            
            # 4. Competitive Threats
            threats_prompt = HuggingFaceLLMService._build_threats_prompt(preprocessed_data)
            threats_text = HuggingFaceLLMService._generate(pipeline, threats_prompt)
            analysis['competitive_threats'] = HuggingFaceLLMService._parse_list(threats_text)
            
            # 5. Feature Comparison (from local insights)
            analysis['feature_comparison'] = HuggingFaceLLMService._build_feature_comparison(
                product_info, preprocessed_data
            )
            
            # 6. Gap Analysis
            analysis['gap_analysis'] = HuggingFaceLLMService._build_gap_analysis(
                preprocessed_data
            )
            
            # 7. Differentiation Strategy
            diff_prompt = HuggingFaceLLMService._build_differentiation_prompt(
                product_info, preprocessed_data
            )
            analysis['differentiation_strategy'] = HuggingFaceLLMService._generate(
                pipeline, diff_prompt
            )
            
            # 8. Pricing Strategy
            pricing_prompt = HuggingFaceLLMService._build_pricing_prompt(
                product_info, preprocessed_data
            )
            analysis['pricing_strategy'] = HuggingFaceLLMService._generate(
                pipeline, pricing_prompt
            )
            
            # 9. Target Audience
            audience_prompt = HuggingFaceLLMService._build_audience_prompt(
                product_info, preprocessed_data
            )
            analysis['target_audience_insights'] = HuggingFaceLLMService._generate(
                pipeline, audience_prompt
            )
            
            # 10. Opportunity Score
            analysis['opportunity_score'] = HuggingFaceLLMService._calculate_opportunity_score(
                preprocessed_data
            )
            
            analysis['analysis_method'] = 'huggingface_cpu'
            analysis['model_used'] = HuggingFaceLLMService._model_name
            
            logger.info("HuggingFace analysis complete")
            return analysis
            
        except Exception as e:
            logger.error(f"HuggingFace analysis failed: {str(e)}")
            return None
    
    @staticmethod
    def _generate(pipeline, prompt: str, max_length: int = 150) -> str:
        """Generate text using the pipeline"""
        try:
            result = pipeline(
                prompt,
                max_length=max_length,
                num_return_sequences=1,
                do_sample=True,
                temperature=0.3
            )
            return result[0]['generated_text'].strip()
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            return "Analysis unavailable"
    
    @staticmethod
    def _build_market_position_prompt(product_info: Dict, preprocessed_data: Dict) -> str:
        """Build prompt for market position"""
        local_insights = preprocessed_data.get('local_insights', {})
        summary = local_insights.get('summary', '')[:500]
        
        return f"""Describe the market position of {product_info.get('name')}, a {product_info.get('description')[:100]}.
Market context: {summary}
Position:"""
    
    @staticmethod
    def _build_advantages_prompt(product_info: Dict, preprocessed_data: Dict) -> str:
        """Build prompt for competitive advantages"""
        features = ', '.join(product_info.get('features', [])[:4])
        
        return f"""List 3 competitive advantages of a product with these features: {features}.
Advantages:
1."""
    
    @staticmethod
    def _build_threats_prompt(preprocessed_data: Dict) -> str:
        """Build prompt for competitive threats"""
        stats = preprocessed_data.get('statistics', {})
        total = stats.get('total_competitors', 0)
        
        return f"""List 3 competitive threats in a market with {total} competitors.
Threats:
1."""
    
    @staticmethod
    def _build_differentiation_prompt(product_info: Dict, preprocessed_data: Dict) -> str:
        """Build prompt for differentiation strategy"""
        features = ', '.join(product_info.get('features', [])[:3])
        
        return f"""Suggest a differentiation strategy for a product with: {features}.
Strategy:"""
    
    @staticmethod
    def _build_pricing_prompt(product_info: Dict, preprocessed_data: Dict) -> str:
        """Build prompt for pricing strategy"""
        pricing_info = preprocessed_data.get('pricing_info', [])
        
        if pricing_info:
            sample = pricing_info[0].get('pricing', 'unknown')
            return f"""Recommend pricing strategy. Market example: {sample}.
Recommendation:"""
        else:
            return f"""Recommend pricing strategy for {product_info.get('name')}.
Recommendation:"""
    
    @staticmethod
    def _build_audience_prompt(product_info: Dict, preprocessed_data: Dict) -> str:
        """Build prompt for target audience"""
        desc = product_info.get('description', '')[:100]
        
        return f"""Identify target audience for: {desc}.
Target audience:"""
    
    @staticmethod
    def _extract_key_competitors(preprocessed_data: Dict) -> List[Dict]:
        """Extract key competitors from local insights"""
        local_insights = preprocessed_data.get('local_insights', {})
        clusters = local_insights.get('clusters', {})
        
        key_comps = []
        
        # Get high similarity competitors
        high_sim = clusters.get('high_similarity', [])[:3]
        for comp in high_sim:
            key_comps.append({
                "name": comp['name'],
                "description": f"High similarity competitor (score: {comp['similarity']})",
                "threat_level": "high"
            })
        
        # Get medium similarity
        med_sim = clusters.get('medium_similarity', [])[:2]
        for comp in med_sim:
            key_comps.append({
                "name": comp['name'],
                "description": f"Medium similarity competitor (score: {comp['similarity']})",
                "threat_level": "medium"
            })
        
        return key_comps if key_comps else [
            {"name": "Market competitors", "description": "Various competitors identified", "threat_level": "medium"}
        ]
    
    @staticmethod
    def _build_feature_comparison(product_info: Dict, preprocessed_data: Dict) -> Dict:
        """Build feature comparison from local insights"""
        local_insights = preprocessed_data.get('local_insights', {})
        feature_insights = local_insights.get('feature_insights', {})
        
        product_features = set(product_info.get('features', []))
        market_features = set()
        
        for feat in feature_insights.get('most_common', []):
            market_features.add(feat['feature'])
        
        unique = list(product_features - market_features)
        common = list(product_features & market_features)
        missing = list(market_features - product_features)
        
        return {
            "unique_features": unique[:5],
            "common_features": common[:5],
            "missing_features": missing[:5]
        }
    
    @staticmethod
    def _build_gap_analysis(preprocessed_data: Dict) -> Dict:
        """Build gap analysis from local insights"""
        local_insights = preprocessed_data.get('local_insights', {})
        topics = local_insights.get('topics', [])
        
        opportunities = []
        if topics:
            for topic in topics[:3]:
                opportunities.append(f"Opportunity in {topic['theme']} segment")
        else:
            opportunities = ["Market research needed for detailed gap analysis"]
        
        return {
            "opportunities": opportunities,
            "underserved_segments": ["Further analysis recommended"]
        }
    
    @staticmethod
    def _calculate_opportunity_score(preprocessed_data: Dict) -> Dict:
        """Calculate opportunity score based on local insights"""
        stats = preprocessed_data.get('statistics', {})
        local_insights = preprocessed_data.get('local_insights', {})
        clusters = local_insights.get('clusters', {})
        
        total_comps = stats.get('total_competitors', 0)
        high_sim = len(clusters.get('high_similarity', []))
        
        # Simple scoring logic
        if total_comps == 0:
            score = 9
            justification = "No competitors found - high opportunity"
        elif high_sim == 0:
            score = 8
            justification = "No direct competitors - good opportunity"
        elif high_sim <= 3:
            score = 7
            justification = "Few direct competitors - moderate opportunity"
        elif high_sim <= 5:
            score = 6
            justification = "Several competitors - competitive market"
        else:
            score = 5
            justification = "Many competitors - saturated market"
        
        return {
            "score": score,
            "justification": justification
        }
    
    @staticmethod
    def _parse_list(text: str) -> List[str]:
        """Parse numbered list from generated text"""
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Match numbered items (1. , 2. , etc.)
            match = re.match(r'^\d+[\.\)]\s*(.+)$', line)
            if match:
                items.append(match.group(1).strip())
            elif line and not line.startswith(('Advantages:', 'Threats:', 'Strategy:')):
                items.append(line)
        
        # Return at least 3 items
        while len(items) < 3:
            items.append("Further analysis recommended")
        
        return items[:5]
    
    @staticmethod
    def get_setup_instructions() -> Dict[str, Any]:
        """Get setup instructions"""
        return {
            "install": {
                "command": "pip install transformers torch",
                "note": "No GPU required - runs on CPU"
            },
            "recommended_models": {
                "google/flan-t5-small": {
                    "size": "80MB",
                    "speed": "Very Fast (CPU)",
                    "quality": "Good",
                    "recommended": True
                },
                "google/flan-t5-base": {
                    "size": "250MB",
                    "speed": "Fast (CPU)",
                    "quality": "Better"
                },
                "facebook/opt-350m": {
                    "size": "350MB",
                    "speed": "Moderate (CPU)",
                    "quality": "Good"
                }
            },
            "usage": {
                "set_model": "Set HF_MODEL=google/flan-t5-small in .env",
                "enable": "Set USE_HUGGINGFACE_LLM=true in .env"
            },
            "requirements": {
                "gpu": "Not required",
                "ram": "4GB minimum, 8GB recommended",
                "disk": "500MB for model"
            }
        }
