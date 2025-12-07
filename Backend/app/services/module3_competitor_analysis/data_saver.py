"""
Data Saver Service for Competitor Analysis
Saves analysis data to JSON files for later review and debugging
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class CompetitorDataSaver:
    """Save competitor analysis data to JSON files with organized folder structure"""
    
    # Base data directory
    BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "competitor_analysis")
    
    # Organized subdirectories
    KEYWORDS_DIR = os.path.join(BASE_DIR, "1_keywords")
    RAW_COMPETITORS_DIR = os.path.join(BASE_DIR, "2_raw_competitors")
    ENRICHED_DIR = os.path.join(BASE_DIR, "3_enriched_data")
    FINAL_ANALYSIS_DIR = os.path.join(BASE_DIR, "4_final_analysis")
    
    @classmethod
    def _ensure_data_dirs(cls):
        """Ensure all data directories exist"""
        os.makedirs(cls.BASE_DIR, exist_ok=True)
        os.makedirs(cls.KEYWORDS_DIR, exist_ok=True)
        os.makedirs(cls.RAW_COMPETITORS_DIR, exist_ok=True)
        os.makedirs(cls.ENRICHED_DIR, exist_ok=True)
        os.makedirs(cls.FINAL_ANALYSIS_DIR, exist_ok=True)
    
    @classmethod
    def save_keywords(
        cls,
        analysis_id: str,
        product_name: str,
        keywords: List[str],
        method: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Save generated keywords to JSON file in 1_keywords folder
        
        Args:
            analysis_id: ID of the analysis
            product_name: Name of the product
            keywords: List of generated keywords
            method: Method used (llm, simple, etc.)
            metadata: Additional metadata
            
        Returns:
            Path to saved file
        """
        try:
            cls._ensure_data_dirs()
            
            timestamp = datetime.utcnow().isoformat()
            # Simple filename: keywords_{analysis_id}.json
            filename = f"keywords_{analysis_id}.json"
            filepath = os.path.join(cls.KEYWORDS_DIR, filename)
            
            data = {
                "analysis_id": analysis_id,
                "product_name": product_name,
                "keywords": keywords,
                "method": method,
                "metadata": metadata or {},
                "timestamp": timestamp
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved keywords to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving keywords: {str(e)}")
            return ""
    
    @classmethod
    def save_raw_competitors(
        cls,
        analysis_id: str,
        product_name: str,
        competitors: List[Dict[str, Any]],
        source: str
    ) -> str:
        """
        Save raw competitor data from a specific source (before enrichment)
        Saved in 2_raw_competitors folder
        
        Args:
            analysis_id: ID of the analysis
            product_name: Name of the product
            competitors: List of competitor data
            source: Source name (product_hunt, github, google_search, etc.)
            
        Returns:
            Path to saved file
        """
        try:
            cls._ensure_data_dirs()
            
            timestamp = datetime.utcnow().isoformat()
            # Simple filename: {source}_{analysis_id}.json
            filename = f"{source}_{analysis_id}.json"
            filepath = os.path.join(cls.RAW_COMPETITORS_DIR, filename)
            
            data = {
                "analysis_id": analysis_id,
                "product_name": product_name,
                "source": source,
                "competitors": competitors,
                "count": len(competitors),
                "timestamp": timestamp
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(competitors)} raw competitors from {source}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving raw competitors from {source}: {str(e)}")
            return ""
    
    @classmethod
    def save_enriched_competitors(
        cls,
        analysis_id: str,
        product_name: str,
        competitors: List[Dict[str, Any]]
    ) -> str:
        """
        Save enriched competitor data (after web scraping)
        Saved in 3_enriched_data folder
        
        Args:
            analysis_id: ID of the analysis
            product_name: Name of the product
            competitors: List of enriched competitor data
            
        Returns:
            Path to saved file
        """
        try:
            cls._ensure_data_dirs()
            
            timestamp = datetime.utcnow().isoformat()
            # Simple filename: enriched_{analysis_id}.json
            filename = f"enriched_{analysis_id}.json"
            filepath = os.path.join(cls.ENRICHED_DIR, filename)
            
            enriched_count = sum(1 for c in competitors if c.get('enriched'))
            
            data = {
                "analysis_id": analysis_id,
                "product_name": product_name,
                "total_competitors": len(competitors),
                "enriched_count": enriched_count,
                "basic_count": len(competitors) - enriched_count,
                "competitors": competitors,
                "timestamp": timestamp
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(competitors)} enriched competitors ({enriched_count} with details)")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving enriched competitors: {str(e)}")
            return ""
    
    @classmethod
    def save_final_analysis(
        cls,
        analysis_id: str,
        product_name: str,
        all_data: Dict[str, Any]
    ) -> str:
        """
        Save complete final analysis results
        Saved in 4_final_analysis folder
        
        Args:
            analysis_id: ID of the analysis
            product_name: Name of the product
            all_data: Complete analysis data
            
        Returns:
            Path to saved file
        """
        try:
            cls._ensure_data_dirs()
            
            timestamp = datetime.utcnow().isoformat()
            # Simple filename: analysis_{analysis_id}.json
            filename = f"analysis_{analysis_id}.json"
            filepath = os.path.join(cls.FINAL_ANALYSIS_DIR, filename)
            
            data = {
                "analysis_id": analysis_id,
                "product_name": product_name,
                "timestamp": timestamp,
                **all_data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved final analysis to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving final analysis: {str(e)}")
            return ""
    
    @classmethod
    def load_analysis(cls, analysis_id: str) -> Dict[str, Any]:
        """
        Load saved analysis data from final_analysis folder
        
        Args:
            analysis_id: ID of the analysis
            
        Returns:
            Analysis data or empty dict if not found
        """
        try:
            filename = f"analysis_{analysis_id}.json"
            filepath = os.path.join(cls.FINAL_ANALYSIS_DIR, filename)
            
            if not os.path.exists(filepath):
                logger.warning(f"Analysis file not found: {filepath}")
                return {}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded analysis from: {filepath}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading analysis: {str(e)}")
            return {}
    
    @classmethod
    def list_saved_analyses(cls) -> List[Dict[str, Any]]:
        """
        List all saved analyses from final_analysis folder
        
        Returns:
            List of analysis metadata
        """
        try:
            cls._ensure_data_dirs()
            
            analyses = []
            if os.path.exists(cls.FINAL_ANALYSIS_DIR):
                for filename in os.listdir(cls.FINAL_ANALYSIS_DIR):
                    if filename.startswith("analysis_") and filename.endswith(".json"):
                        filepath = os.path.join(cls.FINAL_ANALYSIS_DIR, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            analyses.append({
                                "analysis_id": data.get("analysis_id"),
                                "product_name": data.get("product_name"),
                                "timestamp": data.get("timestamp"),
                                "filepath": filepath
                            })
                        except Exception as e:
                            logger.error(f"Error reading {filename}: {str(e)}")
            
            # Sort by timestamp descending
            analyses.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return analyses
            
        except Exception as e:
            logger.error(f"Error listing analyses: {str(e)}")
            return []
