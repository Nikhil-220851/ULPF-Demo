"""
Merges local semantic mapper candidate mappings with AI provider suggestions.

Rules:
- Local and AI AGREE on target_field  → keep the higher confidence, mark source "ai+local"
- Local and AI DISAGREE               → preserve BOTH as a 'candidates' list so the
                                        human confirmation UI can present them
- AI-only mapping                     → added with source "ai"
- Local-only mapping                  → kept as-is with source "local"

The output format is backwards-compatible with the existing candidate_mappings structure
consumed by the frontend ConfirmMappingPanel.
"""
from typing import Optional
from app.models.ai_mapping import AIMappingResponse


def merge_mappings(
    local_candidates: dict,
    ai_response: Optional[AIMappingResponse],
) -> dict:
    """
    Merge local candidates with AI suggestions.

    Args:
        local_candidates: Dict from semantic_mapper in the form:
            { field_name: { mapped_to, confidence, value, token_type, source? } }
        ai_response:      Validated AIMappingResponse from an AIProvider, or None.

    Returns:
        Merged candidate_mappings dict (same structure, extended with 'source' key
        and optional 'conflict_candidates' list for disagreements).
    """
    if ai_response is None:
        # Nothing to merge — tag all local entries with source
        result = {}
        for field, info in local_candidates.items():
            result[field] = {**info, "source": "local"}
        return result

    # Index AI mappings by source_field for O(1) lookup
    ai_by_field: dict = {m.source_field: m for m in ai_response.mappings}

    result = {}

    # Process all local candidates first
    for field, info in local_candidates.items():
        local_target = info.get("mapped_to")
        ai_mapping = ai_by_field.get(field)

        if ai_mapping is None:
            # Local only
            result[field] = {**info, "source": "local"}

        elif ai_mapping.target_field == local_target:
            # Agreement — use higher confidence
            best_confidence = max(info.get("confidence", 0.0), ai_mapping.confidence)
            result[field] = {
                **info,
                "mapped_to": local_target,
                "confidence": best_confidence,
                "source": "ai+local",
                "ai_reason": ai_mapping.reason,
            }

        else:
            # Disagreement — expose both candidates for human review
            result[field] = {
                **info,
                "mapped_to": ai_mapping.target_field,   # AI gets priority in default display
                "confidence": ai_mapping.confidence,
                "source": "ai",
                "ai_reason": ai_mapping.reason,
                "conflict_candidates": [
                    {
                        "target_field": ai_mapping.target_field,
                        "confidence": ai_mapping.confidence,
                        "source": "ai",
                        "reason": ai_mapping.reason,
                    },
                    {
                        "target_field": local_target,
                        "confidence": info.get("confidence", 0.0),
                        "source": "local",
                        "reason": None,
                    },
                ],
            }

    # Add AI-only mappings (fields the local mapper missed)
    for field, ai_mapping in ai_by_field.items():
        if field not in result:
            # We still need the value from the original tokens;
            # local_candidates may not have an entry for this field
            original_info = local_candidates.get(field, {})
            result[field] = {
                "mapped_to": ai_mapping.target_field,
                "confidence": ai_mapping.confidence,
                "value": original_info.get("value", ""),
                "token_type": original_info.get("token_type", "UNKNOWN"),
                "source": "ai",
                "ai_reason": ai_mapping.reason,
            }

    return result
