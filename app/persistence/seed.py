import yaml
from sqlalchemy.orm import Session
from app.persistence.database import SessionLocal
from app.persistence.models import Rule, RuleCondition, RuleAction
from app.core.config import settings
from app.core.logging import logger

def seed_rules():
    db: Session = SessionLocal()
    try:
        if db.query(Rule).first():
            logger.info("Rules already seeded in database.")
            return

        logger.info("Seeding rules from config file...")
        with open(settings.RULES_CONFIG_PATH, 'r') as f:
            data = yaml.safe_load(f)

        for rule_data in data.get("rules", []):
            db_rule = Rule(
                rule_id=rule_data["rule_id"],
                name=rule_data["name"],
                description=rule_data.get("description"),
                enabled=rule_data.get("enabled", True),
                priority=rule_data.get("priority", 0.0),
                condition_group=rule_data.get("condition_group", "all"),
                decision_effect=rule_data["outcome"]["decision_effect"],
                rationale_template=rule_data["outcome"]["rationale_template"]
            )
            db.add(db_rule)
            db.flush() # to get db_rule.id

            for cond_data in rule_data.get("conditions", []):
                db_cond = RuleCondition(
                    rule_id=db_rule.id,
                    field=cond_data["field"],
                    operator=cond_data["operator"],
                    value=cond_data.get("value")
                )
                db.add(db_cond)

            for act_data in rule_data["outcome"].get("actions", []):
                db_act = RuleAction(
                    rule_id=db_rule.id,
                    type=act_data["type"]
                )
                db.add(db_act)

        db.commit()
        logger.info("Successfully seeded rules into database.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed rules: {e}")
    finally:
        db.close()
