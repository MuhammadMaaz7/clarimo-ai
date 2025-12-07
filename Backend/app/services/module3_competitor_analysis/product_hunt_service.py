"""
Product Hunt API Service
Fetches competitor data from Product Hunt
"""

import httpx
import os
from typing import List, Dict, Any
from datetime import datetime
from app.core.logging import logger


class ProductHuntService:
    """Service for fetching data from Product Hunt API"""
    
    def __init__(self):
        self.api_base = "https://api.producthunt.com/v2/api/graphql"
        self.token = os.getenv("PRODUCT_HUNT_TOKEN")
        self.timeout = 15.0
    
    async def search_products(
        self,
        keywords: List[str],
        max_results: int = 10,
        fetch_limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search Product Hunt for similar products
        
        Args:
            keywords: List of keywords to search for
            max_results: Maximum results to return
            fetch_limit: Number of products to fetch before filtering (default 50)
            
        Returns:
            Dictionary with Product Hunt results
        """
        if not self.token:
            logger.warning("Product Hunt token not configured")
            return {
                "products": [],
                "total_found": 0,
                "query": " ".join(keywords),
                "source": "product_hunt",
                "error": "Product Hunt API token not configured"
            }
        
        try:
            query_string = " ".join(keywords)
            
            # GraphQL query for searching posts
            # Note: Product Hunt API v2 has specific search limitations
            graphql_query = """
            query SearchPosts($first: Int!) {
              posts(order: VOTES, first: $first) {
                edges {
                  node {
                    id
                    name
                    tagline
                    description
                    votesCount
                    commentsCount
                    url
                    website
                    createdAt
                    featuredAt
                    topics {
                      edges {
                        node {
                          name
                        }
                      }
                    }
                    makers {
                      id
                      name
                    }
                  }
                }
              }
            }
            """
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            payload = {
                "query": graphql_query,
                "variables": {
                    "first": fetch_limit  # Fetch more products to filter from
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_base,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
            
            # Parse results
            products = []
            edges = data.get("data", {}).get("posts", {}).get("edges", [])
            
            # Convert keywords to lowercase for matching
            keywords_lower = [k.lower() for k in keywords]
            
            for edge in edges:
                node = edge.get("node", {})
                
                # Extract topics
                topics = []
                for topic_edge in node.get("topics", {}).get("edges", []):
                    topics.append(topic_edge.get("node", {}).get("name", ""))
                
                # Extract makers (direct array, not edges)
                # Note: Product Hunt API redacts maker names for privacy
                makers = []
                for maker in node.get("makers", []):
                    name = maker.get("name", "")
                    # Skip redacted names
                    if name and name != "[REDACTED]":
                        makers.append(name)
                
                # If all names were redacted, just store the count
                if not makers and node.get("makers"):
                    makers_count = len(node.get("makers", []))
                else:
                    makers_count = len(makers)
                
                # Filter by keywords - check if any keyword appears in name, tagline, description, or topics
                name = node.get("name", "").lower()
                tagline = node.get("tagline", "").lower()
                description = (node.get("description", "") or "").lower()
                topics_text = " ".join(topics).lower()
                
                # Check if any keyword matches
                matches = any(
                    keyword in name or 
                    keyword in tagline or 
                    keyword in description or 
                    keyword in topics_text
                    for keyword in keywords_lower
                )
                
                if matches or not keywords:  # Include all if no keywords specified
                    product_data = {
                        "id": node.get("id", ""),
                        "name": node.get("name", ""),
                        "tagline": node.get("tagline", ""),
                        "description": node.get("description", "")[:300] if node.get("description") else node.get("tagline", ""),
                        "votes": node.get("votesCount", 0),
                        "comments": node.get("commentsCount", 0),
                        "url": node.get("url", ""),
                        "website": node.get("website", ""),
                        "created_at": node.get("createdAt", ""),
                        "featured_at": node.get("featuredAt", ""),
                        "topics": topics[:5]
                    }
                    
                    # Only include makers if we have real names (not redacted)
                    if makers:
                        product_data["makers"] = makers
                    else:
                        product_data["makers_count"] = makers_count
                    
                    products.append(product_data)
            
            logger.info(f"Found {len(products)} products on Product Hunt for query: {query_string}")
            
            return {
                "products": products,
                "total_found": len(products),
                "query": query_string,
                "source": "product_hunt"
            }
            
        except Exception as e:
            logger.error(f"Product Hunt search failed: {str(e)}")
            return {
                "products": [],
                "total_found": 0,
                "query": " ".join(keywords),
                "source": "product_hunt",
                "error": str(e)
            }


# Singleton instance
_product_hunt_service = None


def get_product_hunt_service() -> ProductHuntService:
    """Get singleton instance of ProductHuntService"""
    global _product_hunt_service
    if _product_hunt_service is None:
        _product_hunt_service = ProductHuntService()
    return _product_hunt_service
