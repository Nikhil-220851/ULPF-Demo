# ULPF — Universal Log Pre-processing Framework

## Problem Being Solved
Heterogeneous network-device logs come in many formats. ULPF processes these logs and converts them into a common universal representation while preserving the raw data, ensuring data quality, and allowing for traceability.

## High-Level Architecture
The common pipeline processes logs through the following stages:
INPUT → FORMAT DETECTION → PARSING → FIELD UNDERSTANDING → NORMALIZATION → VALIDATION → LOSSLESS OUTPUT

## Three-Module Development Structure
The repository is organized around three core modules, each developed independently:
- **Member 1 (app/known_logs/):** Reliable deterministic processing of known/common log formats (JSON, Syslog, CEF, LEEF, Key-Value, CSV/Delimited).
- **Member 2 (app/unknown_logs/):** Handling unknown/custom log formats via structure analysis, semantic field inference, and reusable source profiles.
- **Member 3 (app/trust/):** Ensuring processing is valid, explainable, traceable, and lossless (validation, quarantine, provenance, data quality).

## Repository Structure
- `app/` - Core application code
  - `known_logs/` - Member 1
  - `unknown_logs/` - Member 2
  - `trust/` - Member 3
  - `models/` - Shared contracts
  - `services/ai/` - AI provider abstraction (Groq, extensible)
  - `config.py` - Centralised environment variable configuration
- `tests/` - Unit tests for all modules
- `docs/` - Architecture and schema documentation

## Initial Setup Instructions
1. Create a virtual environment: `python -m venv venv`
2. Activate the virtual environment: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in your API key (optional — AI is gracefully disabled if key is absent)

## How to Run
Run the FastAPI application locally:
```bash
uvicorn app.main:app --reload
```

## Development Rules
- **Member 1:** Owns `app/known_logs/`, `tests/test_known_logs/`, `samples/`
- **Member 2:** Owns `app/unknown_logs/`, `tests/test_unknown_logs/`
- **Member 3:** Owns `app/trust/`, `tests/test_trust/`, `schemas/`
- **Shared:** `app/models/`, `app/core/`, `app/api/`, `app/mappings/`, `tests/test_pipeline.py`, `docs/`
- The shared model/interface must be agreed upon before module implementation begins.

---

"## AI-Assisted Mapping (Groq Integration)

ULPF integrates the **Groq API** as an optional AI assistance layer for unknown log formats.
AI is an enhancement — the pipeline works fully without it.

### How It Works

```
Unknown Log
   ↓
Structure Analyzer        (rule-based token detection)
   ↓
Local Semantic Mapper     (rule-based field mapping)
   ↓
If local confidence < threshold (default 0.75):
   ↓
Groq API                  (AI field mapping suggestions)
   ↓
Pydantic Validation       (strict schema enforcement)
   ↓
Mapping Merger            (AI + local candidates merged)
   ↓
Frontend                  (human reviews AI suggestions)
   ↓
Human Confirmation        (user approves final mapping)
   ↓
Plugin Registry           (AI never writes directly)
```

### Environment Variables

Copy `.env.example` to `.env`:

```env
# Required for AI assistance
GROQ_API_KEY=your_groq_api_key_here

# Model: openai/gpt-oss-20b (recommended default) or openai/gpt-oss-120b
GROQ_MODEL=openai/gpt-oss-20b

# Set to false to disable AI (pipeline still works locally)
AI_MAPPING_ENABLED=true

# AI called only when local mapper confidence is below this threshold
AI_MAPPING_THRESHOLD=0.75

# API request timeout in seconds
AI_REQUEST_TIMEOUT=10
```

Get your free API key at [console.groq.com](https://console.groq.com).
**Never commit a real API key to the repository.**

### Failure / Fallback Behaviour

If Groq is unavailable (network error, bad key, timeout, rate limit, malformed response):
- The pipeline **does not crash**
- `ai_used: false`, `ai_status: "unavailable"` is returned in the API response
- Local semantic mapping continues as normal
- The human confirmation flow is still available

### Example API Response (UNKNOWN format with AI)

```json
{
  "detected_format": "UNKNOWN",
  "ai_used": true,
  "ai_status": "success",
  "candidate_mappings": {
    "field_3": {
      "mapped_to": "user.name",
      "confidence": 0.97,
      "source": "ai",
      "ai_reason": "Value appears to be a username.",
      "value": "bob"
    }
  }
}
```

### Debug Endpoint

Test AI mapping independently (without running the full pipeline):

```bash
POST /ai/map
{
  "raw_log": "2026/09/05 FW-01 ACT=7 N=10.20.30.40 USR=bob",
  "detected_structure": {},
  "candidate_mappings": {}
}
```

### Security

- The `GROQ_API_KEY` is **never** sent to the frontend
- The API key is **never** logged
- Groq **cannot** directly write to the plugin registry"
- All AI responses are **strictly validated** through Pydantic before use
- Invalid target fields, unknown source fields, and duplicate mappings are all **rejected**

### Adding a New AI Provider

Implement the `AIProvider` interface in `app/services/ai/base.py`:

```python
from app.services.ai.base import AIProvider

class MyProvider(AIProvider):
    def suggest_mappings(self, raw_log, structure, candidate_mappings, universal_schema):
        ...  # return AIMappingResponse or None
```

Then swap the provider in `pipeline.py` without changing any other code.
