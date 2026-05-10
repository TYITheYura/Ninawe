from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QCheckBox, QPushButton, QColorDialog, QComboBox,
    QListWidget, QInputDialog, QMessageBox
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor
from core.config import config, BASE_DIR
from core.utils import CreateCustomTheme, MakeLog, SetGlobalAnimations
import shutil
import os
import json
import uuid

class SettingsUIBuilder:
    def __init__(self, targetConfig, sectionName, parentWindow = None):
        self.config = targetConfig
        self.section = sectionName
        self.parentWindow = parentWindow

        self.saveTimer = QTimer()
        self.saveTimer.setSingleShot(True)
        self.saveTimer.timeout.connect(self.CommitSave)

    def BuildSettingRow(self, optionKey, rawValue):
        rowWidget = QWidget()
        layout = QHBoxLayout(rowWidget)
        layout.setContentsMargins(0, 5, 0, 5)

        transKey = f"{self.section.lower()}_{optionKey.lower()}"
        displayName = config.lang.Translate("SettingsGUI.Properties", transKey, fallback = optionKey)

        label = QLabel(displayName)
        label.setObjectName("PropertyLabel")

        layout.addWidget(label)
        layout.addStretch()

        inputWidget = self.DetermineWidget(optionKey, rawValue)
        layout.addWidget(inputWidget)

        return rowWidget

    def DetermineWidget(self, optionKey, value):
        valueStr = str(value).strip().lower()
        INPUT_WIDTH = 250

        if optionKey.lower() == "current_theme":
            return self.BuildThemeSelector(valueStr, optionKey)

        if optionKey.lower() == "language":
            return self.BuildLanguageSelector(valueStr, optionKey)

        if optionKey.lower() == "settings_theme":
            widget = QComboBox()
            widget.setFixedWidth(INPUT_WIDTH)
            widget.addItems(["black", "white"])
            widget.setCurrentText(str(value))
            widget.currentTextChanged.connect(lambda v, o = optionKey: self.OnValueChanged(o, v))
            return widget

        if valueStr in ["true", "false"]:
            widget = QCheckBox()

            text = config.lang.Translate(
                "SettingsGUI.Controls", "toggle_enabled", fallback = "Enabled"
            ) if valueStr == "true" else config.lang.Translate(
                "SettingsGUI.Controls", "toggle_disabled", fallback = "Disabled"
            )

            widget.setText(text)
            widget.setChecked(valueStr == "true")
            widget.setFixedWidth(INPUT_WIDTH)
            widget.toggled.connect(lambda v, w = widget, o = optionKey: self.OnCheckboxToggled(w, o, v))

            return widget

        if valueStr.startswith("#") or valueStr == "transparent" or "color" in optionKey.lower():
            widget = QPushButton()
            widget.setFixedWidth(INPUT_WIDTH)
            widget.setFixedHeight(28)
            widget.setCursor(Qt.CursorShape.PointingHandCursor)
            self.UpdateColorButton(widget, valueStr)
            widget.clicked.connect(lambda _, w = widget, o = optionKey: self.OpenColorPicker(w, o))

            return widget

        widget = QLineEdit()
        widget.setText(str(value))
        widget.setFixedWidth(INPUT_WIDTH)
        widget.textChanged.connect(lambda v, o = optionKey: self.OnValueChanged(o, v))
        return widget

    def OnCheckboxToggled(self, widget, optionKey, isChecked):
        newText = config.lang.Translate(
            "SettingsGUI.Controls", "toggle_enabled", fallback = "Enabled"
        ) if isChecked else config.lang.Translate(
            "SettingsGUI.Controls", "toggle_disabled", fallback = "Disabled"
        )
        widget.setText(newText)

        stringValue = "true" if isChecked else "false"
        self.OnValueChanged(optionKey, stringValue)

    def BuildLanguageSelector(self, currentValue, optionKey):
        widget = QComboBox()
        widget.setFixedWidth(250)

        langs = set()
        for folder in ["app/lang", "userdata/lang"]:
            path = os.path.join(BASE_DIR, folder)
            if os.path.exists(path):
                for f in os.listdir(path):
                    if os.path.isfile(os.path.join(path, f)) and f.endswith(('.json', '.ini')):
                        langs.add(os.path.splitext(f)[0])

        if not langs:
            langs.update(["No langs loaded."])

        sortedLangs = sorted(list(langs))
        widget.addItems(sortedLangs)

        if currentValue in sortedLangs:
            widget.setCurrentText(currentValue)

        widget.currentTextChanged.connect(lambda v, o = optionKey: self.OnValueChanged(o, v))
        return widget

    def BuildThemeSelector(self, currentValue, optionKey):
        container = QWidget()
        container.setFixedWidth(250)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        listWidget = QListWidget()
        listWidget.setObjectName("JSONList")
        listWidget.setFixedHeight(120)

        themes = set()
        for folder in ["app/themes", "userdata/themes"]:
            path = os.path.join(BASE_DIR, folder)
            if os.path.exists(path):
                themes.update([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])

        sortedThemes = sorted(list(themes))
        listWidget.addItems(sortedThemes)

        if currentValue in sortedThemes:
            listWidget.setCurrentRow(sortedThemes.index(currentValue))

        btnLayout = QHBoxLayout()
        btnLayout.setContentsMargins(0, 0, 0, 0)

        btnSave = QPushButton(config.lang.Translate("SettingsGUI.Controls", "save_button", fallback = "Save"))
        btnDelete = QPushButton(config.lang.Translate("SettingsGUI.Controls", "delete_button", fallback = "Delete"))

        btnLayout.addWidget(btnSave)
        btnLayout.addWidget(btnDelete)

        layout.addWidget(listWidget)
        layout.addLayout(btnLayout)

        listWidget.currentTextChanged.connect(lambda v, o = optionKey: self.OnThemeListChanged(v, o))
        btnSave.clicked.connect(lambda: self.SaveThemeAs(listWidget))
        btnDelete.clicked.connect(lambda: self.DeleteTheme(listWidget))

        return container

    def OnThemeListChanged(self, newTheme, optionKey):
        if newTheme and newTheme != config.app.Get("Theme", "current_theme"):
            self.OnValueChanged(optionKey, newTheme)

    def SaveThemeAs(self, listWidget):
        newName, ok = QInputDialog.getText(self.parentWindow, "Save Theme", "Enter new theme name:")

        if not ok or not newName.strip():
            return

        newName = newName.strip()

        if newName in ["default", "custom"]:
            QMessageBox.warning(self.parentWindow, "Error", "Cannot use reserved system names.")
            return

        srcPath = config.theme.currentThemePath
        dstPath = os.path.join(BASE_DIR, "userdata", "themes", newName)

        if os.path.exists(dstPath):
            QMessageBox.warning(self.parentWindow, "Error", "Theme with this name already exists!")
            return

        try:
            shutil.copytree(srcPath, dstPath)
            config.app.Set("Theme", "current_theme", newName)
            config.app.Save("app")
            self.parentWindow.RebuildUI()
        except Exception as e:
            MakeLog("[Error] [ThemeManager]", f"Failed to save theme: {e}")

    def DeleteTheme(self, listWidget):
        themeToDelete = listWidget.currentItem().text() if listWidget.currentItem() else None
        if not themeToDelete:
            return

        if themeToDelete in ["default", "custom"]:
            QMessageBox.warning(self.parentWindow, "Error", "Cannot delete system or scratchpad themes.")
            return

        targetPath = os.path.join(BASE_DIR, "userdata", "themes", themeToDelete)

        if not os.path.exists(targetPath):
            QMessageBox.warning(self.parentWindow, "Error", "You can only delete user themes.")
            return

        reply = QMessageBox.question(
            self.parentWindow, "Confirm", f"Are you sure you want to delete '{themeToDelete}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                isActive = (config.app.Get("Theme", "current_theme") == themeToDelete)
                if isActive:
                    customPath = os.path.join(BASE_DIR, "userdata", "themes", "custom")

                    if os.path.exists(customPath):
                        shutil.rmtree(customPath)

                    os.rename(targetPath, customPath)

                    config.app.Set("Theme", "current_theme", "custom")
                    config.app.Save("app")

                    MakeLog("[Log] [ThemeManager]", f"Active theme '{themeToDelete}' downgraded to 'custom'.")
                else:
                    shutil.rmtree(targetPath)
                    MakeLog("[Log] [ThemeManager]", f"Theme '{themeToDelete}' deleted permanently.")
                self.parentWindow.RebuildUI()
            except Exception as e:
                MakeLog("[Error] [ThemeManager]", f"Failed to delete theme: {e}")

    def OpenColorPicker(self, buttonWidget, optionKey):
        currentColorText = buttonWidget.text().lower()
        initialColor = QColor(currentColorText) if currentColorText != "transparent" else QColor(0, 0, 0, 0)
        color = QColorDialog.getColor(
            initialColor,
            self.parentWindow,
            "Select Color",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )

        if color.isValid():
            colorHex = color.name(QColor.NameFormat.HexArgb) if color.alpha() < 255 else color.name()
            self.UpdateColorButton(buttonWidget, colorHex)
            self.OnValueChanged(optionKey, colorHex)

    def UpdateColorButton(self, button, colorHex):
        if colorHex == "transparent":
            button.setText("Transparent")
        else:
            qcolor = QColor(colorHex)

            # Wow, so now we're communicating in the language of physics???
            luminance = (qcolor.red() * 299 + qcolor.green() * 587 + qcolor.blue() * 114) / 1000

            textColor = "black" if luminance > 128 else "white"

            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colorHex};
                    color: {textColor};
                    font-weight: bold;
                }}
            """)
            button.setText(colorHex.upper())

    def SyncSystemIcon(self, iconType, isEnabled):
        jsonPath = os.path.join(BASE_DIR, "userdata", "preferences", "user", "desktopdata.json")
        if not os.path.exists(jsonPath):
            return

        icons = {
            "show_pc": {
                "type": "system_icon",
                "name": "computer",
                "path": "shell:::{20D04FE0-3AEA-1069-A2D8-08002B30309D}",
                "system_type": "computer",
                "position": [1, 1]
            },
            "show_trash": {
                "type": "system_icon",
                "name": "recycle_bin",
                "path": "shell:::{645FF040-5081-101B-9F08-00AA002F954E}",
                "system_type": "recycle_bin",
                "position": [1, 2]
            }
        }

        if iconType not in icons:
            return

        try:
            with open(jsonPath, "r", encoding="utf-8") as f:
                data = json.load(f)
            desktop = data.get("desktop", [])
            targetType = icons[iconType]["system_type"]
            existing = next((item for item in desktop if item.get("system_type") == targetType), None)

            if isEnabled and not existing:
                newIcon = icons[iconType].copy()
                newIcon["id"] = str(uuid.uuid4())
                desktop.append(newIcon)
                MakeLog("[Log] [SettingsGUI]", f"System icon added to desktop: {targetType}")
            elif not isEnabled and existing:
                desktop.remove(existing)
                MakeLog("[Log] [SettingsGUI]", f"System icon removed from desktop: {targetType}")
            else:
                return

            data["desktop"] = desktop
            with open(jsonPath, "w", encoding = "utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            try:
                from ui.desktop.config import DAConfig
                DAConfig.configUpdated.emit("desktop", [])
            except Exception:
                pass

        except Exception as e:
            MakeLog("[Log] [SettingsGUI]", f"Failed to sync system icons: {e}")

    def OnValueChanged(self, optionKey, newValue):
        currentTheme = config.app.Get("Theme", "current_theme")
        shouldRebuild = False

        if currentTheme != "custom" and self.config == config.theme:
            MakeLog("[Log] [ThemeManager]", f"Forking theme '{currentTheme}' into 'custom'...")

            CreateCustomTheme(currentTheme)

            self.config.Load("custom")
            self.config.Set(self.section, optionKey, newValue)
            self.config.Save("theme")

            config.app.Set("Theme", "current_theme", "custom")
            config.app.Save("app")

            shouldRebuild = True
        else:
            self.config.Set(self.section, optionKey, newValue)
            self.saveTimer.start(500)

        if optionKey.lower() in ["current_theme", "settings_theme", "language"]:
            shouldRebuild = True

        if optionKey.lower() in ["global_blur_enabled"]:
            config.configUpdated.emit("theme", ["ALL"])

        if optionKey.lower() in ["animations_enabled"]:
            SetGlobalAnimations(True if newValue == "true" else False)

        if optionKey.lower() in ["show_pc", "show_trash"]:
            isEnabled = (newValue.lower() == "true")
            self.SyncSystemIcon(optionKey.lower(), isEnabled)

        if shouldRebuild and self.parentWindow:
            QTimer.singleShot(750, self.parentWindow.RebuildUI)

    def CommitSave(self):
        if self.config == config.theme:
            self.config.Save("theme")
        elif self.config == config.app:
            self.config.Save("app")
        else:
            filePath = getattr(self.config, 'configFilePath', None)
            if filePath:
                self.config.Save(filePath)
            else:
                MakeLog(f"[Log] [SettingsGUI] | Cannot save local config, path missing for {self.section}")
