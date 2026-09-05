"""
Groq AI provider implementation.
Uses the official Groq Python SDK to suggest semantic field mappings for unknown logs.

Security notes:
- The API key is read from config and never logged.
- No raw log content is logged at DEBUG level.
- The frontend never receives the API key.
"""
import json
import logging
from typing import Optional

from app.config import GROQ_API_KEY, GROQ_MODEL, AI_REQUEST_TIMEOUT
from app.models.ai_mapping import AIMappingResponse, AIMapping
from app.services.ai.base import AIProvider

try:
    from groq import Groq, APITimeoutError, APIStatusError, APIConnectionError
except ImportError:
    Groq = None
    APITimeoutError = Exception
    APIStatusError = Exception
    APIConnectionError = Exception

logger = logging.getLogger(__name__)

# ── Universal Schema whitelist ─────────────────────────────────────────────────
# Derived directly from UniversalEvent model fields.
# Only these target paths are accepted from the AI.
VALID_TARGET_FIELDS: frozenset = frozenset({
    "event.timestamp", "event.action", "event.outcome", "event.message",
    "event.application", "event.category", "event.type", "event.id",
    "source.ip", "source.port", "source.hostname", "source.domain",
    "source.mac", "source.user",
    "destination.ip", "destination.port", "destination.hostname",
    "destination.domain", "destination.mac",
    "network.protocol", "network.direction", "network.bytes",
    "network.packets", "network.transport",
    "user.name", "user.id", "user.domain", "user.email",
    "device.hostname", "device.ip", "device.mac", "device.type",
    "device.os", "device.vendor",
    "severity",
})

# ── System prompt ──────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are an expert log-format and cybersecurity event normalization assistant.

Your task is to identify semantic mappings between fields in an unknown log format and fields in the provided Universal Event Schema.

CRITICAL: Do NOT include any <think> tags, reasoning, or preamble. Respond IMMEDIATELY with the JSON object.

You must:
1. Analyze the raw log.
2. Analyze the detected structure.
3. Consider field names, values, data types, patterns, and context.
4. Consider existing candidate mappings provided.
5. Map fields ONLY to valid fields in the provided Universal Schema list.
6. Return ONLY valid JSON — no markdown, no explanation outside the JSON.
7. Provide a confidence score between 0.0 and 1.0 for every mapping.
8. Provide a short reason for every mapping.
9. Do NOT invent Universal Schema fields not in the provided list.
10. Do NOT generate code.
11. Do NOT modify plugins or any configuration.
12. Do NOT execute anything.
13. Do NOT make assumptions that cannot be supported by the log content.
14. If a field cannot be mapped confidently, omit it — do not force a mapping.

