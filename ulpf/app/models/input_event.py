from pydantic import BaseModel

class InputEvent(BaseModel):
    """Model for incoming raw log events."""
    raw_payload: str
