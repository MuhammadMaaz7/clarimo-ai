"""
Google Search Service for Competitor Discovery
Uses Google Custom Search API to find competitors
"""

import requests
import os
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


class GoogleSearchService:
    """Service for discovering competitors via Google Search"""
    
    API_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self):
        # Load multiple API keys for fallback
        self.api_keys = self._load_api_keys()
        self.search_engine_ids = self._load_search_engine_ids()
        self.timeout = 15.0
        self.current_key_index = 0
        self.current_engine_index = 0
    
    def _load_api_keys(self) -> List[str]:
        """Load all available Google API keys"""
        keys = []
        
        # Primary key
        primary_key = os.getenv("GOOGLE_API_KEY")
        if primary_key and "your-api-key" not in primary_key.lower():
            keys.append(primary_key)
        
        # Fallback keys (GOOGLE_API_KEY_2, GOOGLE_API_KEY_3, etc.)
        for i in range(2, 11):  # Support up to 10 keys
            key = os.getenv(f"GOOGLE_API_KEY_{i}")
            if key and "your-api-key" not in key.lower():
                keys.append(key)
        
        if keys:
            logger.info(f"Loaded {len(keys)} Google API key(s)")
        else:
            logger.warning("No Google API keys configured")
        
        return keys
    
    def _load_search_engine_ids(self) -> List[str]:
        """Load Google Search Engine ID (same for all keys)"""
        ids = []
        
        # Primary ID (same for all API keys)
        primary_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        if primary_id and "your-search-engine" not in primary_id.lower():
            # Use same engine ID for all API keys
            ids = [primary_id] * len(self.api_keys) if self.api_keys else [primary_id]
        
        if ids:
            logger.info(f"Using Search Engine ID: {primary_id} with {len(self.api_keys)} API key(s)")
        else:
            logger.warning("No Google Search Engine ID configured")
        
        return ids
    
    def _generate_search_queries(
        self,
        product_name: str,
        keywords: List[str],
        max_queries: int = 8
    ) -> List[str]:
        """
        Generate search query variations for competitor discovery
        
        Args:
            product_name: Name of the product
            keywords: List of keywords
            max_queries: Maximum number of queries to generate
            
        Returns:
            List of search queries
        """
        queries = set()
        
        # Strategy 1: Combine top keywords to form product category
        # e.g., ["code", "snippet", "manager"] -> "code snippet manager"
        if len(keywords) >= 2:
            # Combine first 2-3 keywords
            category_2 = f"{keywords[0]} {keywords[1]}"
            queries.add(f"{category_2} software")
            queries.add(f"{category_2} app")
            queries.add(f"{category_2} tool")
            queries.add(f"best {category_2} tools")
            
            if len(keywords) >= 3:
                category_3 = f"{keywords[0]} {keywords[1]} {keywords[2]}"
                queries.add(f"{category_3} software")
                queries.add(f"{category_3} app")
        
        # Strategy 2: Use single keywords only if very specific
        # Avoid generic terms like "code", "app", "software"
        generic_terms = {'app', 'software', 'tool', 'platform', 'service', 'product', 
                        'solution', 'system', 'application', 'program', 'code', 'web'}
        
        for keyword in keywords[:2]:
            if keyword.lower() not in generic_terms and len(keyword) > 4:
                queries.add(f"{keyword} software")
                queries.add(f"{keyword} alternatives")
        
        # Strategy 3: Competitor discovery queries
        if keywords:
            # Use combined keywords for better targeting
            if len(keywords) >= 2:
                main_term = f"{keywords[0]} {keywords[1]}"
            else:
                main_term = keywords[0]
            
            queries.add(f"{main_term} competitors")
            queries.add(f"top {main_term} products")
        
        # Convert to list and limit
        query_list = list(queries)[:max_queries]
        
        logger.info(f"Generated {len(query_list)} search queries: {query_list}")
        return query_list
    
    async def search_competitors(
        self,
        product_name: str,
        keywords: List[str],
        product_description: Optional[str] = None,
        max_results_per_query: int = 5
    ) -> Dict[str, Any]:
        """
        Search for competitors using Google Custom Search with semantic filtering
        
        Args:
            product_name: Name of the product
            keywords: List of keywords to search for
            product_description: Description of the product (for semantic filtering)
            max_results_per_query: Max results per query
            
        Returns:
            Dictionary with competitor URLs and metadata
        """
        if not self.api_keys or not self.search_engine_ids:
            logger.warning("Google Search API credentials not configured")
            return {
                "competitors": [],
                "total_found": 0,
                "source": "google_search",
                "error": "Google Search API credentials not configured"
            }
        
        try:
            # Generate search queries
            queries = self._generate_search_queries(product_name, keywords)
            
            # Track URLs and their scores
            url_scores = defaultdict(int)
            url_info = {}
            
            # Execute searches
            for query in queries:
                logger.info(f"Searching Google: {query}")
                
                results = await self._execute_search(query, max_results_per_query)
                
                for item in results:
                    url = item.get("link", "")
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    
                    if not url or not title:
                        continue
                    
                    # Filter out non-product URLs
                    if self._is_relevant_url(url, title):
                        url_scores[url] += 1  # Increment score for each query that returns this URL
                        
                        if url not in url_info:
                            url_info[url] = {
                                "title": title,
                                "snippet": snippet,
                                "url": url
                            }
            
            # Rank by score (frequency across queries)
            ranked_urls = sorted(url_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Extract competitor data
            competitors = []
            for url, score in ranked_urls[:30]:  # Get more initially for filtering
                info = url_info[url]
                
                # Extract company/product name from title
                name = self._extract_product_name(info["title"])
                
                competitors.append({
                    "name": name,
                    "description": info["snippet"][:200],
                    "url": url,
                    "relevance_score": score,  # How many queries returned this
                    "source": "google_search"
                })
            
            # SEMANTIC FILTERING: Remove irrelevant competitors
            if product_description and len(competitors) > 0:
                logger.info(f"Applying semantic filtering to {len(competitors)} competitors")
                competitors = self._filter_by_semantic_relevance(
                    competitors=competitors,
                    product_description=product_description,
                    keywords=keywords,
                    min_similarity=0.15  # Threshold for relevance
                )
                logger.info(f"After semantic filtering: {len(competitors)} competitors remain")
            
            # Return top 15 after filtering
            competitors = competitors[:15]
            
            logger.info(f"Found {len(competitors)} relevant competitors from Google Search")
            
            return {
                "competitors": competitors,
                "total_found": len(competitors),
                "queries_used": len(queries),
                "source": "google_search"
            }
            
        except Exception as e:
            logger.error(f"Google Search failed: {str(e)}")
            return {
                "competitors": [],
                "total_found": 0,
                "source": "google_search",
                "error": str(e)
            }
    
    def _filter_by_semantic_relevance(
        self,
        competitors: List[Dict[str, Any]],
        product_description: str,
        keywords: List[str],
        min_similarity: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Filter competitors by semantic similarity to user's product
        Removes completely irrelevant results (e.g., IDEs when looking for snippet managers)
        
        Args:
            competitors: List of competitor dictionaries
            product_description: User's product description
            keywords: Search keywords used
            min_similarity: Minimum cosine similarity threshold (0-1)
            
        Returns:
            Filtered list of competitors
        """
        if not competitors:
            return competitors
        
        try:
            # Build reference text from user's product
            keywords_text = " ".join(keywords)
            reference_text = f"{product_description} {keywords_text}"
            
            # Build texts for each competitor
            competitor_texts = []
            for comp in competitors:
                comp_text = f"{comp.get('name', '')} {comp.get('description', '')}"
                competitor_texts.append(comp_text)
            
            # Calculate TF-IDF similarity
            all_texts = [reference_text] + competitor_texts
            
            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=100,
                ngram_range=(1, 2)  # Use 1-2 word phrases
            )
            
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Calculate cosine similarity between reference and each competitor
            reference_vector = tfidf_matrix[0:1]
            competitor_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(reference_vector, competitor_vectors)[0]
            
            # Filter and add similarity scores
            filtered_competitors = []
            for i, comp in enumerate(competitors):
                similarity = similarities[i]
                comp['semantic_similarity'] = float(similarity)
                
                if similarity >= min_similarity:
                    filtered_competitors.append(comp)
                else:
                    logger.debug(
                        f"Filtered out '{comp['name']}' (similarity: {similarity:.3f} < {min_similarity})"
                    )
            
            # Sort by combined score: relevance_score * semantic_similarity
            filtered_competitors.sort(
                key=lambda x: x['relevance_score'] * x['semantic_similarity'],
                reverse=True
            )
            
            return filtered_competitors
            
        except Exception as e:
            logger.warning(f"Semantic filtering failed: {str(e)}, returning unfiltered results")
            return competitors
    
    async def _execute_search(
        self,
        query: str,
        num_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Execute a single Google search with automatic fallback to other API keys
        """
        if not self.api_keys or not self.search_engine_ids:
            return []
        
        # Try all combinations of API keys and search engine IDs
        attempts = []
        for key_idx, api_key in enumerate(self.api_keys):
            for engine_idx, search_engine_id in enumerate(self.search_engine_ids):
                attempts.append((key_idx, engine_idx, api_key, search_engine_id))
        
        # Start with current indices, then try others
        attempts.sort(key=lambda x: (
            0 if x[0] == self.current_key_index and x[1] == self.current_engine_index else 1,
            x[0], x[1]
        ))
        
        last_error = None
        
        for key_idx, engine_idx, api_key, search_engine_id in attempts:
            params = {
                "key": api_key,
                "cx": search_engine_id,
                "q": query,
                "num": num_results
            }
            
            try:
                response = requests.get(self.API_URL, params=params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                
                # Success! Update current indices for next call
                self.current_key_index = key_idx
                self.current_engine_index = engine_idx
                
                return data.get("items", [])
                
            except requests.exceptions.HTTPError as e:
                last_error = str(e)
                
                # If rate limited (429) or quota exceeded (403), try next key
                if response.status_code in [429, 403]:
                    logger.warning(f"API key {key_idx + 1}/{len(self.api_keys)} rate limited, trying next...")
                    continue
                else:
                    # Other HTTP errors, log and try next
                    logger.error(f"HTTP error with key {key_idx + 1}: {str(e)}")
                    continue
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Search failed with key {key_idx + 1}: {str(e)}")
                continue
        
        # All attempts failed
        logger.error(f"All API keys exhausted for query '{query}'. Last error: {last_error}")
        return []
    
    def _is_relevant_url(self, url: str, title: str) -> bool:
        """
        Filter out irrelevant URLs (forums, docs, blogs, articles)
        Keep only actual product/company websites
        """
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Exclude patterns - blogs, articles, forums, docs
        exclude_patterns = [
            'reddit.com', 'stackoverflow.com', 'github.com/issues',
            'youtube.com', 'wikipedia.org', 'quora.com',
            '/docs/', '/documentation/', '/api/', '/blog/', '/article/',
            'linkedin.com', 'twitter.com', 'facebook.com', 'instagram.com',
            'medium.com', 'forbes.com', 'techcrunch.com', 'venturebeat.com',
            '/news/', '/press/', '/resources/', '/guides/', '/tutorials/',
            'capterra.com', 'g2.com', 'trustpilot.com',  # Review sites
            'peoplemanagingpeople.com', 'thedigitalprojectmanager.com',
            'buffer.com/resources', 'hubspot.com/blog',
            'alternatives', 'vs', 'comparison', 'review', 'best',  # Comparison articles
            '.gov', '.edu', 'pubmed', 'usda.gov', 'ers.usda',  # Government/academic
            'honeywell.com/press', 'eleos.health/blog'  # Specific blog URLs
        ]
        
        # Check title for article indicators
        article_indicators = [
            'best', 'top', 'alternatives', 'vs', 'comparison', 'review',
            'guide', 'how to', 'tips', 'tricks', 'essential', 'recommended'
        ]
        
        # Exclude if URL or title contains exclude patterns
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False
        
        # Exclude if title looks like an article
        title_words = title_lower.split()
        if any(indicator in title_words[:5] for indicator in article_indicators):
            # Check if it's a listicle (e.g., "10 Best Tools")
            if any(char.isdigit() for char in title[:20]):
                return False
        
        # Must be a product domain (.com, .io, .app, etc.)
        product_domains = ['.com', '.io', '.app', '.co', '.ai', '.tech', '.software']
        has_product_domain = any(url_lower.endswith(domain) or f'{domain}/' in url_lower for domain in product_domains)
        
        if not has_product_domain:
            return False
        
        # Include patterns (product indicators in URL/domain)
        # Must have clean domain structure (not /blog/ or /resources/)
        url_parts = url_lower.split('/')
        if len(url_parts) <= 4:  # e.g., https://product.com or https://product.com/pricing
            return True
        
        return False
    
    def _extract_product_name(self, title: str) -> str:
        """
        Extract product/company name from page title
        Usually the first part before | or - or :
        """
        # Remove common suffixes
        title = re.sub(r'\s*[\|\-:]\s*.*$', '', title)
        
        # Remove common words
        title = re.sub(r'\s+(Software|App|Tool|Platform|Solution|Product)$', '', title, flags=re.IGNORECASE)
        
        # Limit length
        if len(title) > 50:
            title = title[:50].rsplit(' ', 1)[0] + '...'
        
        return title.strip() or "Unknown Product"


# Singleton instance
_google_search_service = None


def get_google_search_service() -> GoogleSearchService:
    """Get singleton instance of GoogleSearchService"""
    global _google_search_service
    if _google_search_service is None:
        _google_search_service = GoogleSearchService()
    return _google_search_service
