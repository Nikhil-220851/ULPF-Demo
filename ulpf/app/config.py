"""
Centralized configuration for the ULPF application.
All environment variables are loaded here. Never import os.getenv directly in other modules.
"""
import os

# ── Groq API ────────────────────────────────────────────────────────────────────
# Obtain your key at https://console.groq.com
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
# llama-3.1-8b-instant: fast, cheap, great for structured JSON tasks
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# ── AI Mapping Behaviour ────────────────────────────────────────────────────────
# Set to "false" to disable AI assistance entirely.
AI_MAPPING_ENABLED: bool = os.getenv("AI_MAPPING_ENABLED", "true").lower() == "true"

# Local semantic mapper confidence must be BELOW this threshold to trigger an AI call.
# Range: 0.0 – 1.0. Default 0.75 means AI is called only when local confidence < 75 %.
AI_MAPPING_THRESHOLD: float = float(os.getenv("AI_MAPPING_THRESHOLD", "0.75"))

# HTTP timeout in seconds for Groq API requests.
AI_REQUEST_TIMEOUT: int = int(os.getenv("AI_REQUEST_TIMEOUT", "30"))
