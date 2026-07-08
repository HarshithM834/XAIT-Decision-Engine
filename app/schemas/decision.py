from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class TriggeredRuleSummary(BaseModel):
    rule_id: str
    name: str
    decision_effect: str
    priority: float

class JobExecutionSummary(BaseModel):
    job_type: str
    status: str

class DecisionResponse(BaseModel):
    run_id: str
    record_id: str
    status: str
    current_stage: str
    approval_required: bool
    review_required: bool
    final_decision: str
    triggered_rules: List[TriggeredRuleSummary]
    skipped_rules: List[str] = [] # Optional depending on implementation
    rationale: str
    next_action: str
    executed_jobs: List[JobExecutionSummary]
    restartable_stages: List[str]
    source_summary: Optional[str] = None
    timestamps: dict = {}
