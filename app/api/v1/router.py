from fastapi import APIRouter

from app.api.v1.endpoints import decisions, runs, rules, health

api_router = APIRouter()

api_router.include_router(decisions.router, prefix="/decisions", tags=["decisions"])
api_router.include_router(runs.router, prefix="/runs", tags=["runs"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])

# Health doesn't necessarily need a prefix, but let's put it under the API directly
api_router.include_router(health.router, tags=["health"])
