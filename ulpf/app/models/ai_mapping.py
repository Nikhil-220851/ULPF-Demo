"""
Pydantic models for AI-assisted field mapping requests and responses.
"""
from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional, Dict, Any


class AIMapping(BaseModel):
    """A single field mapping proposed by an AI provider."""
    source_field: str
    target_field: str
    confidence: float = 0.9
    reason: str = "AI suggested mapping"
    sample_value: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def handle_reason_aliases(cls, data: dict) -> dict:
        if isinstance(data, dict):
            if "reasoning" in data and "reason" not in data:
                data["reason"] = str(data["reasoning"])
            elif "reason" not in data and "reasoning" not in data:
                data["reason"] = "AI suggested mapping"
            else:
                data["reason"] = str(data.get("reason", "AI suggested mapping"))
            
            if "sample_value" in data:
                data["sample_value"] = str(data["sample_value"])
        return data

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        val = float(v)
        if not (0.0 <= val <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {v}")
        return val


class AIMappingResponse(BaseModel):
    """Structured response from an AI provider."""
    format_name: Optional[str] = "Custom Log Format"
    format_type: Optional[str] = "delimited"
    delimiter: Optional[str] = None
    confidence: Optional[float] = 0.9
    mappings: List[AIMapping] = []

    @model_validator(mode="before")
    @classmethod
    def handle_fields_alias(cls, data: dict) -> dict:
        if isinstance(data, dict):
            if "fields" in data and "mappings" not in data:
                data["mappings"] = data["fields"]
        return data


class AIMapRequest(BaseModel):
    """Input context sent to the AI provider."""
    raw_log: Optional[str] = None
    raw: Optional[str] = None
    detected_structure: Dict[str, Any] = {}
    structure: Dict[str, Any] = {}
    candidate_mappings: Dict[str, Any] = {}
    universal_schema: List[str] = []
