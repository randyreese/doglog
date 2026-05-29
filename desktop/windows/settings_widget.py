import subprocess
import tempfile
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QInputDialog, QFormLayout, QFrame,
)
from PySide6.QtCore import Qt
import api


# ── Reusable ini-list tab ─────────────────────────────────────────────────────

class _IniListTab(QWidget):
    """Tab for managing an ini-file-backed list: + Add / Delete / Move Up / Down / Refresh."""

    def __init__(self, get_ep: str, add_ep: str, delete_ep: str, reorder_ep: str, edit_ep: str = None):
        super().__init__()
        self._get_ep = get_ep
        self._add_ep = add_ep
        self._delete_ep = delete_ep
        self._reorder_ep = reorder_ep
        self._edit_ep = edit_ep or add_ep  # PATCH to {edit_ep}/{key}
        self._items: list = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        self._add_btn = QPushButton("+ Add")
        self._edit_btn = QPushButton("Edit")
        self._del_btn = QPushButton("Delete")
        self._up_btn = QPushButton("▲ Up")
        self._dn_btn = QPushButton("▼ Down")
        self._ref_btn = QPushButton("Refresh")
        for btn in (self._add_btn, self._edit_btn, self._del_btn, self._up_btn, self._dn_btn, self._ref_btn):
            toolbar.addWidget(btn)
        self._add_btn.clicked.connect(self._add)
        self._edit_btn.clicked.connect(self._edit)
        self._del_btn.clicked.connect(self._delete)
        self._up_btn.clicked.connect(self._move_up)
        self._dn_btn.clicked.connect(self._move_down)
        self._ref_btn.clicked.connect(self._load)
        layout.addLayout(toolbar)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Key", "Label"])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(False)
        layout.addWidget(self._table)

        self._load()

    def _load(self):
        try:
            self._items = api.get(self._get_ep)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self._items = []
        self._populate()

    def _populate(self):
        row = self._table.currentRow()
        self._table.setRowCount(0)
        for i, item in enumerate(self._items):
            self._table.insertRow(i)
            key_item = QTableWidgetItem(item.get("value", ""))
            key_item.setData(Qt.ItemDataRole.UserRole, item)
            self._table.setItem(i, 0, key_item)
            self._table.setItem(i, 1, QTableWidgetItem(item.get("label", "")))
        if 0 <= row < self._table.rowCount():
            self._table.setCurrentCell(row, 0)

    def _current_row(self) -> int:
        return self._table.currentRow()

    def _add(self):
        label, ok = QInputDialog.getText(self, "Add Item", "Label:")
        if ok and label.strip():
            try:
                api.post(self._add_ep, json={"label": label.strip()})
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit(self):
        row = self._current_row()
        if row < 0:
            return
        item = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        label, ok = QInputDialog.getText(self, "Edit Label", "Label:", text=item["label"])
        if ok and label.strip() and label.strip() != item["label"]:
            try:
                api.patch(f"{self._edit_ep}/{item['value']}", json={"label": label.strip()})
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete(self):
        row = self._current_row()
        if row < 0:
            return
        item = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        msg = (
            f"Delete '{item['label']}'?\n\n"
            f"Warning: existing records that reference this entry will retain "
            f"the key '{item['value']}' but lose their label."
        )
        if QMessageBox.question(self, "Confirm Delete", msg) == QMessageBox.StandardButton.Yes:
            try:
                api.delete(f"{self._delete_ep}/{item['value']}")
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _move_up(self):
        row = self._current_row()
        if row <= 0:
            return
        self._items.insert(row - 1, self._items.pop(row))
        self._save_order()
        self._populate()
        self._table.setCurrentCell(row - 1, 0)

    def _move_down(self):
        row = self._current_row()
        if row < 0 or row >= len(self._items) - 1:
            return
        self._items.insert(row + 1, self._items.pop(row))
        self._save_order()
        self._populate()
        self._table.setCurrentCell(row + 1, 0)

    def _save_order(self):
        try:
            api.put(self._reorder_ep, json=self._items)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ── Milestone Dogs tab (read-only, reflects dogs table) ───────────────────────

