"""
Pain Point Characteristic Extractor Service
Extracts and formats problem characteristics from pain points
"""

from typing import List, Dict, Any
from app.db.models.pain_points_model import PainPoint
from app.core.logging import logger


class PainPointCharacteristics:
    """Container for pain point characteristics"""
    
    def __init__(self):
        self.problem_titles = []
        self.problem_descriptions = []
        self.key_themes = []
        self.user_quotes = []
        self.affected_user_segments = []
        self.problem_frequency = ""
        self.problem_severity_indicators = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "problem_titles": self.problem_titles,
            "problem_descriptions": self.problem_descriptions,
            "key_themes": self.key_themes,
            "user_quotes": self.user_quotes[:10],  # Limit to 10 quotes
            "affected_user_segments": self.affected_user_segments,
            "problem_frequency": self.problem_frequency,
            "problem_severity_indicators": self.problem_severity_indicators
        }
    
    def to_formatted_string(self) -> str:
        """Convert to formatted string for LLM prompts"""
        lines = []
        
        if self.problem_titles:
            lines.append("Problem Titles:")
            for title in self.problem_titles:
                lines.append(f"  - {title}")
            lines.append("")
        
        if self.problem_descriptions:
            lines.append("Problem Descriptions:")
            for desc in self.problem_descriptions:
                lines.append(f"  - {desc}")
            lines.append("")
        
        if self.key_themes:
            lines.append("Key Themes:")
            for theme in self.key_themes:
                lines.append(f"  - {theme}")
            lines.append("")
        
        if self.user_quotes:
            lines.append("User Quotes (sample):")
            for quote in self.user_quotes[:5]:
                lines.append(f'  - "{quote}"')
            lines.append("")
        
        if self.problem_frequency:
            lines.append(f"Problem Frequency: {self.problem_frequency}")
            lines.append("")
        
        if self.problem_severity_indicators:
            lines.append("Severity Indicators:")
            for indicator in self.problem_severity_indicators:
                lines.append(f"  - {indicator}")
        
        return "\n".join(lines)


