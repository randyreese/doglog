from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QDateEdit, QCheckBox,
)
from PySide6.QtCore import Qt, QDate, QUrl
from PySide6.QtGui import QDesktopServices
from datetime import date as _date
from typing import Optional
import api


def _age_str(milestone_date: _date, birthdate: _date) -> str:
    delta = milestone_date - birthdate
    weeks = delta.days // 7
    if weeks <= 16:
        return f"{weeks} wks"
    months = round(delta.days / 30.44)
    if months < 12:
        return f"{months} mo"
    years = months // 12
    rem = months % 12
    yr = "yr" if years == 1 else "yrs"
    return f"{years} {yr}" if rem == 0 else f"{years} {yr} {rem} mo"


class DiaryEntryDialog(QDialog):
    def __init__(self, dogs: list, event_types: list, record: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Diary Entry" if record else "Add Diary Entry")
        self.setFixedWidth(440)
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._date.setDisplayFormat("yyyy-MM-dd")
        self._date.setDate(QDate.currentDate())

        self._dog_combo = QComboBox()
        self._dog_combo.addItem("All", userData=None)
        for dog in dogs:
            self._dog_combo.addItem(dog["name"], userData=dog["id"])

        self._type_combo = QComboBox()
        for et in event_types:
            self._type_combo.addItem(et["label"], userData=et["value"])

        self._notes1 = QLineEdit()
        self._notes1.setMaxLength(60)
        self._notes1.setPlaceholderText("60 chars")
        self._notes2 = QLineEdit()
        self._notes2.setMaxLength(200)
        self._notes2.setPlaceholderText("URL or text, 200 chars")
        self._weight = QLineEdit()
        self._weight.setPlaceholderText("e.g. 42.5")

        layout.addRow("Date *", self._date)
        layout.addRow("Dog *", self._dog_combo)
        layout.addRow("Type *", self._type_combo)
        layout.addRow("Notes 1", self._notes1)
        layout.addRow("Notes 2 / URL", self._notes2)
        layout.addRow("Weight (lbs)", self._weight)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if record:
            d = record.get("date", "")
            if d:
                self._date.setDate(QDate.fromString(str(d), "yyyy-MM-dd"))
            dog_id = record.get("dog_id")
            for i in range(self._dog_combo.count()):
                if self._dog_combo.itemData(i) == dog_id:
                    self._dog_combo.setCurrentIndex(i)
                    break
            ev = record.get("event_type", "")
            for i in range(self._type_combo.count()):
                if self._type_combo.itemData(i) == ev:
                    self._type_combo.setCurrentIndex(i)
                    break
            self._notes1.setText(record.get("notes1") or "")
            self._notes2.setText(record.get("notes2") or "")
            w = record.get("weight_lbs")
            if w is not None:
                self._weight.setText(str(w))

    def _validate(self):
        w = self._weight.text().strip()
        if w:
            try:
                float(w)
            except ValueError:
                QMessageBox.warning(self, "Validation", "Weight must be a number.")
                return
        self.accept()

    def get_data(self) -> dict:
        w = self._weight.text().strip()
        return {
            "date": self._date.date().toString("yyyy-MM-dd"),
            "dog_id": self._dog_combo.currentData(),
            "event_type": self._type_combo.currentData(),
            "notes1": self._notes1.text().strip() or None,
            "notes2": self._notes2.text().strip() or None,
            "weight_lbs": float(w) if w else None,
        }


class DiaryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._dogs: list = []
        self._event_types: list = []
        self._all_records: list = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        self._add_btn = QPushButton("+ Add")
        self._edit_btn = QPushButton("Edit")
        self._del_btn = QPushButton("Delete")
        self._refresh_btn = QPushButton("Refresh")
        for btn in (self._add_btn, self._edit_btn, self._del_btn, self._refresh_btn):
            toolbar.addWidget(btn)
        self._add_btn.clicked.connect(self._add)
        self._edit_btn.clicked.connect(self._edit)
        self._del_btn.clicked.connect(self._delete)
        self._refresh_btn.clicked.connect(self._load)

        toolbar.addStretch()

        toolbar.addWidget(QLabel("Type:"))
        self._type_filter = QComboBox()
        self._type_filter.setMinimumWidth(130)
        self._type_filter.addItem("(All Types)", userData=None)
        self._type_filter.currentIndexChanged.connect(self._apply_filter)
        toolbar.addWidget(self._type_filter)

        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel("Show:"))

        self._dog_checks: dict[int, QCheckBox] = {}
        self._all_check = QCheckBox("All")
        self._all_check.setChecked(True)
        self._all_check.stateChanged.connect(self._apply_filter)
        self._filter_toolbar = toolbar
        toolbar.addWidget(self._all_check)
        layout.addLayout(toolbar)

        search_bar = QHBoxLayout()
        search_bar.addWidget(QLabel("Search notes:"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("filter by notes…")
        self._search.setMaximumWidth(480)
        self._search.textChanged.connect(self._apply_filter)
        search_bar.addWidget(self._search)
        search_bar.addStretch()
        layout.addLayout(search_bar)

        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ["Date", "Dog", "Age", "Type", "Notes 1", "Notes 2", "Weight"]
        )
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.doubleClicked.connect(self._edit)
        layout.addWidget(self._table)

        self._load()

    def _build_filters(self):
        for cb in self._dog_checks.values():
            self._filter_toolbar.removeWidget(cb)
            cb.deleteLater()
        self._dog_checks.clear()

        all_idx = self._filter_toolbar.indexOf(self._all_check)
        for dog in self._dogs:
            cb = QCheckBox(dog["name"])
            cb.setChecked(True)
            cb.stateChanged.connect(self._apply_filter)
            self._filter_toolbar.insertWidget(all_idx, cb)
            self._dog_checks[dog["id"]] = cb
            all_idx += 1

        self._type_filter.blockSignals(True)
        current_type = self._type_filter.currentData()
        self._type_filter.clear()
        self._type_filter.addItem("(All Types)", userData=None)
        restore_idx = 0
        for i, et in enumerate(self._event_types):
            self._type_filter.addItem(et["label"], userData=et["value"])
            if et["value"] == current_type:
                restore_idx = i + 1
        self._type_filter.setCurrentIndex(restore_idx)
        self._type_filter.blockSignals(False)

    def _load(self):
        try:
            self._dogs = api.get("/dogs/")
            self._event_types = api.get("/milestone-event-types")
            self._all_records = api.get("/milestones/")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load:\n{e}")
            return

        self._build_filters()
        self._apply_filter()

    def _apply_filter(self, *_):
        checked_ids = {dog_id for dog_id, cb in self._dog_checks.items() if cb.isChecked()}
        include_all = self._all_check.isChecked()
        selected_type = self._type_filter.currentData()
        query = self._search.text().strip().lower()

        filtered = [
            r for r in self._all_records
            if (
                (r["dog_id"] is None and include_all)
                or (r["dog_id"] is not None and r["dog_id"] in checked_ids)
            ) and (
                selected_type is None or r.get("event_type") == selected_type
            ) and (
                not query
                or query in (r.get("notes1") or "").lower()
                or query in (r.get("notes2") or "").lower()
            )
        ]
        self._populate(filtered)

    def _populate(self, records: list):
        dog_map = {d["id"]: d for d in self._dogs}
        type_map = {et["value"]: et["label"] for et in self._event_types}
        self._table.setSortingEnabled(False)
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(0)
        for i, r in enumerate(records):
            self._table.insertRow(i)

            date_item = QTableWidgetItem(str(r["date"]))
            date_item.setData(Qt.ItemDataRole.UserRole, r)
            self._table.setItem(i, 0, date_item)

            dog_id = r.get("dog_id")
            dog_name = dog_map[dog_id]["name"] if dog_id and dog_id in dog_map else "All"
            self._table.setItem(i, 1, QTableWidgetItem(dog_name))

            age = ""
            if dog_id and dog_id in dog_map:
                bd = dog_map[dog_id].get("birthdate")
                if bd:
                    try:
                        bd_date = _date.fromisoformat(str(bd)[:10])
                        m_date = _date.fromisoformat(str(r["date"])[:10])
                        age = _age_str(m_date, bd_date)
                    except Exception:
                        pass
            self._table.setItem(i, 2, QTableWidgetItem(age))

            event_key = r.get("event_type") or ""
            self._table.setItem(i, 3, QTableWidgetItem(type_map.get(event_key, event_key)))
            self._table.setItem(i, 4, QTableWidgetItem(r.get("notes1") or ""))

            notes2 = r.get("notes2") or ""
            if notes2.startswith("http://") or notes2.startswith("https://"):
                lbl = QLabel(f'<a href="{notes2}">View post →</a>')
                lbl.setOpenExternalLinks(True)
                lbl.setToolTip(notes2)
                lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                lbl.setContentsMargins(4, 0, 4, 0)
                lbl.setStyleSheet("background: transparent;")
                self._table.setCellWidget(i, 5, lbl)
            else:
                self._table.setItem(i, 5, QTableWidgetItem(notes2))

            w = r.get("weight_lbs")
            self._table.setItem(i, 6, QTableWidgetItem(str(w) if w is not None else ""))

        self._table.setUpdatesEnabled(True)
        self._table.setSortingEnabled(True)

    def _selected(self) -> Optional[dict]:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _add(self):
        dlg = DiaryEntryDialog(self._dogs, self._event_types, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.post("/milestones/", json=dlg.get_data())
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit(self):
        record = self._selected()
        if not record:
            return
        dlg = DiaryEntryDialog(self._dogs, self._event_types, record=record, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.patch(f"/milestones/{record['id']}", json=dlg.get_data())
                self._load()
            except Exception as e:
                detail = getattr(getattr(e, "response", None), "text", "")
                msg = f"{e}\n\n{detail}" if detail else str(e)
                QMessageBox.critical(self, "Error", msg)

    def _delete(self):
        record = self._selected()
        if not record:
            return
        label = f"{record.get('date')}  {record.get('event_type', '')}  {record.get('notes1', '') or ''}"
        if QMessageBox.question(self, "Confirm Delete", f"Delete this diary entry?\n\n{label}") == QMessageBox.StandardButton.Yes:
            try:
                api.delete(f"/milestones/{record['id']}")
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
