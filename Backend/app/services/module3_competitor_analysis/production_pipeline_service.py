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
            logger.info("Step 1/7: Generating search keywords...")
            keywords = await ProductionPipelineService._generate_keywords(product_info)
            logger.info(f"✓ Generated {len(keywords)} keywords: {', '.join(keywords)}")
            
            # Step 2: Fetch Competitors from APIs (Product Hunt, Google, GitHub, Play Store)
            logger.info("Step 2/7: Fetching competitors from multiple sources...")
            raw_competitors = await ProductionPipelineService._fetch_competitors_from_apis(
                product_info, keywords
            )
            logger.info(f"✓ Fetched {len(raw_competitors)} raw competitors")
            
            # Step 3: Filter out blogs, Reddit, non-competitor URLs
            logger.info("Step 3/7: Filtering out blogs, Reddit, and non-competitor URLs...")
            filtered_competitors = ProductionPipelineService._filter_non_competitors(raw_competitors)
            logger.info(f"✓ After filtering: {len(filtered_competitors)} valid competitors")
            
            # Step 4: Compute Similarity & Classify (Direct/Indirect/Not a Competitor)
            logger.info("Step 4/7: Computing similarity and classifying competitors...")
            classified_competitors = ProductionPipelineService._classify_competitors(
                product_info, filtered_competitors
            )
            logger.info(f"✓ Classified: {sum(1 for c in classified_competitors if c.get('competitor_type') == 'direct')} direct, "
                       f"{sum(1 for c in classified_competitors if c.get('competitor_type') == 'indirect')} indirect")
            
            # Step 5: LLM Verification - Select Top 5 Competitors
            logger.info("Step 5/7: LLM verification - selecting top 5 competitors...")
            top_5_competitors = await ProductionPipelineService._llm_select_top_competitors(
                product_info, classified_competitors
            )
            logger.info(f"✓ LLM selected top {len(top_5_competitors)} competitors")
            
            # Step 6: Web Scraping - Extract Features & Pricing for Top 5
            logger.info("Step 6/7: Web scraping top competitors for features and pricing...")
            enriched_top_5 = await ProductionPipelineService._scrape_top_competitors(top_5_competitors)
            logger.info(f"✓ Scraped {sum(1 for c in enriched_top_5 if c.get('enriched'))} competitors")
            
            # Step 7: LLM Structures Output for Comparison Dashboard
            logger.info("Step 7/7: LLM structuring output for comparison dashboard...")
            final_analysis = await ProductionPipelineService._llm_structure_output(
                product_info, enriched_top_5, classified_competitors
            )
            logger.info(f"✓ Analysis structured for dashboard")
            
            # Build Final Response
            response = ProductionPipelineService._build_clean_response(
                product_info, keywords, enriched_top_5, classified_competitors, 
                final_analysis, analysis_id, time.time() - start_time
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
    async def _fetch_competitors_from_apis(
        product_info: Dict[str, Any],
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Step 2: Fetch competitors from APIs (Product Hunt, Google, GitHub, Play Store)
        Returns raw competitor data without filtering or classification
        """
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
        
        return all_competitors
    
    @staticmethod
    def _filter_non_competitors(competitors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Step 3: Filter out blogs, Reddit, and non-competitor URLs
        Removes articles, listicles, review sites, government sites, etc.
        """
        def is_valid_competitor(comp: dict) -> bool:
            """Filter out non-competitors"""
            name = comp.get("name", "").lower()
            description = comp.get("description", "").lower()
            url = comp.get("url", "").lower()
            source = comp.get("source", "")
            
            # Always keep Product Hunt, GitHub, App Store, Play Store
            if source in ['product_hunt', 'github', 'app_store', 'play_store']:
                return True
            
            # For web sources, apply strict filtering
            
            # Exclude Reddit URLs
            if 'reddit.com' in url:
                logger.debug(f"Filtered Reddit URL: {name}")
                return False
            
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
                    logger.debug(f"Filtered article: {name}")
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
                'wikipedia.org', 'youtube.com', 'reddit.com'
            ]
            
            for domain in exclude_domains:
                if domain in url:
                    logger.debug(f"Filtered excluded domain: {name} ({domain})")
                    return False
            
            # Exclude URLs with article/blog paths
            exclude_paths = [
                '/blog/', '/article/', '/news/', '/press/',
                '/resources/', '/guides/', '/products/ball-workout-tool'
            ]
            
            for path in exclude_paths:
                if path in url:
                    logger.debug(f"Filtered blog/article path: {name}")
                    return False
            
            # Must have a reasonable name
            if not comp.get("name") or len(comp.get("name", "")) < 2:
                return False
            
            # Exclude if name has numbers at start (listicles like "10 Best...")
            if name and name[0].isdigit():
                logger.debug(f"Filtered listicle: {name}")
                return False
            
            # For web sources, must be a clean product domain
            if source == 'web' or source == 'google_search':
                # Must end with product domain
                product_domains = ['.com', '.io', '.app', '.co', '.ai']
                has_product_domain = any(url.endswith(domain) or f'{domain}/' in url for domain in product_domains)
                
                if not has_product_domain:
                    logger.debug(f"Filtered non-product domain: {name}")
                    return False
                
                # URL should be short (product homepage, not deep article)
                url_parts = url.split('/')
                if len(url_parts) > 5:  # Too many path segments = likely article
                    logger.debug(f"Filtered deep URL: {name}")
                    return False
            
            return True
        
        filtered = [comp for comp in competitors if is_valid_competitor(comp)]
        logger.info(f"Filtered {len(competitors) - len(filtered)} non-competitors")
        return filtered
    
    @staticmethod
    def _classify_competitors(
        product_info: Dict[str, Any],
        competitors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Step 4: Compute similarity and classify as Direct/Indirect/Not a Competitor
        Uses CompetitorClassifier to calculate similarity scores
        """
        from .competitor_classifier import CompetitorClassifier
        
        classified = CompetitorClassifier.classify_competitors(
            product_info=product_info,
            competitors=competitors
        )
        
        # Get classification summary
        summary = CompetitorClassifier.get_classification_summary(classified)
        logger.info(f"Direct: {summary['direct']}, Indirect: {summary['indirect']}, "
                   f"Avg similarity (direct): {summary['avg_similarity_direct']:.3f}")
        
        return classified
    
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
    async def _llm_select_top_competitors(
        product_info: Dict[str, Any],
        classified_competitors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Step 5: LLM Verification - Select Top 5 Competitors
        LLM reviews all classified competitors and selects the most relevant 5
        """
        # If we have 5 or fewer, return all
        if len(classified_competitors) <= 5:
            return classified_competitors
        
        # Prepare prompt for LLM
        prompt = f"""You are a competitive intelligence analyst. Review the following competitors and select the TOP 5 most relevant competitors for the user's product.

USER'S PRODUCT:
Name: {product_info['name']}
Description: {product_info['description']}
Features: {', '.join(product_info.get('features', []))}

COMPETITORS TO REVIEW ({len(classified_competitors)} total):
"""
        
        for i, comp in enumerate(classified_competitors[:20], 1):  # Limit to top 20 for token efficiency
            comp_type = comp.get('competitor_type', 'unknown')
            similarity = comp.get('similarity_score', 0)
            prompt += f"\n{i}. {comp['name']} ({comp_type.upper()}, {similarity*100:.1f}% similar)"
            prompt += f"\n   Source: {comp.get('source')}"
            prompt += f"\n   Description: {comp.get('description', 'N/A')[:100]}"
        
        prompt += """

INSTRUCTIONS:
1. Select the TOP 5 most relevant competitors
2. Prioritize DIRECT competitors over indirect
3. Consider similarity scores, descriptions, and sources
4. Return ONLY a JSON array of competitor names

Example response:
["Competitor 1", "Competitor 2", "Competitor 3", "Competitor 4", "Competitor 5"]

Return ONLY the JSON array, nothing else:"""
        
        try:
            # Try to get LLM selection
            from .llm_keyword_service import LLMKeywordService
            import json
            import re
            
            # Use the same LLM service
            groq_keys = LLMKeywordService._get_groq_keys()
            
            if groq_keys:
                import requests
                
                for api_key in groq_keys:
                    try:
                        response = requests.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": "llama-3.3-70b-versatile",
                                "messages": [
                                    {"role": "system", "content": "You are a competitive intelligence analyst. Return only valid JSON."},
                                    {"role": "user", "content": prompt}
                                ],
                                "temperature": 0.1,
                                "max_tokens": 500
                            },
                            timeout=15
                        )
                        
                        if response.status_code == 200:
                            llm_response = response.json()["choices"][0]["message"]["content"].strip()
                            
                            # Extract JSON array
                            json_match = re.search(r'\[.*?\]', llm_response, re.DOTALL)
                            if json_match:
                                selected_names = json.loads(json_match.group())
                                
                                # Find competitors by name
                                top_5 = []
                                for name in selected_names[:5]:
                                    for comp in classified_competitors:
                                        if comp['name'].lower() == name.lower():
                                            top_5.append(comp)
                                            break
                                
                                if len(top_5) >= 3:  # At least 3 valid selections
                                    logger.info(f"LLM selected: {[c['name'] for c in top_5]}")
                                    return top_5
                        
                    except Exception as e:
                        logger.warning(f"LLM selection attempt failed: {str(e)}")
                        continue
        
        except Exception as e:
            logger.warning(f"LLM selection failed: {str(e)}")
        
        # Fallback: Select top 5 by quality score
        logger.info("Using fallback selection (quality score)")
        scored = []
        for comp in classified_competitors:
            score = 0
            # Prioritize direct competitors
            if comp.get('competitor_type') == 'direct':
                score += 10
            # Add similarity score
            score += comp.get('similarity_score', 0) * 10
            # Add data quality
            if comp.get('description'): score += 2
            if comp.get('features'): score += 3
            if comp.get('url'): score += 1
            
            scored.append({**comp, 'selection_score': score})
        
        sorted_comps = sorted(scored, key=lambda x: x['selection_score'], reverse=True)
        return sorted_comps[:5]
    
    @staticmethod
    async def _scrape_top_competitors(
        top_competitors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Step 6: Web Scraping - Extract Features & Pricing for Top 5
        Scrapes competitor websites to get detailed feature lists and pricing
        """
        scraper = get_web_scraper_service()
        enriched = []
        
        for comp in top_competitors:
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
                        'product_type': result.get('product_type'),
                        'key_benefits': result.get('key_benefits', [])
                    })
                    logger.info(f"  ✓ Scraped: {comp['name']}")
                else:
                    enriched.append(comp)
                    logger.warning(f"  ✗ Scraping failed: {comp['name']}")
            except Exception as e:
                logger.warning(f"  ✗ Failed to scrape {comp['name']}: {str(e)}")
                enriched.append(comp)
        
        return enriched
    
    @staticmethod
    async def _llm_structure_output(
        product_info: Dict[str, Any],
        top_5_enriched: List[Dict[str, Any]],
        all_classified_competitors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Step 7: LLM Structures Output for Comparison Dashboard
        LLM takes scraped data and structures it for frontend display
        """
        try:
            # Prepare data for LLM
            preprocessed = {
                "statistics": {
                    "total_competitors": len(all_classified_competitors),
                    "direct_competitors": sum(1 for c in all_classified_competitors if c.get('competitor_type') == 'direct'),
                    "indirect_competitors": sum(1 for c in all_classified_competitors if c.get('competitor_type') == 'indirect')
                },
                "top_competitors": top_5_enriched,
                "all_features": [],
                "pricing_info": []
            }
            
            # Collect features and pricing from enriched competitors
            for comp in top_5_enriched:
                if comp.get('features'):
                    preprocessed["all_features"].extend(comp['features'])
                if comp.get('pricing'):
                    preprocessed["pricing_info"].append({
                        "competitor": comp['name'],
                        "pricing": comp['pricing']
                    })
            
            # LLM analysis for insights and structuring
            llm_analysis = await LLMAnalysisService.generate_competitive_analysis(
                product_info=product_info,
                preprocessed_data=preprocessed
            )
            
            return {
                "preprocessed": preprocessed,
                "llm_analysis": llm_analysis
            }
        except Exception as e:
            logger.error(f"LLM structuring failed: {str(e)}")
            return {"preprocessed": {}, "llm_analysis": {}}
    
    @staticmethod
    def _build_clean_response(
        product_info: Dict[str, Any],
        keywords: List[str],
        top_5_enriched: List[Dict[str, Any]],
        all_classified_competitors: List[Dict[str, Any]],
        final_analysis: Dict[str, Any],
        analysis_id: str,
        execution_time: float
    ) -> Dict[str, Any]:
        """Build clean, user-friendly response for frontend"""
        
        preprocessed = final_analysis.get('preprocessed', {})
        llm_analysis = final_analysis.get('llm_analysis', {})
        
        # Get classification summary from all competitors
        from .competitor_classifier import CompetitorClassifier
        classification_summary = CompetitorClassifier.get_classification_summary(all_classified_competitors)
        
        # Clean top 5 competitors for response
        clean_top_5 = []
        for comp in top_5_enriched:
            clean_comp = {
                "name": comp['name'],
                "description": comp.get('description', ''),
                "url": comp.get('url', ''),
                "features": comp.get('features', []),
                "pricing": comp.get('pricing'),
                "target_audience": comp.get('target_audience'),
                "source": comp.get('source', 'unknown'),
                "competitor_type": comp.get('competitor_type'),
                "similarity_score": comp.get('similarity_score')
            }
            clean_top_5.append(clean_comp)
        
        # Build feature matrix from enriched top 5
        feature_matrix = ProductionPipelineService._build_feature_matrix(
            product_info, top_5_enriched
        )
        
        # Build comparison data
        comparison = ProductionPipelineService._build_comparison(
            product_info, top_5_enriched, llm_analysis
        )
        
        # Build gap analysis
        gap_analysis = ProductionPipelineService._build_gap_analysis(llm_analysis)
        
        # Calculate market saturation
        total_comps = len(all_classified_competitors)
        if total_comps < 5:
            market_saturation = "low"
            opportunity_score = 8.5
        elif total_comps < 15:
            market_saturation = "medium"
            opportunity_score = 6.5
        else:
            market_saturation = "high"
            opportunity_score = 4.5
        
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
            
            # Top 5 competitors (LLM selected + scraped)
            "top_competitors": clean_top_5,
            
            # Feature comparison matrix
            "feature_matrix": feature_matrix,
            
            # Comparison dashboard data
            "comparison": comparison,
            
            # Gap analysis
            "gap_analysis": gap_analysis,
            
            # Strategic insights (LLM structured)
            "insights": {
                "market_position": llm_analysis.get('market_position', ''),
                "competitive_advantages": llm_analysis.get('competitive_advantages', []),
                "differentiation_strategy": llm_analysis.get('differentiation_strategy', ''),
                "recommendations": llm_analysis.get('recommendations', [])
            },
            
            # Market insights with classification
            "market_insights": {
                "total_competitors": total_comps,
                "direct_competitors": classification_summary['direct'],
                "indirect_competitors": classification_summary['indirect'],
                "market_saturation": market_saturation,
                "opportunity_score": opportunity_score
            },
            
            # Classification summary
            "classification_summary": classification_summary,
            
            # Metadata
            "metadata": {
                "total_competitors_analyzed": total_comps,
                "top_competitors_selected": len(top_5_enriched),
                "timestamp": datetime.now().isoformat()
            }
        }
    

    
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
