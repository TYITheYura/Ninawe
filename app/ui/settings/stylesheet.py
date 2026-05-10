black = """
    QFrame#MainFrame {
        background-color: rgba(30, 30, 30, 200);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    QLabel {
        color: #FFFFFF;
    }
    QLabel#PropertyLabel {
        margin-left: 15px;
    }
    QLabel#HeaderLabel {
        font-size: 18px;
        font-weight: bold;
        color: #A0A0A0;
        margin: 10px 0 10px 0;
    }
    QListWidget#NavMenu {
        background-color: transparent;
        border: none;
        outline: none;
        padding: 10px;
    }
    QListWidget#NavMenu::item {
        color: #CCCCCC;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 2px;
    }
    QListWidget#NavMenu::item:hover {
        background-color: rgba(255, 255, 255, 0.05);
    }
    QListWidget#NavMenu::item:selected {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        font-weight: bold;
    }
    QListWidget#JSONList {
        background-color: transparent;
        outline: none;
        font-family: Consolas, monospace;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        padding: 2px;
    }
    QListWidget#JSONList::item {
        color: #CCCCCC;
        border-radius: 4px;
        padding: 4px 8px;
        margin-bottom: 2px;
    }
    QListWidget#JSONList::item:hover {
        background-color: rgba(255, 255, 255, 0.05);
    }
    QListWidget#JSONList::item:selected {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        font-weight: bold;
    }
    QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
        border: none;
        background-color: transparent;
    }
    QScrollBar:vertical {
        border: none;
        background-color: transparent;
        width: 8px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar:horizontal {
        border: none;
        background-color: transparent;
        height: 8px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical,
    QScrollBar::handle:horizontal {
        background-color: rgba(255, 255, 255, 0.15);
        min-height: 30px;
        min-width: 30px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover,
    QScrollBar::handle:horizontal:hover {
        background-color: rgba(255, 255, 255, 0.3);
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical,
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        border: none;
        background-color: transparent;
        width: 0px;
        height: 0px;
    }
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical,
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {
        background-color: transparent;
    }
    QTabWidget::pane {
        border: none;
        background-color: transparent;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
    QTabBar::tab {
        background-color: transparent;
        color: #A0A0A0;
        padding: 8px 16px;
        margin-right: 4px;
        border-bottom: 2px solid transparent;
        font-weight: bold;
    }
    QTabBar::tab:hover {
        color: white;
        background-color: rgba(255, 255, 255, 0.05);
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected {
        color: white;
        border-bottom: 2px solid #0078D7;
    }
    QLineEdit {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        padding: 6px 10px;
        color: white;
    }
    QLineEdit:focus {
        border: 1px solid rgba(255, 255, 255, 0.3);
        background-color: rgba(255, 255, 255, 0.1);
    }
    QComboBox {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        padding: 6px 10px;
        color: white;
    }
    QComboBox:hover {
        border: 1px solid rgba(255, 255, 255, 0.2);
        background-color: rgba(255, 255, 255, 0.08);
    }
    QComboBox::drop-down {
        border: none;
        width: 30px;
    }
    QComboBox QAbstractItemView {
        background-color: #252525;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        color: white;
        selection-background-color: rgba(255, 255, 255, 0.1);
        outline: none;
    }
    QCheckBox {
        color: white;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        background-color: rgba(0, 0, 0, 0.2);
    }
    QCheckBox::indicator:hover {
        border: 1px solid rgba(255, 255, 255, 0.4);
    }
    QCheckBox::indicator:checked {
        background-color: #0078D7;
        border: 1px solid #0078D7;
    }
    QPushButton {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        padding: 6px 12px;
        color: white;
    }
    QPushButton:hover {
        background-color: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    QPushButton:pressed {
        background-color: rgba(255, 255, 255, 0.05);
    }
    QPushButton#ActionBtn {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        font-weight: bold;
    }
    QPushButton#ActionBtn:hover {
        background-color: rgba(255, 255, 255, 0.2);
    }
    QPushButton#CloseButton {
        background-color: transparent;
        border: none;
        color: #A0A0A0;
        font-weight: bold;
        border-top-right-radius: 9px;
        border-bottom-left-radius: 9px;
        border-bottom-right-radius: 0px;
        border-top-left-radius: 0px;
        padding: 0px;
        outline: none;
    }
    QPushButton#CloseButton:hover {
        background-color: #E81123;
        color: white;
    }
    QPushButton:disabled {
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        color: rgba(255, 255, 255, 0.3);
    }
    QPushButton#ActionBtn:disabled {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px dashed rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.3);
    }
    QFrame#WidgetGalleryCard {
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
    }
    QFrame#WidgetGalleryCard:hover {
        background-color: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    QTextEdit {
        background-color: rgba(255, 255, 255, 0.05);
        color: #D4D4D4;
        font-family: Consolas, monospace;
        font-size: 13px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        padding: 4px;
    }
"""

