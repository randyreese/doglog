from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QDialog, QFormLayout, QComboBox, QDialogButtonBox,
    QDateEdit, QCheckBox, QScrollArea, QSizePolicy, QSplitter,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QBrush, QColor, QFont
from datetime import date as _date
import api


_HIST_COLOR = QColor('#aaaaaa')
_HIST_BG = QColor('#f5f5f5')


class _DosesTable(QWidget):
    """Inline doses table used in the Add/Edit dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Label", "Amount", "", "", ""])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        for col in (2, 3, 4):
            self._table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self._table.setColumnWidth(col, 28)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setFixedHeight(120)
        layout.addWidget(self._table)

        add_btn = QPushButton("+ Add Dose")
        add_btn.clicked.connect(self._add_dose)
        layout.addWidget(add_btn)

    def populate(self, doses: list):
        """doses: list of {label, amount}"""
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(0)
        for row, dose in enumerate(doses):
            self._insert_row(row, dose.get('label', ''), dose.get('amount', '') or '')
        self._table.setUpdatesEnabled(True)
        self._table.update()

    def _insert_row(self, row: int, label: str, amount: str):
        self._table.insertRow(row)
        lbl_item = QTableWidgetItem(label)
        lbl_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
        self._table.setItem(row, 0, lbl_item)
        amt_item = QTableWidgetItem(amount)
        amt_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
        self._table.setItem(row, 1, amt_item)
        self._set_row_buttons(row)

    def _set_row_buttons(self, row: int):
        up_btn = QPushButton("▲")
        up_btn.setFixedWidth(28)
        up_btn.clicked.connect(lambda _, r=row: self._move(r, -1))
        self._table.setCellWidget(row, 2, up_btn)

        dn_btn = QPushButton("▼")
        dn_btn.setFixedWidth(28)
        dn_btn.clicked.connect(lambda _, r=row: self._move(r, 1))
        self._table.setCellWidget(row, 3, dn_btn)

        x_btn = QPushButton("✕")
        x_btn.setFixedWidth(28)
        x_btn.clicked.connect(lambda _, r=row: self._remove(r))
        self._table.setCellWidget(row, 4, x_btn)

    def _read(self) -> list:
        items = []
        for row in range(self._table.rowCount()):
            l = self._table.item(row, 0)
            a = self._table.item(row, 1)
            items.append({
                'label': l.text().strip() if l else '',
                'amount': a.text().strip() if a else '',
            })
        return items

    def _move(self, row: int, direction: int):
        items = self._read()
        new_row = row + direction
        if 0 <= new_row < len(items):
            items[row], items[new_row] = items[new_row], items[row]
            self.populate(items)

    def _remove(self, row: int):
        items = self._read()
        items.pop(row)
        self.populate(items)

    def _add_dose(self):
        row = self._table.rowCount()
        self._insert_row(row, '', '')
        self._table.editItem(self._table.item(row, 0))

    def get_doses(self) -> list:
        return [
            {'label': it['label'], 'amount': it['amount'] or None, 'sort_order': i}
            for i, it in enumerate(self._read())
            if it['label']
        ]


class MedicationDialog(QDialog):
    def __init__(self, dogs: list, med_names: list,
                 medication: dict = None, parent=None):
        super().__init__(parent)
        self._editing = medication is not None
        self.setWindowTitle("Edit Medication" if self._editing else "Add Medication")
        self.setMinimumWidth(460)

        layout = QFormLayout(self)
        layout.setSpacing(10)

        self._dog_combo = QComboBox()
        for dog in dogs:
            self._dog_combo.addItem(dog['name'], userData=dog['id'])
        if self._editing:
            self._dog_combo.setEnabled(False)

        self._name_combo = QComboBox()
        for mn in med_names:
            self._name_combo.addItem(mn['label'], userData=mn['value'])
        if self._editing:
            self._name_combo.setEnabled(False)

        self._start_chk = QCheckBox()
        self._start_chk.setChecked(True)
        self._start_edit = QDateEdit()
        self._start_edit.setCalendarPopup(True)
        self._start_edit.setDisplayFormat("yyyy-MM-dd")
        self._start_edit.setDate(QDate.currentDate())
        self._start_chk.toggled.connect(self._start_edit.setEnabled)
        start_row = QHBoxLayout()
        start_row.addWidget(self._start_chk)
        start_row.addWidget(self._start_edit)
        start_row.addStretch()

        self._end_chk = QCheckBox()
        self._end_chk.setChecked(False)
        self._end_edit = QDateEdit()
        self._end_edit.setCalendarPopup(True)
        self._end_edit.setDisplayFormat("yyyy-MM-dd")
        self._end_edit.setDate(QDate.currentDate())
        self._end_edit.setEnabled(False)
        self._end_chk.toggled.connect(self._end_edit.setEnabled)
        end_row = QHBoxLayout()
        end_row.addWidget(self._end_chk)
        end_row.addWidget(self._end_edit)
        end_row.addStretch()

        self._doses_table = _DosesTable()

        layout.addRow("Dog *", self._dog_combo)
        layout.addRow("Medication *", self._name_combo)
        layout.addRow("Start", start_row)
        layout.addRow("End (optional)", end_row)
        layout.addRow("Doses", self._doses_table)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if medication:
            for i in range(self._dog_combo.count()):
                if self._dog_combo.itemData(i) == medication['dog_id']:
                    self._dog_combo.setCurrentIndex(i)
                    break
            for i in range(self._name_combo.count()):
                if self._name_combo.itemData(i) == medication.get('name'):
                    self._name_combo.setCurrentIndex(i)
                    break
                # also match by label
                if self._name_combo.itemText(i) == medication.get('name'):
                    self._name_combo.setCurrentIndex(i)
                    break
            start = medication.get('start_date')
            if start:
                self._start_chk.setChecked(True)
                self._start_edit.setDate(QDate.fromString(str(start), "yyyy-MM-dd"))
            end = medication.get('end_date')
            if end:
                self._end_chk.setChecked(True)
                self._end_edit.setDate(QDate.fromString(str(end), "yyyy-MM-dd"))
            self._doses_table.populate(medication.get('doses', []))

    def _validate(self):
        if not self._doses_table.get_doses():
            QMessageBox.warning(self, "Validation", "Add at least one dose.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            'dog_id': self._dog_combo.currentData(),
            'name': self._name_combo.currentText(),
            'start_date': (
                self._start_edit.date().toString("yyyy-MM-dd")
                if self._start_chk.isChecked() else None
            ),
            'end_date': (
                self._end_edit.date().toString("yyyy-MM-dd")
                if self._end_chk.isChecked() else None
            ),
            'doses': self._doses_table.get_doses(),
        }


class MedicationsConfigWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dogs: list = []
        self._med_names: list = []
        self._selected_med_id: int | None = None
        self._tables: list[QTableWidget] = []
        self._row_meta: list[dict] = []  # flat list across all sub-tables

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Toolbar
        toolbar = QHBoxLayout()
        self._add_btn = QPushButton("+ Add")
        self._edit_btn = QPushButton("Edit")
        self._del_btn = QPushButton("Delete")
        self._refresh_btn = QPushButton("Refresh")
        self._edit_btn.setEnabled(False)
        self._del_btn.setEnabled(False)
        for btn in (self._add_btn, self._edit_btn, self._del_btn, self._refresh_btn):
            toolbar.addWidget(btn)
        toolbar.addStretch()
        self._add_btn.clicked.connect(self._add)
        self._edit_btn.clicked.connect(self._edit)
        self._del_btn.clicked.connect(self._delete)
        self._refresh_btn.clicked.connect(self._load)
        layout.addLayout(toolbar)

        self._splitter = QSplitter(Qt.Orientation.Vertical)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setHandleWidth(6)
        layout.addWidget(self._splitter)

        self._load()

    # ── Data loading ───────────────────────────────────────────────────────────

    def _load(self):
        self._selected_med_id = None
        self._edit_btn.setEnabled(False)
        self._del_btn.setEnabled(False)
        try:
            self._dogs = [d for d in api.get('/dogs/') if d.get('active', True)]
            self._med_names = api.get('/medication-names')
        except Exception as exc:
            QMessageBox.warning(self, "Load error", str(exc))
            return
        self._rebuild_tables()

    def _rebuild_tables(self):
        while self._splitter.count():
            w = self._splitter.widget(0)
            w.setParent(None)
            w.deleteLater()
        self._tables.clear()
        self._row_meta.clear()

        today = _date.today()

        for dog in self._dogs:
            try:
                meds = api.get('/medications/', params={'dog_id': dog['id']})
            except Exception:
                meds = []

            active = [m for m in meds if not m['end_date'] or str(m['end_date']) >= str(today)]
            past = [m for m in meds if m['end_date'] and str(m['end_date']) < str(today)]

            pane = QWidget()
            pane_layout = QVBoxLayout(pane)
            pane_layout.setContentsMargins(0, 4, 0, 0)
            pane_layout.setSpacing(4)

            inner = QWidget()
            inner_layout = QVBoxLayout(inner)
            inner_layout.setContentsMargins(0, 0, 0, 0)
            inner_layout.setSpacing(8)
            inner.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

            for section_label, section_meds, is_history in [
                (f"{dog['name']} — Active", active, False),
                (f"{dog['name']} — Past", past, True),
            ]:
                if not section_meds and is_history:
                    continue

                lbl = QLabel(section_label)
                lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold if not is_history else QFont.Weight.Normal))
                if is_history:
                    lbl.setStyleSheet("color: #888;")
                inner_layout.addWidget(lbl)

                table = self._build_section_table(section_meds, is_history)
                self._tables.append(table)
                inner_layout.addWidget(table)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(inner)
            pane_layout.addWidget(scroll)

            self._splitter.addWidget(pane)

    def _build_section_table(self, meds: list, is_history: bool) -> QTableWidget:
        # Build flat rows: one row per dose; span med name + dates across doses
        rows: list[dict] = []
        for med in meds:
            doses = med.get('doses', [])
            if not doses:
                rows.append({
                    'med_id': med['id'], 'is_history': is_history,
                    'med_name': med['name'], 'dose_label': '',
                    'dose_amount': '', 'start': str(med['start_date'] or ''),
                    'end': str(med['end_date'] or ''), 'first_in_med': True,
                })
                continue
            for di, dose in enumerate(doses):
                rows.append({
                    'med_id': med['id'], 'is_history': is_history,
                    'med_name': med['name'] if di == 0 else '',
                    'dose_label': dose['label'],
                    'dose_amount': dose.get('amount', '') or '',
                    'start': str(med['start_date'] or '') if di == 0 else '',
                    'end': str(med['end_date'] or '') if di == 0 else '',
                    'first_in_med': (di == 0),
                })

        table = QTableWidget(len(rows), 5)
        table.setHorizontalHeaderLabels(["Medication", "Dose", "Amount", "Start", "End"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(3, 90)
        table.setColumnWidth(4, 90)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)

        italic_font = QFont()
        italic_font.setItalic(True)

        for row, rd in enumerate(rows):
            texts = [rd['med_name'], rd['dose_label'], rd['dose_amount'], rd['start'], rd['end']]
            for col, text in enumerate(texts):
                it = QTableWidgetItem(text)
                it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                it.setData(Qt.ItemDataRole.UserRole, rd['med_id'])
                if rd['is_history']:
                    it.setForeground(QBrush(_HIST_COLOR))
                    it.setFont(italic_font)
                    it.setBackground(QBrush(_HIST_BG))
                table.setItem(row, col, it)

        # Span medication name + start + end columns across doses
        i = 0
        while i < len(rows):
            mid = rows[i]['med_id']
            j = i + 1
            while j < len(rows) and rows[j]['med_id'] == mid and not rows[j]['first_in_med']:
                j += 1
            if j - i > 1:
                table.setSpan(i, 0, j - i, 1)  # medication name
                table.setSpan(i, 3, j - i, 1)  # start
                table.setSpan(i, 4, j - i, 1)  # end
            i = j

        # Store meta for selection tracking
        table_meta = [{'med_id': rd['med_id']} for rd in rows]

        table.itemSelectionChanged.connect(
            lambda t=table, meta=table_meta: self._on_selection(t, meta)
        )

        return table

    # ── Selection ──────────────────────────────────────────────────────────────

    def _on_selection(self, table: QTableWidget, meta: list):
        for tbl in self._tables:
            if tbl is not table and tbl.selectedItems():
                tbl.clearSelection()

        row = table.currentRow()
        if row < 0 or row >= len(meta):
            self._selected_med_id = None
        else:
            self._selected_med_id = meta[row]['med_id']

        has_sel = self._selected_med_id is not None
        self._edit_btn.setEnabled(has_sel)
        self._del_btn.setEnabled(has_sel)

    # ── CRUD actions ───────────────────────────────────────────────────────────

    def _add(self):
        if not self._dogs:
            QMessageBox.warning(self, "No dogs", "No active dogs found.")
            return
        if not self._med_names:
            QMessageBox.warning(self, "No medications", "Add medication names in Settings first.")
            return
        dlg = MedicationDialog(self._dogs, self._med_names, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        try:
            api.post('/medications/', json=data)
        except Exception as exc:
            QMessageBox.critical(self, "Save error", str(exc))
            return
        self._load()

    def _edit(self):
        if self._selected_med_id is None:
            return
        try:
            meds = api.get('/medications/')
        except Exception as exc:
            QMessageBox.critical(self, "Load error", str(exc))
            return
        med = next((m for m in meds if m['id'] == self._selected_med_id), None)
        if not med:
            QMessageBox.warning(self, "Not found", "Medication not found.")
            self._load()
            return
        dlg = MedicationDialog(self._dogs, self._med_names, medication=med, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        patch = {
            'start_date': data['start_date'],
            'end_date': data['end_date'],
            'doses': data['doses'],
        }
        try:
            api.patch(f'/medications/{self._selected_med_id}', json=patch)
        except Exception as exc:
            QMessageBox.critical(self, "Save error", str(exc))
            return
        self._load()

    def _delete(self):
        if self._selected_med_id is None:
            return
        reply = QMessageBox.question(
            self, "Delete",
            "Delete this medication and all its dose records?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            api.delete(f'/medications/{self._selected_med_id}')
        except Exception as exc:
            QMessageBox.critical(self, "Delete error", str(exc))
            return
        self._load()
