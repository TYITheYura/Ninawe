import importlib
import sys
from PyQt6.QtWidgets import QWidget
from core.config import config as themeConfig

class WidgetManager:
    def __init__(self, parent, widgetType = None):
        if widgetType == None:
            print("[Log] [WidgetManager] | Widget type not selected")

        # link to window
        self.parent = parent
        # taskbar / desktop
        self.widgetType = widgetType
        # imported widget objects
        self.widgets = []

        self.panelHeight = self.panelWidth = None

    def UnloadWidgets(self):
        if not self.widgets:
            return

        print(f"[Log] [WidgetManager] [{self.widgetType.upper()}] | Unloading {len(self.widgets)} widgets...")

        for widget in self.widgets:
            widget.setParent(None)
            widget.deleteLater()
        self.widgets.clear()

    def LoadWidgets(self):
        self.UnloadWidgets()

        configSection = "Taskbar" if self.widgetType == "taskbar" else "Desktop"
        
        # Reading active widgets
        rawList = themeConfig.theme.Get(configSection, "active_widgets", fallback = "")
        
        if not rawList:
            print(f"[Log] [WidgetManager] [WidgetType: {self.widgetType.upper()}] | No active widgets found in config.")
            return

        widgetNames = [x.strip() for x in rawList.split(",")]

        for name in widgetNames:
            if not name:
                continue
            
            try:
                # forming path to widget (module)
                modulePath = f"widgets.{self.widgetType}.{name}"
                
                # reimport module if it imported earlier
                if modulePath in sys.modules:
                    module = importlib.reload(sys.modules[modulePath])
                else:
                    module = importlib.import_module(modulePath)

                # Finding the "Widget" class in the module
                if not hasattr(module, "Widget"):
                    print(f"[Log] [WidgetManager] [WidgetType: {self.widgetType.upper()}] | Widget '{name}' has no class 'Widget' inside __init__.py. Don't know what to do with it.")
                    continue
                else:
                    widgetClass = getattr(module, "Widget")

                # Attaching the widget to the parent
                instance = widgetClass(self.parent)
                # Adding widget to list
                self.widgets.append(instance)
                
                print(f"[Log] [WidgetManager] [WidgetType: {self.widgetType.upper()}] | Loaded: {name}")

            # exceptions
            except ModuleNotFoundError:
                print(f"[Log] [WidgetManager] [WidgetType: {self.widgetType.upper()}] | Widget folder not found: widgets/{self.widgetType}/{name}")
            except Exception as e:
                print(f"[Log] [WidgetManager] [WidgetType: {self.widgetType.upper()}] | Failed to load widget '{name}': {e}")
                import traceback
                traceback.print_exc()

    def ReloadStyles(self, changedSections = None):
        # Reloading winget props (all)
        for widget in self.widgets:
            if hasattr(widget, "Updater"):
                widget.Updater(changedSections)
    
    def InitLayout(self):
        # Reinitializating widget (all)
        for widget in self.widgets:
            if hasattr(widget, "Init"):
                widget.Init()
            else:
                print(f"[Log] [WidgetManager] [WidgetType: {self.widgetType.upper()}] | Failed to init widget")