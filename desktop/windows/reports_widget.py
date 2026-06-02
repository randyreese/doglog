from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSpinBox, QLineEdit, QFileDialog, QScrollArea,
    QFrame, QSizePolicy, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import api


_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _section_header(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
    lbl.setStyleSheet("color: #333; border-bottom: 1px solid #ccc; padding-bottom: 4px;")
    return lbl


def _hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


class ReportsWidget(QWidget):
    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        inner = QWidget()
        inner.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        scroll.setWidget(inner)

        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Vet Report section ────────────────────────────────────────────────
        layout.addWidget(_section_header("Vet Report"))

        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)

        # Dog row
        dog_row = QHBoxLayout()
        dog_row.addWidget(QLabel("Dog:"), 0)
        self._dog_combo = QComboBox()
        self._dog_combo.setMinimumWidth(160)
        dog_row.addWidget(self._dog_combo, 0)
        dog_row.addStretch()
        form_layout.addLayout(dog_row)

        # Period row
        period_row = QHBoxLayout()
        period_row.addWidget(QLabel("Period:"), 0)
        self._month_combo = QComboBox()
        for m in _MONTHS:
            self._month_combo.addItem(m)
        period_row.addWidget(self._month_combo, 0)
        period_row.addSpacing(8)
        self._year_spin = QSpinBox()
        self._year_spin.setRange(2024, 2035)
        self._year_spin.setValue(2026)
        self._year_spin.setFixedWidth(90)
        period_row.addWidget(self._year_spin, 0)
        period_row.addStretch()
        form_layout.addLayout(period_row)

        # File row
        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("File:"), 0)
        self._file_path = QLineEdit()
        self._file_path.setPlaceholderText("Select .xlsx file…")
        self._file_path.setReadOnly(True)
        file_row.addWidget(self._file_path, 1)
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse)
        file_row.addWidget(browse_btn, 0)
        form_layout.addLayout(file_row)

        # Run button + status
        run_row = QHBoxLayout()
        run_row.addStretch()
        self._run_btn = QPushButton("Run Report")
        self._run_btn.setFixedWidth(110)
        self._run_btn.clicked.connect(self._run)
        run_row.addWidget(self._run_btn)
        form_layout.addLayout(run_row)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("color: #555; font-size: 12px;")
        form_layout.addWidget(self._status_lbl)

        layout.addLayout(form_layout)
        layout.addWidget(_hline())
        layout.addStretch()

        self._load_dogs()

    def _load_dogs(self):
        try:
            dogs = api.get("/dogs/", params={"active_only": True})
        except Exception:
            dogs = []
        self._dog_combo.clear()
        for dog in sorted(dogs, key=lambda d: d["name"]):
            self._dog_combo.addItem(dog["name"], dog["id"])

    def _browse(self):
        default_dir = str(Path(__file__).parent.parent.parent / "reports")
        path, _ = QFileDialog.getOpenFileName(
            self, "Select report file", default_dir, "Excel files (*.xlsx)"
        )
        if path:
            self._file_path.setText(path)

    def _run(self):
        dog_id = self._dog_combo.currentData()
        month = self._month_combo.currentIndex() + 1
        year = self._year_spin.value()
        output_file = self._file_path.text().strip()

        if not dog_id:
            QMessageBox.warning(self, "Missing input", "Please select a dog.")
            return
        if not output_file:
            QMessageBox.warning(self, "Missing input", "Please select an output file.")
            return

        self._status_lbl.setText("Running…")
        self._run_btn.setEnabled(False)
        self.repaint()

        try:
            from vet_report import generate
            generate(dog_id, month, year, output_file, base_url=api.BASE_URL)
            dog_name = self._dog_combo.currentText()
            month_name = _MONTHS[month - 1]
            self._status_lbl.setText(
                f"Done — {dog_name} {month_name} {year} written to {Path(output_file).name}"
            )
        except Exception as e:
            self._status_lbl.setText("")
            QMessageBox.critical(self, "Report failed", str(e))
        finally:
            self._run_btn.setEnabled(True)
