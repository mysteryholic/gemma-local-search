from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QLabel, QFrame, QVBoxLayout


def label(text, role="body"):
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setProperty("role", role)
    widget.setWordWrap(True)
    return widget


def card():
    widget = QFrame()
    widget.setObjectName("card")
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(14)
    return widget, layout


def apply_theme(app):
    app.setStyle("Fusion")
    font = app.font()
    font.setPointSize(11)
    app.setFont(font)
    palette = QPalette()
    for role, color in {
        QPalette.ColorRole.Window: "#f5f5f7", QPalette.ColorRole.WindowText: "#1d1d1f",
        QPalette.ColorRole.Base: "#ffffff", QPalette.ColorRole.Text: "#1d1d1f",
        QPalette.ColorRole.Button: "#ffffff", QPalette.ColorRole.ButtonText: "#1d1d1f",
        QPalette.ColorRole.Highlight: "#dcecff", QPalette.ColorRole.HighlightedText: "#005bc4",
        QPalette.ColorRole.PlaceholderText: "#81848b", QPalette.ColorRole.ToolTipBase: "#ffffff",
        QPalette.ColorRole.ToolTipText: "#1d1d1f",
    }.items():
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(STYLE)


STYLE = """
QMainWindow, QWidget#shell { background: #f5f5f7; }
QWidget { color: #1d1d1f; }
QLabel { background: transparent; }
QLabel[role="title"] { font-size: 30px; font-weight: 700; letter-spacing: -1px; }
QLabel[role="subtitle"] { color: #6e6e73; font-size: 13px; }
QLabel[role="eyebrow"] { color: #86868b; font-size: 10px; font-weight: 600; letter-spacing: 1.8px; }
QLabel[role="section"] { font-size: 15px; font-weight: 600; }
QLabel[role="muted"] { color: #737780; font-size: 12px; }
QLabel[role="badge"] { background: #edf7f1; color: #297746; border-radius: 10px; padding: 5px 10px; font-size: 11px; }
QLabel[role="brand"] { font-size: 23px; font-weight: 700; letter-spacing: -0.7px; }
QLabel[role="mark"] { color: white; background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #65adff,stop:1 #0065df); border-radius: 13px; font-size: 25px; font-weight: 600; }
QLabel[role="empty-mark"] { background: #edf3fc; color: #0071e3; border-radius: 20px; font-size: 30px; }
QLabel[role="score"] { color: #0071e3; font-size: 25px; font-weight: 600; }
QWidget#sidebar { background: #ededf0; border-right: 1px solid #e0e0e5; }
QFrame#card { background: white; border: 1px solid #e6e7eb; border-radius: 16px; }
QPushButton { background: #ffffff; border: 1px solid #dedfe4; border-radius: 9px; padding: 9px 16px; font-weight: 500; min-height: 18px; }
QPushButton:hover { background: #f0f3f7; border-color: #c7ccd4; }
QPushButton:pressed { background: #e8ecf2; }
QPushButton:focus { border: 2px solid #5eabff; }
QPushButton[role="primary"] { background: #0071e3; color: #ffffff; border: 1px solid #0071e3; }
QPushButton[role="primary"]:hover { background: #0077ed; }
QPushButton[role="primary"]:pressed { background: #005fc2; }
QPushButton[role="quiet"] { color: #6e6e73; background: transparent; border-color: transparent; }
QPushButton[role="quiet"]:hover { background: #eceef2; }
QPushButton[role="nav"] { text-align: left; background: transparent; border: 1px solid transparent; padding: 12px 15px; border-radius: 9px; font-size: 13px; }
QPushButton[role="nav"]:checked { background: #dce8f8; color: #0066cc; font-weight: 600; }
QPushButton[role="nav"]:hover { background: #e1e5ec; }
QPushButton:disabled { color: #a0a4ac; background: #eceef1; border-color: #e5e7eb; }
QLineEdit, QTextEdit { background: #ffffff; border: 1px solid #e0e3e9; border-radius: 11px; padding: 12px; selection-background-color: #dcecff; selection-color: #005bc4; }
QLineEdit:focus, QTextEdit:focus { border: 1px solid #5ca9f8; }
QLineEdit#search { padding: 15px 18px; font-size: 14px; border-radius: 13px; }
QTextEdit#reading { border: none; padding: 6px; background: transparent; font-size: 14px; }
QTextEdit#conversation { border: none; padding: 16px; font-size: 14px; }
QListWidget { background: transparent; border: none; outline: none; }
QListWidget::item { padding: 12px 10px; margin: 3px 0; border-radius: 9px; border: 1px solid transparent; }
QListWidget::item:selected { background: #eaf3ff; color: #0066cc; border-color: #dcecff; }
QListWidget::item:hover { background: #f2f5f9; }
QListWidget#results::item { padding: 14px; border: 1px solid #edf0f4; margin-bottom: 8px; }
QListWidget#results::item:selected { border-color: #abd0fa; background: #edf5ff; }
QSplitter::handle { background: transparent; width: 12px; height: 12px; }
QScrollBar:vertical { border: none; background: transparent; width: 8px; margin: 4px 0; }
QScrollBar::handle:vertical { background: #c8ccd3; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QCheckBox { spacing: 9px; color: #515761; }
QCheckBox::indicator { width: 18px; height: 18px; }
QProgressBar { background: #e5edf7; border: none; border-radius: 2px; max-height: 4px; }
QProgressBar::chunk { background: #0071e3; border-radius: 2px; }
QToolTip { border: 1px solid #dce0e6; padding: 6px; }
"""
