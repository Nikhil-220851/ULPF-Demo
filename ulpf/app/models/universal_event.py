from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class UniversalEvent(BaseModel):
    """
    Common Universal Event Model.
    Supports top-level semantic areas: event.*, source.*, destination.*, network.*, user.*, device.*, severity
    """
    event: Optional[Dict[str, Any]] = Field(default_factory=dict)
    source: Optional[Dict[str, Any]] = Field(default_factory=dict)
    destination: Optional[Dict[str, Any]] = Field(default_factory=dict)
    network: Optional[Dict[str, Any]] = Field(default_factory=dict)
    user: Optional[Dict[str, Any]] = Field(default_factory=dict)
    device: Optional[Dict[str, Any]] = Field(default_factory=dict)
    severity: Optional[str] = None
