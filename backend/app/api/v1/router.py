from fastapi import APIRouter
from app.api.v1.routes import services, incidents, rag

api_v1_router = APIRouter()

api_v1_router.include_router(services.router, prefix="/services", tags=["Services"])
api_v1_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_v1_router.include_router(rag.router, prefix="/rag", tags=["RAG Knowledge Engine"])
