"""
Product Hunt Fetcher Service - Fetch discussions from Product Hunt GraphQL API
"""
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx

# Configure logging
logger = logging.getLogger(__name__)

# Product Hunt GraphQL API endpoint
PRODUCTHUNT_API_URL = "https://api.producthunt.com/v2/api/graphql"

# GraphQL query for searching products
SEARCH_PRODUCTS_QUERY = """
query SearchProducts($query: String!, $first: Int!) {
  posts(first: $first, order: VOTES, postedAfter: "2023-01-01", search: $query) {
    edges {
      node {
        id
        name
        tagline
        description
        votesCount
        commentsCount
        createdAt
        url
        website
        topics {
          edges {
            node {
              name
            }
          }
        }
        comments(first: 20, order: VOTES) {
          edges {
            node {
              id
              body
              votesCount
              createdAt
              user {
                name
                username
              }
            }
          }
        }
      }
    }
  }
}
"""

class ProductHuntFetcher:
    """Service for fetching discussions from Product Hunt"""
    
    def __init__(self):
        # Use the same environment variable as competitor intelligence module
        self.api_key = os.getenv("PRODUCT_HUNT_TOKEN")
        self.api_url = PRODUCTHUNT_API_URL
        
        if not self.api_key:
            logger.warning("Product Hunt token not found - running in dry-run mode")
    
    async def fetch_product_discussions(
        self, 
        startup_idea: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch discussions from Product Hunt based on startup idea
        
        Args:
            startup_idea: The startup idea to search for
            limit: Maximum number of products to fetch
            
        Returns:
            List of discussion dictionaries
        """
        if not self.api_key:
            logger.info(f"[DRY RUN] Would search Product Hunt for: {startup_idea}")
            return []
        
        try:
            logger.info(f"Searching Product Hunt for: {startup_idea}")
            
            # Search for products
            products = await self._search_products(startup_idea, limit)
            
            # Convert to discussion format
            discussions = []
            for product in products:
                # Add product description as a discussion
                discussions.append({
                    "id": f"ph_product_{product['id']}",
                    "title": product['name'],
                    "content": f"{product['tagline']}. {product.get('description', '')}",
                    "url": product['url'],
                    "source": "producthunt",
                    "community": product['name'],
                    "created_at": product['created_at'],
                    "score": product['votes_count'],
                    "comments_count": product['comments_count'],
                    "metadata": {
                        "website": product.get('website'),
                        "topics": product.get('topics', [])
                    }
                })
                
                # Add comments as separate discussions
                for comment in product.get('comments', []):
                    discussions.append({
                        "id": f"ph_comment_{comment['id']}",
                        "title": f"Comment on {product['name']}",
                        "content": comment['body'],
                        "url": product['url'],
                        "source": "producthunt",
                        "community": product['name'],
                        "created_at": comment['created_at'],
                        "score": comment['votes_count'],
                        "comments_count": 0,
                        "metadata": {
                            "author": comment.get('user', {}).get('username', 'unknown'),
                            "product_name": product['name']
                        }
                    })
            
            logger.info(f"Fetched {len(discussions)} discussions from Product Hunt")
            return discussions
            
        except Exception as e:
            logger.error(f"Error fetching Product Hunt discussions: {str(e)}")
            return []
    
    async def _search_products(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search for products using GraphQL API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            variables = {
                "query": query,
                "first": min(limit, 50)  # Product Hunt API limit
            }
            
            payload = {
                "query": SEARCH_PRODUCTS_QUERY,
                "variables": variables
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Parse response
                products = []
                edges = data.get("data", {}).get("posts", {}).get("edges", [])
                
                for edge in edges:
                    node = edge.get("node", {})
                    
                    # Extract topics
                    topics = []
                    topic_edges = node.get("topics", {}).get("edges", [])
                    for topic_edge in topic_edges:
                        topic_name = topic_edge.get("node", {}).get("name")
                        if topic_name:
                            topics.append(topic_name)
                    
                    # Extract comments
                    comments = []
                    comment_edges = node.get("comments", {}).get("edges", [])
                    for comment_edge in comment_edges:
                        comment_node = comment_edge.get("node", {})
                        comments.append({
                            "id": comment_node.get("id", ""),
                            "body": comment_node.get("body", ""),
                            "votes_count": comment_node.get("votesCount", 0),
                            "created_at": comment_node.get("createdAt", ""),
                            "user": comment_node.get("user", {})
                        })
                    
                    products.append({
                        "id": node.get("id", ""),
                        "name": node.get("name", ""),
                        "tagline": node.get("tagline", ""),
                        "description": node.get("description", ""),
                        "votes_count": node.get("votesCount", 0),
                        "comments_count": node.get("commentsCount", 0),
                        "created_at": node.get("createdAt", ""),
                        "url": node.get("url", ""),
                        "website": node.get("website", ""),
                        "topics": topics,
                        "comments": comments
                    })
                
                logger.info(f"Found {len(products)} products on Product Hunt")
                return products
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Product Hunt API error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Error searching Product Hunt: {str(e)}")
            return []
    
    async def get_product_comments(self, product_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get comments for a specific product"""
        # This would be implemented if we need to fetch more comments
        # For now, we fetch comments in the main search query
        pass

# Create global instance
producthunt_fetcher = ProductHuntFetcher()
