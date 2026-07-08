from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.schemas.payload import NormalizedPayload
from app.schemas.decision import DecisionResponse, TriggeredRuleSummary, JobExecutionSummary
from app.schemas.run import RestartRequest
from app.services.run_manager import RunManager
from app.rules.evaluator import RuleEvaluator
from app.rules.models import RuleDefinition, RuleCondition, RuleOutcome, RuleAction
from app.persistence.models import Rule as DBRule
from app.jobs.executor import JobExecutor
from app.core.exceptions import EngineException
from app.core.logging import logger

class DecisionEngine:
    def __init__(self, db: Session):
        self.db = db
        self.run_manager = RunManager(db)
        
        # Load rules from DB
        db_rules = self.db.query(DBRule).all()
        pydantic_rules = []
        for r in db_rules:
            # Map SQLAlchemy models to Pydantic models for evaluator
            conditions = [RuleCondition(field=c.field, operator=c.operator, value=c.value) for c in r.conditions]
            actions = [RuleAction(type=a.type) for a in r.actions]
            outcome = RuleOutcome(decision_effect=r.decision_effect, actions=actions, rationale_template=r.rationale_template)
            p_rule = RuleDefinition(
                rule_id=r.rule_id,
                name=r.name,
                description=r.description,
                enabled=r.enabled,
                priority=r.priority,
                condition_group=r.condition_group,
                conditions=conditions,
                outcome=outcome
            )
            pydantic_rules.append(p_rule)

        self.evaluator = RuleEvaluator(pydantic_rules)
        self.job_executor = JobExecutor()

    def process_evaluate(self, payload: NormalizedPayload, force: bool = False) -> DecisionResponse:
        request_hash = self.run_manager.compute_idempotency_hash(payload)
        
        # Idempotency check
        if not force:
            existing_run = self.run_manager.get_run_by_hash(request_hash)
            if existing_run and existing_run.status == "completed":
                logger.info(f"Idempotent request matched run {existing_run.id}")
                return self._build_decision_response(existing_run)

        # Create new run
        run = self.run_manager.create_run(payload, request_hash)
        
        return self._execute_pipeline(run.id, "validated")

    def process_restart(self, run_id: str, request: RestartRequest) -> DecisionResponse:
        run = self.run_manager.get_run(run_id)
        if not run:
            raise EngineException(code="NOT_FOUND", message=f"Run {run_id} not found", status_code=404)

        valid_stages = ["rule_evaluation", "decision_generated", "job_execution"]
        if request.restart_from_stage not in valid_stages:
            raise EngineException(code="INVALID_RESTART_STAGE", message=f"Cannot restart from {request.restart_from_stage}")

        if run.status == "completed" and not request.force:
            raise EngineException(code="ALREADY_COMPLETED", message="Cannot restart a completed run without force flag", status_code=400)

        # Validation for restart prerequisites
        if request.restart_from_stage == "rule_evaluation" and not run.payload:
            raise EngineException(code="MISSING_PREREQUISITE", message="Missing payload for rule evaluation")
            
        if request.restart_from_stage == "job_execution" and not run.final_decision:
            raise EngineException(code="MISSING_PREREQUISITE", message="Missing decision for job execution")

        self.run_manager.add_event(run.id, "restarted", "completed", {"reason": request.reason, "stage": request.restart_from_stage})
        self.run_manager.update_run_stage(run.id, request.restart_from_stage, "restarted")

        return self._execute_pipeline(run.id, request.restart_from_stage)

    def _execute_pipeline(self, run_id: str, start_stage: str) -> DecisionResponse:
        try:
            # 1. Validation/Normalization (already done by Pydantic, just recording)
            if start_stage in ["validated", "normalized", "rule_evaluation"]:
                self.run_manager.update_run_stage(run_id, "rule_evaluation")
                self.run_manager.add_event(run_id, "rule_evaluation", "in_progress")
                
                run = self.run_manager.get_run(run_id)
                payload_dict = run.payload
                
                # 2. Rule Evaluation
                triggered_rules = self.evaluator.evaluate(payload_dict)
                decision, resolved_rules = self.evaluator.resolve_decision(triggered_rules)
                
                # Deduplicate actions, format rationale
                actions = []
                rationales = []
                for rule in resolved_rules:
                    actions.extend([a.model_dump() for a in rule.outcome.actions])
                    if rule.outcome.rationale_template:
                        rationales.append(rule.outcome.rationale_template)
                
                combined_rationale = "; ".join(rationales) if rationales else "No rules triggered or no rationale provided."
                
                # Determine next action (if any actions require send_email, prioritize it)
                next_action = "none"
                if any(a.get("type") == "send_email" for a in actions):
                    next_action = "send_email"

                self.run_manager.save_decision(run_id, decision, combined_rationale, resolved_rules, next_action)
                self.run_manager.add_event(run_id, "decision_generated", "completed")
                start_stage = "job_execution"

            # 3. Job Execution
            if start_stage == "job_execution":
                self.run_manager.update_run_stage(run_id, "job_execution")
                self.run_manager.add_event(run_id, "job_execution", "in_progress")
                
                run = self.run_manager.get_run(run_id)
                
                if run.next_action == "send_email" and run.final_decision == "additional_approval_required":
                    # For v1, mock email action
                    executed = self.job_executor.execute_jobs([{"type": "send_email"}], run.payload, {"decision": run.final_decision})
                    self.run_manager.save_job_executions(run_id, executed)
                    
                    if any(j["status"] == "failed" for j in executed):
                        raise Exception("A required job failed to execute")

                self.run_manager.add_event(run_id, "job_execution", "completed")

            # 4. Completion
            self.run_manager.update_run_stage(run_id, "completed", "completed")
            self.run_manager.add_event(run_id, "completed", "completed")

        except Exception as e:
            logger.error(f"Pipeline failed for run {run_id}", exc_info=True)
            self.run_manager.update_run_stage(run_id, "failed", "failed", error=str(e))
            self.run_manager.add_event(run_id, "failed", "completed", {"error": str(e)})

        run = self.run_manager.get_run(run_id)
        return self._build_decision_response(run)

    def _build_decision_response(self, run) -> DecisionResponse:
        tr_summaries = [
            TriggeredRuleSummary(
                rule_id=tr.rule_id,
                name=tr.name,
                decision_effect=tr.decision_effect,
                priority=tr.priority
            ) for tr in run.triggered_rules
        ]

        je_summaries = [
            JobExecutionSummary(
                job_type=je.job_type,
                status=je.status
            ) for je in run.job_executions
        ]

        return DecisionResponse(
            run_id=run.id,
            record_id=run.record_id,
            status=run.status,
            current_stage=run.current_stage,
            approval_required=run.approval_required or False,
            review_required=run.review_required or False,
            final_decision=run.final_decision or "pending",
            triggered_rules=tr_summaries,
            rationale=run.rationale or "",
            next_action=run.next_action or "none",
            executed_jobs=je_summaries,
            restartable_stages=["rule_evaluation", "decision_generated", "job_execution"],
            timestamps={
                "created_at": run.created_at.isoformat(),
                "updated_at": run.updated_at.isoformat()
            }
        )
