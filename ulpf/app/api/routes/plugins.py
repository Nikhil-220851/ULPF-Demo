from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.plugins.manager import plugin_manager
import uuid

router = APIRouter()

class PluginConfirmation(BaseModel):
    name: str
    signature: Dict[str, Any]
    field_mappings: Dict[str, str]

class PluginUpdateRequest(BaseModel):
    name: Optional[str] = None
    signature: Optional[Dict[str, Any]] = None
    field_mappings: Optional[Dict[str, str]] = None

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

@router.delete("/plugins/{plugin_id}")
async def delete_plugin(plugin_id: str):
    success = plugin_manager.delete_plugin(plugin_id)
    if success:
        return {"status": "success", "message": f"Plugin {plugin_id} deleted successfully"}
    return {"status": "error", "message": f"Failed to delete plugin {plugin_id}"}

@router.put("/plugins/{plugin_id}")
async def update_plugin(plugin_id: str, update_req: PluginUpdateRequest):
    existing = plugin_manager.plugins.get(plugin_id)
    if not existing:
        return {"status": "error", "message": f"Plugin {plugin_id} not found"}

    if update_req.name:
        existing["name"] = update_req.name
    if update_req.signature is not None:
        existing["signature"] = update_req.signature
    if update_req.field_mappings is not None:
        existing["field_mappings"] = update_req.field_mappings

    success = plugin_manager.save_plugin(existing)
    if success:
        return {"status": "success", "plugin": existing}
    return {"status": "error", "message": f"Failed to update plugin {plugin_id}"}
