from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_auth import router as auth_router
from app.api.routes_problems import router as problems_router
from app.api.routes_user_input import router as user_input_router
from app.api.routes_keywords import router as keywords_router
from app.api.routes_reddit import router as reddit_router
from app.api.routes_embeddings import router as embeddings_router
from app.api.routes_semantic_filtering import router as semantic_filtering_router
from app.api.routes_processing_status import router as processing_status_router
from app.api.routes_clustering import router as clustering_router
from app.api.routes_pain_points import router as pain_points_router

app = FastAPI(title="Clarimo AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth_router, prefix="/api")
app.include_router(problems_router, prefix="/api")
app.include_router(user_input_router, prefix="/api")
app.include_router(keywords_router, prefix="/api")
app.include_router(reddit_router, prefix="/api")
app.include_router(embeddings_router, prefix="/api")
app.include_router(semantic_filtering_router, prefix="/api")
app.include_router(clustering_router, prefix="/api")
app.include_router(pain_points_router, prefix="/api")
app.include_router(processing_status_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Clarimo AI Backend is running successfully 🚀"}

@app.get("/api/performance/{input_id}")
async def get_performance_metrics(input_id: str):
    """Get performance metrics for a specific input"""
    from fastapi import HTTPException
    from app.services.performance_logger import performance_logger
    
    summary = performance_logger.get_pipeline_summary(input_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Pipeline not found or completed")
    
    return summary
