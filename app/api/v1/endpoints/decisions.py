from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.persistence.database import get_db
from app.schemas.payload import NormalizedPayload
from app.schemas.decision import DecisionResponse
from app.services.engine import DecisionEngine
from app.core.security import get_api_key

router = APIRouter()

from typing import Dict, Any
from app.services.mapper import PayloadMapper

@router.post("/evaluate", response_model=DecisionResponse)
async def evaluate_decision(
    raw_payload: Dict[str, Any],
    idempotency_key: str = Header(None),
    force: bool = False,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    # 1. Map arbitrary JSON to the normalized structure
    mapper = PayloadMapper()
    mapped_dict = mapper.map_payload(raw_payload)
    
    from pydantic import ValidationError
    from fastapi import HTTPException
    # 2. Validate against strict schema
    try:
        payload = NormalizedPayload(**mapped_dict)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    engine = DecisionEngine(db)
    return engine.process_evaluate(payload, force=force)
