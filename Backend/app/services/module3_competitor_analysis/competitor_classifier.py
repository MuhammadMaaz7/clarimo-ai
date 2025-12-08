"""
Competitor Classification Service
Classifies competitors as Direct or Indirect based on multiple factors
"""

import logging
from typing import Dict, Any, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class CompetitorClassifier:
    """
    Classifies competitors as Direct or Indirect based on:
    1. Text similarity (TF-IDF + cosine similarity)
    2. Feature overlap
    3. Topic/category overlap
    4. Source matching
    """
    
    # Classification thresholds
    DIRECT_THRESHOLD = 0.25  # Similarity score >= 0.25 = Direct
    INDIRECT_THRESHOLD = 0.10  # Similarity score >= 0.10 = Indirect
    
    @staticmethod
    def classify_competitors(
        product_info: Dict[str, Any],
        competitors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Classify all competitors as direct or indirect
        
        Args:
            product_info: User's product information
            competitors: List of competitor data
            
        Returns:
            List of competitors with competitor_type and similarity_score added
        """
        if not competitors:
            return []
        
        logger.info(f"Classifying {len(competitors)} competitors...")
        
        # Calculate similarity scores
        similarity_scores = CompetitorClassifier._calculate_similarity_scores(
            product_info, 
            competitors
        )
        
        # Classify each competitor
        classified_competitors = []
        for i, competitor in enumerate(competitors):
            similarity_score = similarity_scores[i]
            
            # Calculate feature overlap bonus
            feature_bonus = CompetitorClassifier._calculate_feature_overlap(
                product_info, 
                competitor
            )
            
            # Calculate topic overlap bonus
            topic_bonus = CompetitorClassifier._calculate_topic_overlap(
                product_info, 
                competitor
            )
            
            # Adjust similarity score with bonuses
            adjusted_score = similarity_score + feature_bonus + topic_bonus
            adjusted_score = min(adjusted_score, 1.0)  # Cap at 1.0
            
            # Classify based on adjusted score
            if adjusted_score >= CompetitorClassifier.DIRECT_THRESHOLD:
                competitor_type = "direct"
            elif adjusted_score >= CompetitorClassifier.INDIRECT_THRESHOLD:
                competitor_type = "indirect"
            else:
                competitor_type = "indirect"  # Default to indirect for very low similarity
            
            # Add classification to competitor
            competitor['competitor_type'] = competitor_type
            competitor['similarity_score'] = round(adjusted_score, 3)
            
            classified_competitors.append(competitor)
        
        # Log classification results
        direct_count = sum(1 for c in classified_competitors if c['competitor_type'] == 'direct')
        indirect_count = len(classified_competitors) - direct_count
        
        logger.info(f"Classification complete: {direct_count} direct, {indirect_count} indirect")
        
        return classified_competitors
    
    @staticmethod
    def _calculate_similarity_scores(
        product_info: Dict[str, Any],
        competitors: List[Dict[str, Any]]
    ) -> List[float]:
        """
        Calculate text similarity using TF-IDF and cosine similarity
        """
        try:
            # Extract product text
            product_text = CompetitorClassifier._extract_text(product_info)
            
            # Extract competitor texts
            competitor_texts = [
                CompetitorClassifier._extract_text(comp) 
                for comp in competitors
            ]
            
            # Combine all texts for vectorization
            all_texts = [product_text] + competitor_texts
            
            # TF-IDF vectorization
            vectorizer = TfidfVectorizer(
                max_features=200,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1
            )
            
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Calculate cosine similarity between product and each competitor
            product_vector = tfidf_matrix[0:1]
            competitor_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(product_vector, competitor_vectors)[0]
            
            return similarities.tolist()
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {str(e)}")
            # Return default low similarity scores
            return [0.1] * len(competitors)
    
    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> str:
        """
        Extract all relevant text from product/competitor data
        """
        text_parts = []
        
        # Name (weighted more heavily by repeating)
        name = data.get('product_name') or data.get('name', '')
        if name:
            text_parts.extend([name] * 3)  # Repeat 3x for higher weight
        
        # Description
        description = data.get('product_description') or data.get('description', '')
        if description:
            text_parts.append(description)
        
        # Features
        features = data.get('key_features') or data.get('features', [])
        if features:
            text_parts.extend(features)
        
        # Topics/categories
        topics = data.get('topics', [])
        if topics:
            text_parts.extend(topics)
        
        # Key benefits
        benefits = data.get('key_benefits', [])
        if benefits:
            text_parts.extend(benefits)
        
        # Product type
        product_type = data.get('product_type', '')
        if product_type:
            text_parts.append(product_type)
        
        return ' '.join(filter(None, text_parts))
    
    @staticmethod
    def _calculate_feature_overlap(
        product_info: Dict[str, Any],
        competitor: Dict[str, Any]
    ) -> float:
        """
        Calculate feature overlap bonus (0-0.15)
        More shared features = higher bonus
        """
        product_features = set(
            f.lower() for f in (product_info.get('key_features') or [])
        )
        competitor_features = set(
            f.lower() for f in (competitor.get('features') or [])
        )
        
        if not product_features or not competitor_features:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(product_features & competitor_features)
        union = len(product_features | competitor_features)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        
        # Convert to bonus (max 0.15)
        bonus = jaccard * 0.15
        
        return bonus
    
    @staticmethod
    def _calculate_topic_overlap(
        product_info: Dict[str, Any],
        competitor: Dict[str, Any]
    ) -> float:
        """
        Calculate topic/category overlap bonus (0-0.10)
        Shared topics = higher bonus
        """
        # Extract product topics from description/features
        product_text = (
            product_info.get('product_description', '') + ' ' +
            ' '.join(product_info.get('key_features', []))
        ).lower()
        
        competitor_topics = [
            t.lower() for t in (competitor.get('topics') or [])
        ]
        
        if not competitor_topics:
            return 0.0
        
        # Check how many competitor topics appear in product text
        matching_topics = sum(
            1 for topic in competitor_topics 
            if topic in product_text
        )
        
        if matching_topics == 0:
            return 0.0
        
        # Calculate overlap ratio
        overlap_ratio = matching_topics / len(competitor_topics)
        
        # Convert to bonus (max 0.10)
        bonus = overlap_ratio * 0.10
        
        return bonus
    
    @staticmethod
    def get_classification_summary(
        competitors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get summary statistics of classification
        """
        if not competitors:
            return {
                "total": 0,
                "direct": 0,
                "indirect": 0,
                "direct_percentage": 0,
                "avg_similarity_direct": 0,
                "avg_similarity_indirect": 0
            }
        
        direct_competitors = [
            c for c in competitors 
            if c.get('competitor_type') == 'direct'
        ]
        indirect_competitors = [
            c for c in competitors 
            if c.get('competitor_type') == 'indirect'
        ]
        
        # Calculate average similarities
        avg_sim_direct = 0
        if direct_competitors:
            scores = [c.get('similarity_score', 0) for c in direct_competitors]
            avg_sim_direct = sum(scores) / len(scores)
        
        avg_sim_indirect = 0
        if indirect_competitors:
            scores = [c.get('similarity_score', 0) for c in indirect_competitors]
            avg_sim_indirect = sum(scores) / len(scores)
        
        return {
            "total": len(competitors),
            "direct": len(direct_competitors),
            "indirect": len(indirect_competitors),
            "direct_percentage": round(len(direct_competitors) / len(competitors) * 100, 1),
            "avg_similarity_direct": round(avg_sim_direct, 3),
            "avg_similarity_indirect": round(avg_sim_indirect, 3),
            "top_direct_competitors": [
                {
                    "name": c.get('name'),
                    "similarity": c.get('similarity_score'),
                    "source": c.get('source')
                }
                for c in sorted(
                    direct_competitors, 
                    key=lambda x: x.get('similarity_score', 0), 
                    reverse=True
                )[:5]
            ]
        }
