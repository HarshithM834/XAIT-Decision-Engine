from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class FinancialsSchema(BaseModel):
    total_price: Optional[float] = None
    total_cost: Optional[float] = None
    margin: Optional[float] = None

class DocumentsSchema(BaseModel):
    so_summary_found: Optional[bool] = None
    sow_found: Optional[bool] = None
    latest_document_timestamp: Optional[datetime] = None
    source_mismatch_detected: Optional[bool] = None

class ExtractedFieldsSchema(BaseModel):
    status: Optional[str] = None
    approval_threshold: Optional[str] = None
    approval_type: Optional[str] = None
    customer_name: Optional[str] = None
    region: Optional[str] = None
    business_unit: Optional[str] = None
    
    @field_validator("status", mode="before")
    def trim_status(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

class WorkflowContextSchema(BaseModel):
    requested_start_stage: Optional[str] = None
    restart_allowed: bool = False
    initiated_by: Optional[str] = None

class MetadataSchema(BaseModel):
    upstream_system: Optional[str] = None
    payload_version: str
    notes: Optional[str] = None

    model_config = {"extra": "allow"} # allow extra fields

class NormalizedPayload(BaseModel):
    record_id: str
    source: str
    captured_at: datetime
    financials: FinancialsSchema = Field(default_factory=FinancialsSchema)
    documents: DocumentsSchema = Field(default_factory=DocumentsSchema)
    extracted_fields: ExtractedFieldsSchema = Field(default_factory=ExtractedFieldsSchema)
    workflow_context: WorkflowContextSchema = Field(default_factory=WorkflowContextSchema)
    metadata: MetadataSchema = Field(default_factory=lambda: MetadataSchema(payload_version="1.0"))
    
    @field_validator("source", mode="before")
    def normalize_source(cls, v):
        if isinstance(v, str):
            return v.lower().replace(" ", "_")
        return v