white = """
    QFrame#MainFrame {
        background-color: rgba(255, 255, 255, 220);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 10px;
    }
    QLabel {
        color: #202020;
    }
    QLabel#PropertyLabel {
        margin-left: 15px;
    }
    QLabel#HeaderLabel {
        font-size: 18px;
        font-weight: bold;
        color: #707070;
        margin: 10px 0 10px 0;
    }
    QListWidget#NavMenu {
        background-color: transparent;
        border: none;
        outline: none;
        padding: 10px;
    }
    QListWidget#NavMenu::item {
        color: #404040;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 2px;
    }
    QListWidget#NavMenu::item:hover {
        background-color: rgba(0, 0, 0, 0.04);
    }
    QListWidget#NavMenu::item:selected {
        background-color: rgba(0, 120, 215, 0.12);
        color: #000000;
        font-weight: bold;
    }
    QListWidget#JSONList {
        background-color: rgba(255, 255, 255, 0.7);
        outline: none;
        font-family: Consolas, monospace;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 4px;
        padding: 2px;
    }
    QListWidget#JSONList::item {
        color: #303030;
        border-radius: 4px;
        padding: 4px 8px;
        margin-bottom: 2px;
    }
    QListWidget#JSONList::item:hover {
        background-color: rgba(0, 0, 0, 0.04);
    }
    QListWidget#JSONList::item:selected {
        background-color: rgba(0, 120, 215, 0.12);
        color: #000000;
        font-weight: bold;
    }
    QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
        border: none;
        background-color: transparent;
    }
    QScrollBar:vertical {
        border: none;
        background-color: transparent;
        width: 8px;
        margin: 0px;
    }
    QScrollBar:horizontal {
        border: none;
        background-color: transparent;
        height: 8px;
        margin: 0px;
    }
    QScrollBar::handle:vertical,
    QScrollBar::handle:horizontal {
        background-color: rgba(0, 0, 0, 0.15);
        min-height: 30px;
        min-width: 30px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover,
    QScrollBar::handle:horizontal:hover {
        background-color: rgba(0, 0, 0, 0.3);
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical,
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        border: none;
        background-color: transparent;
        width: 0px;
        height: 0px;
    }
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical,
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {
        background-color: transparent;
    }
    QTabWidget::pane {
        border: none;
        background-color: transparent;
        border-top: 1px solid rgba(0, 0, 0, 0.06);
    }
    QTabBar::tab {
        background-color: transparent;
        color: #707070;
        padding: 8px 16px;
        margin-right: 4px;
        border-bottom: 2px solid transparent;
        font-weight: bold;
    }
    QTabBar::tab:hover {
        color: black;
        background-color: rgba(0, 0, 0, 0.04);
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected {
        color: black;
        border-bottom: 2px solid #0078D7;
    }
    QLineEdit {
        background-color: rgba(255, 255, 255, 0.75);
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 4px;
        padding: 6px 10px;
        color: black;
    }
    QLineEdit:focus {
        border: 1px solid rgba(0, 120, 215, 0.5);
        background-color: white;
    }
    QComboBox {
        background-color: rgba(255, 255, 255, 0.75);
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 4px;
        padding: 6px 10px;
        color: black;
    }
    QComboBox:hover {
        border: 1px solid rgba(0, 0, 0, 0.2);
        background-color: rgba(255, 255, 255, 1);
    }
    QComboBox::drop-down {
        border: none;
        width: 30px;
    }
    QComboBox QAbstractItemView {
        background-color: white;
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 4px;
        color: black;
        selection-background-color: rgba(0, 120, 215, 0.12);
        outline: none;
    }
    QCheckBox {
        color: black;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid rgba(0, 0, 0, 0.2);
        background-color: rgba(255, 255, 255, 0.75);
    }
    QCheckBox::indicator:hover {
        border: 1px solid rgba(0, 0, 0, 0.4);
    }
    QCheckBox::indicator:checked {
        background-color: #0078D7;
        border: 1px solid #0078D7;
    }
    QPushButton {
        background-color: rgba(255, 255, 255, 0.75);
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 4px;
        padding: 6px 12px;
        color: black;
    }
    QPushButton:hover {
        background-color: rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(0, 0, 0, 0.2);
    }
    QPushButton:pressed {
        background-color: rgba(0, 0, 0, 0.08);
    }
    QPushButton#ActionBtn {
        background-color: rgba(255, 255, 255, 0.75);
        border: 1px solid rgba(0, 0, 0, 0.15);
        color: black;
        font-weight: bold;
    }
    QPushButton#ActionBtn:hover {
        background-color: rgba(240, 240, 240, 0.75);
        border: 1px solid rgba(0, 0, 0, 0.25);
    }
    QPushButton#ActionBtn:disabled {
        background-color: rgba(255, 255, 255, 0.5);
        border: 1px solid rgba(0, 0, 0, 0.05);
        color: rgba(0, 0, 0, 0.3);
    }
    QPushButton#CloseButton {
        background-color: transparent;
        border: none;
        color: #606060;
        font-weight: bold;
        border-top-right-radius: 9px;
        border-bottom-left-radius: 9px;
        border-bottom-right-radius: 0px;
        border-top-left-radius: 0px;
        padding: 0px;
        outline: none;
    }
    QPushButton#CloseButton:hover {
        background-color: #E81123;
        color: white;
    }
    QPushButton:disabled {
        background-color: rgba(0, 0, 0, 0.02);
        border: 1px solid rgba(0, 0, 0, 0.05);
        color: rgba(0, 0, 0, 0.3);
    }
    QFrame#WidgetGalleryCard {
        background-color: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(0, 0, 0, 0.05);
        border-radius: 8px;
    }
    QFrame#WidgetGalleryCard:hover {
        background-color: rgba(255, 255, 255, 1);
        border: 1px solid rgba(0, 0, 0, 0.1);
    }
    QTextEdit {
        background-color: rgba(255, 255, 255, 0.75);
        color: #202020;
        font-family: Consolas, monospace;
        font-size: 13px;
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 4px;
        padding: 4px;
    }
"""
