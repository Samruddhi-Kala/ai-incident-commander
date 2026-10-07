from fastapi import APIRouter
from app.api.v1.routes import services, incidents, rag, tools, investigations, remediations, evaluations

api_v1_router = APIRouter()

api_v1_router.include_router(services.router, prefix="/services", tags=["Services"])
api_v1_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_v1_router.include_router(rag.router, prefix="/rag", tags=["RAG Knowledge Engine"])
api_v1_router.include_router(tools.router, prefix="/tools", tags=["Engineering Tools"])
api_v1_router.include_router(investigations.router, prefix="/investigations", tags=["Investigations"])
api_v1_router.include_router(remediations.router, prefix="/remediations", tags=["Remediation"])
api_v1_router.include_router(evaluations.router, prefix="/evaluations", tags=["AI Investigation Evaluations"])


