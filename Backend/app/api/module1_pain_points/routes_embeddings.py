"""
Embeddings API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import logging
from pathlib import Path

from app.db.models.user_model import UserResponse
from app.core.security import get_current_user
from app.services.module1_pain_points.embedding_service import embedding_service
from app.services.shared.processing_lock_service import processing_lock_service, ProcessingStage
from app.services.module1_pain_points.user_input_service import UserInputService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/embeddings", tags=["Embeddings"])


@router.post("/generate/{input_id}")
async def generate_embeddings_for_input(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user),
    use_gpu: bool = Query(False, description="Use CPU processing (recommended)"),
    batch_size: int = Query(32, ge=1, le=128, description="Batch size for embedding generation")
):
    """
    Manually trigger embedding generation for a specific input.
    
    This endpoint allows manual embedding generation if automatic generation failed
    or if you want to regenerate with different parameters.
    """
    try:
        logger.info(f"Manual embedding generation requested for input {input_id} by user {current_user.id}")
        
        # Check if process is already running
        if await processing_lock_service.is_processing(current_user.id, input_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Processing already in progress for this input"
            )
        
        # Acquire processing lock
        lock_acquired = await processing_lock_service.acquire_lock(current_user.id, input_id)
        if not lock_acquired:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Processing already in progress for this input"
            )
        
        # Update processing stage
        await processing_lock_service.update_stage(current_user.id, input_id, ProcessingStage.EMBEDDINGS)
        await UserInputService.update_processing_stage(current_user.id, input_id, ProcessingStage.EMBEDDINGS.value)
        
        # Find the Reddit JSON file for this input
        reddit_files_dir = Path("data/reddit_posts") / current_user.id
        if not reddit_files_dir.exists():
            await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Reddit data found for this user"
            )
        
        # Look for Reddit JSON files for this input
        pattern = f"reddit_posts_{input_id}_*.json"
        reddit_files = list(reddit_files_dir.glob(pattern))
        
        if not reddit_files:
            await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Reddit data files found for this input"
            )
        
        # Use the most recent file
        reddit_file = max(reddit_files, key=lambda f: f.stat().st_ctime)
        
        # Generate embeddings
        result = await embedding_service.generate_embeddings_for_reddit_data(
            user_id=current_user.id,
            input_id=input_id,
            reddit_json_path=str(reddit_file),
            use_gpu=use_gpu,
            batch_size=batch_size
        )
        
        if result["success"]:
            logger.info(f"Manual embedding generation completed for input {input_id}")
            # Don't release lock here - let the pipeline continue to next stage
            return {
                "success": True,
                "message": result["message"],
                "documents_processed": result["documents_processed"],
                "output_directory": result["output_directory"],
                "files_created": result["files_created"]
            }
        else:
            logger.error(f"Manual embedding generation failed for input {input_id}: {result.get('error')}")
            await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Embedding generation failed: {result.get('message')}"
            )
        
    except HTTPException:
        # Release lock on HTTP exceptions
        await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
        raise
    except Exception as e:
        logger.error(f"Error in manual embedding generation for input {input_id}: {str(e)}")
        await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {str(e)}"
        )


@router.get("/")
async def get_user_embeddings(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get list of embeddings for the authenticated user.
    """
    try:
        logger.info(f"Getting embeddings for user {current_user.id}")
        
        embeddings = await embedding_service.list_user_embeddings(current_user.id)
        
        logger.info(f"Retrieved {len(embeddings)} embedding records for user {current_user.id}")
        return {
            "embeddings": embeddings,
            "total_embeddings": len(embeddings)
        }
        
    except Exception as e:
        logger.error(f"Error getting embeddings for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get embeddings: {str(e)}"
        )


