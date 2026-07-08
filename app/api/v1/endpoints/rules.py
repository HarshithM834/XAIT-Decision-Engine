from fastapi import APIRouter, Depends
from app.rules.evaluator import load_rules
from app.rules.models import RulesConfig
from app.core.security import get_api_key
import yaml

router = APIRouter()

@router.get("", response_model=RulesConfig)
async def get_rules(api_key: str = Depends(get_api_key)):
    """Returns the currently loaded rules."""
    return load_rules()

@router.post("/validate")
async def validate_rules(config_body: str, api_key: str = Depends(get_api_key)):
    """Validates a YAML string as a valid rules configuration."""
    try:
        data = yaml.safe_load(config_body)
        config = RulesConfig(**data)
        return {"status": "valid", "rules_count": len(config.rules)}
    except Exception as e:
        return {"status": "invalid", "error": str(e)}
