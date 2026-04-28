import os
from core.config import config as configurator
from core.config import ConfigUpdateChecker
from core.utils import LoadFont
from ui.taskbar import TBConfig
from easydict import EasyDict as easyDict
from PyQt6.QtWidgets import QApplication

class IconConfig(ConfigUpdateChecker):
    def __init__(self):
        self.section = "Desktop.Icon"

        super().__init__([self.section])

        self.itemWidth = 0
        self.itemHeight = 0
        self.spacingX = 0
        self.spacingY = 0
        self.bitmapSize = 0
        self.containerBorderRadius = 0
        self.containerBorder = 0
        self.iconLabelFontFamily = None

        self.iconColors = easyDict(
            {
                "hover": {},
                "selected": {},
                "hoverOnSelected": {},
                "drop": {}
            }
        )

        self.iconLabelStatus = True
        self.iconStyleSheet = ""
        self.labelStyleSheet = ""

        self.Updater()

    def Updater(self):
        self.iconLabelStatus = configurator.theme.GetBool(self.section, "icon_label_status", fallback = True)
        self.iconLabelFontSize = configurator.theme.GetInt(self.section, "icon_label_font_size", fallback = 11)
        self.itemWidth = configurator.theme.GetInt(self.section, "item_width", fallback = 85)
        self.itemHeight = configurator.theme.GetInt(self.section, "item_height", fallback = 110)
        self.spacingX = configurator.theme.GetInt(self.section, "spacing_x", fallback = 0)
        self.spacingY = configurator.theme.GetInt(self.section, "spacing_y", fallback = 0)
        self.bitmapSize = configurator.theme.GetInt(self.section, "bitmap_size", fallback = 48)
        self.iconLabelCompensator = configurator.theme.GetInt(self.section, "icon_label_compensator", fallback = 0)
        self.containerBorderRadius = configurator.theme.GetInt(self.section, "icon_container_border_radius", fallback = 0)
        self.containerBorder = configurator.theme.GetInt(self.section, "icon_container_border", fallback = 0)

        self.iconColors.hover.background = configurator.theme.Get(self.section, "icon_hover_background", fallback = "#44FFFFFF")
        self.iconColors.hover.border = configurator.theme.Get(self.section, "icon_hover_border", fallback = "#55FFFFFF")

        self.iconColors.selected.background = configurator.theme.Get(self.section, "icon_selected_background", fallback = "#55FFFFFF")
        self.iconColors.selected.border = configurator.theme.Get(self.section, "icon_selected_border", fallback = "#66FFFFFF")

        self.iconColors.hoverOnSelected.background = configurator.theme.Get(self.section, "icon_hover_on_selected_background", fallback = "#66FFFFFF")
        self.iconColors.hoverOnSelected.border = configurator.theme.Get(self.section, "icon_hover_on_selected_border", fallback = "#77FFFFFF")

        self.iconColors.drop.background = configurator.theme.Get(self.section, "icon_drop_background", fallback = "#77FFFFFF")
        self.iconColors.drop.border = configurator.theme.Get(self.section, "icon_drop_border", fallback = "#88FFFFFF")

        rawFont = configurator.theme.Get(self.section, "icon_label_font_family", fallback = "Segoe UI")

        if rawFont == "default":
            rawFont = configurator.theme.globals.fontFamily

        themePath = configurator.theme.GetThemePath(
            configurator.app.Get("Theme", "current_theme", fallback = "default")
        )

        self.iconLabelFontFamily = LoadFont(rawFont, themePath)

        self.iconStyleSheet = f"""
            QFrame#IconFrame {{
                background: transparent;
                border: {self.containerBorder}px solid transparent;
                border-radius: {self.containerBorderRadius}px;
            }}
            QFrame#IconFrame:hover {{
                background: {self.iconColors.hover.background};
                border: {self.containerBorder}px solid {self.iconColors.hover.border};
            }}
            QFrame#IconFrame[selected = "true"] {{
                background: {self.iconColors.selected.background};
                border: {self.containerBorder}px solid {self.iconColors.selected.border};
            }}
            QFrame#IconFrame[selected = "true"]:hover {{
                background: {self.iconColors.hoverOnSelected.background};
                border: {self.containerBorder}px solid {self.iconColors.hoverOnSelected.border};
            }}
            QFrame#IconFrame[drop_hover = "true"] {{
                background: {self.iconColors.drop.background};
                border: {self.containerBorder}px solid {self.iconColors.drop.border};
            }}
            QFrame#WidgetFrame {{
                background: transparent;
            }}
        """

        self.labelStyleSheet = f"""
            color: white;
            font-size: {self.iconLabelFontSize}px;
            font-family: "{self.iconLabelFontFamily}";
            background: transparent;
        """

