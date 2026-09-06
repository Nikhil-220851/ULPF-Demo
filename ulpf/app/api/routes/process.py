from fastapi import APIRouter
from app.models.input_event import InputEvent, BatchInput
from app.models.processing_result import ProcessingResult, BatchProcessingResult
from app.core.pipeline import process_event

router = APIRouter()

@router.post("/process", response_model=ProcessingResult)
async def process_log(event: InputEvent):
    return process_event(event)

@router.post("/process/batch", response_model=BatchProcessingResult)
async def process_batch(batch: BatchInput):
    results = []
    ai_cache = {}
    for evt in batch.events:
        if isinstance(evt, str):
            if evt.strip():
                results.append(process_event(InputEvent(raw_payload=evt), ai_cache=ai_cache))
        elif isinstance(evt, InputEvent):
            if evt.raw_payload.strip():
                results.append(process_event(evt, ai_cache=ai_cache))
        else:
            raw = getattr(evt, "raw_payload", None) or (evt.get("raw_payload") if isinstance(evt, dict) else None)
            if raw and raw.strip():
                results.append(process_event(InputEvent(**(evt if isinstance(evt, dict) else evt.dict())), ai_cache=ai_cache))
            
    return BatchProcessingResult(
        total=len(batch.events),
        processed=len(results),
        results=results
    )
