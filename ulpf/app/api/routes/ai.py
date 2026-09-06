"""
AI schema mapping and unknown format inference endpoints.
POST /ai/map — Debug and test endpoint for Groq AI field mapping.
POST /unknown/infer — Dedicated endpoint for unknown format schema inference.
"""
from fastapi import APIRouter
from typing import Dict, Any, List, Optional
from app.models.ai_mapping import AIMapRequest
from app.services.ai.groq_provider import groq_provider, infer_unknown_mapping, VALID_TARGET_FIELDS
from app.services.ai.merger import merge_mappings
from app.config import AI_MAPPING_ENABLED

router = APIRouter()


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

    raw_text = request.raw_log or request.raw or ""
    struct = request.detected_structure or request.structure or {}

    ai_response = groq_provider.suggest_mappings(
        raw_log=raw_text,
        structure=struct,
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
        "format_name": ai_response.format_name,
        "format_type": ai_response.format_type,
        "delimiter": ai_response.delimiter,
        "confidence": ai_response.confidence,
        "mappings": [
            {
                "source_field": m.source_field,
                "target_field": m.target_field,
                "confidence": m.confidence,
                "reason": m.reason,
                "sample_value": m.sample_value
            }
            for m in ai_response.mappings
        ],
        "merged_candidate_mappings": merged,
    }


@router.post("/unknown/infer")
async def infer_unknown(request: AIMapRequest):
    """
    Dedicated endpoint for AI schema inference on unknown log formats.
    Returns status, confidence, and proposed field mappings.
    """
    if not AI_MAPPING_ENABLED:
        return {
            "status": "AI_MAPPING_DISABLED",
            "message": "AI mapping is disabled in config.",
            "mappings": []
        }

    raw_text = request.raw_log or request.raw or ""
    struct = request.detected_structure or request.structure or {}

    ai_response = infer_unknown_mapping(raw_text, struct)
    if ai_response is None:
        return {
            "status": "AI_MAPPING_FAILED",
            "message": "Unable to infer schema mapping. Please retry or map fields manually.",
            "raw": raw_text,
            "structure": struct,
            "mappings": []
        }

    return {
        "status": "SUCCESS",
        "format_name": ai_response.format_name,
        "format_type": ai_response.format_type,
        "delimiter": ai_response.delimiter,
        "confidence": ai_response.confidence,
        "mappings": [
            {
                "source_field": m.source_field,
                "sample_value": m.sample_value,
                "target_field": m.target_field,
                "confidence": m.confidence,
                "reason": m.reason
            }
            for m in ai_response.mappings
        ]
    }
