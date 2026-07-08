from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import EngineException, engine_exception_handler, global_exception_handler

from app.api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description="XAIT Approval Decision Engine API",
    version="1.0.0",
)

app.include_router(api_router, prefix="/v1")

# Exception handlers
app.add_exception_handler(EngineException, engine_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# CORS Middleware (configurable if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    from app.persistence.database import engine, Base
    from app.persistence.seed import seed_rules
    # Create tables if they don't exist (useful for tests/dev without migrations)
    # But Alembic is preferred. We still run this just in case.
    Base.metadata.create_all(bind=engine)
    logger.info("Application starting up, database connected.")
    
    # Seed the initial database rules from YAML
    seed_rules()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")

# Base routes to check before API routers
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "XAIT Approval Decision Engine is running."}
