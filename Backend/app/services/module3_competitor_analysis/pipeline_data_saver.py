"""
Pipeline Data Saver
Saves data at every step of the competitor analysis pipeline
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PipelineDataSaver:
    """Saves pipeline data at each step"""
    
    BASE_DIR = "data/competitor_analysis"
    
    @staticmethod
    def _ensure_directory(path: str):
        """Ensure directory exists"""
        os.makedirs(path, exist_ok=True)
    
    @staticmethod
    def _get_safe_filename(product_name: str, analysis_id: str) -> str:
        """Get safe filename from product name"""
        safe_name = product_name.replace(" ", "_").replace("/", "_").lower()
        return f"{safe_name}_{analysis_id}"
    
    @staticmethod
    def save_step_1_keywords(
        analysis_id: str,
        product_name: str,
        keywords: List[str],
        method: str = "llm"
    ):
        """Save Step 1: Generated Keywords"""
        try:
            dir_path = os.path.join(PipelineDataSaver.BASE_DIR, "1_keywords")
            PipelineDataSaver._ensure_directory(dir_path)
            
            filename = PipelineDataSaver._get_safe_filename(product_name, analysis_id)
            filepath = os.path.join(dir_path, f"{filename}.json")
            
            data = {
                "analysis_id": analysis_id,
                "product_name": product_name,
                "keywords": keywords,
                "method": method,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Saved keywords to: 1_keywords/{filename}.json")
        except Exception as e:
            logger.error(f"Failed to save keywords: {str(e)}")
    
    @staticmethod
    def save_step_2_raw_competitors(
        analysis_id: str,
        product_name: str,
        competitors: List[Dict[str, Any]]
    ):
        """Save Step 2: Raw Competitors from APIs"""
        try:
            dir_path = os.path.join(PipelineDataSaver.BASE_DIR, "2_raw_competitors")
            PipelineDataSaver._ensure_directory(dir_path)
            
            filename = PipelineDataSaver._get_safe_filename(product_name, analysis_id)
            filepath = os.path.join(dir_path, f"{filename}.json")
            
            # Group by source
            by_source = {}
            for comp in competitors:
                source = comp.get('source', 'unknown')
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(comp)
            
            data = {
                "analysis_id": analysis_id,
                "product_name": product_name,
                "total_competitors": len(competitors),
                "by_source": {k: len(v) for k, v in by_source.items()},
                "competitors": competitors,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Saved raw competitors to: 2_raw_competitors/{filename}.json")
        except Exception as e:
            logger.error(f"Failed to save raw competitors: {str(e)}")
    
    @staticmethod
    def save_step_3_filtered_competitors(
        analysis_id: str,
        product_name: str,
        filtered_competitors: List[Dict[str, Any]],
        removed_count: int
    ):
        """Save Step 3: Filtered Competitors (after removing blogs/reddit)"""
        try:
            dir_path = os.path.join(PipelineDataSaver.BASE_DIR, "3_filtered_competitors")
            PipelineDataSaver._ensure_directory(dir_path)
            
            filename = PipelineDataSaver._get_safe_filename(product_name, analysis_id)
            filepath = os.path.join(dir_path, f"{filename}.json")
            
            data = {
                "analysis_id": analysis_id,
                "product_name": product_name,
                "total_after_filtering": len(filtered_competitors),
                "removed_count": removed_count,
                "competitors": filtered_competitors,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Saved filtered competitors to: 3_filtered_competitors/{filename}.json")
        except Exception as e:
            logger.error(f"Failed to save filtered competitors: {str(e)}")
    
    @staticmethod
    def save_step_4_classified_competitors(
        analysis_id: str,
        product_name: str,
        classified_competitors: List[Dict[str, Any]]
    ):
        """Save Step 4: Classified Competitors (direct/indirect)"""
        try:
            dir_path = os.path.join(PipelineDataSaver.BASE_DIR, "4_classified_competitors")
            PipelineDataSaver._ensure_directory(dir_path)
            
            filename = PipelineDataSaver._get_safe_filename(product_name, analysis_id)
            filepath = os.path.join(dir_path, f"{filename}.json")
            
            direct = [c for c in classified_competitors if c.get('competitor_type') == 'direct']
            indirect = [c for c in classified_competitors if c.get('competitor_type') == 'indirect']
            
            data = {
                "analysis_id": analysis_id,
                "product_name": product_name,
                "total_competitors": len(classified_competitors),
                "direct_count": len(direct),
                "indirect_count": len(indirect),
                "direct_competitors": direct,
                "indirect_competitors": indirect,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Saved classified competitors to: 4_classified_competitors/{filename}.json")
        except Exception as e:
            logger.error(f"Failed to save classified competitors: {str(e)}")
    
    @staticmethod
    def save_step_5_top_candidates(
        analysis_id: str,
        product_name: str,
        top_candidates: List[Dict[str, Any]]
    ):
        """Save Step 5: Top 10 Candidates selected by LLM"""
        try:
            dir_path = os.path.join(PipelineDataSaver.BASE_DIR, "5_top_candidates")
            PipelineDataSaver._ensure_directory(dir_path)
            
            filename = PipelineDataSaver._get_safe_filename(product_name, analysis_id)
            filepath = os.path.join(dir_path, f"{filename}.json")
            
            data = {
                "analysis_id": analysis_id,
                "product_name": product_name,
                "total_candidates": len(top_candidates),
                "candidates": top_candidates,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Saved top candidates to: 5_top_candidates/{filename}.json")
        except Exception as e:
            logger.error(f"Failed to save top candidates: {str(e)}")
    
    @staticmethod
    def save_step_6_enriched_competitors(
        analysis_id: str,
        product_name: str,
        enriched_competitors: List[Dict[str, Any]]
    ):
        """Save Step 6: Enriched Top 5 (with scraped/LLM features)"""
        try:
            dir_path = os.path.join(PipelineDataSaver.BASE_DIR, "6_enriched_competitors")
            PipelineDataSaver._ensure_directory(dir_path)
            
            filename = PipelineDataSaver._get_safe_filename(product_name, analysis_id)
            filepath = os.path.join(dir_path, f"{filename}.json")
            
            scraped = [c for c in enriched_competitors if c.get('data_source') == 'scraped']
            llm_extracted = [c for c in enriched_competitors if c.get('data_source') == 'llm_extracted']
            
            data = {
                "analysis_id": analysis_id,
                "product_name": product_name,
                "total_enriched": len(enriched_competitors),
                "scraped_count": len(scraped),
                "llm_extracted_count": len(llm_extracted),
                "competitors": enriched_competitors,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Saved enriched competitors to: 6_enriched_competitors/{filename}.json")
        except Exception as e:
            logger.error(f"Failed to save enriched competitors: {str(e)}")
    
    @staticmethod
    def save_step_7_final_analysis(
        analysis_id: str,
        product_name: str,
        final_response: Dict[str, Any]
    ):
        """Save Step 7: Final Analysis with Feature Matrix"""
        try:
            dir_path = os.path.join(PipelineDataSaver.BASE_DIR, "7_final_analysis")
            PipelineDataSaver._ensure_directory(dir_path)
            
            filename = PipelineDataSaver._get_safe_filename(product_name, analysis_id)
            filepath = os.path.join(dir_path, f"{filename}.json")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(final_response, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Saved final analysis to: 7_final_analysis/{filename}.json")
        except Exception as e:
            logger.error(f"Failed to save final analysis: {str(e)}")
