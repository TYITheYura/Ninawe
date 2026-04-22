import json
import os
from core.utils import MakeLog

class Manager:
    def __init__(self, filepath):
        self.filepath = filepath
        self.state = {"applist": []}
        self.Load()

    def Load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding = "utf-8") as f:
                    self.state = json.load(f)
            except Exception as e:
                MakeLog("[Log] [TaskbarWidget] [AppListManager]", f"Failed to load JSON: {e}")
        return self.state

    def Save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok = True)
        try:
            with open(self.filepath, "w", encoding = "utf-8") as f:
                json.dump(self.state, f, indent = 4)
        except Exception as e:
            MakeLog("[Log] [TaskbarWidget] [AppListManager]", f"Failed to save JSON: {e}")

    def PinApp(self, path):
        path = os.path.normpath(path).lower()
        if path not in self.state["applist"]:
            self.state["applist"].append(path)
            self.Save()

    def UnpinApp(self, path):
        path = os.path.normpath(path).lower()
        if path in self.state["applist"]:
            self.state["applist"].remove(path)
            self.Save()

    def UpdatePinnedOrder(self, newOrderList):
        self.state = {"applist": newOrderList}
        self.Save()
