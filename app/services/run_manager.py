import json
import hashlib
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.persistence.models import Run, RunEvent, TriggeredRule, JobExecution
from app.schemas.payload import NormalizedPayload

class RunManager:
    def __init__(self, db: Session):
        self.db = db

    def compute_idempotency_hash(self, payload: NormalizedPayload) -> str:
        # Simple hash of the normalized payload model dump
        payload_json = payload.model_dump_json(exclude={"workflow_context": True, "metadata": {"notes": True}})
        return hashlib.sha256(payload_json.encode('utf-8')).hexdigest()

    def get_run(self, run_id: str) -> Optional[Run]:
        return self.db.query(Run).filter(Run.id == run_id).first()

    def get_latest_run_by_record(self, record_id: str) -> Optional[Run]:
        return self.db.query(Run).filter(Run.record_id == record_id).order_by(Run.created_at.desc()).first()

    def get_run_by_hash(self, request_hash: str) -> Optional[Run]:
        return self.db.query(Run).filter(Run.request_hash == request_hash).first()

    def create_run(self, payload: NormalizedPayload, request_hash: str) -> Run:
        run = Run(
            record_id=payload.record_id,
            source=payload.source,
            request_hash=request_hash,
            payload=payload.model_dump(mode='json'),
            status="pending",
            current_stage="received"
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        self.add_event(run.id, "received", "completed")
        return run

    def add_event(self, run_id: str, stage: str, status: str, details: Optional[Dict[str, Any]] = None):
        event = RunEvent(run_id=run_id, stage=stage, status=status, details=details)
        self.db.add(event)
        self.db.commit()

    def update_run_stage(self, run_id: str, stage: str, status: str = "in_progress", error: Optional[str] = None):
        run = self.get_run(run_id)
        if run:
            run.current_stage = stage
            run.status = status
            if error:
                run.last_error = error
            self.db.commit()
            self.db.refresh(run)

    def save_decision(self, run_id: str, decision: str, rationale: str, rules: List[Any], next_action: str):
        run = self.get_run(run_id)
        if run:
            run.final_decision = decision
            run.rationale = rationale
            run.next_action = next_action
            
            if decision == "additional_approval_required":
                run.approval_required = True
                run.review_required = False
            elif decision == "review_required":
                run.approval_required = False
                run.review_required = True
            elif decision == "validation_failed":
                run.approval_required = False
                run.review_required = False
            else:
                run.approval_required = False
                run.review_required = False

            # Clear existing rules if restarting
            self.db.query(TriggeredRule).filter(TriggeredRule.run_id == run.id).delete()
            
            for rule in rules:
                tr = TriggeredRule(
                    run_id=run.id,
                    rule_id=rule.rule_id,
                    name=rule.name,
                    decision_effect=rule.outcome.decision_effect,
                    priority=rule.priority
                )
                self.db.add(tr)
            
            self.db.commit()

    def save_job_executions(self, run_id: str, executions: List[Dict[str, str]]):
        run = self.get_run(run_id)
        if run:
            for exec_data in executions:
                je = JobExecution(
                    run_id=run.id,
                    job_type=exec_data["job_type"],
                    status=exec_data["status"],
                    details={"error": exec_data.get("error")} if "error" in exec_data else None
                )
                self.db.add(je)
            self.db.commit()
