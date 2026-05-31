from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QDialog, QFormLayout, QComboBox, QDialogButtonBox,
    QDateEdit, QCheckBox, QScrollArea, QSizePolicy, QInputDialog,
    QGroupBox, QMenu, QSplitter,
)
from PySide6.QtCore import Qt, QDate, QPoint
from PySide6.QtGui import QBrush, QColor, QFont
from datetime import date as _date
import api


_HIST_COLOR = QColor('#aaaaaa')
_HIST_BG = QColor('#f5f5f5')


class _ItemsTable(QWidget):
    """Inline ingredient table used in the Add/Edit dialog."""

    def __init__(self, ingredients: list, parent=None):
        super().__init__(parent)
        self._ingredients = ingredients  # [{value, label}]
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Food", "Amount", "", "", ""])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        for col in (2, 3, 4):
            self._table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self._table.setColumnWidth(col, 28)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setFixedHeight(140)
        layout.addWidget(self._table)

        add_btn = QPushButton("+ Add Ingredient")
        add_btn.clicked.connect(self._add_ingredient)
        layout.addWidget(add_btn)

    def populate(self, items: list):
        """items: list of {food_name, amount}"""
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(0)
        for row, item in enumerate(items):
            self._insert_row(row, item.get('food_name', ''), item.get('amount', '') or '')
        self._table.setUpdatesEnabled(True)
        self._table.update()

    def _insert_row(self, row: int, food: str, amount: str):
        self._table.insertRow(row)
        food_item = QTableWidgetItem(food)
        food_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
        self._table.setItem(row, 0, food_item)
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
            f = self._table.item(row, 0)
            a = self._table.item(row, 1)
            items.append({
                'food_name': f.text().strip() if f else '',
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

    def _add_ingredient(self):
        already = {item['food_name'] for item in self._read()}
        choices = [i['label'] for i in self._ingredients if i['label'] not in already]
        if not choices:
            choices_raw = [i['label'] for i in self._ingredients]
            if not choices_raw:
                QMessageBox.information(self, "No ingredients", "No ingredients configured in Settings.")
                return
            choices = choices_raw  # all added — still allow re-adding
        choice, ok = QInputDialog.getItem(self, "Add Ingredient", "Select:", choices, 0, False)
        if ok and choice:
            row = self._table.rowCount()
            self._insert_row(row, choice, '')
            self._table.editItem(self._table.item(row, 1))

    def get_items(self) -> list:
        """Returns list of {food_name, amount, sort_order}."""
        return [
            {'food_name': it['food_name'], 'amount': it['amount'] or None, 'sort_order': i}
            for i, it in enumerate(self._read())
            if it['food_name']
        ]


class MealConfigDialog(QDialog):
    def __init__(self, dogs: list, slots: list, ingredients: list,
                 config: dict = None, parent=None):
        super().__init__(parent)
        self._editing = config is not None
        self.setWindowTitle("Edit Meal Config" if self._editing else "Add Meal Config")
        self.setMinimumWidth(480)

        layout = QFormLayout(self)
        layout.setSpacing(10)

        self._dog_combo = QComboBox()
        for dog in dogs:
            self._dog_combo.addItem(dog['name'], userData=dog['id'])
        if self._editing:
            self._dog_combo.setEnabled(False)

        self._slot_combo = QComboBox()
        for slot in slots:
            self._slot_combo.addItem(slot['label'], userData=slot['value'])
        if self._editing:
            self._slot_combo.setEnabled(False)

        self._date_chk = QCheckBox()
        self._date_chk.setChecked(True)
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        self._date_edit.setDate(QDate.currentDate())
        self._date_chk.toggled.connect(self._date_edit.setEnabled)
        date_row = QHBoxLayout()
        date_row.addWidget(self._date_chk)
        date_row.addWidget(self._date_edit)
        date_row.addStretch()

        self._items_table = _ItemsTable(ingredients)

        layout.addRow("Dog *", self._dog_combo)
        layout.addRow("Slot *", self._slot_combo)
        layout.addRow("Eff. Date", date_row)
        layout.addRow("Ingredients", self._items_table)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if config:
            for i in range(self._dog_combo.count()):
                if self._dog_combo.itemData(i) == config['dog_id']:
                    self._dog_combo.setCurrentIndex(i)
                    break
            for i in range(self._slot_combo.count()):
                if self._slot_combo.itemData(i) == config['meal_slot']:
                    self._slot_combo.setCurrentIndex(i)
                    break
            eff = config.get('effective_date')
            if eff:
                self._date_chk.setChecked(True)
                self._date_edit.setDate(QDate.fromString(str(eff), "yyyy-MM-dd"))
            self._items_table.populate(config.get('items', []))

    def _validate(self):
        if not self._items_table.get_items():
            QMessageBox.warning(self, "Validation", "Add at least one ingredient.")
            return
        self.accept()

    def get_data(self) -> dict:
        eff = (
            self._date_edit.date().toString("yyyy-MM-dd")
            if self._date_chk.isChecked() else None
        )
        return {
            'dog_id': self._dog_combo.currentData(),
            'meal_slot': self._slot_combo.currentData(),
            'effective_date': eff,
            'items': self._items_table.get_items(),
        }


class MealConfigWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dogs: list = []
        self._slots: list = []
        self._ingredients: list = []
        self._selected_config_id: int | None = None
        self._selected_dog_id: int | None = None
        self._tables: dict[int, QTableWidget] = {}  # dog_id -> table
        self._row_meta: dict[int, list] = {}         # dog_id -> [{config_id, slot_key}]
        self._clipboard: list | None = None          # copied items [{food_name, amount}]

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
        layout.addWidget(self._splitter)

        self._load()

    # ── Data loading ───────────────────────────────────────────────────────────

    def _load(self):
        self._selected_config_id = None
        self._selected_dog_id = None
        self._edit_btn.setEnabled(False)
        self._del_btn.setEnabled(False)
        try:
            self._dogs = [d for d in api.get('/dogs/') if d.get('active', True)]
            self._slots = api.get('/meal-slots')
            self._ingredients = api.get('/meal-ingredients')
        except Exception as exc:
            QMessageBox.warning(self, "Load error", str(exc))
            return
        self._rebuild_tables()

    def _rebuild_tables(self):
        # Clear existing splitter panes
        while self._splitter.count():
            w = self._splitter.widget(0)
            w.setParent(None)
            w.deleteLater()
        self._tables.clear()
        self._row_meta.clear()

        for dog in self._dogs:
            try:
                configs = api.get('/meal-configs/', params={'dog_id': dog['id']})
            except Exception:
                configs = []

            pane = QWidget()
            pane_layout = QVBoxLayout(pane)
            pane_layout.setContentsMargins(0, 4, 0, 0)
            pane_layout.setSpacing(4)

            label = QLabel(dog['name'])
            label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            pane_layout.addWidget(label)

            table = self._build_table(dog['id'], configs)
            self._tables[dog['id']] = table

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(table)
            pane_layout.addWidget(scroll)

            self._splitter.addWidget(pane)

    def _build_table(self, dog_id: int, configs: list) -> QTableWidget:
        # configs: [{id, dog_id, meal_slot, effective_date, items:[{id,food_name,amount,sort_order}]}]
        # Group by slot, newest first (backend already orders effective_date desc per slot)
        configs_by_slot: dict[str, list] = {}
        for cfg in configs:
            slot = cfg['meal_slot']
            configs_by_slot.setdefault(slot, []).append(cfg)

        rows: list[dict] = []
        for slot in self._slots:
            slot_key = slot['value']
            slot_label = slot['label']
            slot_configs = configs_by_slot.get(slot_key, [])

            if not slot_configs:
                rows.append({
                    'slot_label': slot_label, 'slot_key': slot_key,
                    'config_id': None, 'is_history': False,
                    'food': '—', 'amount': '', 'eff_date': '',
                    'first_in_slot': True, 'first_in_config': True,
                })
                continue

            for ci, cfg in enumerate(slot_configs):
                is_history = ci > 0
                items = cfg.get('items', [])
                if not items:
                    rows.append({
                        'slot_label': slot_label, 'slot_key': slot_key,
                        'config_id': cfg['id'], 'is_history': is_history,
                        'food': '(empty)', 'amount': '', 'eff_date': cfg['effective_date'],
                        'first_in_slot': (ci == 0), 'first_in_config': True,
                    })
                    continue
                for ii, item in enumerate(items):
                    rows.append({
                        'slot_label': slot_label if (ci == 0 and ii == 0) else '',
                        'slot_key': slot_key,
                        'config_id': cfg['id'], 'is_history': is_history,
                        'food': item['food_name'],
                        'amount': item.get('amount', '') or '',
                        'eff_date': cfg['effective_date'] if ii == 0 else '',
                        'first_in_slot': (ci == 0 and ii == 0), 'first_in_config': (ii == 0),
                    })

        table = QTableWidget(len(rows), 4)
        table.setHorizontalHeaderLabels(["Slot", "Food", "Amount", "Eff. Date"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(False)

        italic_font = QFont()
        italic_font.setItalic(True)

        row_meta = []
        for row, rd in enumerate(rows):
            for col, text in enumerate([rd['slot_label'], rd['food'], rd['amount'], str(rd['eff_date'])]):
                it = QTableWidgetItem(text)
                it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                it.setData(Qt.ItemDataRole.UserRole, rd['config_id'])
                if rd['is_history']:
                    it.setForeground(QBrush(_HIST_COLOR))
                    it.setFont(italic_font)
                    it.setBackground(QBrush(_HIST_BG))
                table.setItem(row, col, it)
            row_meta.append({'config_id': rd['config_id'], 'slot_key': rd['slot_key']})

        self._row_meta[dog_id] = row_meta

        # Span slot column across all rows in the same slot group
        i = 0
        while i < len(rows):
            key = rows[i]['slot_key']
            j = i + 1
            while j < len(rows) and rows[j]['slot_key'] == key:
                j += 1
            if j - i > 1:
                table.setSpan(i, 0, j - i, 1)
            i = j

        table.itemSelectionChanged.connect(
            lambda t=table, did=dog_id: self._on_selection(t, did)
        )
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(
            lambda pos, t=table, did=dog_id: self._context_menu(pos, t, did)
        )

        return table

    # ── Selection ──────────────────────────────────────────────────────────────

    def _on_selection(self, table: QTableWidget, dog_id: int):
        # Deselect all other tables
        for did, tbl in self._tables.items():
            if did != dog_id and tbl.selectedItems():
                tbl.clearSelection()

        row = table.currentRow()
        meta = self._row_meta.get(dog_id, [])
        if row < 0 or row >= len(meta):
            self._selected_config_id = None
            self._selected_dog_id = None
        else:
            self._selected_config_id = meta[row]['config_id']
            self._selected_dog_id = dog_id

        has_sel = self._selected_config_id is not None
        self._edit_btn.setEnabled(has_sel)
        self._del_btn.setEnabled(has_sel)

    # ── Context menu (copy / paste) ────────────────────────────────────────────

    def _context_menu(self, pos: QPoint, table: QTableWidget, dog_id: int):
        row = table.rowAt(pos.y())
        if row < 0:
            return
        meta = self._row_meta.get(dog_id, [])
        if row >= len(meta):
            return
        rd = meta[row]
        config_id = rd['config_id']
        slot_key = rd['slot_key']

        menu = QMenu(self)
        copy_action = menu.addAction("Copy slot config")
        copy_action.setEnabled(config_id is not None)
        paste_action = menu.addAction(
            f"Paste as new config{' ✓' if self._clipboard else ''}"
        )
        paste_action.setEnabled(self._clipboard is not None)

        action = menu.exec(table.viewport().mapToGlobal(pos))
        if action == copy_action:
            self._copy_config(config_id, dog_id)
        elif action == paste_action:
            self._paste_config(dog_id, slot_key)

    def _copy_config(self, config_id: int, dog_id: int):
        try:
            configs = api.get('/meal-configs/', params={'dog_id': dog_id})
        except Exception as exc:
            QMessageBox.critical(self, "Copy error", str(exc))
            return
        cfg = next((c for c in configs if c['id'] == config_id), None)
        if not cfg:
            return
        self._clipboard = [{'food_name': it['food_name'], 'amount': it.get('amount', '') or ''}
                           for it in cfg.get('items', [])]

    def _paste_config(self, dog_id: int, slot_key: str):
        if not self._clipboard:
            return
        try:
            self._ingredients = api.get('/meal-ingredients')
        except Exception:
            pass
        # Build a fake config dict to pre-fill the dialog (dog/slot read-only, items pre-loaded)
        fake_config = {
            'dog_id': dog_id,
            'meal_slot': slot_key,
            'effective_date': None,
            'items': self._clipboard,
        }
        dlg = MealConfigDialog(self._dogs, self._slots, self._ingredients,
                               config=fake_config, parent=self)
        # Re-enable dog + slot dropdowns — paste is creating a new record, not editing
        dlg._dog_combo.setEnabled(True)
        dlg._slot_combo.setEnabled(True)
        dlg.setWindowTitle("Add Meal Config (from clipboard)")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        if not data['effective_date']:
            QMessageBox.warning(self, "Validation", "Effective date is required.")
            return
        try:
            api.post('/meal-configs/', json=data)
        except Exception as exc:
            QMessageBox.critical(self, "Save error", str(exc))
            return
        self._load()

    # ── CRUD actions ───────────────────────────────────────────────────────────

    def _add(self):
        if not self._dogs:
            QMessageBox.warning(self, "No dogs", "No active dogs found.")
            return
        try:
            self._ingredients = api.get('/meal-ingredients')
        except Exception:
            pass
        dlg = MealConfigDialog(self._dogs, self._slots, self._ingredients, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        if not data['effective_date']:
            QMessageBox.warning(self, "Validation", "Effective date is required.")
            return
        try:
            api.post('/meal-configs/', json=data)
        except Exception as exc:
            QMessageBox.critical(self, "Save error", str(exc))
            return
        self._load()

    def _edit(self):
        if self._selected_config_id is None:
            return
        try:
            self._ingredients = api.get('/meal-ingredients')
        except Exception:
            pass
        # Find the full config data from the current tables
        try:
            configs = api.get('/meal-configs/', params={'dog_id': self._selected_dog_id})
        except Exception as exc:
            QMessageBox.critical(self, "Load error", str(exc))
            return
        config = next((c for c in configs if c['id'] == self._selected_config_id), None)
        if not config:
            QMessageBox.warning(self, "Not found", "Config not found.")
            self._load()
            return
        dlg = MealConfigDialog(self._dogs, self._slots, self._ingredients,
                               config=config, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        patch = {'effective_date': data['effective_date'], 'items': data['items']}
        try:
            api.patch(f'/meal-configs/{self._selected_config_id}', json=patch)
        except Exception as exc:
            QMessageBox.critical(self, "Save error", str(exc))
            return
        self._load()

    def _delete(self):
        if self._selected_config_id is None:
            return
        reply = QMessageBox.question(
            self, "Delete",
            "Delete this meal config? Previous version (if any) becomes current.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            api.delete(f'/meal-configs/{self._selected_config_id}')
        except Exception as exc:
            QMessageBox.critical(self, "Delete error", str(exc))
            return
        self._load()
