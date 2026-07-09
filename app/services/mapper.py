import yaml
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from jsonpath_ng import parse
from app.core.config import settings
from app.core.logging import logger

class MappingField(BaseModel):
    target: str
    json_path: str
    type_cast: Optional[str] = None
    default_value: Optional[Any] = None

class MappingRule(BaseModel):
    source_pattern: str
    fields: List[MappingField]

class PayloadMappingConfig(BaseModel):
    mappings: List[MappingRule]

def load_payload_mappings(file_path: str = settings.PAYLOAD_MAPPING_PATH) -> PayloadMappingConfig:
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        return PayloadMappingConfig(**data)
    except FileNotFoundError:
        logger.warning(f"Payload mapping file not found at {file_path}. Mapping will be bypassed.")
        return PayloadMappingConfig(mappings=[])

class PayloadMapper:
    def __init__(self, config: PayloadMappingConfig = None):
        self.config = config or load_payload_mappings()

    def _cast_value(self, value: Any, type_cast: Optional[str]) -> Any:
        if value is None or type_cast is None:
            return value
            
        try:
            if type_cast == "float":
                if isinstance(value, str):
                    # Remove currency symbols and commas (e.g. "$250,000.00" -> "250000.00")
                    clean_str = re.sub(r'[^\d.-]', '', value)
                    return float(clean_str) if clean_str else 0.0
                return float(value)
            elif type_cast == "float_percent":
                if isinstance(value, str):
                    # Remove % signs and cast, then divide by 100 (e.g. "28.5%" -> 0.285)
                    clean_str = re.sub(r'[^\d.-]', '', value)
                    return float(clean_str) / 100.0 if clean_str else 0.0
                return float(value)
            elif type_cast == "integer":
                if isinstance(value, str):
                    clean_str = re.sub(r'[^\d.-]', '', value)
                    return int(float(clean_str)) if clean_str else 0
                return int(value)
            elif type_cast == "boolean":
                if isinstance(value, str):
                    return value.lower() in ["true", "1", "yes", "y"]
                return bool(value)
            elif type_cast == "string":
                return str(value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to cast {value} to {type_cast}")
            
        return value

    def _set_nested_value(self, target_dict: Dict[str, Any], path: str, value: Any):
        keys = path.split('.')
        current = target_dict
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def map_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempts to map an arbitrary JSON payload to the NormalizedPayload structure
        based on configured mapping rules.
        """
        # We need a way to identify the source to pick the right mapping rule.
        # If there is no 'source' field, we might just try all rules or a default rule.
        # For simplicity, we check if any rule's pattern matches the payload structure or a specific field.
        # Here we'll just evaluate rules until one has fields that match. 
        # A more robust approach checks a 'source' key if it exists in the raw payload.
        
        source_val = raw_payload.get("source", "")
        if not source_val and "meta" in raw_payload and isinstance(raw_payload["meta"], dict):
            source_val = raw_payload["meta"].get("SourceName", "")

        active_rule = None
        for rule in self.config.mappings:
            if re.match(rule.source_pattern, str(source_val), re.IGNORECASE):
                active_rule = rule
                break
                
        if not active_rule:
            # If no mapping matches, return the raw payload and let Pydantic handle it (or fail)
            return raw_payload

        mapped_payload = {}
        for field in active_rule.fields:
            try:
                jsonpath_expr = parse(field.json_path)
                match = jsonpath_expr.find(raw_payload)
                if match:
                    # Take the first match
                    val = match[0].value
                    val = self._cast_value(val, field.type_cast)
                    self._set_nested_value(mapped_payload, field.target, val)
                elif field.default_value is not None:
                    self._set_nested_value(mapped_payload, field.target, field.default_value)
            except Exception as e:
                logger.error(f"Error extracting JSONPath {field.json_path}: {e}")

        # Preserve the original payload under raw_context if needed, 
        # but for now we just return the newly mapped structure.
        # We might need to copy over other fields that didn't need mapping.
        # If the user wants to retain unknown fields, the Pydantic schema allows extras in metadata.
        
        return mapped_payload
