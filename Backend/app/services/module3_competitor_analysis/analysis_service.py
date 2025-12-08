"""
Competitor Analysis Service
Handles analysis lifecycle and orchestration
"""

import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import BackgroundTasks
from app.db.database import db, competitor_analyses_collection, products_collection
from app.db.models.competitor_analysis_model import (
    CompetitiveAnalysisResponse,
    AnalysisStatusResponse,
    AnalysisHistoryItem,
    Competitor,
    MarketInsights,
    PositioningAnalysis,
    FeatureComparison
)
from app.core.logging import logger


class CompetitorAnalysisService:
    """Service for managing competitor analyses"""
    
    @staticmethod
    async def start_analysis(
        product_id: str,
        user_id: str,
        background_tasks: BackgroundTasks
    ) -> CompetitiveAnalysisResponse:
        """
        Start a new competitor analysis
        
        Args:
            product_id: ID of the product to analyze
            user_id: ID of the user
            background_tasks: FastAPI background tasks
            
        Returns:
            CompetitiveAnalysisResponse with IN_PROGRESS status
        """
        # Verify product exists and belongs to user
        product = products_collection.find_one({
            "id": product_id,
            "user_id": user_id
        })
        
        if not product:
            raise ValueError(f"Product {product_id} not found or does not belong to user")
        
        # Create analysis record
        analysis_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        analysis_doc = {
            "analysis_id": analysis_id,
            "product_id": product_id,
            "user_id": user_id,
            "status": "in_progress",
            "competitors": [],
            "market_insights": None,
            "positioning_analysis": None,
            "feature_comparison": None,
            "recommendations": [],
            "created_at": now,
            "completed_at": None,
            "error_message": None
        }
        
        competitor_analyses_collection.insert_one(analysis_doc)
        
        logger.info(f"Created analysis {analysis_id} for product {product_id}")
        
        # Queue background task to execute analysis
        background_tasks.add_task(
            CompetitorAnalysisService._execute_analysis_background,
            analysis_id,
            product
        )
        
        return CompetitiveAnalysisResponse(
            analysis_id=analysis_id,
            product_id=product_id,
            user_id=user_id,
            status="in_progress",
            competitors=[],
            market_insights=None,
            positioning_analysis=None,
            feature_comparison=None,
            recommendations=[],
            created_at=now.isoformat(),
            completed_at=None,
            error_message=None
        )
    
    @staticmethod
    async def _execute_analysis_background(analysis_id: str, product: dict):
        """
        Execute analysis in background
        
        Args:
            analysis_id: ID of the analysis
            product: Product document
        """
        try:
            logger.info(f"Starting background analysis {analysis_id}")
            
            # Import services
            from app.services.module3_competitor_analysis.product_hunt_service import get_product_hunt_service
            from app.services.module3_competitor_analysis.google_search_service import get_google_search_service
            from app.services.module2_validation.external_data_service import ExternalDataService
            from app.services.module3_competitor_analysis.llm_keyword_service import LLMKeywordService
            from app.services.module3_competitor_analysis.keyword_extractor import CompetitorKeywordExtractor
            from app.services.module3_competitor_analysis.data_saver import CompetitorDataSaver
            from app.services.module3_competitor_analysis.web_scraper_service import get_web_scraper_service
            
            # Extract product information
            product_name = product.get("product_name", "")
            product_description = product.get("product_description", "")
            key_features = product.get("key_features", [])
            
            # Try LLM-based keyword generation first (better quality)
            llm_result = await LLMKeywordService.generate_competitor_keywords(
                product_name=product_name,
                product_description=product_description,
                key_features=key_features,
                max_keywords=5
            )
            
            if llm_result.get("success"):
                llm_keywords = llm_result["keywords"]
                # Simplify multi-word keywords to single words for better Product Hunt matching
                # "ai task manager" -> "task", "smart scheduling" -> "scheduling"
                keywords = []
                for kw in llm_keywords:
                    words = kw.split()
                    # Take the most meaningful word (usually the last or second word)
                    if len(words) > 1:
                        # Prefer non-generic words
                        meaningful_words = [w for w in words if w.lower() not in ['app', 'tool', 'software', 'platform', 'smart', 'intelligent']]
                        if meaningful_words:
                            keywords.append(meaningful_words[0])
                        else:
                            keywords.append(words[-1])  # Take last word
                    else:
                        keywords.append(kw)
                
                # Remove duplicates while preserving order
                keywords = list(dict.fromkeys(keywords))[:5]
                keyword_method = "llm_simplified"
                logger.info(f"LLM keywords for '{product_name}': {llm_keywords}")
                logger.info(f"Simplified for search: {keywords}")
            else:
                # Fallback to simple extraction
                keywords = CompetitorKeywordExtractor.extract_keywords(
                    product_name=product_name,
                    product_description=product_description,
                    key_features=key_features,
                    max_keywords=5
                )
                keyword_method = "simple"
                logger.info(f"Simple extraction keywords for '{product_name}': {keywords}")
            
            # Save keywords to JSON
            CompetitorDataSaver.save_keywords(
                analysis_id=analysis_id,
                product_name=product_name,
                keywords=keywords,
                method=keyword_method,
                metadata=llm_result if keyword_method == "llm" else {}
            )
            
            # Helper function to filter out non-competitors
            def is_valid_competitor(comp: dict) -> bool:
                """Filter out blogs, articles, government sites, and non-product URLs"""
                name = comp.get("name", "").lower()
                description = comp.get("description", "").lower()
                url = comp.get("url", "").lower()
                source = comp.get("source", "")
                
                # Always keep Product Hunt, GitHub, App Store, Play Store
                if source in ['product_hunt', 'github', 'app_store', 'play_store']:
                    return True
                
                # For web sources, apply strict filtering
                
                # Exclude article/blog indicators in name
                article_indicators = [
                    'best', 'top', 'alternatives', 'vs', 'comparison', 'review',
                    'guide', 'how to', 'tips', 'essential', 'recommended',
                    'blog', 'article', 'news', 'approved', 'certification',
                    'screening', 'survey', 'analysis software', 'tools for'
                ]
                
                # Check if name looks like an article title
                for indicator in article_indicators:
                    if indicator in name[:40]:
                        return False
                
                # Exclude government, academic, review sites
                exclude_domains = [
                    # Review/comparison sites
                    'forbes.com', 'techcrunch.com', 'capterra.com', 'g2.com',
                    'peoplemanagingpeople.com', 'thedigitalprojectmanager.com',
                    'buffer.com', 'hubspot.com', 'trustpilot.com',
                    # Government/academic
                    '.gov', '.edu', 'usda.gov', 'fns.usda', 'ers.usda',
                    'pubmed', 'nih.gov', 'biomedcentral.com',
                    # Tool/equipment sellers (not software)
                    'krstrikeforce.com', 'homedepot.com',
                    # Generic info sites
                    'wikipedia.org', 'youtube.com'
                ]
                
                for domain in exclude_domains:
                    if domain in url:
                        return False
                
                # Exclude URLs with article/blog paths
                exclude_paths = [
                    '/blog/', '/article/', '/news/', '/press/',
                    '/resources/', '/guides/', '/products/ball-workout-tool'
                ]
                
                for path in exclude_paths:
                    if path in url:
                        return False
                
                # Must have a reasonable name
                if not comp.get("name") or len(comp.get("name", "")) < 2:
                    return False
                
                # Exclude if name has numbers at start (listicles like "10 Best...")
                if name and name[0].isdigit():
                    return False
                
                # For web sources, must be a clean product domain
                if source == 'web':
                    # Must end with product domain
                    product_domains = ['.com', '.io', '.app', '.co', '.ai']
                    has_product_domain = any(url.endswith(domain) or f'{domain}/' in url for domain in product_domains)
                    
                    if not has_product_domain:
                        return False
                    
                    # URL should be short (product homepage, not deep article)
                    url_parts = url.split('/')
                    if len(url_parts) > 5:  # Too many path segments = likely article
                        return False
                
                return True
            
            # Collect competitors from multiple sources
            all_competitors = []
            raw_competitors = []  # Store all before filtering
            
            # 1. Product Hunt
            try:
                ph_service = get_product_hunt_service()
                # Fetch from larger pool (50 products) to get better matches
                ph_results = await ph_service.search_products(
                    keywords=keywords, 
                    max_results=15,
                    fetch_limit=50
                )
                
                ph_competitors = []
                for product_data in ph_results.get("products", []):
                    competitor = {
                        "name": product_data.get("name"),
                        "description": product_data.get("description", "")[:200],
                        "source": "product_hunt",
                        "url": product_data.get("url"),
                        "votes": product_data.get("votes"),
                        "comments": product_data.get("comments"),
                        "topics": product_data.get("topics", [])
                    }
                    raw_competitors.append(competitor)
                    ph_competitors.append(competitor)
                
                # Save Product Hunt data
                CompetitorDataSaver.save_competitors(
                    analysis_id=analysis_id,
                    product_name=product_name,
                    competitors=ph_competitors,
                    source="product_hunt"
                )
                
                logger.info(f"Found {len(ph_competitors)} competitors from Product Hunt")
            except Exception as e:
                logger.error(f"Product Hunt search failed: {str(e)}")
            
            # 2. GitHub (for open source competitors)
            try:
                external_service = ExternalDataService()
                github_results = await external_service.search_github(keywords)
                
                github_competitors = []
                for repo in github_results.get("repositories", [])[:5]:
                    competitor = {
                        "name": repo.get("name"),
                        "description": repo.get("description", "")[:200],
                        "source": "github",
                        "url": repo.get("url"),
                        "stars": repo.get("stars"),
                        "forks": repo.get("forks")
                    }
                    raw_competitors.append(competitor)
                    github_competitors.append(competitor)
                
                # Save GitHub data
                CompetitorDataSaver.save_competitors(
                    analysis_id=analysis_id,
                    product_name=product_name,
                    competitors=github_competitors,
                    source="github"
                )
                
                logger.info(f"Found {len(github_competitors)} competitors from GitHub")
            except Exception as e:
                logger.error(f"GitHub search failed: {str(e)}")
            
            # 3. App Store (for mobile apps)
            try:
                query = " ".join(keywords[:3])
                app_store_results = await external_service.search_app_store(query)
                
                app_store_competitors = []
                for app in app_store_results.get("apps", [])[:5]:
                    competitor = {
                        "name": app.get("name"),
                        "description": app.get("description", "")[:200],
                        "source": "app_store",
                        "url": app.get("url"),
                        "rating": app.get("rating"),
                        "rating_count": app.get("rating_count"),
                        "price": app.get("price")
                    }
                    raw_competitors.append(competitor)
                    app_store_competitors.append(competitor)
                
                # Save App Store data
                CompetitorDataSaver.save_competitors(
                    analysis_id=analysis_id,
                    product_name=product_name,
                    competitors=app_store_competitors,
                    source="app_store"
                )
                
                logger.info(f"Found {len(app_store_competitors)} competitors from App Store")
            except Exception as e:
                logger.error(f"App Store search failed: {str(e)}")
            
            # 4. Google Search (for web-based competitors)
            try:
                google_service = get_google_search_service()
                google_results = await google_service.search_competitors(
                    product_name=product_name,
                    keywords=keywords,
                    product_description=product_description,
                    max_results_per_query=5
                )
                
                google_competitors = []
                for comp_data in google_results.get("competitors", []):
                    competitor = {
                        "name": comp_data.get("name"),
                        "description": comp_data.get("description", "")[:200],
                        "source": "web",
                        "url": comp_data.get("url"),
                        "relevance_score": comp_data.get("relevance_score", 0)
                    }
                    raw_competitors.append(competitor)
                    google_competitors.append(competitor)
                
                # Save Google Search data
                CompetitorDataSaver.save_competitors(
                    analysis_id=analysis_id,
                    product_name=product_name,
                    competitors=google_competitors,
                    source="google_search"
                )
                
                logger.info(f"Found {len(google_competitors)} competitors from Google Search")
            except Exception as e:
                logger.error(f"Google Search failed: {str(e)}")
            
            # 5. Play Store (for Android apps)
            try:
                query = " ".join(keywords[:3])
                play_store_results = await external_service.search_play_store(query)
                
                play_store_competitors = []
                for app in play_store_results.get("apps", [])[:5]:
                    competitor = {
                        "name": app.get("name"),
                        "description": app.get("description", "")[:200],
                        "source": "play_store",
                        "url": app.get("url"),
                        "rating": app.get("rating"),
                        "rating_count": app.get("rating_count"),
                        "installs": app.get("installs")
                    }
                    raw_competitors.append(competitor)
                    play_store_competitors.append(competitor)
                
                # Save Play Store data
                CompetitorDataSaver.save_competitors(
                    analysis_id=analysis_id,
                    product_name=product_name,
                    competitors=play_store_competitors,
                    source="play_store"
                )
                
                logger.info(f"Found {len(play_store_competitors)} competitors from Play Store")
            except Exception as e:
                logger.error(f"Play Store search failed: {str(e)}")
            
            # Filter competitors - remove blogs, articles, non-products
            logger.info(f"Filtering {len(raw_competitors)} raw competitors...")
            all_competitors = [comp for comp in raw_competitors if is_valid_competitor(comp)]
            logger.info(f"After filtering: {len(all_competitors)} valid competitors")
            
            # Classify competitors as direct/indirect
            from app.services.module3_competitor_analysis.competitor_classifier import CompetitorClassifier
            
            logger.info("Classifying competitors as direct/indirect...")
            all_competitors = CompetitorClassifier.classify_competitors(
                product_info={
                    "product_name": product_name,
                    "product_description": product_description,
                    "key_features": key_features
                },
                competitors=all_competitors
            )
            
            # Get classification summary
            classification_summary = CompetitorClassifier.get_classification_summary(all_competitors)
            logger.info(f"Classification: {classification_summary['direct']} direct, {classification_summary['indirect']} indirect")
            
            # Enrich top competitors with web scraping (limit to top 10 to save time)
            logger.info("Enriching top competitors with web scraping...")
            scraper = get_web_scraper_service()
            
            enriched_count = 0
            for i, competitor in enumerate(all_competitors[:10]):  # Only scrape top 10
                if competitor.get('url'):
                    try:
                        scraped_data = await scraper.scrape_competitor_data(
                            url=competitor['url'],
                            competitor_name=competitor['name']
                        )
                        
                        if scraped_data.get('scrape_success'):
                            # Add scraped data to competitor
                            competitor['features'] = scraped_data.get('features', [])
                            competitor['pricing'] = scraped_data.get('pricing')
                            competitor['target_audience'] = scraped_data.get('target_audience')
                            competitor['key_benefits'] = scraped_data.get('key_benefits', [])
                            competitor['product_type'] = scraped_data.get('product_type')
                            competitor['enriched'] = True
                            enriched_count += 1
                            logger.info(f"Enriched {competitor['name']} ({i+1}/10)")
                    except Exception as e:
                        logger.error(f"Failed to enrich {competitor['name']}: {str(e)}")
                        competitor['enriched'] = False
            
            logger.info(f"Successfully enriched {enriched_count} competitors with detailed data")
            
            # Calculate market insights
            total_competitors = len(all_competitors)
            
            # Determine market saturation
            if total_competitors < 5:
                market_saturation = "low"
                opportunity_score = 8.5
            elif total_competitors < 15:
                market_saturation = "medium"
                opportunity_score = 6.5
            else:
                market_saturation = "high"
                opportunity_score = 4.5
            
            # Extract key trends from topics
            all_topics = []
            for comp in all_competitors:
                if comp.get("topics"):
                    all_topics.extend(comp["topics"])
            
            # Count topic frequency
            from collections import Counter
            topic_counts = Counter(all_topics)
            key_trends = [topic for topic, count in topic_counts.most_common(5)]
            
            if not key_trends:
                key_trends = ["AI integration", "User experience focus", "Mobile-first approach"]
            
            # Generate positioning analysis
            positioning = {
                "your_strengths": key_features[:3] if key_features else ["Unique value proposition"],
                "your_weaknesses": ["Market awareness", "User base growth"],
                "opportunities": [
                    f"Differentiate with unique features" if total_competitors > 10 else "First-mover advantage in niche",
                    "Focus on underserved user segments",
                    "Leverage emerging trends"
                ],
                "threats": [
                    f"High competition with {total_competitors} similar products" if total_competitors > 10 else "Potential new entrants",
                    "Established competitors with larger user bases",
                    "Rapid market changes"
                ]
            }
            
            # Generate recommendations
            recommendations = [
                f"Focus on differentiation - {total_competitors} competitors found in this space",
                "Emphasize unique features that competitors lack",
                "Consider targeting a specific niche to reduce direct competition"
            ]
            
            if market_saturation == "high":
                recommendations.append("Market is saturated - focus on innovation and unique value proposition")
            elif market_saturation == "low":
                recommendations.append("Low competition detected - opportunity for market leadership")
            
            # Prepare full analysis data
            analysis_data = {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "keywords": keywords,
                "keyword_method": keyword_method,
                "competitors": all_competitors,
                "classification_summary": classification_summary,
                "market_insights": {
                    "total_competitors": total_competitors,
                    "direct_competitors": classification_summary['direct'],
                    "indirect_competitors": classification_summary['indirect'],
                    "market_saturation": market_saturation,
                    "opportunity_score": opportunity_score,
                    "key_trends": key_trends
                },
                "positioning_analysis": positioning,
                "feature_comparison": [],
                "recommendations": recommendations
            }
            
            # Save full analysis to JSON
            CompetitorDataSaver.save_full_analysis(
                analysis_id=analysis_id,
                product_name=product_name,
                all_data=analysis_data
            )
            
            # Update database
            competitor_analyses_collection.update_one(
                {"analysis_id": analysis_id},
                {"$set": analysis_data}
            )
            
            logger.info(f"Completed analysis {analysis_id} with {total_competitors} competitors")
            
        except Exception as e:
            logger.error(f"Analysis {analysis_id} failed: {str(e)}")
            competitor_analyses_collection.update_one(
                {"analysis_id": analysis_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": str(e),
                        "completed_at": datetime.utcnow()
                    }
                }
            )
    
    @staticmethod
    def get_analysis_result(
        analysis_id: str,
        user_id: str
    ) -> Optional[CompetitiveAnalysisResponse]:
        """
        Get analysis result by ID
        
        Args:
            analysis_id: ID of the analysis
            user_id: ID of the user
            
        Returns:
            CompetitiveAnalysisResponse or None if not found
        """
        analysis = competitor_analyses_collection.find_one({
            "analysis_id": analysis_id,
            "user_id": user_id
        })
        
        if not analysis:
            return None
        
        # Parse competitors
        competitors = [Competitor(**c) for c in analysis.get("competitors", [])]
        
        # Parse market insights
        market_insights = None
        if analysis.get("market_insights"):
            market_insights = MarketInsights(**analysis["market_insights"])
        
        # Parse positioning analysis
        positioning_analysis = None
        if analysis.get("positioning_analysis"):
            positioning_analysis = PositioningAnalysis(**analysis["positioning_analysis"])
        
        # Parse feature comparison
        feature_comparison = None
        if analysis.get("feature_comparison"):
            feature_comparison = [FeatureComparison(**f) for f in analysis["feature_comparison"]]
        
        return CompetitiveAnalysisResponse(
            analysis_id=analysis["analysis_id"],
            product_id=analysis["product_id"],
            user_id=analysis["user_id"],
            status=analysis["status"],
            competitors=competitors,
            market_insights=market_insights,
            positioning_analysis=positioning_analysis,
            feature_comparison=feature_comparison,
            recommendations=analysis.get("recommendations", []),
            created_at=analysis["created_at"].isoformat(),
            completed_at=analysis["completed_at"].isoformat() if analysis.get("completed_at") else None,
            error_message=analysis.get("error_message")
        )
    
    @staticmethod
    def get_analysis_status(
        analysis_id: str,
        user_id: str
    ) -> Optional[AnalysisStatusResponse]:
        """
        Get analysis status for polling
        
        Args:
            analysis_id: ID of the analysis
            user_id: ID of the user
            
        Returns:
            AnalysisStatusResponse or None if not found
        """
        analysis = competitor_analyses_collection.find_one({
            "analysis_id": analysis_id,
            "user_id": user_id
        })
        
        if not analysis:
            return None
        
        # Calculate progress based on status
        progress = 0
        current_stage = "Initializing"
        
        if analysis["status"] == "in_progress":
            progress = 50
            current_stage = "Analyzing competitors"
        elif analysis["status"] == "completed":
            progress = 100
            current_stage = "Completed"
        elif analysis["status"] == "failed":
            progress = 0
            current_stage = "Failed"
        
        return AnalysisStatusResponse(
            analysis_id=analysis["analysis_id"],
            status=analysis["status"],
            progress=progress,
            current_stage=current_stage,
            estimated_completion=None
        )
    
    @staticmethod
    def get_analysis_history(
        product_id: str,
        user_id: str
    ) -> List[AnalysisHistoryItem]:
        """
        Get analysis history for a product
        
        Args:
            product_id: ID of the product
            user_id: ID of the user
            
        Returns:
            List of AnalysisHistoryItem
        """
        analyses = list(competitor_analyses_collection.find({
            "product_id": product_id,
            "user_id": user_id
        }).sort("created_at", -1))
        
        result = []
        for analysis in analyses:
            result.append(AnalysisHistoryItem(
                analysis_id=analysis["analysis_id"],
                product_id=analysis["product_id"],
                competitors_found=len(analysis.get("competitors", [])),
                opportunity_score=analysis.get("market_insights", {}).get("opportunity_score", 0) if analysis.get("market_insights") else 0,
                status=analysis["status"],
                created_at=analysis["created_at"].isoformat(),
                completed_at=analysis["completed_at"].isoformat() if analysis.get("completed_at") else None
            ))
        
        return result
