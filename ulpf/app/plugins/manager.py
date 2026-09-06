import json
import os
import glob
from typing import Dict, List, Optional

PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "storage")

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, dict] = {}
        self.ensure_storage()
        self.load_plugins()

    def ensure_storage(self):
        if not os.path.exists(PLUGINS_DIR):
            os.makedirs(PLUGINS_DIR, exist_ok=True)

    def load_plugins(self):
        self.plugins.clear()
        for filepath in glob.glob(os.path.join(PLUGINS_DIR, "*.json")):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    plugin = json.load(f)
                    if plugin.get("enabled", True):
                        self.plugins[plugin.get("plugin_id")] = plugin
            except Exception as e:
                print(f"Failed to load plugin {filepath}: {e}")

    def save_plugin(self, plugin_def: dict) -> bool:
        try:
            plugin_id = plugin_def.get("plugin_id")
            if not plugin_id:
                return False
                
            self.ensure_storage()
            filepath = os.path.join(PLUGINS_DIR, f"{plugin_id}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(plugin_def, f, indent=2)
            
            self.plugins[plugin_id] = plugin_def
            return True
        except Exception as e:
            print(f"Failed to save plugin {plugin_def.get('plugin_id')}: {e}")
            return False

    def delete_plugin(self, plugin_id: str) -> bool:
        try:
            if plugin_id in self.plugins:
                del self.plugins[plugin_id]
            filepath = os.path.join(PLUGINS_DIR, f"{plugin_id}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
            return True
        except Exception as e:
            print(f"Failed to delete plugin {plugin_id}: {e}")
            return False

    def get_all_plugins(self) -> List[dict]:
        return list(self.plugins.values())

    def match_plugin(self, raw_payload: str, structure: dict) -> Optional[dict]:
        """
        Matches a raw event / its structure against stored plugins.
        """
        format_type = structure.get("format_type", "delimited")
        delim = structure.get("delimiter")
        field_count = structure.get("fields", 0)
        line_count = structure.get("line_count", 1)
        
        for plugin_id, plugin in self.plugins.items():
            sig = plugin.get("signature", {})
            
            sig_format_type = sig.get("format_type", "delimited")
            
            # Format types must match
            if sig_format_type != format_type:
                continue
                
            # For delimited logs, check delimiter and field count
            if format_type == "delimited":
                if sig.get("delimiter") == delim and sig.get("field_count") == field_count:
                    return plugin
            
            # For multiline logs, check prefix pattern (if any), line count, and field count
            elif format_type == "multiline_bracketed":
                import re
                prefix_pattern = sig.get("prefix_pattern")
                if prefix_pattern:
                    try:
                        if not re.search(prefix_pattern, raw_payload):
                            continue
                    except:
                        pass # Invalid regex in plugin
                        
                if sig.get("line_count") == line_count and sig.get("field_count") == field_count:
                    return plugin
                
        return None

plugin_manager = PluginManager()