class _MilestoneDogsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        ref_btn = QPushButton("Refresh")
        ref_btn.clicked.connect(self._load)
        toolbar.addWidget(ref_btn)
        layout.addLayout(toolbar)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Name", "Track Pee"])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)

        note = QLabel("\"All\" is always available as a milestone dog option.\nDog add/edit/archive coming in Sprint 7.")
        note.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(note)

        self._load()

    def _load(self):
        try:
            dogs = api.get("/dogs/")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            dogs = []
        self._table.setRowCount(0)
        for i, dog in enumerate(dogs):
            self._table.insertRow(i)
            self._table.setItem(i, 0, QTableWidgetItem(dog.get("name", "")))
            track = "Yes" if dog.get("track_pee") else "No"
            item = QTableWidgetItem(track)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(i, 1, item)


# ── App tab ───────────────────────────────────────────────────────────────────

class _AppTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        layout.addWidget(QLabel("<b>Backend</b>"))
        layout.addSpacing(4)

        try:
            url_label = QLabel(f"Connected to: {api.BASE_URL}")
        except Exception:
            url_label = QLabel("Connected to: (unknown)")
        url_label.setStyleSheet("color: #555;")
        layout.addWidget(url_label)

        self._sep()
        layout.addWidget(self._sep())
        layout.addWidget(QLabel("<b>Dev Tools</b>"))
        layout.addSpacing(4)

        pull_row = QHBoxLayout()
        pull_row.addWidget(QLabel("Pull Prod DB"))
        pull_row.addSpacing(12)
        pull_btn = QPushButton("Pull →")
        pull_btn.clicked.connect(self._pull_prod_db)
        pull_row.addWidget(pull_btn)
        pull_row.addStretch()
        layout.addLayout(pull_row)

        layout.addWidget(self._sep())
        layout.addStretch()

    def _sep(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def _pull_prod_db(self):
        dest = Path(__file__).parent.parent.parent / "backend" / "doglog.db"

        if dest.exists():
            reply = QMessageBox.question(
                self, "Overwrite?",
                "backend/doglog.db already exists.\nOverwrite with the current production DB?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        with tempfile.TemporaryFile() as err_f:
            step1 = subprocess.run(
                ["ssh", "mini@mint.local",
                 "docker cp doglog-doglog-1:/data/doglog.db /tmp/doglog.db.pull"],
                stdout=subprocess.DEVNULL, stderr=err_f,
            )
            if step1.returncode != 0:
                err_f.seek(0)
                err_text = err_f.read().decode(errors="replace")
                QMessageBox.critical(self, "Pull failed", f"ssh/docker cp failed:\n{err_text or '(no output)'}")
                return

        with tempfile.TemporaryFile() as err_f:
            step2 = subprocess.run(
                ["scp", "mini@mint.local:/tmp/doglog.db.pull", str(dest)],
                stdout=subprocess.DEVNULL, stderr=err_f,
            )
            if step2.returncode != 0:
                err_f.seek(0)
                err_text = err_f.read().decode(errors="replace")
                QMessageBox.critical(self, "Pull failed", f"scp failed:\n{err_text or '(no output)'}")
                subprocess.run(["ssh", "mini@mint.local", "rm -f /tmp/doglog.db.pull"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return

        subprocess.run(["ssh", "mini@mint.local", "rm -f /tmp/doglog.db.pull"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        QMessageBox.information(self, "Success", f"Production DB pulled to:\n{dest.name}")


# ── Settings page (QTabWidget) ────────────────────────────────────────────────

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()

        tabs.addTab(_placeholder_tab("Dogs — coming in Sprint 7"), "Dogs")
        tabs.addTab(
            _IniListTab("/meal-slots", "/meal-slots", "/meal-slots", "/meal-slots"),
            "Meal Slots",
        )
        tabs.addTab(
            _IniListTab("/meal-ingredients", "/meal-ingredients", "/meal-ingredients", "/meal-ingredients"),
            "Meal Ingredients",
        )
        tabs.addTab(
            _IniListTab("/medication-names", "/medication-names", "/medication-names", "/medication-names"),
            "Medications",
        )
        tabs.addTab(
            _IniListTab("/health-types", "/health-types", "/health-types", "/health-types"),
            "Health Types",
        )
        tabs.addTab(
            _IniListTab(
                "/milestone-event-types",
                "/milestone-event-types",
                "/milestone-event-types",
                "/milestone-event-types",
            ),
            "Milestone Types",
        )
        tabs.addTab(_AppTab(), "App")

        layout.addWidget(tabs)


def _placeholder_tab(text: str) -> QWidget:
    w = QWidget()
    layout = QVBoxLayout(w)
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet("color: #999; font-size: 14px;")
    layout.addWidget(lbl)
    return w
