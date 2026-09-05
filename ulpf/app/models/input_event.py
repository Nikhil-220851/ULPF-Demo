from pydantic import BaseModel
from typing import List, Optional, Union

class InputEvent(BaseModel):
    """Model for incoming raw log events."""
    raw_payload: str
    source_file: Optional[str] = None
    source_file_index: Optional[int] = None

class BatchInput(BaseModel):
    events: List[Union[InputEvent, str]]
