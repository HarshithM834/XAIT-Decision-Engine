from typing import List, Union, Any, Optional
from pydantic import BaseModel, Field

class RuleCondition(BaseModel):
    field: str
    operator: str  # equals, not_equals, greater_than, etc.
    value: Optional[Any] = None

class RuleAction(BaseModel):
    type: str # send_email, none

class RuleOutcome(BaseModel):
    decision_effect: str # require_additional_approval, no_additional_approval, etc.
    actions: List[RuleAction]
    rationale_template: str

class RuleDefinition(BaseModel):
    rule_id: str
    name: str
    description: Optional[str] = None
    enabled: bool = True
    priority: float = 0
    condition_group: str = "all" # all, any
    conditions: List[RuleCondition]
    outcome: RuleOutcome

class RulesConfig(BaseModel):
    rules: List[RuleDefinition]
