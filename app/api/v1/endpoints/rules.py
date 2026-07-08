from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.persistence.database import get_db
from app.persistence.models import Rule as DBRule, RuleCondition, RuleAction
from app.rules.models import RuleDefinition
from app.core.security import get_api_key

router = APIRouter()

def _map_to_pydantic(db_rule: DBRule) -> dict:
    return {
        "rule_id": db_rule.rule_id,
        "name": db_rule.name,
        "description": db_rule.description,
        "enabled": db_rule.enabled,
        "priority": db_rule.priority,
        "condition_group": db_rule.condition_group,
        "conditions": [{"field": c.field, "operator": c.operator, "value": c.value} for c in db_rule.conditions],
        "outcome": {
            "decision_effect": db_rule.decision_effect,
            "actions": [{"type": a.type} for a in db_rule.actions],
            "rationale_template": db_rule.rationale_template
        }
    }

@router.get("", response_model=List[RuleDefinition])
async def get_rules(db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """Fetch all configured rules from the database."""
    rules = db.query(DBRule).all()
    return [_map_to_pydantic(r) for r in rules]

@router.post("", response_model=RuleDefinition)
async def create_rule(rule: RuleDefinition, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """Create a new rule."""
    existing = db.query(DBRule).filter(DBRule.rule_id == rule.rule_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Rule with id {rule.rule_id} already exists.")
    
    db_rule = DBRule(
        rule_id=rule.rule_id,
        name=rule.name,
        description=rule.description,
        enabled=rule.enabled,
        priority=rule.priority,
        condition_group=rule.condition_group,
        decision_effect=rule.outcome.decision_effect,
        rationale_template=rule.outcome.rationale_template
    )
    db.add(db_rule)
    db.flush()

    for cond in rule.conditions:
        db.add(RuleCondition(rule_id=db_rule.id, field=cond.field, operator=cond.operator, value=cond.value))
    
    for act in rule.outcome.actions:
        db.add(RuleAction(rule_id=db_rule.id, type=act.type))

    db.commit()
    return _map_to_pydantic(db_rule)

@router.put("/{rule_id}", response_model=RuleDefinition)
async def update_rule(rule_id: str, rule: RuleDefinition, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """Update an existing rule."""
    db_rule = db.query(DBRule).filter(DBRule.rule_id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    
    # Update primitive fields
    db_rule.name = rule.name
    db_rule.description = rule.description
    db_rule.enabled = rule.enabled
    db_rule.priority = rule.priority
    db_rule.condition_group = rule.condition_group
    db_rule.decision_effect = rule.outcome.decision_effect
    db_rule.rationale_template = rule.outcome.rationale_template

    # Replace conditions and actions
    db.query(RuleCondition).filter(RuleCondition.rule_id == db_rule.id).delete()
    db.query(RuleAction).filter(RuleAction.rule_id == db_rule.id).delete()

    for cond in rule.conditions:
        db.add(RuleCondition(rule_id=db_rule.id, field=cond.field, operator=cond.operator, value=cond.value))
    
    for act in rule.outcome.actions:
        db.add(RuleAction(rule_id=db_rule.id, type=act.type))

    db.commit()
    return _map_to_pydantic(db_rule)

@router.delete("/{rule_id}")
async def delete_rule(rule_id: str, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """Delete a rule."""
    db_rule = db.query(DBRule).filter(DBRule.rule_id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    
    db.delete(db_rule)
    db.commit()
    return {"status": "success", "message": f"Rule {rule_id} deleted."}
