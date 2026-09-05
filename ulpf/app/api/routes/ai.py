"""
Optional debug endpoint for testing AI mapping directly.
POST /ai/map — accepts a raw log + structure + candidate mappings,
               calls the configured AI provider, returns validated suggestions.

This endpoint is for developer/demo use only.
The API key is never exposed in the response.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List

from app.services.ai.groq_provider import groq_provider, VALID_TARGET_FIELDS
from app.services.ai.merger import merge_mappings
from app.config import AI_MAPPING_ENABLED

router = APIRouter()


class AIMapRequest(BaseModel):
    raw_log: str
    detected_structure: Dict[str, Any] = {}
    candidate_mappings: Dict[str, Any] = {}


@router.post("/ai/map")
async def ai_map(request: AIMapRequest):
    if not AI_MAPPING_ENABLED:
        return {
            "success": False,
            "ai_provider": "groq",
            "ai_status": "disabled",
            "message": "AI mapping is disabled. Set AI_MAPPING_ENABLED=true to enable.",
            "mappings": [],
        }

    ai_response = groq_provider.suggest_mappings(
        raw_log=request.raw_log,
        structure=request.detected_structure,
        candidate_mappings=request.candidate_mappings,
        universal_schema=sorted(VALID_TARGET_FIELDS),
    )

    if ai_response is None:
        return {
            "success": False,
            "ai_provider": "groq",
            "ai_status": "unavailable",
            "message": "AI mapping unavailable; check GROQ_API_KEY and network connectivity.",
            "mappings": [],
        }

    merged = merge_mappings(request.candidate_mappings, ai_response)

    return {
        "success": True,
        "ai_provider": "groq",
        "ai_status": "success",
        "mappings": [
            {
                "source_field": m.source_field,
                "target_field": m.target_field,
                "confidence": m.confidence,
                "reason": m.reason,
            }
            for m in ai_response.mappings
        ],
        "merged_candidate_mappings": merged,
    }
