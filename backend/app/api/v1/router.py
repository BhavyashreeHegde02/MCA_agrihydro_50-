"""Version 1 of the API, assembled from its endpoint modules."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics, auth, crops, farms, irrigation, predictions, recommendations,
    water_intelligence,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(farms.router)
api_router.include_router(crops.router)
api_router.include_router(predictions.router)
api_router.include_router(irrigation.router)
api_router.include_router(analytics.router)
api_router.include_router(recommendations.router)
api_router.include_router(water_intelligence.router)
