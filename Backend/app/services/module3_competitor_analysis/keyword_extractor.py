"""
Keyword Extractor for Competitor Analysis
Extracts relevant search keywords from product information
"""

import re
from typing import List, Set


class CompetitorKeywordExtractor:
    """Extract keywords for competitor search"""
    
    # Common stop words to exclude
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'you', 'your', 'our', 'we', 'they',
        'this', 'these', 'those', 'can', 'could', 'would', 'should'
    }
    
    # Technology and product keywords (high value)
    TECH_KEYWORDS = {
        'ai', 'ml', 'machine learning', 'artificial intelligence',
        'automation', 'smart', 'intelligent', 'cloud', 'saas',
        'platform', 'app', 'software', 'tool', 'service', 'solution',
        'api', 'mobile', 'web', 'desktop', 'analytics', 'dashboard',
        'real-time', 'realtime', 'collaborative', 'integration'
    }
    
    # Category keywords
    CATEGORY_KEYWORDS = {
        'productivity', 'management', 'tracking', 'monitoring',
        'planning', 'scheduling', 'organization', 'collaboration',
        'communication', 'workflow', 'automation', 'optimization',
        'analysis', 'reporting', 'visualization', 'security',
        'finance', 'health', 'fitness', 'education', 'learning',
        'social', 'entertainment', 'gaming', 'shopping', 'travel'
    }
    
    @staticmethod
    def extract_keywords(
        product_name: str,
        product_description: str,
        key_features: List[str],
        max_keywords: int = 5
    ) -> List[str]:
        """
        Extract relevant keywords for competitor search
        IMPROVED: Preserves meaningful phrases instead of just single words
        
        Args:
            product_name: Name of the product
            product_description: Description of the product
            key_features: List of key features
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of keywords for search (can include phrases)
        """
        keywords: List[str] = []
        
        # 1. FIRST: Try to extract product category from name
        # e.g., "CodeSnippetVault" -> "code snippet"
        # e.g., "TaskMaster" -> "task"
        name_phrases = CompetitorKeywordExtractor._extract_phrases_from_name(product_name)
        keywords.extend(name_phrases)
        
        # 2. Extract key noun phrases from description (2-3 word combinations)
        desc_phrases = CompetitorKeywordExtractor._extract_noun_phrases(product_description)
        keywords.extend(desc_phrases[:3])  # Top 3 phrases
        
        # 3. Extract category keywords from description
        desc_lower = product_description.lower()
        for category_keyword in CompetitorKeywordExtractor.CATEGORY_KEYWORDS:
            if category_keyword in desc_lower:
                keywords.append(category_keyword)
        
        # 4. Extract specific feature-related terms
        for feature in key_features[:3]:  # Top 3 features
            feature_lower = feature.lower()
            # Look for specific patterns like "X editor", "X manager", "X tool"
            if any(term in feature_lower for term in ['editor', 'manager', 'tool', 'tracker', 'organizer']):
                # Extract the phrase
                words = CompetitorKeywordExtractor._extract_words(feature)
                if len(words) >= 2:
                    keywords.append(f"{words[0]} {words[1]}".lower())
        
        # 5. Fallback: Extract important single words if we don't have enough
        if len(keywords) < 3:
            desc_words = CompetitorKeywordExtractor._extract_words(product_description)
            for word in desc_words[:30]:
                word_lower = word.lower()
                if (len(word) > 5 and 
                    word_lower not in CompetitorKeywordExtractor.STOP_WORDS and
                    word_lower not in {'software', 'application', 'platform', 'service', 'product', 'solution'} and
                    word.isalpha()):
                    keywords.append(word_lower)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        # Prioritize keywords
        prioritized = CompetitorKeywordExtractor._prioritize_keywords(
            unique_keywords,
            product_description.lower()
        )
        
        # Return top keywords
        return prioritized[:max_keywords]
    
    @staticmethod
    def _extract_phrases_from_name(product_name: str) -> List[str]:
        """
        Extract meaningful phrases from product name
        e.g., "CodeSnippetVault" -> ["code snippet", "snippet vault"]
        e.g., "TaskMaster" -> ["task manager"]
        """
        phrases = []
        
        # Split camelCase or PascalCase
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', product_name)
        
        if len(words) >= 2:
            # Combine consecutive words
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i+1]}".lower()
                phrases.append(phrase)
        
        # Also add individual meaningful words
        for word in words:
            if len(word) > 4 and word.lower() not in CompetitorKeywordExtractor.STOP_WORDS:
                phrases.append(word.lower())
        
        return phrases
    
    @staticmethod
    def _extract_noun_phrases(text: str) -> List[str]:
        """
        Extract meaningful noun phrases (2-3 words)
        e.g., "code snippet manager", "task management tool"
        """
        phrases = []
        words = CompetitorKeywordExtractor._extract_words(text)
        
        # Look for patterns: [adjective/noun] + [noun] + [optional: tool/app/manager]
        tool_words = {'tool', 'app', 'manager', 'editor', 'tracker', 'organizer', 'platform', 'software'}
        
        for i in range(len(words) - 1):
            word1 = words[i].lower()
            word2 = words[i+1].lower()
            
            # Skip if either word is a stop word or too short
            if (word1 in CompetitorKeywordExtractor.STOP_WORDS or 
                word2 in CompetitorKeywordExtractor.STOP_WORDS or
                len(word1) < 3 or len(word2) < 3):
                continue
            
            # 2-word phrase
            phrase = f"{word1} {word2}"
            phrases.append(phrase)
            
            # 3-word phrase if next word is a tool word
            if i + 2 < len(words):
                word3 = words[i+2].lower()
                if word3 in tool_words:
                    phrase3 = f"{word1} {word2} {word3}"
                    phrases.append(phrase3)
        
        return phrases
    
    @staticmethod
    def _extract_words(text: str) -> List[str]:
        """Extract words from text"""
        # Remove special characters and split
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        return words
    
    @staticmethod
    def _prioritize_keywords(keywords: List[str], description: str) -> List[str]:
        """
        Prioritize keywords based on relevance
        
        Priority order:
        1. Tech keywords (AI, ML, etc.)
        2. Category keywords (productivity, management, etc.)
        3. Words that appear multiple times
        4. Longer words (more specific)
        """
        scored_keywords = []
        
        for keyword in keywords:
            score = 0
            
            # Tech keywords get highest priority
            if keyword in CompetitorKeywordExtractor.TECH_KEYWORDS:
                score += 100
            
            # Category keywords get high priority
            if keyword in CompetitorKeywordExtractor.CATEGORY_KEYWORDS:
                score += 50
            
            # Frequency in description
            score += description.count(keyword) * 10
            
            # Length (longer = more specific)
            score += len(keyword)
            
            scored_keywords.append((keyword, score))
        
        # Sort by score descending
        scored_keywords.sort(key=lambda x: x[1], reverse=True)
        
        return [kw for kw, score in scored_keywords]
    
    @staticmethod
    def extract_category(product_description: str) -> str:
        """
        Extract product category from description
        
        Returns:
            Category string (e.g., "productivity", "health", "finance")
        """
        desc_lower = product_description.lower()
        
        # Check for category keywords
        for category in CompetitorKeywordExtractor.CATEGORY_KEYWORDS:
            if category in desc_lower:
                return category
        
        return "general"
