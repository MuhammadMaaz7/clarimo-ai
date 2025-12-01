from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Authentication routes
from app.api.routes_auth import router as auth_router

# Module 1: Pain Point Discovery routes
from app.api.module1_pain_points.routes_problems import router as problems_router
from app.api.module1_pain_points.routes_user_input import router as user_input_router
from app.api.module1_pain_points.routes_keywords import router as keywords_router
from app.api.module1_pain_points.routes_reddit import router as reddit_router
from app.api.module1_pain_points.routes_embeddings import router as embeddings_router
from app.api.module1_pain_points.routes_semantic_filtering import router as semantic_filtering_router
from app.api.module1_pain_points.routes_processing_status import router as processing_status_router
from app.api.module1_pain_points.routes_clustering import router as clustering_router
from app.api.module1_pain_points.routes_pain_points import router as pain_points_router
from app.api.module1_pain_points.routes_ranking import router as ranking_router

# Module 2: Idea Validation routes
from app.api.module2_validation.routes_ideas import router as ideas_router
from app.api.module2_validation.routes_validations import router as validations_router
from app.api.module2_validation.routes_shared import router as shared_router

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
app.include_router(ranking_router, prefix="/api")
app.include_router(processing_status_router, prefix="/api")
app.include_router(ideas_router, prefix="/api")
app.include_router(validations_router, prefix="/api")
app.include_router(shared_router, prefix="/api")  # Public shared validations (no auth required)

@app.get("/")
async def root():
    return {"message": "Clarimo AI Backend is running successfully 🚀"}

@app.get("/api/performance/{input_id}")
async def get_performance_metrics(input_id: str):
    """Get performance metrics for a specific input"""
    from fastapi import HTTPException
    from app.services.shared.performance_logger import performance_logger
    
    summary = performance_logger.get_pipeline_summary(input_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Pipeline not found or completed")
    
    return summary
