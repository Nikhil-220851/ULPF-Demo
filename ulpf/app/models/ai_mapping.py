"""
Pydantic models for AI-assisted field mapping requests and responses.
"""
from pydantic import BaseModel, field_validator
from typing import List, Optional


class AIMapping(BaseModel):
    """A single field mapping proposed by an AI provider."""
    source_field: str
    target_field: str
    confidence: float
    reason: str

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {v}")
        return v


class AIMappingResponse(BaseModel):
    """Structured response from an AI provider."""
    mappings: List[AIMapping]


class AIMappingRequest(BaseModel):
    """Input context sent to the AI provider."""
    raw_log: str
    detected_structure: dict
    candidate_mappings: dict
    universal_schema: List[str]