@router.get("/status")
async def get_embedding_system_status(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get status of the embedding system (conda environment, dependencies, etc.).
    """
    try:
        logger.info(f"Checking embedding system status for user {current_user.id}")
        
        return {
            "system_status": "CPU-based embedding service (no external dependencies)",
            "model_name": "mixedbread-ai/mxbai-embed-large-v1",
            "default_gpu": embedding_service.use_gpu,
            "default_batch_size": embedding_service.batch_size,
            "processing_mode": "CPU (simple and reliable)"
        }
        
    except Exception as e:
        logger.error(f"Error checking embedding system status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check system status: {str(e)}"
        )


@router.get("/{input_id}")
async def get_embedding_details(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get details of embeddings for a specific input.
    """
    try:
        logger.info(f"Getting embedding details for input {input_id} (user: {current_user.id})")
        
        # Check if embeddings exist for this input
        embeddings_dir = Path("data/embeddings") / current_user.id / input_id
        if not embeddings_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No embeddings found for this input"
            )
        
        # Get metadata
        metadata_file = embeddings_dir / "faiss_metadata.json"
        metadata = {}
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        
        # List files in the embeddings directory
        files = []
        for file_path in embeddings_dir.iterdir():
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                    "created_at": file_path.stat().st_ctime
                })
        
        return {
            "input_id": input_id,
            "embeddings_dir": str(embeddings_dir),
            "metadata": metadata,
            "files": files,
            "total_files": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting embedding details for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get embedding details: {str(e)}"
        )


@router.delete("/{input_id}")
async def delete_embeddings(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete embeddings for a specific input.
    """
    try:
        logger.info(f"Deleting embeddings for input {input_id} (user: {current_user.id})")
        
        # Check if embeddings exist
        embeddings_dir = Path("data/embeddings") / current_user.id / input_id
        if not embeddings_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No embeddings found for this input"
            )
        
        # Delete the entire embeddings directory
        import shutil
        shutil.rmtree(embeddings_dir)
        
        logger.info(f"Successfully deleted embeddings for input {input_id}")
        return {
            "success": True,
            "message": f"Embeddings deleted for input {input_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting embeddings for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete embeddings: {str(e)}"
        )

@router.get("/cache/stats")
async def get_cache_statistics(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get global embedding cache statistics
    
    Shows tiered cache performance with exact, normalized, and semantic matching.
    The optimized cache uses multiple strategies to maximize cache hit rates.
    """
    try:
        logger.info(f"Getting cache statistics for user {current_user.id}")
        
        stats = embedding_service.get_cache_statistics()
        
        return {
            "success": True,
            "cache_statistics": stats,
            "explanation": {
                "purpose": "Tiered cache system with exact, normalized, and semantic matching",
                "scope": "Global cache shared across all users and inputs",
                "benefit": "Dramatically improved cache hit rates through intelligent text matching",
                "tiers": {
                    "exact": "Direct hash match (fastest)",
                    "normalized": "Text normalization for variations (fast)",
                    "semantic": "Cosine similarity for similar content (comprehensive)"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting cache statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}"
        )


@router.delete("/cache/clear")
async def clear_embedding_cache(
    current_user: UserResponse = Depends(get_current_user),
    cache_type: str = Query("all", description="Cache type to clear: 'all', 'optimized', or 'legacy'")
):
    """
    Clear the global embedding cache
    
    This will remove cached embeddings based on the cache_type parameter.
    - 'all': Clear both optimized and legacy caches
    - 'optimized': Clear only the new tiered cache
    - 'legacy': Clear only the old simple cache
    
    Note: This affects all users since the cache is global.
    """
    try:
        logger.info(f"Clearing {cache_type} embedding cache requested by user {current_user.id}")
        
        if cache_type not in ["all", "optimized", "legacy"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cache_type. Must be 'all', 'optimized', or 'legacy'"
            )
        
        result = await embedding_service.clear_global_cache(cache_type)
        
        if result["success"]:
            logger.info(f"Cache cleared: {result['embeddings_removed']} embeddings, {result['space_freed_mb']} MB freed")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.post("/cache/migrate")
async def migrate_legacy_cache(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Migrate legacy cache to optimized cache structure
    
    This endpoint migrates embeddings from the old simple cache format
    to the new optimized tiered cache system. This is typically done
    automatically, but can be triggered manually if needed.
    """
    try:
        logger.info(f"Cache migration requested by user {current_user.id}")
        
        result = embedding_service.migrate_legacy_cache()
        
        if result["success"]:
            logger.info(f"Cache migration completed: {result['migrated_count']} embeddings migrated")
        
        return result
        
    except Exception as e:
        logger.error(f"Error migrating cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to migrate cache: {str(e)}"
        )