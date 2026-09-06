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
from typing import Optional, Dict, Any

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
# ── Universal Schema whitelist ─────────────────────────────────────────────────
# Derived directly from UniversalEvent model fields + composite endpoint aliases.
VALID_TARGET_FIELDS: frozenset = frozenset({
    "event.timestamp", "event.action", "event.outcome", "event.message",
    "event.application", "event.category", "event.type", "event.id",
    "source.ip", "source.port", "source.hostname", "source.domain",
    "source.mac", "source.user", "source.endpoint", "COMPOSITE_SOURCE_ENDPOINT",
    "destination.ip", "destination.port", "destination.hostname",
    "destination.domain", "destination.mac", "destination.endpoint", "COMPOSITE_DESTINATION_ENDPOINT",
    "network.protocol", "network.direction", "network.bytes",
    "network.packets", "network.transport",
    "user.name", "user.id", "user.domain", "user.email",
    "device.hostname", "device.ip", "device.mac", "device.type",
    "device.os", "device.vendor",
    "severity", "COMPOSITE_ENDPOINT",
})

# ── System prompt ──────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are a semantic log field mapping engine for the Universal Log Preprocessing Framework (ULPF).

Your task is to analyze an unknown log payload, identify its structure and delimiter, and map its logical fields to ULPF Universal Schema fields.

CRITICAL INSTRUCTIONS:
1. IDENTIFY DELIMITER: Determine the actual delimiter used in the raw log (e.g. "::", "|", ";", ",", "\\t").
2. DO NOT TREAT DELIMITERS AS FIELDS: Delimiter tokens like "::" or "|" MUST NEVER be extracted or mapped as semantic fields.
3. COMBINE TIMESTAMP COMPONENTS: Date and time components (e.g. "2026/09/05" and "17:42:31") MUST be treated as a single combined timestamp field ("2026/09/05 17:42:31") mapped to "event.timestamp".
4. COMPOSITE ENDPOINTS: Values containing IP#PORT (e.g. "192.168.44.27#51542" or "10.20.30.40#443") should be mapped to "source.ip" (or "COMPOSITE_SOURCE_ENDPOINT") and "destination.ip" (or "COMPOSITE_DESTINATION_ENDPOINT").
5. RETURN STRICT VALID JSON ONLY.

DO NOT return Markdown code blocks.
DO NOT return explanations or prose.

