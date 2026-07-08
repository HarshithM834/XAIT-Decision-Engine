from typing import Dict, Any, List, Tuple
from app.rules.models import RuleDefinition
from app.core.logging import logger

def get_field_value(payload: Dict[str, Any], path: str) -> Any:
    """Gets a value from a nested dictionary using a dotted path."""
    keys = path.split('.')
    val = payload
    for key in keys:
        if isinstance(val, dict) and key in val:
            val = val[key]
        else:
            return None
    return val

class RuleEvaluator:
    def __init__(self, rules: List[RuleDefinition]):
        self.rules = sorted([r for r in rules if r.enabled], key=lambda x: x.priority, reverse=True)

    def evaluate(self, payload: Dict[str, Any]) -> List[RuleDefinition]:
        triggered = []
        for rule in self.rules:
            if self._evaluate_rule(rule, payload):
                triggered.append(rule)
        return triggered

    def _evaluate_rule(self, rule: RuleDefinition, payload: Dict[str, Any]) -> bool:
        if not rule.conditions:
            return False

        results = []
        for condition in rule.conditions:
            field_value = get_field_value(payload, condition.field)
            res = self._evaluate_condition(condition.operator, field_value, condition.value)
            results.append(res)

        if rule.condition_group == "all":
            return all(results)
        elif rule.condition_group == "any":
            return any(results)
        return False

    def _evaluate_condition(self, op: str, field_val: Any, target_val: Any) -> bool:
        if op == "exists":
            return field_val is not None
        if op == "not_exists":
            return field_val is None
        
        # If field is None but we are checking equality/greater etc., it fails
        if field_val is None:
            if op == "equals" and target_val is None: return True
            return False

        if op == "equals":
            return field_val == target_val
        if op == "not_equals":
            return field_val != target_val
        if op == "greater_than":
            return field_val > target_val
        if op == "greater_or_equal":
            return field_val >= target_val
        if op == "less_than":
            return field_val < target_val
        if op == "less_or_equal":
            return field_val <= target_val
        if op == "in":
            return field_val in target_val
        if op == "not_in":
            return field_val not in target_val
        if op == "boolean_true":
            return bool(field_val) is True
        if op == "boolean_false":
            return bool(field_val) is False

        return False

    def resolve_decision(self, triggered_rules: List[RuleDefinition]) -> Tuple[str, List[RuleDefinition]]:
        """
        Conflict strategy:
        1. fail_validation
        2. require_additional_approval
        3. flag_for_review
        4. no_additional_approval
        """
        if not triggered_rules:
            return "no_additional_approval_required", []

        effects = [r.outcome.decision_effect for r in triggered_rules]

        if "fail_validation" in effects:
            return "validation_failed", triggered_rules
        if "require_additional_approval" in effects:
            return "additional_approval_required", triggered_rules
        if "flag_for_review" in effects:
            return "review_required", triggered_rules
            
        return "no_additional_approval_required", triggered_rules
