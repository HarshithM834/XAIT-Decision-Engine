from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.persistence.database import get_db

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "alive"}

@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
        
    return {
        "status": "ready" if db_status == "ok" else "not_ready",
        "database": db_status
    }