Return format (strict JSON, no other text):
{
  "mappings": [
    {
      "source_field": "USR",
      "target_field": "user.name",
      "confidence": 0.95,
      "reason": "USR field corresponds to user name"
    }
  ]
}"""


def _build_user_message(
    raw_log: str,
    structure: dict,
    candidate_mappings: dict,
    universal_schema: list,
) -> str:
    """Build the structured user message sent to Groq."""
    # Summarise existing local candidates (only mapped ones)
    local_candidates = [
        {
            "source_field": field,
            "candidate": info.get("mapped_to"),
            "confidence": info.get("confidence", 0.0),
        }
        for field, info in candidate_mappings.items()
        if info.get("mapped_to")
    ]

    payload = {
        "raw_log": raw_log,
        "detected_structure": {
            "format_type": structure.get("format_type"),
            "delimiter": structure.get("delimiter"),
            "tokens": structure.get("tokens", {}),
            "data_types": structure.get("data_types", []),
        },
        "existing_local_candidates": local_candidates,
        "universal_schema_valid_targets": universal_schema,
    }
    return json.dumps(payload, indent=2)


def _validate_response(
    response_obj: AIMappingResponse,
    tokens: dict,
) -> AIMappingResponse:
    """
    Validate AI response strictly.
    - source_field must exist in the analyzed tokens
    - target_field must be in VALID_TARGET_FIELDS
    - confidence must be 0.0–1.0 (already enforced by Pydantic)
    - no two mappings may share the same target_field
    """
    seen_targets: set = set()
    valid_mappings = []

    for mapping in response_obj.mappings:
        # source_field must exist in the log tokens
        if mapping.source_field not in tokens:
            logger.warning(
                "AI returned unknown source_field '%s' — rejected", mapping.source_field
            )
            continue

        # target_field must be a valid Universal Schema path
        if mapping.target_field not in VALID_TARGET_FIELDS:
            logger.warning(
                "AI returned invalid target_field '%s' — rejected", mapping.target_field
            )
            continue

        # No duplicate target fields
        if mapping.target_field in seen_targets:
            logger.warning(
                "AI returned duplicate target_field '%s' — second mapping rejected",
                mapping.target_field,
            )
            continue

        seen_targets.add(mapping.target_field)
        valid_mappings.append(mapping)

    return AIMappingResponse(mappings=valid_mappings)


class GroqProvider(AIProvider):
    """
    Groq implementation of the AIProvider interface.
    Uses the official groq Python SDK.
    Falls back safely (returns None) on any error.
    """

    def suggest_mappings(
        self,
        raw_log: str,
        structure: dict,
        candidate_mappings: dict,
        universal_schema: list,
    ) -> Optional[AIMappingResponse]:
        if not GROQ_API_KEY:
            logger.warning("GROQ_API_KEY is not set — Groq provider disabled")
            return None

        if Groq is None:
            logger.error(
                "groq package is not installed — cannot call Groq API. "
                "Run: pip install groq"
            )
            return None

        user_message = _build_user_message(
            raw_log, structure, candidate_mappings, universal_schema
        )

        try:
            client = Groq(api_key=GROQ_API_KEY, timeout=AI_REQUEST_TIMEOUT)
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,   # low temperature for deterministic structured output
                max_tokens=1000,
            )
        except APITimeoutError:
            logger.warning("Groq API request timed out after %ds", AI_REQUEST_TIMEOUT)
            return None
        except APIStatusError as e:
            logger.warning("Groq API returned HTTP %d", e.status_code)
            return None
        except APIConnectionError as e:
            logger.warning("Groq API network error: %s", type(e).__name__)
            return None
        except Exception as e:
            logger.warning("Groq API unexpected error: %s", type(e).__name__)
            return None

        try:
            raw_content = completion.choices[0].message.content.strip()
        except (AttributeError, IndexError) as e:
            logger.warning("Groq response structure unexpected: %s", e)
            return None

        # Strip thinking block (<think> or <think>...</think>)
        if "<think>" in raw_content:
            if "</think>" in raw_content:
                raw_content = raw_content.split("</think>")[-1].strip()
            else:
                # Unclosed <think> tag — JSON object will be at the end after the thinking text
                raw_content = raw_content.split("<think>")[-1].strip()

        # Strip markdown code fences if model wraps in ```json ... ```
        if "```" in raw_content:
            lines = raw_content.splitlines()
            raw_content = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            ).strip()

        # Extract first/last JSON object block
        start_idx = raw_content.find("{")
        end_idx = raw_content.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            raw_content = raw_content[start_idx:end_idx + 1]

        try:
            parsed_json = json.loads(raw_content)
            ai_response = AIMappingResponse(**parsed_json)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Groq response is not valid JSON or schema mismatch: %s", e)
            return None

        tokens = structure.get("tokens", {})
        try:
            validated = _validate_response(ai_response, tokens)
        except Exception as e:
            logger.warning("Groq response validation failed: %s", e)
            return None

        if not validated.mappings:
            logger.info("Groq returned no valid mappings after validation")
            return None

        logger.info(
            "Groq suggested %d validated mappings", len(validated.mappings)
        )
        return validated


# ── Module-level singleton ─────────────────────────────────────────────────────
groq_provider = GroqProvider()
