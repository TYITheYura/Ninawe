import json
import os
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QStackedWidget,
    QLabel, QLineEdit, QFormLayout, QPushButton, QTextEdit
)
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtCore import Qt
from core.utils import MakeLog
from core.config import config

class JSONEditor(QWidget):
    def __init__(self, jsonPath, rootKey = None):
        super().__init__()
        self.jsonPath = jsonPath
        self.rootKey = rootKey
        self.data = {}
        self.targetArray = []

        self.InitUI()
        self.LoadData()

    def InitUI(self):
        self.setMinimumHeight(250)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = QHBoxLayout()

        self.btnAdd = QPushButton("+")
        self.btnAdd.clicked.connect(self.AddNewStruct)

        self.btnDelete = QPushButton("-")
        self.btnDelete.clicked.connect(self.DeleteStruct)

        self.btnUp = QPushButton("↑")
        self.btnUp.setFixedWidth(30)
        self.btnUp.clicked.connect(self.MoveUp)

        self.btnDown = QPushButton("↓")
        self.btnDown.setFixedWidth(30)
        self.btnDown.clicked.connect(self.MoveDown)

        self.btnToggleMode = QPushButton("</> " + config.lang.Translate("SettingsGUI.Controls", "edit_json_button", fallback = "Edit JSON"))
        self.btnToggleMode.setCheckable(True)
        self.btnToggleMode.clicked.connect(self.ToggleMode)

        self.toolbar.addWidget(self.btnAdd)
        self.toolbar.addWidget(self.btnDelete)
        self.toolbar.addWidget(self.btnUp)
        self.toolbar.addWidget(self.btnDown)
        self.toolbar.addStretch()
        self.toolbar.addWidget(self.btnToggleMode)

        self.mainLayout.addLayout(self.toolbar)

        self.stack = QStackedWidget()
        self.mainLayout.addWidget(self.stack)

        self.uiPage = QWidget()
        self.uiLayout = QHBoxLayout(self.uiPage)
        self.uiLayout.setContentsMargins(0, 0, 0, 0)

        self.listWidget = QListWidget()
        self.listWidget.setObjectName("JSONList")
        self.listWidget.setMaximumWidth(200)
        self.listWidget.currentRowChanged.connect(self.OnItemSelected)

        self.formContainer = QWidget()
        self.formLayout = QFormLayout(self.formContainer)
        self.formLayout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.uiLayout.addWidget(self.listWidget)
        self.uiLayout.addWidget(self.formContainer, 1)
        self.stack.addWidget(self.uiPage)

        self.rawPage = QWidget()
        self.rawLayout = QVBoxLayout(self.rawPage)
        self.rawLayout.setContentsMargins(0, 0, 0, 0)

        self.rawEditor = QTextEdit()
        metrics = QFontMetrics(self.rawEditor.font())
        self.rawEditor.setTabStopDistance(metrics.horizontalAdvance(' ') * 4)
        self.rawLayout.addWidget(self.rawEditor)
        self.stack.addWidget(self.rawPage)

    def LoadData(self):
        if not os.path.exists(self.jsonPath):
            MakeLog("[Log] [JSONEditor]", f"JSON not found: {self.jsonPath}")
            return

        with open(self.jsonPath, "r", encoding = "utf-8") as f:
            self.data = json.load(f)

        if self.rootKey and self.rootKey in self.data:
            self.targetArray = self.data[self.rootKey]
        elif isinstance(self.data, list):
            self.targetArray = self.data
        else:
            self.targetArray = []

        self.RefreshList()

    def RefreshList(self, keepIndex=0):
        self.listWidget.clear()
        for item in self.targetArray:
            name = item.get("label_id") or item.get("label") or item.get("id") or item.get("action") or "Unknown/Separator"
            self.listWidget.addItem(name)

        if self.listWidget.count() > 0:
            self.listWidget.setCurrentRow(min(keepIndex, self.listWidget.count() - 1))
        else:
            self.OnItemSelected(-1)

    def AddNewStruct(self):
        newItem = {
            "label_id": "New.Item",
            "label": "New Item",
            "action": "none"
        }
        self.targetArray.append(newItem)
        self.SaveData()
        self.RefreshList(len(self.targetArray) - 1)

    def DeleteStruct(self):
        row = self.listWidget.currentRow()
        if row >= 0 and row < len(self.targetArray):
            del self.targetArray[row]
            self.SaveData()
            nextRow = max(0, min(row, len(self.targetArray) - 1))
            self.RefreshList(nextRow)

    def MoveUp(self):
        row = self.listWidget.currentRow()
        if row > 0:
            self.targetArray[row], self.targetArray[row - 1] = self.targetArray[row - 1], self.targetArray[row]
            self.SaveData()
            self.RefreshList(row - 1)

    def MoveDown(self):
        row = self.listWidget.currentRow()
        if row >= 0 and row < len(self.targetArray) - 1:
            self.targetArray[row], self.targetArray[row + 1] = self.targetArray[row + 1], self.targetArray[row]
            self.SaveData()
            self.RefreshList(row + 1)

    def ToggleMode(self):
        if self.btnToggleMode.isChecked():
            self.btnToggleMode.setText(config.lang.Translate("SettingsGUI.Controls", "back_to_ui_button", fallback = "Back to UI"))
            self.btnAdd.setEnabled(False)
            self.btnDelete.setEnabled(False)
            self.btnUp.setEnabled(False)
            self.btnDown.setEnabled(False)

            self.setMinimumHeight(400)

            formattedJson = json.dumps(self.targetArray, indent=4, ensure_ascii=False)
            self.rawEditor.setPlainText(formattedJson)
            self.stack.setCurrentIndex(1)
        else:
            success = self.SaveRawData()
            if success:
                self.btnToggleMode.setText("</> " + config.lang.Translate("SettingsGUI.Controls", "edit_json_button", fallback = "Edit JSON"))
                self.btnAdd.setEnabled(True)
                self.btnDelete.setEnabled(True)
                self.btnUp.setEnabled(True)
                self.btnDown.setEnabled(True)
                self.setMinimumHeight(250)
                self.stack.setCurrentIndex(0)
            else:
                self.btnToggleMode.setChecked(True)

    def SaveRawData(self):
        rawText = self.rawEditor.toPlainText()
        try:
            parsedArray = json.loads(rawText)
            if not isinstance(parsedArray, list):
                raise ValueError("Root element must be a JSON array []")

            self.targetArray = parsedArray
            if self.rootKey:
                self.data[self.rootKey] = self.targetArray
            else:
                self.data = self.targetArray

            self.SaveData()
            self.RefreshList(self.listWidget.currentRow())
            MakeLog("[Log] [JSONEditor] Raw JSON saved successfully.")
            return True
        except Exception as e:
            MakeLog(f"[Log] [JSONEditor] Invalid JSON: {e}")
            return False

    def OnItemSelected(self, index):
        for i in reversed(range(self.formLayout.count())):
            widgetToRemove = self.formLayout.itemAt(i).widget()
            if widgetToRemove:
                widgetToRemove.setParent(None)

        if index < 0 or index >= len(self.targetArray):
            return

        itemData = self.targetArray[index]

        for key, value in itemData.items():
            if isinstance(value, (str, int, float, bool)):
                inputField = QLineEdit(str(value))
                inputField.textChanged.connect(lambda text, k = key, idx = index: self.UpdateJSONValue(idx, k, text))
                self.formLayout.addRow(QLabel(key.capitalize() + ":"), inputField)
            elif isinstance(value, (list, dict)):
                stubField = QLineEdit("[Complex Object - Use \"Edit JSON\" to edit]")
                stubField.setReadOnly(True)
                stubField.setStyleSheet("color: gray; background-color: transparent; border: 1px dashed gray;")
                self.formLayout.addRow(QLabel(key.capitalize() + ":"), stubField)

    def UpdateJSONValue(self, index, key, newValue):
        self.targetArray[index][key] = newValue
        self.SaveData()

    def SaveData(self):
        with open(self.jsonPath, "w", encoding = "utf-8") as f:
            json.dump(self.data, f, indent = 4, ensure_ascii = False)
