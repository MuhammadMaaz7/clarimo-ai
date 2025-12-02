"""
External Data Service
Fetches real market data from HackerNews and GitHub APIs
"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.logging import logger


class ExternalDataService:
    """Service for fetching external market validation data"""
    
    def __init__(self):
        self.hn_api_base = "https://hn.algolia.com/api/v1"
        self.github_api_base = "https://api.github.com"
        self.itunes_api_base = "https://itunes.apple.com"
        self.play_store_api_base = "https://serpapi.com/search"  # Alternative: use web scraping
        self.timeout = 10.0
    
    async def search_similar_products(
        self,
        keywords: List[str],
        max_results: int = 10,
        include_app_stores: bool = True
    ) -> Dict[str, Any]:
        """
        Search for similar products across HackerNews, GitHub, and App Stores
        
        Args:
            keywords: List of keywords to search for
            max_results: Maximum results per source
            include_app_stores: Whether to search app stores
            
        Returns:
            Dictionary with results from all sources
        """
        # Search all sources in parallel
        hn_results = await self._search_hackernews(keywords, max_results)
        github_results = await self._search_github(keywords, max_results)
        
        app_store_results = {}
        play_store_results = {}
        
        if include_app_stores:
            app_store_results = await self._search_app_store(keywords, max_results)
            play_store_results = await self._search_play_store(keywords, max_results)
        
        total_found = (
            len(hn_results.get("products", [])) + 
            len(github_results.get("repositories", [])) +
            len(app_store_results.get("apps", [])) +
            len(play_store_results.get("apps", []))
        )
        
        return {
            "hackernews": hn_results,
            "github": github_results,
            "app_store": app_store_results,
            "play_store": play_store_results,
            "total_products_found": total_found,
            "search_keywords": keywords,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _search_hackernews(
        self,
        keywords: List[str],
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search HackerNews for Show HN posts (product launches)
        
        Args:
            keywords: Search keywords
            max_results: Maximum results to return
            
        Returns:
            Dictionary with HackerNews results
        """
        try:
            # Build search query
            query = " ".join(keywords)
            
            # Search for Show HN posts (product launches)
            url = f"{self.hn_api_base}/search"
            params = {
                "query": query,
                "tags": "show_hn",
                "hitsPerPage": max_results
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # Parse results
            products = []
            for hit in data.get("hits", []):
                products.append({
                    "title": hit.get("title", ""),
                    "url": hit.get("url", ""),
                    "points": hit.get("points", 0),
                    "num_comments": hit.get("num_comments", 0),
                    "created_at": hit.get("created_at", ""),
                    "author": hit.get("author", ""),
                    "story_text": hit.get("story_text", "")[:200] if hit.get("story_text") else ""
                })
            
            logger.info(f"Found {len(products)} products on HackerNews for query: {query}")
            
            return {
                "products": products,
                "total_found": data.get("nbHits", 0),
                "query": query,
                "source": "hackernews"
            }
            
        except Exception as e:
            logger.error(f"HackerNews search failed: {str(e)}")
            return {
                "products": [],
                "total_found": 0,
                "query": " ".join(keywords),
                "source": "hackernews",
                "error": str(e)
            }
    
    async def _search_github(
        self,
        keywords: List[str],
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search GitHub for similar open source projects
        
        Args:
            keywords: Search keywords
            max_results: Maximum results to return
            
        Returns:
            Dictionary with GitHub results
        """
        try:
            # Build search query
            query = " ".join(keywords)
            
            # Search repositories
            url = f"{self.github_api_base}/search/repositories"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": max_results
            }
            
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Clarimo-AI-Validator"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            # Parse results
            repositories = []
            for repo in data.get("items", []):
                repositories.append({
                    "name": repo.get("full_name", ""),
                    "description": repo.get("description", "")[:200] if repo.get("description") else "",
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "language": repo.get("language", ""),
                    "url": repo.get("html_url", ""),
                    "created_at": repo.get("created_at", ""),
                    "updated_at": repo.get("updated_at", ""),
                    "topics": repo.get("topics", [])[:5]
                })
            
            logger.info(f"Found {len(repositories)} repositories on GitHub for query: {query}")
            
            return {
                "repositories": repositories,
                "total_found": data.get("total_count", 0),
                "query": query,
                "source": "github"
            }
            
        except Exception as e:
            logger.error(f"GitHub search failed: {str(e)}")
            return {
                "repositories": [],
                "total_found": 0,
                "query": " ".join(keywords),
                "source": "github",
                "error": str(e)
            }
    
    async def _search_app_store(
        self,
        keywords: List[str],
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search Apple App Store for similar apps
        
        Args:
            keywords: Search keywords
            max_results: Maximum results to return
            
        Returns:
            Dictionary with App Store results
        """
        try:
            # Build search query
            query = " ".join(keywords)
            
            # Search App Store using iTunes Search API
            url = f"{self.itunes_api_base}/search"
            params = {
                "term": query,
                "entity": "software",
                "limit": max_results,
                "country": "US"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # Parse results
            apps = []
            for app in data.get("results", []):
                apps.append({
                    "name": app.get("trackName", ""),
                    "developer": app.get("artistName", ""),
                    "description": app.get("description", "")[:200] if app.get("description") else "",
                    "rating": app.get("averageUserRating", 0),
                    "rating_count": app.get("userRatingCount", 0),
                    "price": app.get("price", 0),
                    "currency": app.get("currency", "USD"),
                    "category": app.get("primaryGenreName", ""),
                    "url": app.get("trackViewUrl", ""),
                    "icon_url": app.get("artworkUrl100", ""),
                    "release_date": app.get("releaseDate", ""),
                    "version": app.get("version", ""),
                    "bundle_id": app.get("bundleId", "")
                })
            
            logger.info(f"Found {len(apps)} apps on App Store for query: {query}")
            
            return {
                "apps": apps,
                "total_found": data.get("resultCount", 0),
                "query": query,
                "source": "app_store"
            }
            
        except Exception as e:
            logger.error(f"App Store search failed: {str(e)}")
            return {
                "apps": [],
                "total_found": 0,
                "query": " ".join(keywords),
                "source": "app_store",
                "error": str(e)
            }
    
    async def _search_play_store(
        self,
        keywords: List[str],
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search Google Play Store for similar apps
        
        Note: Uses a simplified approach with google-play-scraper library
        For production, consider using official Google Play Developer API
        
        Args:
            keywords: Search keywords
            max_results: Maximum results to return
            
        Returns:
            Dictionary with Play Store results
        """
        try:
            # Try to use google-play-scraper if available
            try:
                from google_play_scraper import search as play_search
                
                query = " ".join(keywords)
                results = play_search(query, n_hits=max_results, lang="en", country="us")
                
                apps = []
                for app in results:
                    apps.append({
                        "name": app.get("title", ""),
                        "developer": app.get("developer", ""),
                        "description": app.get("description", "")[:200] if app.get("description") else app.get("summary", "")[:200],
                        "rating": app.get("score", 0),
                        "rating_count": app.get("ratings", 0),
                        "price": app.get("price", 0),
                        "free": app.get("free", True),
                        "category": app.get("genre", ""),
                        "url": f"https://play.google.com/store/apps/details?id={app.get('appId', '')}",
                        "icon_url": app.get("icon", ""),
                        "app_id": app.get("appId", ""),
                        "installs": app.get("installs", "")
                    })
                
                logger.info(f"Found {len(apps)} apps on Play Store for query: {query}")
                
                return {
                    "apps": apps,
                    "total_found": len(apps),
                    "query": query,
                    "source": "play_store"
                }
                
            except ImportError:
                logger.warning("google-play-scraper not installed. Play Store search disabled.")
                return {
                    "apps": [],
                    "total_found": 0,
                    "query": " ".join(keywords),
                    "source": "play_store",
                    "error": "google-play-scraper library not installed. Install with: pip install google-play-scraper"
                }
            
        except Exception as e:
            logger.error(f"Play Store search failed: {str(e)}")
            return {
                "apps": [],
                "total_found": 0,
                "query": " ".join(keywords),
                "source": "play_store",
                "error": str(e)
            }
    
    def extract_keywords_from_idea(
        self,
        title: str,
        problem_statement: str,
        solution_description: str,
        target_market: str
    ) -> List[str]:
        """
        Extract relevant keywords from idea for searching
        
        Args:
            title: Idea title
            problem_statement: Problem description
            solution_description: Solution description
            target_market: Target market
            
        Returns:
            List of keywords for searching
        """
        import re
        
        # Combine all text
        all_text = f"{title} {problem_statement} {solution_description} {target_market}"
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your'
        }
        
        # Extract words (3+ characters)
        words = re.findall(r'\b[a-z]{3,}\b', all_text.lower())
        
        # Filter stop words and get unique keywords
        keywords = []
        seen = set()
        for word in words:
            if word not in stop_words and word not in seen:
                keywords.append(word)
                seen.add(word)
        
        # Return top 5 most relevant keywords
        # Prioritize words from title and solution
        title_words = set(re.findall(r'\b[a-z]{3,}\b', title.lower()))
        solution_words = set(re.findall(r'\b[a-z]{3,}\b', solution_description.lower()))
        
        # Sort by relevance (title > solution > other)
        def keyword_score(word):
            score = 0
            if word in title_words:
                score += 3
            if word in solution_words:
                score += 2
            return score
        
        keywords.sort(key=keyword_score, reverse=True)
        
        return keywords[:5]


# Singleton instance
_external_data_service = None


def get_external_data_service() -> ExternalDataService:
    """Get singleton instance of ExternalDataService"""
    global _external_data_service
    if _external_data_service is None:
        _external_data_service = ExternalDataService()
    return _external_data_service
