from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QMessageBox, QAbstractItemView, QComboBox, QFormLayout, QDialogButtonBox,
    QTimeEdit, QDoubleSpinBox
)
from PyQt6.QtCore import QTime
from datetime import timedelta, time


def to_qtime(value):
    if isinstance(value, QTime):
        return value
    elif isinstance(value, str):
        return QTime.fromString(value, "HH:mm:ss")
    elif isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) % 60
        seconds = total_seconds % 60
        return QTime(hours, minutes, seconds)
    elif isinstance(value, time):
        return QTime(value.hour, value.minute, value.second)
    else:
        return QTime()


class EditShiftDialog(QDialog):
    def __init__(self, parent=None, shift_data=None, employees=None):
        super().__init__(parent)
        self.setWindowTitle("Изменить смену")

        self.employee_selector = QComboBox()
        self.start_time_edit = QTimeEdit()
        self.end_time_edit = QTimeEdit()
        self.hourly_rate_edit = QDoubleSpinBox()
        self.hourly_rate_edit.setRange(0, 10000)
        self.hourly_rate_edit.setSuffix(" ₽/ч")

        layout = QFormLayout()
        layout.addRow("Сотрудник:", self.employee_selector)
        layout.addRow("Начало смены:", self.start_time_edit)
        layout.addRow("Конец смены:", self.end_time_edit)
        layout.addRow("Ставка:", self.hourly_rate_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)
        self.setLayout(layout)

        for emp_id, name in employees.items():
            self.employee_selector.addItem(name, emp_id)

        if shift_data:
            self.employee_selector.setCurrentIndex(
                self.employee_selector.findData(shift_data['employee_id'])
            )
            self.start_time_edit.setTime(to_qtime(shift_data['shift_start']))
            self.end_time_edit.setTime(to_qtime(shift_data['shift_end']))

            start = to_qtime(shift_data['shift_start'])
            end = to_qtime(shift_data['shift_end'])
            hours = start.secsTo(end) / 3600
            if hours > 0:
                self.hourly_rate_edit.setValue(float(shift_data['shift_salary']) / hours)

        self.shift_data = shift_data

    def get_data(self):
        return (
            self.employee_selector.currentData(),
            self.start_time_edit.time().toString("HH:mm:ss"),
            self.end_time_edit.time().toString("HH:mm:ss"),
            self.hourly_rate_edit.value()
        )


class ManageShiftsDialog(QDialog):
    def __init__(self, parent=None, db=None, employees=None):
        super().__init__(parent)
        self.setWindowTitle("Управление сменами")
        self.db = db
        self.employees = employees

        self.layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Сотрудник", "Дата", "Начало", "Конец", "Зарплата", "ID"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.load_data()

        self.edit_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")
        self.close_button = QPushButton("Закрыть")

        self.edit_button.clicked.connect(self.edit_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.close_button.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.close_button)

        self.layout.addWidget(QLabel("Все смены:"))
        self.layout.addWidget(self.table)
        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def load_data(self):
        self.table.setRowCount(0)
        shifts = self.db.fetch_all("""
            SELECT s.id, s.shift_date, s.shift_start, s.shift_end, s.shift_salary, s.employee_id,
                   e.first_name, e.last_name
            FROM shifts s
            JOIN employees e ON s.employee_id = e.id
            ORDER BY s.shift_date DESC
        """)

        for shift in shifts:
            row = self.table.rowCount()
            self.table.insertRow(row)
            emp_name = f"{shift['first_name']} {shift['last_name']}"
            self.table.setItem(row, 0, QTableWidgetItem(emp_name))
            self.table.setItem(row, 1, QTableWidgetItem(str(shift['shift_date'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(shift['shift_start'])))
            self.table.setItem(row, 3, QTableWidgetItem(str(shift['shift_end'])))
            self.table.setItem(row, 4, QTableWidgetItem(f"{shift['shift_salary']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(str(shift['id'])))

    def get_selected_shift_id(self):
        selected = self.table.currentRow()
        if selected == -1:
            return None
        return int(self.table.item(selected, 5).text())

    def edit_selected(self):
        shift_id = self.get_selected_shift_id()
        if not shift_id:
            QMessageBox.warning(self, "Ошибка", "Выберите смену для редактирования.")
            return

        shift = self.db.fetch_one("SELECT * FROM shifts WHERE id = %s", (shift_id,))
        if not shift:
            QMessageBox.critical(self, "Ошибка", "Смена не найдена.")
            return

        dialog = EditShiftDialog(self, shift_data=shift, employees=self.employees)
        if dialog.exec():
            employee_id, start_time, end_time, hourly_rate = dialog.get_data()
            start = QTime.fromString(start_time, "HH:mm:ss")
            end = QTime.fromString(end_time, "HH:mm:ss")

            if not start.isValid() or not end.isValid() or start >= end:
                QMessageBox.warning(self, "Ошибка", "Некорректное время.")
                return

            hours = start.secsTo(end) / 3600
            salary = round(hourly_rate * hours, 2)

            self.db.execute("""
                UPDATE shifts SET employee_id=%s, shift_start=%s, shift_end=%s, shift_salary=%s
                WHERE id=%s
            """, (employee_id, start_time, end_time, salary, shift_id))

            QMessageBox.information(self, "Обновлено", "Смена обновлена.")
            self.load_data()

    def delete_selected(self):
        shift_id = self.get_selected_shift_id()
        if not shift_id:
            QMessageBox.warning(self, "Ошибка", "Выберите смену для удаления.")
            return

        reply = QMessageBox.question(self, "Удаление", "Удалить выбранную смену?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM shifts WHERE id = %s", (shift_id,))
            QMessageBox.information(self, "Удалено", "Смена удалена.")
            self.load_data()
