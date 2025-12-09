"""
Local Analysis Service
Uses local NLP/ML techniques to analyze ALL competitor data without API calls
Generates summaries and insights that can be sent to LLM for final analysis
"""

import logging
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import LatentDirichletAllocation

logger = logging.getLogger(__name__)


class NLPAnalysisEngine:
    """
    Performs comprehensive local analysis using NLP/ML techniques
    - TF-IDF for keyword extraction
    - Cosine similarity for clustering
    - Topic modeling for theme discovery
    - Statistical analysis
    """
    
    @staticmethod
    async def analyze_all_competitors(
        product_info: Dict[str, Any],
        competitors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze ALL competitors locally and generate comprehensive summary
        
        Args:
            product_info: User's product information
            competitors: ALL competitors (not filtered)
            
        Returns:
            Comprehensive local analysis summary
        """
        logger.info(f"Starting local analysis of {len(competitors)} competitors")
        
        # 1. Extract all text content
        competitor_texts = NLPAnalysisEngine._extract_texts(competitors)
        
        # 2. TF-IDF Analysis - Find important keywords
        tfidf_insights = NLPAnalysisEngine._tfidf_analysis(competitor_texts)
        
        # 3. Topic Modeling - Discover themes
        topics = NLPAnalysisEngine._topic_modeling(competitor_texts)
        
        # 4. Similarity Clustering
        clusters = NLPAnalysisEngine._similarity_clustering(
            product_info, 
            competitors, 
            competitor_texts
        )
        
        # 5. Feature Extraction
        feature_insights = NLPAnalysisEngine._extract_features(competitors)
        
        # 6. Pricing Analysis
        pricing_insights = NLPAnalysisEngine._analyze_pricing(competitors)
        
        # 7. Source Analysis
        source_insights = NLPAnalysisEngine._analyze_sources(competitors)
        
        # 8. Generate Condensed Summary
        summary = NLPAnalysisEngine._generate_summary(
            competitors=competitors,
            tfidf_insights=tfidf_insights,
            topics=topics,
            clusters=clusters,
            feature_insights=feature_insights,
            pricing_insights=pricing_insights,
            source_insights=source_insights
        )
        
        logger.info("Local analysis complete")
        
        return {
            "summary": summary,
            "tfidf_insights": tfidf_insights,
            "topics": topics,
            "clusters": clusters,
            "feature_insights": feature_insights,
            "pricing_insights": pricing_insights,
            "source_insights": source_insights,
            "total_analyzed": len(competitors)
        }
    
    @staticmethod
    def _extract_texts(competitors: List[Dict[str, Any]]) -> List[str]:
        """Extract all text content from competitors"""
        texts = []
        for comp in competitors:
            text_parts = [
                comp.get('name', ''),
                comp.get('description', ''),
                ' '.join(comp.get('features', [])),
                ' '.join(comp.get('topics', [])),
                comp.get('target_audience', '') or '',
                ' '.join(comp.get('key_benefits', []))
            ]
            texts.append(' '.join(filter(None, text_parts)))
        return texts
    
    @staticmethod
    def _tfidf_analysis(texts: List[str]) -> Dict[str, Any]:
        """
        Use TF-IDF to find most important keywords across all competitors
        """
        try:
            if not texts or len(texts) < 2:
                return {"keywords": [], "note": "Insufficient data"}
            
            # TF-IDF vectorization
            vectorizer = TfidfVectorizer(
                max_features=50,
                stop_words='english',
                ngram_range=(1, 2),  # Unigrams and bigrams
                min_df=2  # Must appear in at least 2 documents
            )
            
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get average TF-IDF scores
            avg_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            
            # Sort by importance
            top_indices = avg_scores.argsort()[-20:][::-1]
            top_keywords = [
                {
                    "keyword": feature_names[i],
                    "importance": round(float(avg_scores[i]), 3)
                }
                for i in top_indices
            ]
            
            return {
                "top_keywords": top_keywords,
                "total_keywords": len(feature_names)
            }
            
        except Exception as e:
            logger.error(f"TF-IDF analysis failed: {str(e)}")
            return {"keywords": [], "error": str(e)}
    
    @staticmethod
    def _topic_modeling(texts: List[str], n_topics: int = 5) -> List[Dict[str, Any]]:
        """
        Use LDA to discover hidden topics/themes in competitor descriptions
        """
        try:
            if not texts or len(texts) < 5:
                return []
            
            # Count vectorization (LDA needs count data)
            vectorizer = CountVectorizer(
                max_features=100,
                stop_words='english',
                min_df=2
            )
            
            count_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # LDA topic modeling
            lda = LatentDirichletAllocation(
                n_components=min(n_topics, len(texts) // 2),
                random_state=42,
                max_iter=10
            )
            
            lda.fit(count_matrix)
            
            # Extract topics
            topics = []
            for topic_idx, topic in enumerate(lda.components_):
                top_indices = topic.argsort()[-5:][::-1]
                top_words = [feature_names[i] for i in top_indices]
                
                topics.append({
                    "topic_id": topic_idx + 1,
                    "keywords": top_words,
                    "theme": NLPAnalysisEngine._infer_theme(top_words)
                })
            
            return topics
            
        except Exception as e:
            logger.error(f"Topic modeling failed: {str(e)}")
            return []
    
    @staticmethod
    def _infer_theme(keywords: List[str]) -> str:
        """Infer theme name from keywords"""
        keyword_str = ' '.join(keywords).lower()
        
        themes = {
            "AI & Automation": ["ai", "automation", "intelligent", "smart", "machine"],
            "Health & Wellness": ["health", "fitness", "wellness", "medical", "care"],
            "Productivity": ["productivity", "workflow", "task", "management", "organize"],
            "Analytics & Data": ["analytics", "data", "insights", "metrics", "reporting"],
            "Communication": ["chat", "messaging", "communication", "collaboration", "team"],
            "E-commerce": ["shop", "store", "payment", "commerce", "product"],
            "Education": ["learning", "education", "course", "training", "teach"],
            "Finance": ["finance", "payment", "money", "banking", "investment"]
        }
        
        for theme, theme_keywords in themes.items():
            if any(kw in keyword_str for kw in theme_keywords):
                return theme
        
        return "General"
    
    @staticmethod
    def _similarity_clustering(
        product_info: Dict[str, Any],
        competitors: List[Dict[str, Any]],
        texts: List[str]
    ) -> Dict[str, Any]:
        """
        Cluster competitors by similarity to user's product
        """
        try:
            if len(texts) < 2:
                return {"clusters": []}
            
            # Vectorize
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Product vector
            product_text = ' '.join([
                product_info.get('name', ''),
                product_info.get('description', ''),
                ' '.join(product_info.get('features', []))
            ])
            product_vector = vectorizer.transform([product_text])
            
            # Calculate similarities
            similarities = cosine_similarity(product_vector, tfidf_matrix)[0]
            
            # Categorize
            high_similarity = []
            medium_similarity = []
            low_similarity = []
            
            for i, (comp, sim) in enumerate(zip(competitors, similarities)):
                comp_summary = {
                    "name": comp.get('name'),
                    "similarity": round(float(sim), 3),
                    "source": comp.get('source')
                }
                
                if sim > 0.3:
                    high_similarity.append(comp_summary)
                elif sim > 0.15:
                    medium_similarity.append(comp_summary)
                else:
                    low_similarity.append(comp_summary)
            
            return {
                "high_similarity": sorted(high_similarity, key=lambda x: x['similarity'], reverse=True)[:10],
                "medium_similarity": sorted(medium_similarity, key=lambda x: x['similarity'], reverse=True)[:10],
                "low_similarity_count": len(low_similarity)
            }
            
        except Exception as e:
            logger.error(f"Clustering failed: {str(e)}")
            return {"clusters": []}
    
    @staticmethod
    def _extract_features(competitors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract and analyze features"""
        all_features = []
        for comp in competitors:
            all_features.extend(comp.get('features', []))
        
        if not all_features:
            return {"total": 0, "common": []}
        
        feature_freq = Counter(all_features)
        
        return {
            "total_features": len(all_features),
            "unique_features": len(set(all_features)),
            "most_common": [
                {"feature": f, "count": c}
                for f, c in feature_freq.most_common(15)
            ]
        }
    
    @staticmethod
    def _analyze_pricing(competitors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze pricing patterns"""
        pricing_data = []
        pricing_models = []
        
        for comp in competitors:
            pricing = comp.get('pricing')
            if pricing:
                pricing_str = str(pricing).lower()
                pricing_data.append(pricing_str)
                
                # Categorize
                if 'free' in pricing_str and ('$' in pricing_str or 'paid' in pricing_str):
                    pricing_models.append('freemium')
                elif 'free' in pricing_str:
                    pricing_models.append('free')
                elif 'contact' in pricing_str or 'enterprise' in pricing_str:
                    pricing_models.append('enterprise')
                elif '$' in pricing_str:
                    pricing_models.append('paid')
                else:
                    pricing_models.append('unknown')
        
        # Extract prices
        prices = []
        for p in pricing_data:
            matches = re.findall(r'\$(\d+)', p)
            prices.extend([int(m) for m in matches])
        
        return {
            "models": dict(Counter(pricing_models)),
            "price_range": {
                "min": min(prices) if prices else None,
                "max": max(prices) if prices else None,
                "avg": round(np.mean(prices), 2) if prices else None,
                "median": round(np.median(prices), 2) if prices else None
            },
            "sample_pricing": pricing_data[:10]
        }
    
    @staticmethod
    def _analyze_sources(competitors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data sources"""
        sources = Counter(c.get('source', 'unknown') for c in competitors)
        
        # Quality by source
        quality_by_source = defaultdict(lambda: {"total": 0, "with_features": 0, "with_pricing": 0})
        
        for comp in competitors:
            source = comp.get('source', 'unknown')
            quality_by_source[source]["total"] += 1
            if comp.get('features'):
                quality_by_source[source]["with_features"] += 1
            if comp.get('pricing'):
                quality_by_source[source]["with_pricing"] += 1
        
        return {
            "distribution": dict(sources),
            "quality_by_source": dict(quality_by_source)
        }
    
    @staticmethod
    def _generate_summary(
        competitors: List[Dict[str, Any]],
        tfidf_insights: Dict[str, Any],
        topics: List[Dict[str, Any]],
        clusters: Dict[str, Any],
        feature_insights: Dict[str, Any],
        pricing_insights: Dict[str, Any],
        source_insights: Dict[str, Any]
    ) -> str:
        """
        Generate a condensed text summary of ALL competitor data
        This summary will be sent to LLM instead of raw data
        """
        summary_parts = []
        
        # Overview
        summary_parts.append(f"MARKET OVERVIEW: Analyzed {len(competitors)} competitors from {len(source_insights['distribution'])} sources.")
        
        # Key themes
        if topics:
            theme_names = [t['theme'] for t in topics]
            summary_parts.append(f"MARKET THEMES: {', '.join(set(theme_names))}")
        
        # Important keywords
        if tfidf_insights.get('top_keywords'):
            top_kw = [kw['keyword'] for kw in tfidf_insights['top_keywords'][:10]]
            summary_parts.append(f"KEY MARKET TERMS: {', '.join(top_kw)}")
        
        # Similarity clusters
        high_sim = clusters.get('high_similarity', [])
        if high_sim:
            names = [c['name'] for c in high_sim[:5]]
            summary_parts.append(f"MOST SIMILAR COMPETITORS: {', '.join(names)}")
        
        # Features
        if feature_insights.get('most_common'):
            common_features = [f['feature'] for f in feature_insights['most_common'][:8]]
            summary_parts.append(f"COMMON FEATURES IN MARKET: {', '.join(common_features)}")
        
        # Pricing
        pricing_models = pricing_insights.get('models', {})
        if pricing_models:
            summary_parts.append(f"PRICING MODELS: {dict(pricing_models)}")
        
        price_range = pricing_insights.get('price_range', {})
        if price_range.get('avg'):
            summary_parts.append(f"PRICE RANGE: ${price_range['min']}-${price_range['max']} (avg: ${price_range['avg']})")
        
        # Top competitors with details
        summary_parts.append("\nTOP COMPETITORS:")
        for i, comp in enumerate(competitors[:8], 1):
            comp_line = f"{i}. {comp.get('name')} ({comp.get('source')})"
            if comp.get('description'):
                comp_line += f" - {comp.get('description')[:100]}"
            summary_parts.append(comp_line)
        
        return '\n'.join(summary_parts)
