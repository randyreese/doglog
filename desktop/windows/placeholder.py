from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class Placeholder(QWidget):
    def __init__(self, text: str):
        super().__init__()
        layout = QVBoxLayout(self)
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #999; font-size: 16px;")
        layout.addWidget(lbl)
