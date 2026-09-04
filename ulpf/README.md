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
- `tests/` - Unit tests for all modules
- `docs/` - Architecture and schema documentation

## Initial Setup Instructions
1. Create a virtual environment: `python -m venv venv`
2. Activate the virtual environment: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
3. Install dependencies: `pip install -r requirements.txt`

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
