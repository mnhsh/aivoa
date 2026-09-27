from fastapi import APIRouter

from app.api.routes import analyze, deviations, documents, health, knowledge, workflow

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(documents.router)
api_router.include_router(analyze.router)
api_router.include_router(deviations.router)
api_router.include_router(workflow.router)
api_router.include_router(knowledge.router)
