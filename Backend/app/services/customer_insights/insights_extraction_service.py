"""
Insights Extraction Service - Extract recurring themes, pain points, and desired features
"""
import logging
from typing import List, Dict, Any
from collections import Counter
import re

# Configure logging
logger = logging.getLogger(__name__)

class InsightsExtractionService:
    """Service for extracting insights from discussions"""
    
    def extract_pain_points(self, discussions: List[Dict[str, Any]]) -> List[str]:
        """
        Extract recurring pain points from discussions
        
        Args:
            discussions: List of discussion dictionaries
            
        Returns:
            List of pain points (sorted by frequency)
        """
        try:
            logger.info(f"Extracting pain points from {len(discussions)} discussions...")
            
            pain_keywords = [
                "problem", "issue", "difficult", "hard", "frustrating", "annoying",
                "slow", "expensive", "complicated", "confusing", "broken", "bad",
                "hate", "dislike", "struggle", "challenge", "pain", "trouble",
                "can't", "cannot", "doesn't work", "not working", "fails", "error"
            ]
            
            pain_phrases = []
            
            for discussion in discussions:
                text = f"{discussion.get('title', '')} {discussion.get('content', '')}".lower()
                
                # Look for pain-related phrases
                for keyword in pain_keywords:
                    if keyword in text:
                        # Extract context around keyword
                        pattern = rf'([^.!?]*{re.escape(keyword)}[^.!?]*[.!?])'
                        matches = re.findall(pattern, text)
                        
                        for match in matches:
                            cleaned = match.strip()
                            if len(cleaned) > 20 and len(cleaned) < 200:
                                pain_phrases.append(cleaned)
            
            # Count frequency and return top pain points
            if pain_phrases:
                pain_counter = Counter(pain_phrases)
                top_pains = [pain for pain, count in pain_counter.most_common(15)]
                logger.info(f"Extracted {len(top_pains)} pain points")
                return top_pains
            
            return ["No specific pain points identified"]
            
        except Exception as e:
            logger.error(f"Error extracting pain points: {str(e)}")
            return []
    
    def extract_desired_features(self, discussions: List[Dict[str, Any]]) -> List[str]:
        """
        Extract desired features from discussions
        
        Args:
            discussions: List of discussion dictionaries
            
        Returns:
            List of desired features (sorted by frequency)
        """
        try:
            logger.info(f"Extracting desired features from {len(discussions)} discussions...")
            
            feature_keywords = [
                "want", "need", "looking for", "wish", "hope", "would like",
                "should have", "missing", "lack", "require", "must have",
                "feature request", "add", "include", "support", "integrate"
            ]
            
            feature_phrases = []
            
            for discussion in discussions:
                text = f"{discussion.get('title', '')} {discussion.get('content', '')}".lower()
                
                # Look for feature-related phrases
                for keyword in feature_keywords:
                    if keyword in text:
                        # Extract context around keyword
                        pattern = rf'([^.!?]*{re.escape(keyword)}[^.!?]*[.!?])'
                        matches = re.findall(pattern, text)
                        
                        for match in matches:
                            cleaned = match.strip()
                            if len(cleaned) > 20 and len(cleaned) < 200:
                                feature_phrases.append(cleaned)
            
            # Count frequency and return top features
            if feature_phrases:
                feature_counter = Counter(feature_phrases)
                top_features = [feature for feature, count in feature_counter.most_common(15)]
                logger.info(f"Extracted {len(top_features)} desired features")
                return top_features
            
            return ["No specific feature requests identified"]
            
        except Exception as e:
            logger.error(f"Error extracting desired features: {str(e)}")
            return []
    
    def identify_recurring_themes(self, discussions: List[Dict[str, Any]]) -> List[str]:
        """
        Identify recurring themes from discussions
        
        Args:
            discussions: List of discussion dictionaries
            
        Returns:
            List of recurring themes
        """
        try:
            logger.info(f"Identifying recurring themes from {len(discussions)} discussions...")
            
            # Extract all words from discussions
            all_words = []
            
            for discussion in discussions:
                text = f"{discussion.get('title', '')} {discussion.get('content', '')}".lower()
                
                # Clean and tokenize
                words = re.findall(r'\b[a-z]{4,}\b', text)
                all_words.extend(words)
            
            # Filter out common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
                'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your',
                'his', 'her', 'its', 'our', 'their', 'me', 'him', 'us', 'them',
                'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
                'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
                'only', 'own', 'same', 'than', 'too', 'very', 'just', 'about'
            }
            
            # Count word frequencies
            word_freq = Counter([word for word in all_words if word not in stop_words])
            
            # Get top themes
            top_themes = [word for word, count in word_freq.most_common(20)]
            
            logger.info(f"Identified {len(top_themes)} recurring themes")
            return top_themes
            
        except Exception as e:
            logger.error(f"Error identifying recurring themes: {str(e)}")
            return []
    
    def generate_insight_summary(
        self, 
        pain_points: List[str], 
        features: List[str], 
        themes: List[str]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive insight summary
        
        Args:
            pain_points: List of pain points
            features: List of desired features
            themes: List of recurring themes
            
        Returns:
            Dictionary with insight summary
        """
        try:
            # Extract keywords from themes (top 15)
            keywords = themes[:15] if themes else []
            
            summary = {
                "pain_points": pain_points[:10],  # Top 10 pain points
                "desired_features": features[:10],  # Top 10 features
                "recurring_themes": themes[:10],  # Top 10 themes
                "keywords": keywords
            }
            
            logger.info("Generated insight summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating insight summary: {str(e)}")
            return {
                "pain_points": [],
                "desired_features": [],
                "recurring_themes": [],
                "keywords": []
            }

# Create global instance
insights_extraction_service = InsightsExtractionService()
