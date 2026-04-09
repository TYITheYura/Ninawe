import os
import json
from core.utils import MakeLog

class DesktopStateManager:
    def __init__(self, filepath):
        self.filepath = filepath
        self.state = {"desktop": []}
        self.Load()

    def Load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding = "utf-8") as f:
                    self.state = json.load(f)
            except Exception as e:
                MakeLog("[Log] [StateManager]", f"Failed to read JSON: {e}")
        return self.state

    def Save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok = True)
        try:
            with open(self.filepath, "w", encoding = "utf-8") as f:
                json.dump(self.state, f, indent = 4, ensure_ascii = False)
        except Exception as e:
            MakeLog("[Log] [StateManager]", f"Failed to save JSON: {e}")

    def UpdatePosition(self, identifier, gridX, gridY, isWidget = False):
        try:
            for data in self.state.get("desktop", []):
                if isWidget and data.get("type") == "widget":
                    if data.get("id") == identifier:
                        data["position"] = [gridX, gridY]
                        break
                elif not isWidget and data.get("type") != "widget":
                    if data.get("path") == identifier:
                        data["position"] = [gridX, gridY]
                        break
            self.Save()
        except Exception as e:
            MakeLog("[Log] [StateManager]", f"Failed to save new position for {identifier}: {e}")

    def RemoveItem(self, identifier, isWidget = False):
        try:
            if isWidget:
                self.state["desktop"] = [
                    item for item in self.state.get("desktop", []) if not (item.get("type") == "widget" and item.get("id") == identifier)
                ]
            else:
                self.state["desktop"] = [
                    item for item in self.state.get("desktop", []) if item.get("path") != identifier
                ]
            self.Save()
        except Exception as e:
            MakeLog("[Log] [StateManager]", f"Failed to remove item {identifier} from JSON: {e}")

    def UpdateEntireDesktop(self, newDesktopArray):
        self.state["desktop"] = newDesktopArray
        self.Save()
