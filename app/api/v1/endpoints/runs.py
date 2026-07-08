from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.persistence.database import get_db
from app.schemas.run import RestartRequest
from app.schemas.decision import DecisionResponse
from app.services.engine import DecisionEngine
from app.services.run_manager import RunManager
from app.core.security import get_api_key

router = APIRouter()

@router.get("/{run_id}", response_model=DecisionResponse)
async def get_run(run_id: str, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    engine = DecisionEngine(db)
    run = engine.run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return engine._build_decision_response(run)

@router.get("/by-record/{record_id}", response_model=DecisionResponse)
async def get_run_by_record(record_id: str, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    engine = DecisionEngine(db)
    run = engine.run_manager.get_latest_run_by_record(record_id)
    if not run:
        raise HTTPException(status_code=404, detail="No runs found for this record")
    return engine._build_decision_response(run)

@router.post("/{run_id}/restart", response_model=DecisionResponse)
async def restart_run(run_id: str, request: RestartRequest, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    engine = DecisionEngine(db)
    return engine.process_restart(run_id, request)
