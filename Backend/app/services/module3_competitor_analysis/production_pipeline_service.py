"""
Production-Ready Competitor Analysis Pipeline
Optimized for frontend integration with clean API responses
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
import os

from .llm_keyword_service import LLMKeywordService
from .google_search_service import get_google_search_service
from .product_hunt_service import get_product_hunt_service
from app.services.module2_validation.external_data_service import ExternalDataService
from .web_scraper_service import get_web_scraper_service
from .intelligent_analysis_service import IntelligentAnalysisService
from .llm_analysis_service import LLMAnalysisService
from app.core.logging_config import setup_logger
from app.db.database import db

# Setup logger with UTF-8 support
log_dir = os.path.join(os.path.dirname(__file__), '../../../logs')
log_file = os.path.join(log_dir, 'competitor_analysis.log')
logger = setup_logger(__name__, log_file)


class ProductionPipelineService:
    """
    Production-ready pipeline with:
    - Clean API responses (no technical details)
    - Proper logging (console + file)
    - Optimized performance
    - User-friendly error messages
    """
    
    @staticmethod
    async def analyze_product(
        product_info: Dict[str, Any],
        analysis_id: Optional[str] = None,
        user_id: Optional[str] = None,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Main entry point for competitor analysis
        Returns clean, user-friendly data for frontend
        
        Args:
            product_info: {
                "name": str,
                "description": str,
                "features": List[str],
                "pricing": str (optional),
                "target_audience": str (optional)
            }
            
        Returns:
            Clean analysis results for frontend display
        """
        import time
        start_time = time.time()
        
        if not analysis_id:
            import uuid
            analysis_id = f"analysis_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"="*80)
        logger.info(f"Starting competitor analysis: {analysis_id}")
        logger.info(f"Product: {product_info['name']}")
        logger.info(f"="*80)
        
        try:
            # Step 1: Generate Keywords
            logger.info("Step 1/5: Generating search keywords...")
            keywords = await ProductionPipelineService._generate_keywords(product_info)
            logger.info(f"✓ Generated {len(keywords)} keywords: {', '.join(keywords)}")
            
            # Step 2: Discover Competitors
            logger.info("Step 2/5: Discovering competitors from multiple sources...")
            competitors = await ProductionPipelineService._discover_competitors(
                product_info, keywords
            )
            logger.info(f"✓ Discovered {len(competitors)} competitors")
            
            # Step 3: Enrich Top Competitors
            logger.info("Step 3/5: Enriching top competitors with detailed data...")
            enriched = await ProductionPipelineService._enrich_competitors(competitors)
            logger.info(f"✓ Enriched {sum(1 for c in enriched if c.get('enriched'))} competitors")
            
            # Step 4: Analyze & Compare
            logger.info("Step 4/5: Analyzing competitive landscape...")
            analysis = await ProductionPipelineService._analyze_competitors(
                product_info, enriched
            )
            logger.info(f"✓ Analysis complete")
            
            # Step 5: Build Clean Response
            logger.info("Step 5/5: Preparing results...")
            response = ProductionPipelineService._build_clean_response(
                product_info, keywords, enriched, analysis, analysis_id, time.time() - start_time
            )
            
            logger.info(f"="*80)
            logger.info(f"Analysis complete: {analysis_id}")
            logger.info(f"Execution time: {response['execution_time']:.1f}s")
            logger.info(f"Top competitors: {len(response['top_competitors'])}")
            logger.info(f"="*80)
            
            # Save to database if requested
            if save_to_db and user_id:
                try:
                    ProductionPipelineService._save_to_database(
                        analysis_id, user_id, product_info, response
                    )
                    logger.info(f"✓ Saved analysis to database")
                except Exception as e:
                    logger.error(f"Failed to save to database: {str(e)}")
                    # Don't fail the whole analysis if DB save fails
            
            return response
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": "Analysis failed. Please try again.",
                "analysis_id": analysis_id
            }
    
    @staticmethod
    async def _generate_keywords(product_info: Dict[str, Any]) -> List[str]:
        """Generate keywords (hide technical details)"""
        try:
            result = await LLMKeywordService.generate_competitor_keywords(
                product_name=product_info['name'],
                product_description=product_info['description'],
                key_features=product_info.get('features', []),
                max_keywords=5
            )
            
            if result.get('success'):
                keywords = []
                for kw in result['keywords']:
                    words = kw.split()
                    if len(words) > 1:
                        meaningful = [w for w in words if w.lower() not in 
                                    ['app', 'tool', 'software', 'platform', 'smart', 'ai']]
                        keywords.append(meaningful[0] if meaningful else words[-1])
                    else:
                        keywords.append(kw)
                return list(dict.fromkeys(keywords))[:5]
            else:
                # Fallback
                return product_info['description'].split()[:5]
        except Exception as e:
            logger.warning(f"Keyword generation failed, using fallback: {str(e)}")
            return product_info['description'].split()[:5]
    
    @staticmethod
    async def _discover_competitors(
        product_info: Dict[str, Any],
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """Discover competitors from all sources"""
        all_competitors = []
        
        # Fetch from all sources concurrently
        tasks = [
            ProductionPipelineService._fetch_product_hunt(keywords),
            ProductionPipelineService._fetch_google(
                product_info['name'], 
                keywords, 
                product_info.get('description', '')
            ),
            ProductionPipelineService._fetch_github(keywords),
            ProductionPipelineService._fetch_app_stores(keywords)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Source fetch failed: {str(result)}")
                continue
            if result:
                all_competitors.extend(result.get('competitors', []))
        
        logger.info(f"Fetched {len(all_competitors)} total competitors")
        return all_competitors
    
    @staticmethod
    async def _fetch_product_hunt(keywords: List[str]) -> Dict[str, Any]:
        """Fetch from Product Hunt"""
        try:
            service = get_product_hunt_service()
            result = await service.search_products(keywords, max_results=10)
            
            competitors = []
            for p in result.get('products', []):
                competitors.append({
                    "name": p['name'],
                    "description": p.get('description', '')[:200],
                    "url": p['url'],
                    "source": "product_hunt",
                    "votes": p.get('votes'),
                    "topics": p.get('topics', [])
                })
            
            logger.info(f"Product Hunt: {len(competitors)} competitors")
            return {"competitors": competitors}
        except Exception as e:
            logger.warning(f"Product Hunt failed: {str(e)}")
            return {"competitors": []}
    
    @staticmethod
    async def _fetch_google(
        product_name: str, 
        keywords: List[str], 
        product_description: str = ""
    ) -> Dict[str, Any]:
        """Fetch from Google Search with semantic filtering"""
        try:
            service = get_google_search_service()
            result = await service.search_competitors(
                product_name=product_name,
                keywords=keywords,
                product_description=product_description,
                max_results_per_query=5
            )
            
            logger.info(f"Google Search: {len(result.get('competitors', []))} competitors")
            return result
        except Exception as e:
            logger.warning(f"Google Search failed: {str(e)}")
            return {"competitors": []}
    
    @staticmethod
    async def _fetch_github(keywords: List[str]) -> Dict[str, Any]:
        """Fetch from GitHub"""
        try:
            service = ExternalDataService()
            result = await service.search_github(keywords, max_results=10)
            
            competitors = []
            for repo in result.get('repositories', []):
                competitors.append({
                    "name": repo['name'],
                    "description": repo.get('description', '')[:200],
                    "url": repo['url'],
                    "source": "github",
                    "stars": repo.get('stars')
                })
            
            logger.info(f"GitHub: {len(competitors)} competitors")
            return {"competitors": competitors}
        except Exception as e:
            logger.warning(f"GitHub failed: {str(e)}")
            return {"competitors": []}
    
    @staticmethod
    async def _fetch_app_stores(keywords: List[str]) -> Dict[str, Any]:
        """Fetch from App Stores"""
        try:
            service = ExternalDataService()
            query = " ".join(keywords[:2])
            
            app_store_task = service.search_app_store(query, max_results=5)
            play_store_task = service.search_play_store(query, max_results=5)
            
            app_store_result, play_store_result = await asyncio.gather(
                app_store_task, play_store_task, return_exceptions=True
            )
            
            competitors = []
            
            if not isinstance(app_store_result, Exception):
                for app in app_store_result.get('apps', []):
                    competitors.append({
                        "name": app['name'],
                        "description": app.get('description', '')[:200],
                        "url": app.get('url'),
                        "source": "app_store",
                        "rating": app.get('rating')
                    })
            
            if not isinstance(play_store_result, Exception):
                for app in play_store_result.get('apps', []):
                    competitors.append({
                        "name": app['name'],
                        "description": app.get('description', '')[:200],
                        "url": app.get('url'),
                        "source": "play_store",
                        "rating": app.get('rating')
                    })
            
            logger.info(f"App Stores: {len(competitors)} competitors")
            return {"competitors": competitors}
        except Exception as e:
            logger.warning(f"App Stores failed: {str(e)}")
            return {"competitors": []}
    
    @staticmethod
    async def _enrich_competitors(
        competitors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich top competitors with web scraping (only Google results)"""
        scraper = get_web_scraper_service()
        enriched = []
        
        # Only scrape Google results (they need enrichment)
        google_comps = [c for c in competitors if c.get('source') == 'google_search']
        other_comps = [c for c in competitors if c.get('source') != 'google_search']
        
        # Scrape top 5 Google results
        scraped_count = 0
        for comp in google_comps[:5]:
            if not comp.get('url'):
                enriched.append(comp)
                continue
            
            try:
                result = await scraper.scrape_competitor_data(comp['url'], comp['name'])
                
                if result.get('scrape_success'):
                    enriched.append({
                        **comp,
                        'enriched': True,
                        'features': result.get('features', []),
                        'pricing': result.get('pricing'),
                        'target_audience': result.get('target_audience'),
                        'product_type': result.get('product_type')
                    })
                    scraped_count += 1
                    logger.info(f"  ✓ Enriched: {comp['name']}")
                else:
                    enriched.append(comp)
            except Exception as e:
                logger.warning(f"  ✗ Failed to enrich {comp['name']}: {str(e)}")
                enriched.append(comp)
        
        # Add remaining competitors
        enriched.extend(google_comps[5:])
        enriched.extend(other_comps)
        
        logger.info(f"Enriched {scraped_count} competitors with detailed data")
        return enriched
    
    @staticmethod
    async def _analyze_competitors(
        product_info: Dict[str, Any],
        competitors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze competitors and generate insights"""
        try:
            # Local analysis on all competitors
            preprocessed = await IntelligentAnalysisService.analyze_competitors(
                product_info=product_info,
                competitors=competitors,
                max_competitors_for_llm=15,
                use_local_analysis=True
            )
            
            # LLM analysis for insights
            llm_analysis = await LLMAnalysisService.generate_competitive_analysis(
                product_info=product_info,
                preprocessed_data=preprocessed
            )
            
            return {
                "preprocessed": preprocessed,
                "llm_analysis": llm_analysis
            }
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {"preprocessed": {}, "llm_analysis": {}}
    
    @staticmethod
    def _build_clean_response(
        product_info: Dict[str, Any],
        keywords: List[str],
        competitors: List[Dict[str, Any]],
        analysis: Dict[str, Any],
        analysis_id: str,
        execution_time: float
    ) -> Dict[str, Any]:
        """Build clean, user-friendly response for frontend"""
        
        preprocessed = analysis.get('preprocessed', {})
        llm_analysis = analysis.get('llm_analysis', {})
        
        # Select top 5 competitors (best quality data)
        top_competitors = ProductionPipelineService._select_top_competitors(competitors, 5)
        
        # Build feature matrix
        feature_matrix = ProductionPipelineService._build_feature_matrix(
            product_info, top_competitors
        )
        
        # Build comparison data
        comparison = ProductionPipelineService._build_comparison(
            product_info, top_competitors, llm_analysis
        )
        
        # Build gap analysis
        gap_analysis = ProductionPipelineService._build_gap_analysis(llm_analysis)
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "execution_time": round(execution_time, 1),
            
            # Product info
            "product": {
                "name": product_info['name'],
                "description": product_info['description'],
                "features": product_info.get('features', []),
                "pricing": product_info.get('pricing')
            },
            
            # Top competitors (clean, user-friendly)
            "top_competitors": top_competitors,
            
            # Feature comparison matrix
            "feature_matrix": feature_matrix,
            
            # Comparison dashboard data
            "comparison": comparison,
            
            # Gap analysis
            "gap_analysis": gap_analysis,
            
            # Strategic insights
            "insights": {
                "market_position": llm_analysis.get('market_position', ''),
                "competitive_advantages": llm_analysis.get('competitive_advantages', []),
                "differentiation_strategy": llm_analysis.get('differentiation_strategy', ''),
                "recommendations": llm_analysis.get('recommendations', [])
            },
            
            # Metadata (minimal)
            "metadata": {
                "total_competitors_analyzed": len(competitors),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def _select_top_competitors(
        competitors: List[Dict[str, Any]],
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """Select top N competitors based on data quality"""
        scored = []
        
        for comp in competitors:
            score = 0
            if comp.get('description'): score += 3
            if comp.get('features'): score += 5
            if comp.get('pricing'): score += 2
            if comp.get('url'): score += 1
            if comp.get('enriched'): score += 3
            
            scored.append({**comp, 'quality_score': score})
        
        # Sort by score and return top N
        sorted_comps = sorted(scored, key=lambda x: x['quality_score'], reverse=True)
        
        # Clean up (remove internal fields)
        clean_comps = []
        for comp in sorted_comps[:count]:
            clean = {
                "name": comp['name'],
                "description": comp.get('description', ''),
                "url": comp.get('url', ''),
                "features": comp.get('features', []),
                "pricing": comp.get('pricing'),
                "target_audience": comp.get('target_audience'),
                "source": comp.get('source', 'unknown')
            }
            clean_comps.append(clean)
        
        return clean_comps
    
    @staticmethod
    def _build_feature_matrix(
        product_info: Dict[str, Any],
        competitors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build feature comparison matrix - ONLY use real scraped features"""
        # Only include competitors that have scraped features
        enriched_competitors = [c for c in competitors if c.get('enriched') and c.get('features')]
        
        if not enriched_competitors:
            # No enriched data, return minimal matrix
            return {
                "features": product_info.get('features', [])[:10],
                "products": [{
                    "name": product_info['name'],
                    "is_user_product": True,
                    "feature_support": {
                        feat: True for feat in product_info.get('features', [])[:10]
                    }
                }]
            }
        
        # Collect ONLY real features from user + enriched competitors
        all_features = set(product_info.get('features', []))
        for comp in enriched_competitors:
            if comp.get('features'):
                all_features.update(comp.get('features', []))
        
        # Limit to reasonable number
        feature_list = list(all_features)[:12]
        
        # Build matrix
        matrix = {
            "features": feature_list,
            "products": []
        }
        
        # Add user's product
        matrix["products"].append({
            "name": product_info['name'],
            "is_user_product": True,
            "feature_support": {
                feat: feat in product_info.get('features', [])
                for feat in feature_list
            }
        })
        
        # Add ONLY enriched competitors (with real data)
        for comp in enriched_competitors[:5]:  # Max 5 competitors
            matrix["products"].append({
                "name": comp['name'],
                "is_user_product": False,
                "feature_support": {
                    feat: feat in comp.get('features', [])
                    for feat in feature_list
                }
            })
        
        return matrix
    
    @staticmethod
    def _build_comparison(
        product_info: Dict[str, Any],
        competitors: List[Dict[str, Any]],
        llm_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build comparison dashboard data"""
        return {
            "pricing": {
                "user_product": product_info.get('pricing', 'Not specified'),
                "competitors": [
                    {
                        "name": c['name'],
                        "pricing": c.get('pricing', 'Not available')
                    }
                    for c in competitors if c.get('pricing')
                ]
            },
            "feature_count": {
                "user_product": len(product_info.get('features', [])),
                "competitors": [
                    {
                        "name": c['name'],
                        "count": len(c.get('features', []))
                    }
                    for c in competitors
                ]
            },
            "positioning": llm_analysis.get('market_position', '')
        }
    
    @staticmethod
    def _build_gap_analysis(llm_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Build gap analysis data"""
        gap = llm_analysis.get('gap_analysis', {})
        
        return {
            "opportunities": gap.get('opportunities', [])[:5],  # Top 5
            "unique_strengths": llm_analysis.get('competitive_advantages', [])[:5],
            "areas_to_improve": gap.get('missing_features', [])[:5],
            "market_gaps": gap.get('underserved_segments', [])[:3]
        }

    
    @staticmethod
    def _save_to_database(
        analysis_id: str,
        user_id: str,
        product_info: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ):
        """Save analysis to database (synchronous)"""
        # Create document
        doc = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "product": product_info,
            "result": analysis_result,
            "created_at": datetime.now(),
            "status": "completed"
        }
        
        # Save to competitor_analyses collection
        db.competitor_analyses.insert_one(doc)
    
    @staticmethod
    def get_user_analyses(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all analyses for a user (synchronous)"""
        cursor = db.competitor_analyses.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit)
        
        analyses = []
        for doc in cursor:
            analyses.append({
                "analysis_id": doc["analysis_id"],
                "product_name": doc["product"]["name"],
                "competitors_found": doc["result"]["metadata"]["total_competitors_analyzed"],
                "created_at": doc["created_at"].isoformat(),
                "status": doc.get("status", "completed")
            })
        
        return analyses
    
    @staticmethod
    def get_analysis_by_id(analysis_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get specific analysis by ID (synchronous)"""
        doc = db.competitor_analyses.find_one({
            "analysis_id": analysis_id,
            "user_id": user_id
        })
        
        if doc:
            return doc["result"]
        return None
