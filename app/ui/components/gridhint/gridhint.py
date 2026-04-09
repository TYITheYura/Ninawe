from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt

class GridHintWidget(QFrame):
    def __init__(self, parent = None, config = None):
        super().__init__(parent)
        self.setObjectName("GridHint")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # I won't be making any "independent" styles for it for now, since it's only used in desktop.py anyway.
        # I'll think about a better implementation for this component in the future...
        self.setStyleSheet(f"""
            QFrame#GridHint {{
                background-color: {config.groupSelectionColors.get("background")};
                border: 2px dashed {config.groupSelectionColors.get("border")};
                border-radius: {config.groupSelectionBorderRadius}px;
            }}
        """)
        self.hide()