class DesktopConfig(ConfigUpdateChecker):
    def __init__(self):
        self.section = "Desktop"

        super().__init__([self.section])

        self.desktopInfoFile = configurator.theme.GetPath("userdata\\preferences\\user\\desktopdata.json")
        self.desktopPath = os.path.normpath(os.path.expanduser("~/Desktop"))
        self.wallpaperList = []
        self.groupSelectionColors = {}
        self.wallpaperMode = None
        self.windowMarginX = 0
        self.windowMarginY = 0
        self.isCarousel = None
        self.intervalInMin = None
        self.shuffle = None
        self.backgroundPath = None
        self.transitionMs = 0
        self.groupSelectionBorderRadius = 0
        self.groupSelectionBorderWidth = 0
        self.selectionStyleSheet = ""

        self.Updater()

    def Updater(self):
        self.wallpaperMode = configurator.theme.Get(self.section, "wallpaper_mode", fallback = "cover")
        self.isCarousel = configurator.theme.GetBool(self.section, "wallpaper_carousel", fallback = True)
        self.intervalInMin = configurator.theme.GetFloat(self.section, "carousel_interval_min", fallback = 10)
        self.shuffle = configurator.theme.GetBool(self.section, "carousel_shuffle", fallback = False)
        self.backgroundPath = configurator.theme.GetResource(configurator.theme.Get(self.section, "wallpaper_path"))
        self.transitionMs = configurator.theme.GetInt(self.section, "wallpaper_transition_ms", fallback = 500)
        self.windowMarginX = configurator.theme.GetInt(self.section, "window_margin_x", fallback = 0)
        self.windowMarginY = configurator.theme.GetInt(self.section, "window_margin_y", fallback = 0)
        self.groupSelectionBorderRadius = configurator.theme.GetInt(self.section, "group_selection_border_radius", fallback = 0)
        self.groupSelectionBorderWidth = configurator.theme.GetInt(self.section, "group_selection_border_width", fallback = 0)
        self.groupSelectionColors["background"] = configurator.theme.Get(self.section, "group_selection_background", fallback = "#55FFFFFF")
        self.groupSelectionColors["border"] = configurator.theme.Get(self.section, "group_selection_border", fallback = "#66FFFFFF")

        self.selectionStyleSheet = f"""
            background-color: {self.groupSelectionColors.get("background")};
            border: {self.groupSelectionBorderWidth}px solid {self.groupSelectionColors.get("border")};
            border-radius: {self.groupSelectionBorderRadius}px;
        """

class WorkAreaConfig(ConfigUpdateChecker):
    def __init__(self):
        self.section = "Desktop.System"

        super().__init__([self.section])

        self.workArea = easyDict(
            {
                "top": {},
                "right": {},
                "bottom": {},
                "left": {}
            }
        )

        self.taskbarMarginX = 0
        self.taskbarMarginY = 0

        self.sw = 0
        self.sh = 0

        self.Updater()

    def Updater(self):
        screen = QApplication.primaryScreen().geometry()
        self.sw, self.sh = screen.width(), screen.height()

        self.workArea.top = configurator.theme.GetInt(self.section, "work_area_padding_top", fallback = 0)
        self.workArea.right = configurator.theme.GetInt(self.section, "work_area_padding_right", fallback = 0)
        self.workArea.bottom = configurator.theme.GetInt(self.section, "work_area_padding_bottom", fallback = 0)
        self.workArea.left = configurator.theme.GetInt(self.section, "work_area_padding_left", fallback = 0)

        # Horizontal
        self.taskbarMarginY = TBConfig.panelY + TBConfig.panelHeight

        # Vertical
        self.taskbarMarginX = TBConfig.panelX + TBConfig.panelWidth


WAConfig = WorkAreaConfig()
DConfig = DesktopConfig()
IConfig = IconConfig()
