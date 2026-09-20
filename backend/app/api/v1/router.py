from fastapi import APIRouter
from app.api.v1.routes import services, incidents

api_v1_router = APIRouter()

api_v1_router.include_router(services.router, prefix="/services", tags=["Services"])
api_v1_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
