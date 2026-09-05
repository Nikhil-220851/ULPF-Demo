from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from app.plugins.manager import plugin_manager
import uuid

router = APIRouter()

class PluginConfirmation(BaseModel):
    name: str
    signature: Dict[str, Any]
    field_mappings: Dict[str, str]

@router.post("/plugins/confirm")
async def confirm_plugin(confirmation: PluginConfirmation):
    plugin_id = confirmation.name.lower().replace(" ", "_") + "_" + str(uuid.uuid4())[:8]
    plugin_def = {
        "plugin_id": plugin_id,
        "name": confirmation.name,
        "version": "1.0",
        "signature": confirmation.signature,
        "field_mappings": confirmation.field_mappings,
        "created_by": "human-confirmed",
        "confidence": 1.0,
        "enabled": True
    }
    
    success = plugin_manager.save_plugin(plugin_def)
    if success:
        return {"status": "success", "plugin": plugin_def}
    return {"status": "error", "message": "Failed to save plugin"}

@router.get("/plugins")
async def list_plugins():
    return plugin_manager.get_all_plugins()