Expected JSON format:
{
  "format_name": "Custom Gateway Firewall Log",
  "format_type": "delimited",
  "delimiter": "::",
  "confidence": 0.97,
  "fields": [
    {
      "source_field": "field_1",
      "sample_value": "GW-ALPHA",
      "target_field": "device.hostname",
      "confidence": 0.99,
      "reason": "Gateway hostname"
    },
    {
      "source_field": "field_2",
      "sample_value": "2026/09/05 17:42:31",
      "target_field": "event.timestamp",
      "confidence": 0.99,
      "reason": "Combined timestamp"
    },
    {
      "source_field": "field_3",
      "sample_value": "192.168.44.27#51542",
      "target_field": "source.ip",
      "confidence": 0.99,
      "reason": "Source IP and port"
    },
    {
      "source_field": "field_4",
      "sample_value": "10.20.30.40#443",
      "target_field": "destination.ip",
      "confidence": 0.99,
      "reason": "Destination IP and port"
    },
    {
      "source_field": "field_5",
      "sample_value": "TCP",
      "target_field": "network.transport",
      "confidence": 0.99,
      "reason": "Network protocol"
    },
    {
      "source_field": "field_6",
      "sample_value": "BLOCK",
      "target_field": "event.action",
      "confidence": 0.98,
      "reason": "Firewall action"
    },
    {
      "source_field": "field_7",
      "sample_value": "analyst",
      "target_field": "user.name",
      "confidence": 0.95,
      "reason": "Username"
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
        "instruction": "Analyze the log payload and return a valid json response object matching the requested schema.",
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


def _repair_truncated_json(s: str) -> Optional[dict]:
    """
    Safely repair truncated or formatting-flawed JSON responses.
    Handles code-block wrapping, unclosed strings, trailing commas, and unclosed brackets.
    """
    s = s.strip()

    # Fast path
    try:
        return json.loads(s)
    except Exception:
        pass

    # Strip thinking block (<think> ... </think>)
    if "<think>" in s:
        if "</think>" in s:
            s = s.split("</think>")[-1].strip()
        else:
            s = s.split("<think>")[-1].strip()

    # Strip markdown code fences if model wraps in ```json ... ```
    if "```" in s:
        lines = s.splitlines()
        s = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        ).strip()

    # Locate JSON start
    start_idx = s.find("{")
    if start_idx != -1:
        s = s[start_idx:]

    # 1. Close unclosed double-quoted string if truncated mid-string
    in_string = False
    escape = False
    for char in s:
        if escape:
            escape = False
        elif char == '\\':
            escape = True
        elif char == '"':
            in_string = not in_string

    if in_string:
        s += '"'

    # 2. Strip trailing colon or comma if truncated right after key or item
    s = s.rstrip()
    if s.endswith(":") or s.endswith(","):
        s = s[:-1].rstrip()

    # 3. Track unclosed brackets/braces
    stack = []
    in_str = False
    esc = False
    for char in s:
        if esc:
            esc = False
        elif char == '\\':
            esc = True
        elif char == '"':
            in_str = not in_str
        elif not in_str:
            if char in '{[':
                stack.append(char)
            elif char in '}]':
                if stack:
                    stack.pop()

    # Append missing closing brackets in reverse order
    for opener in reversed(stack):
        if opener == '{':
            s += '}'
        elif opener == '[':
            s += ']'

    # Try loading repaired string
    try:
        return json.loads(s)
    except Exception:
        pass

    # Fallback: if the trailing mapping object was partially written and invalid,
    # drop the trailing incomplete object before the mappings array closer
    last_item_idx = s.rfind(",{")
    if last_item_idx != -1:
        truncated = s[:last_item_idx] + "]}"
        try:
            return json.loads(truncated)
        except Exception:
            pass

    return None


def _validate_response(
    response_obj: AIMappingResponse,
    tokens: dict,
) -> AIMappingResponse:
    """
    Validate AI response strictly.
    - source_field must exist in the analyzed tokens or token index (e.g. field_0, field_1)
    - target_field must be in VALID_TARGET_FIELDS
    - confidence must be 0.0–1.0
    - no two mappings may share the same target_field
    - keep reasoning SHORT (max 1 sentence)
    """
    seen_targets: set = set()
    valid_mappings = []

    # Build map of token keys for 0-based and 1-based indexing
    token_keys = list(tokens.keys())
    token_index_map = {key: key for key in token_keys}
    for idx, key in enumerate(token_keys):
        if f"field_{idx}" not in token_index_map:
            token_index_map[f"field_{idx}"] = key
        if str(idx) not in token_index_map:
            token_index_map[str(idx)] = key

    for mapping in response_obj.mappings:
        src = mapping.source_field
        if tokens:
            if src in token_index_map:
                mapping.source_field = token_index_map[src]
            else:
                logger.warning(
                    "AI returned unknown source_field '%s' — rejected", src
                )
                continue

        # Alias target_field normalization
        tf = mapping.target_field
        if tf in ("COMPOSITE_SOURCE_ENDPOINT", "source.endpoint", "COMPOSITE_ENDPOINT"):
            mapping.target_field = "source.ip"
        elif tf in ("COMPOSITE_DESTINATION_ENDPOINT", "destination.endpoint"):
            mapping.target_field = "destination.ip"

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

        # Truncate reasoning to 1 short sentence max
        reason = mapping.reason.strip()
        if "." in reason:
            reason = reason.split(".")[0] + "."
        mapping.reason = reason[:120]

        seen_targets.add(mapping.target_field)
        valid_mappings.append(mapping)

    return AIMappingResponse(
        format_name=response_obj.format_name or "Custom Log Format",
        format_type=response_obj.format_type or "delimited",
        delimiter=response_obj.delimiter,
        confidence=response_obj.confidence or 0.9,
        mappings=valid_mappings
    )


class GroqProvider(AIProvider):
    """
    Groq implementation of the AIProvider interface.
    Uses the official groq Python SDK with JSON mode.
    Falls back safely (returns None) on any error.
    """

    def suggest_mappings(
        self,
        raw_log: str,
        structure: dict,
        candidate_mappings: dict,
        universal_schema: list,
    ) -> Optional[AIMappingResponse]:
        import app.config as cfg

        api_key = GROQ_API_KEY if GROQ_API_KEY == "" else (cfg.GROQ_API_KEY or GROQ_API_KEY)
        model = cfg.GROQ_MODEL
        timeout = cfg.AI_REQUEST_TIMEOUT

        if not api_key:
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

        completion = None
        try:
            client = Groq(api_key=api_key, timeout=timeout)
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=2048,
                )
            except APIStatusError as err:
                if err.status_code == 400:
                    logger.warning("Groq API returned HTTP 400 with json_object mode, retrying without response_format...")
                    completion = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": _SYSTEM_PROMPT},
                            {"role": "user", "content": user_message},
                        ],
                        temperature=0.1,
                        max_tokens=2048,
                    )
                else:
                    raise err
        except APITimeoutError:
            logger.warning("Groq API request timed out after %ds", timeout)
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

        if not completion:
            return None

        try:
            raw_content = completion.choices[0].message.content.strip()
        except (AttributeError, IndexError) as e:
            logger.warning("Groq response structure unexpected: %s", e)
            return None

        # Safe JSON parsing & repair layer
        parsed_json = _repair_truncated_json(raw_content)
        if not parsed_json:
            logger.warning("Groq raw response received: %s", raw_content[:300])
            logger.warning("Groq JSON parsing and repair failed")
            return None

        try:
            ai_response = AIMappingResponse(**parsed_json)
        except Exception as e:
            logger.warning("Groq response schema mismatch: %s", e)
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

        logger.info("Groq suggested %d validated mappings", len(validated.mappings))
        return validated


def infer_unknown_mapping(raw_event: str, structure: dict) -> Optional[AIMappingResponse]:
    """
    Dedicated helper to infer schema mapping for an unknown raw event using Groq.
    """
    return groq_provider.suggest_mappings(
        raw_log=raw_event,
        structure=structure,
        candidate_mappings={},
        universal_schema=sorted(VALID_TARGET_FIELDS)
    )


# ── Module-level singleton ─────────────────────────────────────────────────────
groq_provider = GroqProvider()
