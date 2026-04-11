from core.config import config as configurator
from core.config import ConfigUpdateChecker
from easydict import EasyDict as easyDict
from core.utils import RAWToPerOrPix
from PyQt6.QtWidgets import QApplication

class LaunchpadConfig(ConfigUpdateChecker):
    def __init__(self):
        self.section = "Launchpad"
        self.launchpadInfoFile = configurator.theme.GetPath("userdata\\preferences\\user\\launchpaddata.json")

        self.Styles = easyDict(
            {
                "mainContainer": {
                    "bgColor": {},
                    "borderWidth": {},
                    "borderRadius": {},
                    "borderColor": {}
                },
                "scroll": {
                    "color": {},
                    "hoverColor": {},
                    "borderRadius": {},
                    "width": {}
                },
                "search": {
                    "main": {
                        "border": {},
                        "padding": {},
                        "text": {}
                    },
                    "default": {},
                    "focus": {}
                }
            }
        )

        self.columns = 0
        self.containerWidth = 0
        self.containerHeight = 0
        self.containerBGColor = ""
        self.isFullscreen = True
        self.fullscreenColor = ""
        self.blurEnabled = False
        self.blurMode = 0

        self.containerStyle = ""
        self.searchbarStyle = ""

        super().__init__([self.section])

        self.Updater()

    def Updater(self):

        screen = QApplication.primaryScreen().geometry()
        self.sw, self.sh = screen.width(), screen.height()

        rawContainerWidth = configurator.theme.Get(self.section, "main_container_width", fallback = 720)
        rawContainerHeight = configurator.theme.Get(self.section, "main_container_height", fallback = 520)

        self.containerWidth = RAWToPerOrPix(rawContainerWidth, self.sw)
        self.containerHeight = RAWToPerOrPix(rawContainerHeight, self.sh)

        self.isFullscreen = configurator.theme.GetBool(self.section, "fullscreen", fallback = True)
        self.blurEnabled = configurator.theme.GetBool(self.section, "blur_enabled", fallback = True)
        self.blurMode = configurator.theme.GetInt(self.section, "blur_mode", fallback = True)

        self.columns = configurator.theme.GetInt(self.section, "main_container_columns", fallback = 4)
        self.containerBGColor = configurator.theme.Get(self.section, "main_container_bg_color", fallback = 520)

        # main container styles

        mainContainerBGColor = configurator.theme.Get(self.section, "main_container_bg_color", fallback = "#FFFFFF")

        # don't do this again please
        self.Styles.mainContainer.bgColor = "transparent" if self.blurEnabled and self.blurMode == 1 and not self.isFullscreen else mainContainerBGColor
        self.Styles.mainContainer.borderWidth = configurator.theme.GetInt(self.section, "main_container_border_width", fallback = 0)
        self.Styles.mainContainer.borderRadius = 0 if self.blurEnabled and self.isFullscreen is False else configurator.theme.GetInt(self.section, "main_container_border_radius", fallback = 10)
        self.Styles.mainContainer.borderColor = configurator.theme.Get(self.section, "main_container_border_color", fallback = "#FFFFFF")

        # this neither
        self.fullscreenColor = configurator.theme.Get(self.section, "fullscreen_color", fallback = "#FFFFFF") if self.isFullscreen else mainContainerBGColor

        self.containerStyle = f"""
            QFrame#LaunchpadContainer {{
                background-color: {self.Styles.mainContainer.bgColor};
                border-radius: {self.Styles.mainContainer.borderRadius}px;
                border: {self.Styles.mainContainer.borderWidth}px solid {self.Styles.mainContainer.borderColor};
            }}
        """

        # End

        # Searchbar styles

        self.Styles.search.main.border.width = configurator.theme.GetInt(self.section, "searchbar_border_width", fallback = 0)
        self.Styles.search.main.border.radius = configurator.theme.GetInt(self.section, "searchbar_border_radius", fallback = 0)
        self.Styles.search.main.padding.x = configurator.theme.GetInt(self.section, "searchbar_padding_x", fallback = 10)
        self.Styles.search.main.padding.y = configurator.theme.GetInt(self.section, "searchbar_padding_y", fallback = 0)
        self.Styles.search.main.text.color = configurator.theme.Get(self.section, "searchbar_text_color", fallback = "#FFFFFF")
        self.Styles.search.main.text.size = configurator.theme.GetInt(self.section, "searchbar_text_size", fallback = 14)

        self.Styles.search.default.bgColor = configurator.theme.Get(self.section, "searchbar_default_bg_color", fallback = "#FFFFFF")
        self.Styles.search.default.borderColor = configurator.theme.Get(self.section, "searchbar_default_border_color", fallback = "#FFFFFF")
        self.Styles.search.focus.bgColor = configurator.theme.Get(self.section, "searchbar_focus_bg_color", fallback = "#FFFFFF")
        self.Styles.search.focus.borderColor = configurator.theme.Get(self.section, "searchbar_focus_border_color", fallback = "#FFFFFF")

        self.searchbarStyle = f"""
            QLineEdit {{
                background-color: {self.Styles.search.default.bgColor};
                border-radius: {self.Styles.search.main.border.radius}px;
                padding: 0px 15px;
                color: {self.Styles.search.main.text.color};
                font-size: {self.Styles.search.main.text.size}px;
                border: {self.Styles.search.main.border.width}px solid {self.Styles.search.default.borderColor};
            }}
            QLineEdit:focus {{
                border-color: {self.Styles.search.focus.borderColor};
                background-color: {self.Styles.search.focus.bgColor};
            }}
        """

        # End

        # Scroll styles

        self.Styles.scroll.color = configurator.theme.Get(self.section, "scroll_color", fallback = "#FFFFFF")
        self.Styles.scroll.hoverColor = configurator.theme.Get(self.section, "scroll_hover_color", fallback = "#FFFFFF")
        self.Styles.scroll.borderRadius = configurator.theme.GetInt(self.section, "scroll_border_radius", fallback = 0)
        self.Styles.scroll.width = configurator.theme.GetInt(self.section, "scoll_width", fallback = 8)

        self.scrollAreaStyle = f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: {self.Styles.scroll.width}px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.Styles.scroll.color};
                min-height: 30px;
                border-radius: {self.Styles.scroll.borderRadius}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.Styles.scroll.hoverColor};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                width: 0px;
                background: none;
                border: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """

        # End

class ItemConfig(ConfigUpdateChecker):
    def __init__(self):
        self.section = "Launchpad.Item"

        self.Styles = easyDict(
            {
                "container": {
                    "main": {},
                    "default": {},
                    "hover": {},
                    "pressed": {}
                },
                "icon": {
                    "main": {},
                    "default": {},
                    "hover": {}
                }
            }
        )

        self.containerStyle = ""
        self.iconStyle = ""

        self.containerWidth = 0
        self.containerHeight = 0
        self.iconSize = 48

        super().__init__([self.section])

        self.Updater()

    def Updater(self):

        # Main container styles

        self.Styles.container.main.borderRadius = configurator.theme.GetInt(self.section, "item_container_border_radius", fallback = 0)
        self.Styles.container.main.borderWidth = configurator.theme.GetInt(self.section, "item_container_border_width", fallback = 0)

        self.Styles.container.default.color = configurator.theme.Get(self.section, "item_container_default_bg_color", fallback = "#FFFFFF")
        self.Styles.container.default.borderColor = configurator.theme.Get(self.section, "item_container_default_border_color", fallback = "#FFFFFF")

        self.Styles.container.hover.color = configurator.theme.Get(self.section, "item_container_hover_bg_color", fallback = "#FFFFFF")
        self.Styles.container.hover.borderColor = configurator.theme.Get(self.section, "item_container_hover_border_color", fallback = "#FFFFFF")

        self.Styles.container.pressed.color = configurator.theme.Get(self.section, "item_container_pressed_bg_color", fallback = "#FFFFFF")
        self.Styles.container.pressed.borderColor = configurator.theme.Get(self.section, "item_container_pressed_border_color", fallback = "#FFFFFF")

        self.containerStyle = f"""
            LaunchpadItem {{
                background-color: {self.Styles.container.default.color};
                border: {self.Styles.container.main.borderWidth}px solid {self.Styles.container.default.borderColor};
                border-radius: {self.Styles.container.main.borderRadius};
            }}
            LaunchpadItem:hover {{
                background-color: {self.Styles.container.hover.color};
                border-color: {self.Styles.container.hover.borderColor};
            }}
            LaunchpadItem[isPressed = "true"] {{
                background-color: {self.Styles.container.pressed.color};
                border-color: {self.Styles.container.pressed.borderColor};
            }}
            LaunchpadItem:focus {{
                background-color: {self.Styles.container.hover.color};
                border-color: {self.Styles.container.hover.borderColor};
            }}
        """

        # Icon container styles

        self.Styles.icon.main.borderRadius = configurator.theme.GetInt(self.section, "item_container_icon_border_radius", fallback = 0)
        self.Styles.icon.main.borderWidth = configurator.theme.GetInt(self.section, "item_container_icon_border_width", fallback = 0)

        self.Styles.icon.default.color = configurator.theme.Get(self.section, "item_container_icon_bg_color", fallback = "#FFFFFF")
        self.Styles.icon.default.borderColor = configurator.theme.Get(self.section, "item_container_icon_border_color", fallback = "#FFFFFF")

        self.iconStyle = f"""
            QLabel#IconLabel {{
                background-color: {self.Styles.icon.default.color};
                border: {self.Styles.icon.main.borderWidth}px solid {self.Styles.icon.default.borderColor};
                border-radius: {self.Styles.icon.main.borderRadius};
            }}
        """

        # you don't understand, this is other thing

        self.containerWidth = configurator.theme.GetInt(self.section, "item_container_width", fallback = 100)
        self.containerHeight = configurator.theme.GetInt(self.section, "item_container_height", fallback = 120)

        self.iconSize = configurator.theme.GetInt(self.section, "item_icon_size", fallback = 48)
        self.iconPadding = configurator.theme.GetInt(self.section, "item_icon_padding", fallback = 15)


LConfig = LaunchpadConfig()
IConfig = ItemConfig()
