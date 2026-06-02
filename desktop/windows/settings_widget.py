import subprocess
import tempfile
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QInputDialog, QFormLayout, QFrame,
    QDialog, QDialogButtonBox, QLineEdit, QDateEdit, QCheckBox, QComboBox,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush
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


# ── Dogs tab ──────────────────────────────────────────────────────────────────

class _DogDialog(QDialog):
    def __init__(self, record: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Dog" if record else "Add Dog")
        self.setFixedWidth(400)
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self._name = QLineEdit()
        self._name.setMaxLength(60)

        self._bd_chk = QCheckBox()
        self._bd_edit = QDateEdit()
        self._bd_edit.setCalendarPopup(True)
        self._bd_edit.setDisplayFormat("yyyy-MM-dd")
        self._bd_edit.setDate(QDate.currentDate())
        self._bd_edit.setEnabled(False)
        self._bd_chk.toggled.connect(self._bd_edit.setEnabled)
        bd_row = QHBoxLayout()
        bd_row.setContentsMargins(0, 0, 0, 0)
        bd_row.addWidget(self._bd_chk)
        bd_row.addWidget(self._bd_edit)
        bd_row.addStretch()

        self._breed = QLineEdit()
        self._breed.setMaxLength(60)

        self._track_pee = QCheckBox("Track pee events")
        self._track_pee.setChecked(True)

        self._active_chk = QCheckBox("Active")
        self._active_chk.setChecked(True)

        layout.addRow("Name *", self._name)
        layout.addRow("Birthdate", bd_row)
        layout.addRow("Breed", self._breed)
        layout.addRow("", self._track_pee)
        if record:
            layout.addRow("", self._active_chk)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if record:
            self._name.setText(record.get("name", ""))
            bd = record.get("birthdate")
            if bd:
                self._bd_chk.setChecked(True)
                self._bd_edit.setDate(QDate.fromString(str(bd)[:10], "yyyy-MM-dd"))
            self._breed.setText(record.get("breed") or "")
            self._track_pee.setChecked(record.get("track_pee", True))
            self._active_chk.setChecked(record.get("active", True))

    def _validate(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "Validation", "Name is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self._name.text().strip(),
            "birthdate": self._bd_edit.date().toString("yyyy-MM-dd") if self._bd_chk.isChecked() else None,
            "breed": self._breed.text().strip() or None,
            "track_pee": self._track_pee.isChecked(),
            "active": self._active_chk.isChecked(),
        }


class _DogsTab(QWidget):
    def __init__(self):
        super().__init__()
        self._dogs: list = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        self._add_btn = QPushButton("+ Add")
        self._edit_btn = QPushButton("Edit")
        self._arch_btn = QPushButton("Archive")
        self._ref_btn = QPushButton("Refresh")
        for btn in (self._add_btn, self._edit_btn, self._arch_btn, self._ref_btn):
            toolbar.addWidget(btn)
        toolbar.addStretch()
        self._add_btn.clicked.connect(self._add)
        self._edit_btn.clicked.connect(self._edit)
        self._arch_btn.clicked.connect(self._toggle_archive)
        self._ref_btn.clicked.connect(self._load)
        layout.addLayout(toolbar)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Name", "Birthdate", "Breed", "Track Pee", "Status"])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.doubleClicked.connect(self._edit)
        self._table.currentItemChanged.connect(self._on_selection)
        layout.addWidget(self._table)

        self._load()

    def _load(self):
        try:
            self._dogs = api.get("/dogs/", params={"active_only": False})
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        self._populate()

    def _populate(self):
        grey = QBrush(QColor("#aaa"))
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(0)
        for i, dog in enumerate(self._dogs):
            self._table.insertRow(i)
            active = dog.get("active", True)

            def _item(text, center=False, dog=dog, active=active):
                it = QTableWidgetItem(str(text) if text is not None else "")
                it.setData(Qt.ItemDataRole.UserRole, dog)
                if center:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if not active:
                    it.setForeground(grey)
                return it

            self._table.setItem(i, 0, _item(dog.get("name", "")))
            self._table.setItem(i, 1, _item(dog.get("birthdate") or ""))
            self._table.setItem(i, 2, _item(dog.get("breed") or ""))
            self._table.setItem(i, 3, _item("Yes" if dog.get("track_pee") else "No", center=True))
            self._table.setItem(i, 4, _item("Archived" if not active else "", center=True))

        self._table.setUpdatesEnabled(True)

    def _on_selection(self, *_):
        dog = self._selected()
        if dog:
            self._arch_btn.setText("Restore" if not dog.get("active", True) else "Archive")

    def _selected(self) -> dict | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _add(self):
        dlg = _DogDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.post("/dogs/", json=dlg.get_data())
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit(self):
        dog = self._selected()
        if not dog:
            return
        dlg = _DogDialog(record=dog, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.patch(f"/dogs/{dog['id']}", json=dlg.get_data())
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _toggle_archive(self):
        dog = self._selected()
        if not dog:
            return
        active = dog.get("active", True)
        action = "Restore" if not active else "Archive"
        if QMessageBox.question(self, f"Confirm {action}", f"{action} {dog['name']}?") == QMessageBox.StandardButton.Yes:
            try:
                data = {
                    "name": dog["name"],
                    "birthdate": str(dog["birthdate"]) if dog.get("birthdate") else None,
                    "breed": dog.get("breed"),
                    "track_pee": dog.get("track_pee", True),
                    "active": not active,
                }
                api.patch(f"/dogs/{dog['id']}", json=data)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


# ── Health Types tab ─────────────────────────────────────────────────────────

_RCOL_OPTIONS = [("—", ""), ("Activity", "activity"), ("Event", "event")]


class _HealthTypeDialog(QDialog):
    def __init__(self, record: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Health Type" if record else "Add Health Type")
        self.setFixedWidth(340)
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self._label = QLineEdit()
        self._label.setMaxLength(60)

        self._rcol = QComboBox()
        for display, value in _RCOL_OPTIONS:
            self._rcol.addItem(display, value)

        layout.addRow("Label:", self._label)
        layout.addRow("Report column:", self._rcol)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if record:
            self._label.setText(record.get("label", ""))
            rc = record.get("report_column", "")
            idx = next((i for i, (_, v) in enumerate(_RCOL_OPTIONS) if v == rc), 0)
            self._rcol.setCurrentIndex(idx)

    def _validate(self):
        if not self._label.text().strip():
            QMessageBox.warning(self, "Validation", "Label is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "label": self._label.text().strip(),
            "report_column": self._rcol.currentData(),
        }


class _HealthTypesTab(QWidget):
    def __init__(self):
        super().__init__()
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
        for btn in (self._add_btn, self._edit_btn, self._del_btn,
                    self._up_btn, self._dn_btn, self._ref_btn):
            toolbar.addWidget(btn)
        self._add_btn.clicked.connect(self._add)
        self._edit_btn.clicked.connect(self._edit)
        self._del_btn.clicked.connect(self._delete)
        self._up_btn.clicked.connect(self._move_up)
        self._dn_btn.clicked.connect(self._move_down)
        self._ref_btn.clicked.connect(self._load)
        layout.addLayout(toolbar)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Key", "Label", "Report Column"])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.doubleClicked.connect(self._edit)
        layout.addWidget(self._table)

        self._load()

    def _load(self):
        try:
            self._items = api.get("/health-types")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self._items = []
        self._populate()

    def _populate(self):
        row = self._table.currentRow()
        self._table.setRowCount(0)
        rcol_display = {v: d for d, v in _RCOL_OPTIONS}
        for i, item in enumerate(self._items):
            self._table.insertRow(i)
            key_item = QTableWidgetItem(item.get("value", ""))
            key_item.setData(Qt.ItemDataRole.UserRole, item)
            self._table.setItem(i, 0, key_item)
            self._table.setItem(i, 1, QTableWidgetItem(item.get("label", "")))
            rc = item.get("report_column", "")
            self._table.setItem(i, 2, QTableWidgetItem(rcol_display.get(rc, "—")))
        if 0 <= row < self._table.rowCount():
            self._table.setCurrentCell(row, 0)

    def _current_item(self) -> dict | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        cell = self._table.item(row, 0)
        return cell.data(Qt.ItemDataRole.UserRole) if cell else None

    def _add(self):
        dlg = _HealthTypeDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                api.post("/health-types", json=data)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit(self):
        item = self._current_item()
        if not item:
            return
        dlg = _HealthTypeDialog(record=item, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                api.patch(f"/health-types/{item['value']}", json=data)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete(self):
        item = self._current_item()
        if not item:
            return
        msg = (
            f"Delete '{item['label']}'?\n\n"
            f"Warning: existing records that reference this entry will retain "
            f"the key '{item['value']}' but lose their label."
        )
        if QMessageBox.question(self, "Confirm Delete", msg) == QMessageBox.StandardButton.Yes:
            try:
                api.delete(f"/health-types/{item['value']}")
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _move_up(self):
        row = self._table.currentRow()
        if row <= 0:
            return
        self._items.insert(row - 1, self._items.pop(row))
        self._save_order()
        self._populate()
        self._table.setCurrentCell(row - 1, 0)

    def _move_down(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._items) - 1:
            return
        self._items.insert(row + 1, self._items.pop(row))
        self._save_order()
        self._populate()
        self._table.setCurrentCell(row + 1, 0)

    def _save_order(self):
        try:
            api.put("/health-types", json=self._items)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


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

        tabs.addTab(_DogsTab(), "Dogs")
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
        tabs.addTab(_HealthTypesTab(), "Health Types")
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
