from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QStackedWidget, QLabel, QScrollArea, QSizeGrip,
    QSizePolicy, QFrame, QCheckBox, QPushButton, QTabWidget, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from core.config import config, BASE_DIR, ConfigWrapper
from core.utils import MakeLog, InternalWindowFader
from core.managers import shellSignals
from ui.components import TitleBar
from .settingbuilder import SettingsUIBuilder
from .jsoneditor import JSONEditor
from .stylesheet import black, white
import configparser
import os
import json
import uuid

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        shellSignals.toggleSettingsWindow.connect(self.show)
        self.internalWindowFader = InternalWindowFader(self)
        self.InitUI()

    def InitUI(self):
        self.resize(1120, 560)
        self.setMinimumSize(560, 420)

        self.baseLayout = QVBoxLayout(self)
        self.baseLayout.setContentsMargins(20, 20, 20, 20)

        self.mainFrame = QFrame(self)
        self.mainFrame.setObjectName("MainFrame")
        self.baseLayout.addWidget(self.mainFrame)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 255))
        shadow.setOffset(0, 0)
        self.mainFrame.setGraphicsEffect(shadow)

        self.windowLayout = QVBoxLayout(self.mainFrame)
        self.windowLayout.setContentsMargins(0, 0, 0, 0)
        self.windowLayout.setSpacing(0)

        self.titleBar = TitleBar(self.mainFrame)
        self.titleBar.titleLabel.setText(config.lang.Translate("SettingsGUI.Title", "window_title", fallback = "Ninawe Settings"))
        self.windowLayout.addWidget(self.titleBar)

        self.contentWidget = QWidget()
        self.contentLayout = QHBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        self.contentLayout.setSpacing(0)

        self.navMenu = QListWidget()
        self.navMenu.setObjectName("NavMenu")
        self.navMenu.setMaximumWidth(200)

        self.pagesStack = QStackedWidget()

        self.contentLayout.addWidget(self.navMenu)
        self.contentLayout.addWidget(self.pagesStack)

        self.windowLayout.addWidget(self.contentWidget)

        self.gripLayout = QHBoxLayout()
        self.gripLayout.setContentsMargins(0, 0, 0, 0)
        self.gripLayout.addStretch()

        self.sizeGrip = QSizeGrip(self.mainFrame)
        self.gripLayout.addWidget(self.sizeGrip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

        self.windowLayout.addLayout(self.gripLayout)

        self.setObjectName("SettingsWindowRoot")

        self.ApplyGlobalStyles()

        self.SetupPages()

        self.navMenu.currentRowChanged.connect(self.ChangePage)
        self.navMenu.setCurrentRow(0)

    def showEvent(self, event):
        geometry = self.frameGeometry()
        centerPoint = self.screen().availableGeometry().center()
        geometry.moveCenter(centerPoint)
        self.move(geometry.topLeft())
        self.internalWindowFader.FadeIn()

    def closeEvent(self, event):
        event.ignore()
        self.internalWindowFader.FadeOut(self.hide)

    def ApplyGlobalStyles(self):
        current_theme = config.app.Get("Theme", "settings_theme", fallback = "black")

        if current_theme == "white":
            self.mainFrame.setStyleSheet(white)
        else:
            self.mainFrame.setStyleSheet(black)

    def SetupPages(self):
        categories = [
            ("General", ["App", "Performance", "Theme"], config.app, "nav_general"),
            ("Hotkeys", ["Hotkeys"], config.app, "nav_hotkeys"),
            ("Desktop", ["Desktop$", "Desktop.Icon$", "Desktop.System$", "Desktop.SystemIcons$"], [config.theme, config.app], "nav_desktop"),
            ("Launchpad", "Launchpad", [config.theme, config.app], "nav_launchpad"),
            ("Taskbar", ["Taskbar.Geometry$", "Taskbar.Position$", "Taskbar$"], config.theme, "nav_taskbar"),
            ("PowerMenu", "PowerMenu", config.theme, "nav_powermenu"),
            ("ContextMenu", "ContextMenu", config.theme, "nav_contextmenu"),
            ("Widgets", None, None, "nav_widgets")
        ]

        for rawName, prefixes, targetCfg, key in categories:
            displayName = config.lang.Translate("SettingsGUI.Nav", key, fallback = rawName)
            self.navMenu.addItem(displayName)

            pageWidget = QWidget()
            pageLayout = QVBoxLayout(pageWidget)

            pageLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
            pageLayout.setSpacing(5)

            if rawName == "PowerMenu":
                headerLabel = QLabel(
                    config.lang.Translate(
                        "SettingsGUI.Sections", "sections_powermenu_buttons",
                        fallback = "PowerMenu Buttons"
                    )
                )
                headerLabel.setObjectName("HeaderLabel")
                pageLayout.addWidget(headerLabel)

                jsonPath = os.path.join(BASE_DIR, "userdata", "preferences", "user", "powermenudata.json")
                buttonList = JSONEditor(jsonPath, rootKey = "buttons")

                pageLayout.addWidget(buttonList)

            elif rawName == "ContextMenu":
                headerLabel = QLabel(
                    config.lang.Translate(
                        "SettingsGUI.Sections", "sections_contextmenu_desktop",
                        fallback = "Desktop Context Menu"
                    )
                )
                headerLabel.setObjectName("HeaderLabel")
                pageLayout.addWidget(headerLabel)

                jsonPath = os.path.join(BASE_DIR, "userdata", "preferences", "user", "contextmenudata.json")
                desktopList = JSONEditor(jsonPath, rootKey = "desktop")
                itemList = JSONEditor(jsonPath, rootKey = "item")

                pageLayout.addWidget(desktopList)

                headerLabel = QLabel(
                    config.lang.Translate(
                        "SettingsGUI.Sections", "sections_contextmenu_desktop_item",
                        fallback = "Desktop Item Context Menu"
                    )
                )
                headerLabel.setObjectName("HeaderLabel")
                pageLayout.addWidget(headerLabel)

                pageLayout.addWidget(itemList)

            elif rawName == "Widgets":
                self.SetupWidgetsPage(pageLayout)
                self.pagesStack.addWidget(pageWidget)
                continue

            if isinstance(targetCfg, list):
                for cfg in targetCfg:
                    self.SetupPage(prefixes, cfg, pageLayout)
            elif prefixes is not None:
                self.SetupPage(prefixes, targetCfg, pageLayout)

            pageLayout.addStretch()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(pageWidget)
            self.pagesStack.addWidget(scroll)

    def SetupWidgetsPage(self, pageLayout):
        mainTabs = QTabWidget()
        pageLayout.addWidget(mainTabs)

        settingsTab = QWidget()
        settingsLayout = QVBoxLayout(settingsTab)
        self.SetupActiveWidgetsSettings(settingsLayout)
        mainTabs.addTab(settingsTab, config.lang.Translate("SettingsGUI.Nav.Widgets", "widgets_tab_settings", fallback = "Settings"))

        galleryTab = QWidget()
        galleryLayout = QVBoxLayout(galleryTab)
        self.SetupWidgetGallery(galleryLayout)
        mainTabs.addTab(galleryTab, config.lang.Translate("SettingsGUI.Nav.Widgets", "widgets_tab_gallery", fallback = "Add Widgets"))

    def SetupActiveWidgetsSettings(self, layout):
        tabs = QTabWidget()
        layout.addWidget(tabs)

        activeWidgets = set()

        taskbarRaw = config.theme.Get("Taskbar.ActiveWidgets", "active_widgets", fallback="")
        for w in taskbarRaw.split(","):
            wName = w.strip()
            if wName:
                activeWidgets.add((wName, "taskbar"))

        desktopJsonPath = os.path.join(BASE_DIR, "userdata", "preferences", "user", "desktopdata.json")
        if os.path.exists(desktopJsonPath):
            try:
                with open(desktopJsonPath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("desktop", []):
                        if item.get("type") == "widget":
                            wName = item.get("name")
                            if wName:
                                activeWidgets.add((wName, "desktop"))
            except Exception as e:
                MakeLog("[Log] [SettingsGUI]", f"Failed to parse desktop JSON: {e}")

        for widgetName, widgetType in activeWidgets:
            widgetConfigPathSys = os.path.join(BASE_DIR, "app", "widgets", widgetType, widgetName, "config.ini")
            widgetConfigPathUser = os.path.join(BASE_DIR, "userdata", "widgets", widgetType, widgetName, "config.ini")

            localPath = None
            if os.path.exists(widgetConfigPathUser):
                localPath = widgetConfigPathUser
            elif os.path.exists(widgetConfigPathSys):
                localPath = widgetConfigPathSys

            if not localPath:
                MakeLog("[Log] [SettingsGUI]", f"Widget config not found: {widgetName} at {widgetType}")
                continue

            tempParser = configparser.ConfigParser(interpolation = None)
            tempParser.read(localPath, encoding = "utf-8")

            if tempParser.has_section("Meta"):
                targetSection = tempParser.get("Meta", "target_section", fallback = None)
                tabName = tempParser.get("Meta", "name", fallback = widgetName)
            else:
                MakeLog("[Log] [SettingsGUI]", f"No [Meta] section in {widgetName}")
                continue

            if not targetSection:
                MakeLog("[Log] [SettingsGUI]", f"target_section is empty in {widgetName}")
                continue
            elif targetSection == "None":
                continue

            widgetTab = QWidget()
            tabLayout = QVBoxLayout(widgetTab)
            tabLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
            tabLayout.setSpacing(5)

            isBound = any(s == targetSection or s.startswith(targetSection + ".") for s in config.theme.parser.sections())
            cbname = config.lang.Translate(
                "SettingsGUI.Controls", "link_button",
                fallback = "Link \"|arg|\" to Theme Config"
            ).split("|arg|")

            bindCb = QCheckBox(cbname[0] + widgetName + cbname[1])
            bindCb.setChecked(isBound)
            bindCb.toggled.connect(lambda checked, ts=targetSection, lp=localPath: self.ToggleWidgetThemeBind(checked, ts, lp))

            headerLayout = QHBoxLayout()
            headerLayout.addWidget(bindCb)
            headerLayout.addStretch()
            tabLayout.addLayout(headerLayout)

            if isBound:
                self.SetupPage(targetSection, config.theme, tabLayout)
            else:
                localConfig = ConfigWrapper()
                localConfig.parser.read(localPath, encoding="utf-8")
                localConfig.configFilePath = localPath
                self.SetupPage(targetSection, localConfig, tabLayout)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(widgetTab)

            tabs.addTab(scroll, tabName)

    def ToggleWidgetThemeBind(self, isChecked, targetSection, localPath):
        localParser = configparser.ConfigParser(interpolation = None)
        localParser.read(localPath, encoding = "utf-8")

        if isChecked:
            for section in localParser.sections():
                if section.lower() in ["meta", "layout"]:
                    continue
                if section == targetSection or section.startswith(targetSection + "."):
                    if not config.theme.parser.has_section(section):
                        config.theme.parser.add_section(section)

                    for key, val in localParser.items(section):
                        config.theme.parser.set(section, key, val)

            config.theme.Save("theme")
            MakeLog("[Log] [SettingsGUI]", f"Linked {targetSection} (and its subsections) to theme config.")

        else:
            sectionsToRemove = []
            for section in config.theme.parser.sections():
                if section == targetSection or section.startswith(targetSection + "."):
                    if not localParser.has_section(section):
                        localParser.add_section(section)

                    for key, val in config.theme.parser.items(section):
                        localParser.set(section, key, val)

                    sectionsToRemove.append(section)

            with open(localPath, "w", encoding="utf-8") as f:
                localParser.write(f)

            MakeLog("[Log] [SettingsGUI]", f"Unlinked {targetSection} from theme config.")

            for section in sectionsToRemove:
                config.theme.parser.remove_section(section)
            config.theme.Save("theme")

        self.RebuildUI()

    def SetupWidgetGallery(self, layout):
        galleryTabs = QTabWidget()
        layout.addWidget(galleryTabs)

        taskbarGallery = QWidget()
        taskbarLayout = QVBoxLayout(taskbarGallery)
        taskbarLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.WidgetGallery(taskbarLayout, "taskbar")
        taskbarGalleryLayout_scroll = QScrollArea()
        taskbarGalleryLayout_scroll.setWidgetResizable(True)
        taskbarGalleryLayout_scroll.setWidget(taskbarGallery)
        galleryTabs.addTab(taskbarGalleryLayout_scroll, "Taskbar")

        desktopGallery = QWidget()
        desktopLayout = QVBoxLayout(desktopGallery)
        desktopLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.WidgetGallery(desktopLayout, "desktop")
        desktopGalleryLayout_scroll = QScrollArea()
        desktopGalleryLayout_scroll.setWidgetResizable(True)
        desktopGalleryLayout_scroll.setWidget(desktopGallery)
        galleryTabs.addTab(desktopGalleryLayout_scroll, "Desktop")

    def SetupPage(self, prefixes, targetConfig, pageLayout):
        if isinstance(prefixes, str):
            prefixes = [prefixes]

        allSections = targetConfig.parser.sections()
        matchingSections = []

        for p in prefixes:
            exactMatchOnly = p.endswith("$")
            cleanPrefix = p[:-1] if exactMatchOnly else p

            for s in allSections:
                if exactMatchOnly:
                    if s == cleanPrefix and s not in matchingSections:
                        matchingSections.append(s)
                else:
                    if (s == cleanPrefix or s.startswith(cleanPrefix + ".")) and s not in matchingSections:
                        matchingSections.append(s)

        matchingSections.sort(
            key = lambda x: (
                next((i for i, p in enumerate(prefixes) if x == p.strip("$") or x.startswith(p.strip("$") + ".")), 99), x
            )
        )

        if not matchingSections:
            return

        for section in matchingSections:
            displayName = section
            for p in prefixes:
                cleanPrefix = p.rstrip("$")

                if section == cleanPrefix:
                    fallbackName = cleanPrefix.split(".")[-1]
                    transKey = f"sections_{cleanPrefix.lower().replace('.', '_')}"
                    displayName = config.lang.Translate("SettingsGUI.Sections", transKey, fallback = fallbackName)
                    break
                elif section.startswith(cleanPrefix + "."):
                    subName = section.replace(cleanPrefix + ".", "")
                    fallbackName = subName.split(".")[-1]
                    transKey = f"sections_{cleanPrefix.lower().replace('.', '_')}_{subName.lower().replace('.', '_')}"
                    displayName = config.lang.Translate("SettingsGUI.Sections", transKey, fallback = fallbackName)
                    break

            headerLabel = QLabel(displayName)
            headerLabel.setObjectName("HeaderLabel")
            pageLayout.addWidget(headerLabel)

            self.RenderSectionFields(section, targetConfig, pageLayout)

    def RenderSectionFields(self, section, targetConfig, layout):
        builder = SettingsUIBuilder(targetConfig, section, parentWindow = self)

        for option, value in targetConfig.parser.items(section):
            if option.lower() in ["meta", "target_section"]:
                continue
            row = builder.BuildSettingRow(option, value)
            layout.addWidget(row)

    def WidgetGallery(self, layout, widgetType):
        widgetDirs = {}
        appPath = os.path.join(BASE_DIR, "app", "widgets", widgetType)
        userPath = os.path.join(BASE_DIR, "userdata", "widgets", widgetType)

        if os.path.exists(appPath):
            for d in os.listdir(appPath):
                if os.path.isdir(os.path.join(appPath, d)):
                    widgetDirs[d] = os.path.join(appPath, d)

        if os.path.exists(userPath):
            for d in os.listdir(userPath):
                if os.path.isdir(os.path.join(userPath, d)):
                    widgetDirs[d] = os.path.join(userPath, d)

        activeTaskbarRaw = config.theme.Get("Taskbar.ActiveWidgets", "active_widgets", fallback="")
        activeTaskbarList = [w.strip() for w in activeTaskbarRaw.split(",") if w.strip()]

        for wName, wPath in widgetDirs.items():
            iniPath = os.path.join(wPath, "config.ini")
            if not os.path.exists(iniPath):
                continue

            parser = configparser.ConfigParser(interpolation = None)
            parser.read(iniPath, encoding = "utf-8")

            displayName = parser.get("Meta", "name", fallback = wName)
            description = parser.get("Meta", "description", fallback = "Custom widget for Ninawe.")

            card = QFrame()
            card.setObjectName("WidgetGalleryCard")
            cardLayout = QHBoxLayout(card)
            cardLayout.setContentsMargins(15, 15, 15, 15)

            infoLayout = QVBoxLayout()
            titleLbl = QLabel(displayName)
            descLbl = QLabel(description)
            descLbl.setWordWrap(True)

            descLbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

            infoLayout.addWidget(titleLbl)
            infoLayout.addWidget(descLbl)

            cardLayout.addLayout(infoLayout, 1)

            if widgetType == "taskbar":
                isActive = wName in activeTaskbarList
                toggleCb = QCheckBox(config.lang.Translate("SettingsGUI.Controls", "widget_active", fallback = "Active"))
                toggleCb.setChecked(isActive)

                toggleCb.toggled.connect(lambda checked, name = wName: self.ToggleTaskbarWidget(name, checked))
                cardLayout.addWidget(toggleCb)

            elif widgetType == "desktop":
                addBtn = QPushButton(config.lang.Translate("SettingsGUI.Controls", "widget_add_desktop", fallback = "Add to Desktop"))
                addBtn.setObjectName("ActionBtn")
                addBtn.setCursor(Qt.CursorShape.PointingHandCursor)
                addBtn.clicked.connect(lambda _, name = wName: self.AddDesktopWidget(name))
                cardLayout.addWidget(addBtn)

            layout.addWidget(card)

        layout.addStretch()

    def ToggleTaskbarWidget(self, widgetName, isActive):
        activeRaw = config.theme.Get("Taskbar.ActiveWidgets", "active_widgets", fallback="")
        activeList = [w.strip() for w in activeRaw.split(",") if w.strip()]

        if isActive and widgetName not in activeList:
            activeList.append(widgetName)
        elif not isActive and widgetName in activeList:
            activeList.remove(widgetName)

        newList = ", ".join(activeList)

        config.theme.Set("Taskbar.ActiveWidgets", "active_widgets", newList)
        config.theme.Save("theme")

        MakeLog("[Log] [SettingsGUI]", f"Taskbar widgets updated: {newList}")

    def AddDesktopWidget(self, widgetName):
        jsonPath = os.path.join(BASE_DIR, "userdata", "preferences", "user", "desktopdata.json")
        data = {"desktop": []}

        if os.path.exists(jsonPath):
            try:
                with open(jsonPath, "r", encoding = "utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                MakeLog("[Log] [SettingsGUI]", f"Failed to read desktop JSON: {e}")

        newWidget = {
            "type": "widget",
            "name": widgetName,
            "position": [0, 0],
            "id": str(uuid.uuid4())
        }

        data.setdefault("desktop", []).append(newWidget)

        try:
            with open(jsonPath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            MakeLog("[Log] [SettingsGUI]", f"Added {widgetName} to desktop JSON.")

            try:
                from ui.desktop.config import DAConfig
                DAConfig.configUpdated.emit("desktop", [])
                MakeLog("[Log] [SettingsGUI]", "Emitted update signal to Desktop.")
            except ImportError as e:
                MakeLog("[Log] [SettingsGUI]", f"Failed to import DAConfig: {e}")

        except Exception as e:
            MakeLog("[Log] [SettingsGUI]", f"Failed to save desktop JSON: {e}")

    def ChangePage(self, index):
        self.pagesStack.setCurrentIndex(index)

    def RebuildUI(self):
        MakeLog("[Log] [SettingsGUI]", "Rebuilding UI due to theme/config change...")
        self.titleBar.titleLabel.setText(config.lang.Translate("SettingsGUI.Title", "window_title", fallback = "Ninawe Settings"))
        self.ApplyGlobalStyles()
        currentIndex = self.navMenu.currentRow()
        self.navMenu.clear()

        while self.pagesStack.count() > 0:
            widget = self.pagesStack.widget(0)
            self.pagesStack.removeWidget(widget)
            widget.deleteLater()

        self.SetupPages()
        self.navMenu.setCurrentRow(currentIndex)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F5:
            self.RebuildUI()
        else:
            super().keyPressEvent(event)
