from core.config import config as configurator
from core.utils import LoadFont
from easydict import EasyDict as easyDict

class ContextMenuConfig:
    def __init__(self):
        # Main context menu path (in case of important negotiations)
        self.contextMenuDataPath = configurator.theme.GetPath("userdata\\preferences\\user\\contextmenudata.json")
        # Stylesheet
        self.section = "ContextMenu"
        self.menuBGColor = ""
        self.menuBorder = easyDict(
            {
                "color": str,
                "width": int,
                "radius": int
            }
        )
        self.item = easyDict(
            {
                "color": str,
                "paddingX": int,
                "paddingY": int,
                "margin": int,
                "radius": int
            }
        )
        self.separator = easyDict(
            {
                "color": str,
                "height": int,
                "marginX": int,
                "marginY": int
            }
        )
        self.fontColor = ""
        self.fontSize = 0
        self.fontFamily = ""
        self.contextMenuStyleSheet = ""

    def Updater(self):
        self.menuBGColor = configurator.theme.Get(self.section, "menu_bg_color", fallback = "#FFFFFFFF")
        self.menuBorder.color = configurator.theme.Get(self.section, "menu_border_color", fallback = "black")
        self.menuBorder.width = configurator.theme.GetInt(self.section, "menu_border_width", fallback = 1)
        self.menuBorder.radius = configurator.theme.GetInt(self.section, "menu_border_radius", fallback = 0)
        self.menuPadding = configurator.theme.GetInt(self.section, "menu_padding", fallback = 5)
        self.item.color = configurator.theme.Get(self.section, "item_selected_bg_color", fallback = "#AAAAAA")
        self.item.paddingX = configurator.theme.GetInt(self.section, "item_padding_x", fallback = 15)
        self.item.paddingY = configurator.theme.GetInt(self.section, "item_padding_y", fallback = 4)
        self.item.margin = configurator.theme.GetInt(self.section, "item_margin", fallback = 2)
        self.separator.color = configurator.theme.Get(self.section, "separator_bg_color", fallback = "#999999")
        self.separator.height = configurator.theme.GetInt(self.section, "separator_height", fallback = 1)
        self.separator.marginX = configurator.theme.GetInt(self.section, "separator_margin_x", fallback = 10)
        self.separator.marginY = configurator.theme.GetInt(self.section, "separator_margin_y", fallback = 4)

        self.item.radius = max(0, self.menuBorder.radius - self.menuPadding)

        self.fontSize = configurator.theme.Get(self.section, "font_size", fallback = 11)
        self.fontSize = configurator.theme.globals.fontSize if self.fontSize == "default" else configurator.theme.GetInt(self.section, "font_size", fallback = 11)

        self.fontColor = configurator.theme.Get(self.section, "font_color", fallback = 11)
        self.fontColor = configurator.theme.globals.fontColor if self.fontColor == "default" else self.fontColor

        self.fontFamily = configurator.theme.Get(self.section, "font_family", fallback = "Segoe UI")

        if self.fontFamily == "default":
            self.fontFamily = configurator.theme.globals.fontFamily

        themePath = configurator.theme.GetThemePath(
            configurator.app.Get("Theme", "current_theme", fallback = "default")
        )

        self.fontFamily = LoadFont(self.fontFamily, themePath)

        self.contextMenuStyleSheet = f"""
            QMenu {{
                background-color: {self.menuBGColor};
                color: {self.fontColor};
                border: {self.menuBorder.width}px solid {self.menuBorder.color};
                border-radius: {self.menuBorder.radius}px;
                padding: {self.menuPadding}px;
                font-family: {self.fontFamily};
                font-size: {self.fontSize}px;
            }}
            QMenu::item {{
                padding: {self.item.paddingY}px {self.item.paddingX}px {self.item.paddingY}px {self.item.paddingX}px;
                border-radius: {self.item.radius}px;
                margin: {self.item.margin}px;
            }}
            QMenu::item:selected {{
                background-color: {self.item.color};
            }}
            QMenu::separator {{
                height: {self.separator.height}px;
                background: {self.separator.color};
                margin: {self.separator.marginY}px {self.separator.marginX}px;
            }}
            QMenu::indicator {{
                width: 0px; height: 0px;
            }}
        """


CMConfig = ContextMenuConfig()