class PainPointExtractorService:
    """Service for extracting characteristics from pain points"""
    
    @staticmethod
    def extract_characteristics(pain_points: List[PainPoint]) -> PainPointCharacteristics:
        """
        Extract problem characteristics from pain points
        
        Args:
            pain_points: List of pain points
            
        Returns:
            PainPointCharacteristics object
        """
        characteristics = PainPointCharacteristics()
        
        if not pain_points:
            return characteristics
        
        # Extract titles and descriptions
        for pain_point in pain_points:
            if pain_point.problem_title:
                characteristics.problem_titles.append(pain_point.problem_title)
            
            if pain_point.problem_description:
                characteristics.problem_descriptions.append(pain_point.problem_description)
        
        # Extract user quotes from post references
        for pain_point in pain_points:
            for post_ref in pain_point.post_references[:3]:  # Limit to 3 posts per pain point
                if post_ref.text:
                    # Extract meaningful quotes (sentences with problem indicators)
                    quote = PainPointExtractorService._extract_meaningful_quote(post_ref.text)
                    if quote:
                        characteristics.user_quotes.append(quote)
        
        # Identify key themes
        characteristics.key_themes = PainPointExtractorService._identify_themes(pain_points)
        
        # Determine problem frequency
        total_posts = sum(len(pp.post_references) for pp in pain_points)
        if total_posts > 100:
            characteristics.problem_frequency = "Very frequent (100+ discussions)"
        elif total_posts > 50:
            characteristics.problem_frequency = "Frequent (50+ discussions)"
        elif total_posts > 20:
            characteristics.problem_frequency = "Moderate (20+ discussions)"
        else:
            characteristics.problem_frequency = f"Limited ({total_posts} discussions)"
        
        # Identify severity indicators
        characteristics.problem_severity_indicators = PainPointExtractorService._identify_severity_indicators(pain_points)
        
        # Identify affected user segments
        characteristics.affected_user_segments = PainPointExtractorService._identify_user_segments(pain_points)
        
        return characteristics
    
    @staticmethod
    def _extract_meaningful_quote(text: str, max_length: int = 200) -> str:
        """
        Extract a meaningful quote from post text
        
        Args:
            text: Post text
            max_length: Maximum quote length
            
        Returns:
            Extracted quote or empty string
        """
        # Look for sentences with problem indicators
        problem_keywords = [
            "problem", "issue", "frustrat", "annoying", "difficult",
            "struggle", "pain", "hate", "wish", "need", "want",
            "can't", "cannot", "unable", "impossible", "hard to"
        ]
        
        # Split into sentences
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > max_length:
                continue
            
            # Check if sentence contains problem indicators
            lower_sentence = sentence.lower()
            if any(keyword in lower_sentence for keyword in problem_keywords):
                return sentence
        
        # If no problem-indicating sentence found, return first reasonable sentence
        for sentence in sentences:
            sentence = sentence.strip()
            if 20 <= len(sentence) <= max_length:
                return sentence
        
        return ""
    
    @staticmethod
    def _identify_themes(pain_points: List[PainPoint]) -> List[str]:
        """
        Identify key themes from pain point titles and descriptions
        
        Args:
            pain_points: List of pain points
            
        Returns:
            List of identified themes
        """
        themes = []
        
        # Common theme keywords
        theme_keywords = {
            "time": ["time", "slow", "fast", "quick", "speed", "delay"],
            "cost": ["expensive", "cost", "price", "cheap", "afford", "money"],
            "complexity": ["complex", "complicated", "difficult", "confusing", "hard"],
            "reliability": ["reliable", "crash", "bug", "error", "fail", "broken"],
            "usability": ["easy", "user-friendly", "intuitive", "simple", "ux"],
            "integration": ["integrate", "connect", "sync", "compatible", "work with"],
            "support": ["support", "help", "documentation", "guide", "tutorial"],
            "features": ["feature", "functionality", "capability", "option", "missing"]
        }
        
        # Combine all text
        all_text = " ".join([
            pp.problem_title + " " + pp.problem_description
            for pp in pain_points
        ]).lower()
        
        # Identify themes
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                themes.append(theme.capitalize())
        
        return themes[:5]  # Return top 5 themes
    
    @staticmethod
    def _identify_severity_indicators(pain_points: List[PainPoint]) -> List[str]:
        """
        Identify severity indicators from pain points
        
        Args:
            pain_points: List of pain points
            
        Returns:
            List of severity indicators
        """
        indicators = []
        
        # Count total discussions
        total_posts = sum(len(pp.post_references) for pp in pain_points)
        if total_posts > 50:
            indicators.append(f"High discussion volume ({total_posts} posts)")
        
        # Check for high engagement
        total_upvotes = 0
        total_comments = 0
        post_count = 0
        
        for pain_point in pain_points:
            for post_ref in pain_point.post_references:
                if post_ref.score:
                    total_upvotes += post_ref.score
                if post_ref.num_comments:
                    total_comments += post_ref.num_comments
                post_count += 1
        
        if post_count > 0:
            avg_upvotes = total_upvotes / post_count
            avg_comments = total_comments / post_count
            
            if avg_upvotes > 50:
                indicators.append(f"High community resonance (avg {int(avg_upvotes)} upvotes)")
            
            if avg_comments > 20:
                indicators.append(f"Active discussions (avg {int(avg_comments)} comments)")
        
        # Check for urgency keywords in text
        urgency_keywords = ["urgent", "critical", "immediately", "asap", "desperate", "crucial"]
        all_text = " ".join([
            pp.problem_description + " " + " ".join([pr.text for pr in pp.post_references[:5]])
            for pp in pain_points
        ]).lower()
        
        urgency_count = sum(1 for keyword in urgency_keywords if keyword in all_text)
        if urgency_count > 0:
            indicators.append(f"Urgency expressed in discussions")
        
        return indicators
    
    @staticmethod
    def _identify_user_segments(pain_points: List[PainPoint]) -> List[str]:
        """
        Identify affected user segments from subreddit names and content
        
        Args:
            pain_points: List of pain points
            
        Returns:
            List of user segments
        """
        segments = set()
        
        # Extract subreddits
        subreddits = set()
        for pain_point in pain_points:
            for post_ref in pain_point.post_references:
                subreddits.add(post_ref.subreddit.lower())
        
        # Map subreddits to user segments
        segment_mapping = {
            "entrepreneur": "Entrepreneurs",
            "smallbusiness": "Small Business Owners",
            "startup": "Startup Founders",
            "freelance": "Freelancers",
            "programming": "Developers",
            "webdev": "Web Developers",
            "design": "Designers",
            "marketing": "Marketers",
            "sales": "Sales Professionals",
            "productivity": "Productivity Seekers",
            "student": "Students",
            "teacher": "Educators",
            "fitness": "Fitness Enthusiasts",
            "finance": "Finance Professionals"
        }
        
        for subreddit in subreddits:
            for key, segment in segment_mapping.items():
                if key in subreddit:
                    segments.add(segment)
        
        # If no specific segments identified, use generic
        if not segments:
            segments.add("General Users")
        
        return list(segments)
    
    @staticmethod
    def format_for_solution_fit_analysis(pain_points: List[PainPoint]) -> str:
        """
        Format pain point characteristics specifically for solution fit analysis
        
        Args:
            pain_points: List of pain points
            
        Returns:
            Formatted string for LLM prompt
        """
        characteristics = PainPointExtractorService.extract_characteristics(pain_points)
        
        formatted = f"""
Pain Point Analysis Summary:

Number of Pain Points: {len(pain_points)}
Total Discussions: {sum(len(pp.post_references) for pp in pain_points)}

{characteristics.to_formatted_string()}

Subreddits Mentioned:
"""
        
        # Add subreddit list
        subreddits = set()
        for pain_point in pain_points:
            for post_ref in pain_point.post_references:
                subreddits.add(post_ref.subreddit)
        
        for subreddit in sorted(subreddits):
            formatted += f"  - r/{subreddit}\n"
        
        return formatted
