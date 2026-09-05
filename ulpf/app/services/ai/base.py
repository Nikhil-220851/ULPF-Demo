"""
Abstract base class for AI mapping providers.
Implement this interface to add new AI providers (OpenAI, Gemini, Ollama, etc.)
without touching the pipeline.
"""
from abc import ABC, abstractmethod
from typing import Optional
from app.models.ai_mapping import AIMappingResponse


class AIProvider(ABC):
    """
    Interface for AI-assisted field mapping providers.
    All implementations must be safe to call — they must return None
    on any failure rather than raising exceptions into the pipeline.
    """

    @abstractmethod
    def suggest_mappings(
        self,
        raw_log: str,
        structure: dict,
        candidate_mappings: dict,
        universal_schema: list,
    ) -> Optional[AIMappingResponse]:
        """
        Ask the AI provider to suggest semantic field mappings.

        Args:
            raw_log:            The original raw log string.
            structure:          Output of structure_analyzer (tokens, types, format_type).
            candidate_mappings: Output of local semantic_mapper (may be partial).
            universal_schema:   Whitelist of valid Universal Schema target paths.

        Returns:
            AIMappingResponse if suggestions are available and valid, else None.
            Returning None signals the pipeline to fall back to local mapping.
        """
        ...
