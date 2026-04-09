import importlib
import sys
import os
import configparser
from core.utils import MakeLog

class WidgetManager:
    def __init__(self, parent, widgetType = None):
        if widgetType is None:
            MakeLog("[Log] [WidgetManager] | Widget type not selected")

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

        MakeLog(f"[Log] [WidgetManager] [{self.widgetType.upper()}] | Unloading {len(self.widgets)} widgets...")

        for widget in self.widgets:
            widget.setParent(None)
            widget.deleteLater()
        self.widgets.clear()

    def LoadWidgets(self):
        self.UnloadWidgets()

        configSection = "Taskbar" if self.widgetType == "taskbar" else "Desktop"

        # Reading active widgets
        from core.config import config as themeConfig  # lazy loading btw (hate ImportError: cannot import name 'config' from partially initialized module 'core.config')
        rawList = themeConfig.theme.Get(configSection, "active_widgets", fallback = "")

        if not rawList:
            MakeLog(f"[Log] [WidgetManager] [WidgetType: {self.widgetType.upper()}] | No active widgets found in config.")
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
                    MakeLog(f"[Log] [WidgetManager] [WidgetType: {self.widgetType.upper()}] | Widget '{name}' has no class 'Widget' inside __init__.py. Don't know what to do with it.")
                    continue
                else:
                    widgetClass = getattr(module, "Widget")

                # Attaching the widget to the parent
                instance = widgetClass(self.parent)
                # Adding widget to list
                self.widgets.append(instance)

                MakeLog(f"[Log] [WidgetManager] [WidgetType: {self.widgetType.upper()}] | Loaded: {name}")

            # exceptions
            except ModuleNotFoundError:
                MakeLog(f"[Log] [WidgetManager] [WidgetType: {self.widgetType.upper()}] | Widget folder not found: widgets/{self.widgetType}/{name}")
            except Exception as e:
                MakeLog(f"[Log] [WidgetManager] [WidgetType: {self.widgetType.upper()}] | Failed to load widget '{name}': {e}")
                import traceback
                traceback.print_exc()

    # It can be called without creating an object, although I haven't figured out how to implement it in LoadWidgets properly yet...
    @staticmethod
    def GetWidgetConfig(widgetType, name):
        # Standart w/h props
        BIWidgetConfig = {
            "minWidth": 200,
            "minHeight": 200
        }

        try:
            # priority: 1 - userdata, 2 - app
            from core.config import config as themeConfig
            userPath = themeConfig.theme.GetPath(f"userdata\\widgets\\{widgetType}\\{name}\\config.ini")
            appPath = themeConfig.theme.GetPath(f"app\\widgets\\{widgetType}\\{name}\\config.ini")

            # widget path
            targetPath = userPath if os.path.exists(userPath) else appPath

            if os.path.exists(targetPath):
                # getting data from config
                parser = configparser.ConfigParser()
                parser.read(targetPath, encoding = 'utf-8')

                if parser.has_section("Layout"):
                    # set w/h
                    BIWidgetConfig["minWidth"] = parser.getint("Layout", "min_width", fallback = 200)
                    BIWidgetConfig["minHeight"] = parser.getint("Layout", "min_height", fallback = 200)
        except Exception as e:
            MakeLog(f"[Log] [WidgetManager] [WidgetType: {widgetType.upper()}] | Failed to read config for {name}: {e}")

        return BIWidgetConfig

    # Same here
    @staticmethod
    def GetWidgetClass(widgetType, name):
        try:
            # creating path to module
            modulePath = f"widgets.{widgetType}.{name}"

            # if already imported
            if modulePath in sys.modules:
                module = importlib.reload(sys.modules[modulePath])
            else:
                # else importing
                module = importlib.import_module(modulePath)

            # Showing error if widget class is not found
            if not hasattr(module, "Widget"):
                MakeLog(f"[Log] [WidgetManager] [WidgetType: {widgetType.upper()}] | Widget '{name}' has no class 'Widget'.")
                return None

            # Else returning class
            MakeLog(f"[Log] [WidgetManager] [WidgetType: {widgetType.upper()}] | Loaded: {name}")
            return getattr(module, "Widget")

        except ModuleNotFoundError:
            MakeLog(f"[Log] [WidgetManager] [WidgetType: {widgetType.upper()}] | Widget folder not found: widgets/{widgetType}/{name}")
        except Exception as e:
            MakeLog(f"[Log] [WidgetManager] [WidgetType: {widgetType.upper()}] | Failed to get widget class '{name}': {e}")

        return None

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
                MakeLog(f"[Log] [WidgetManager] [WidgetType: {self.widgetType.upper()}] | Failed to init widget")
