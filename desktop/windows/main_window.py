from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from windows.diary_widget import DiaryWidget
from windows.meal_config_widget import MealConfigWidget
from windows.medications_config_widget import MedicationsConfigWidget
from windows.reports_widget import ReportsWidget
from windows.settings_widget import SettingsWidget
from windows.placeholder import Placeholder


_NAV_ITEMS = [
    "Diary",
    "Meal Config",
    "Medications Config",
    "Dry Food Forecast",
    "Reports",
    "Settings",
]

_NAV_BTN_STYLE = """
QPushButton {
    text-align: left;
    padding: 10px 16px;
    border: none;
    background: transparent;
    font-size: 14px;
}
QPushButton:hover { background: #e8e8e8; }
QPushButton:checked { background: #d0d8e8; font-weight: bold; }
"""


class MainWindow(QMainWindow):
    def __init__(self, dev_mode: bool = False):
        super().__init__()
        self.setWindowTitle("[DEV] Dog Log" if dev_mode else "Dog Log")
        self.resize(1100, 720)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet("background: #f0f0f0; border-right: 1px solid #ccc;")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        title_lbl = QLabel("Dog Log")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setContentsMargins(0, 16, 0, 16)
        sb_layout.addWidget(title_lbl)

        self._nav_buttons: list[QPushButton] = []
        self._stack = QStackedWidget()

        pages = [
            DiaryWidget(),
            MealConfigWidget(),
            MedicationsConfigWidget(),
            Placeholder("Dry Food Forecast — coming in Sprint 8"),
            ReportsWidget(),
            SettingsWidget(),
        ]

        for i, label in enumerate(_NAV_ITEMS):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(_NAV_BTN_STYLE)
            btn.clicked.connect(lambda checked, idx=i: self._nav(idx))
            sb_layout.addWidget(btn)
            self._nav_buttons.append(btn)
            self._stack.addWidget(pages[i])

        sb_layout.addStretch()
        layout.addWidget(sidebar)
        layout.addWidget(self._stack)

        self._nav(0)

    def _nav(self, idx: int):
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == idx)
        self._stack.setCurrentIndex(idx)
