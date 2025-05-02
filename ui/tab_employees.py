from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QCalendarWidget, QTextBrowser,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QTimeEdit,
    QDoubleSpinBox, QPushButton
)
from PyQt6.QtCore import QDate, QTime
from database.db import Database
from datetime import datetime, timedelta, time


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
        return QTime()  # пустое значение


class EditShiftDialog(QDialog):
    def __init__(self, parent=None, shift_data=None, employees=None):
        super().__init__(parent)
        self.setWindowTitle("Изменить смену")

        self.employee_selector = QComboBox()
        self.start_time_edit = QTimeEdit()
        self.end_time_edit = QTimeEdit()
        self.hourly_rate_edit = QDoubleSpinBox()
        self.hourly_rate_edit.setRange(0, 10000)
        self.hourly_rate_edit.setValue(200.0)
        self.hourly_rate_edit.setSuffix(" ₽/ч")

        layout = QFormLayout()
        layout.addRow("Сотрудник:", self.employee_selector)
        layout.addRow("Начало смены:", self.start_time_edit)
        layout.addRow("Конец смены:", self.end_time_edit)
        layout.addRow("Зарплата в час:", self.hourly_rate_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)
        self.setLayout(layout)

        for emp_id, full_name in employees.items():
            self.employee_selector.addItem(full_name, emp_id)

        if shift_data:
            self.employee_selector.setCurrentIndex(
                self.employee_selector.findData(shift_data['employee_id'])
            )
            self.start_time_edit.setTime(to_qtime(shift_data['shift_start']))
            self.end_time_edit.setTime(to_qtime(shift_data['shift_end']))

            hours = self.calculate_hours(shift_data)
            if hours > 0:
                # Преобразуем зарплату в float, чтобы избежать ошибки с decimal
                self.hourly_rate_edit.setValue(
                    float(shift_data['shift_salary']) / hours
                )

        self.shift_data = shift_data

    def get_data(self):
        return (
            self.employee_selector.currentData(),
            self.start_time_edit.time().toString("HH:mm:ss"),
            self.end_time_edit.time().toString("HH:mm:ss"),
            self.hourly_rate_edit.value()
        )

    def calculate_hours(self, shift):
        start = to_qtime(shift['shift_start'])
        end = to_qtime(shift['shift_end'])
        return start.secsTo(end) / 3600


class ManageShiftsDialog(QDialog):
    def __init__(self, parent=None, db=None, employees=None):
        super().__init__(parent)
        self.setWindowTitle("Управление сменами")
        self.db = db
        self.employees = employees

        self.employee_selector = QComboBox()
        for emp_id, name in employees.items():
            self.employee_selector.addItem(name, emp_id)
        self.employee_selector.currentIndexChanged.connect(self.load_shifts)

        self.shifts_selector = QComboBox()
        self.edit_button = QPushButton("Редактировать")
        self.delete_button = QPushButton("Удалить")
        self.close_button = QPushButton("Закрыть")

        self.edit_button.clicked.connect(self.edit_shift)
        self.delete_button.clicked.connect(self.delete_shift)
        self.close_button.clicked.connect(self.accept)

        layout = QFormLayout()
        layout.addRow("Сотрудник:", self.employee_selector)
        layout.addRow("Смены:", self.shifts_selector)
        layout.addRow(self.edit_button, self.delete_button)
        layout.addRow(self.close_button)
        self.setLayout(layout)

        self.load_shifts()

    def load_shifts(self):
        self.shifts_selector.clear()
        emp_id = self.employee_selector.currentData()
        if emp_id is None:
            return

        shifts = self.db.fetch_all("""
            SELECT * FROM shifts WHERE employee_id = %s ORDER BY shift_date
        """, (emp_id,))
        self.shift_map = {}

        for shift in shifts:
            label = f"{shift['shift_date']} ({shift['shift_start']} - {shift['shift_end']})"
            self.shifts_selector.addItem(label, shift['id'])
            self.shift_map[shift['id']] = shift

    def edit_shift(self):
        try:
            shift_id = self.shifts_selector.currentData()
            if not shift_id:
                QMessageBox.warning(self, "Ошибка", "Смена не выбрана.")
                return

            shift = self.shift_map.get(shift_id)
            if not shift:
                QMessageBox.warning(self, "Ошибка", "Не удалось найти данные смены.")
                return

            dialog = EditShiftDialog(self, shift_data=shift, employees=self.employees)
            if dialog.exec():
                employee_id, start_time, end_time, hourly_rate = dialog.get_data()

                start = QTime.fromString(start_time, "HH:mm:ss")
                end = QTime.fromString(end_time, "HH:mm:ss")
                if not start.isValid() or not end.isValid():
                    QMessageBox.warning(self, "Ошибка", "Некорректное время.")
                    return

                hours = start.secsTo(end) / 3600
                if hours <= 0:
                    QMessageBox.warning(self, "Ошибка", "Время окончания должно быть позже начала.")
                    return

                # Преобразуем зарплату в float, чтобы избежать ошибок с типами данных
                total_salary = round(float(hourly_rate) * hours, 2)

                self.db.execute("""
                    UPDATE shifts 
                    SET shift_start = %s, shift_end = %s, shift_salary = %s, employee_id = %s 
                    WHERE id = %s
                """, (start_time, end_time, total_salary, employee_id, shift_id))

                QMessageBox.information(self, "Обновлено", "Смена успешно обновлена.")
                self.load_shifts()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить редактирование:\n{e}")

    def delete_shift(self):
        shift_id = self.shifts_selector.currentData()
        if shift_id and QMessageBox.question(self, "Удаление", "Удалить выбранную смену?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM shifts WHERE id = %s", (shift_id,))
            QMessageBox.information(self, "Удалено", "Смена удалена.")
            self.load_shifts()


class ManageShiftsDialog(QDialog):
    def __init__(self, parent=None, db=None, employees=None):
        super().__init__(parent)
        self.setWindowTitle("Управление сменами")
        self.db = db
        self.employees = employees

        self.employee_selector = QComboBox()
        for emp_id, name in employees.items():
            self.employee_selector.addItem(name, emp_id)
        self.employee_selector.currentIndexChanged.connect(self.load_shifts)

        self.shifts_selector = QComboBox()
        self.edit_button = QPushButton("Редактировать")
        self.delete_button = QPushButton("Удалить")
        self.close_button = QPushButton("Закрыть")

        self.edit_button.clicked.connect(self.edit_shift)
        self.delete_button.clicked.connect(self.delete_shift)
        self.close_button.clicked.connect(self.accept)

        layout = QFormLayout()
        layout.addRow("Сотрудник:", self.employee_selector)
        layout.addRow("Смены:", self.shifts_selector)
        layout.addRow(self.edit_button, self.delete_button)
        layout.addRow(self.close_button)
        self.setLayout(layout)

        self.load_shifts()

    def load_shifts(self):
        self.shifts_selector.clear()
        emp_id = self.employee_selector.currentData()
        if emp_id is None:
            return

        shifts = self.db.fetch_all("""
            SELECT * FROM shifts WHERE employee_id = %s ORDER BY shift_date
        """, (emp_id,))
        self.shift_map = {}

        for shift in shifts:
            label = f"{shift['shift_date']} ({shift['shift_start']} - {shift['shift_end']})"
            self.shifts_selector.addItem(label, shift['id'])
            self.shift_map[shift['id']] = shift

    def edit_shift(self):
        try:
            shift_id = self.shifts_selector.currentData()
            if not shift_id:
                QMessageBox.warning(self, "Ошибка", "Смена не выбрана.")
                return

            shift = self.shift_map.get(shift_id)
            if not shift:
                QMessageBox.warning(self, "Ошибка", "Не удалось найти данные смены.")
                return

            dialog = EditShiftDialog(self, shift_data=shift, employees=self.employees)
            if dialog.exec():
                employee_id, start_time, end_time, hourly_rate = dialog.get_data()

                start = QTime.fromString(start_time, "HH:mm:ss")
                end = QTime.fromString(end_time, "HH:mm:ss")
                if not start.isValid() or not end.isValid():
                    QMessageBox.warning(self, "Ошибка", "Некорректное время.")
                    return

                hours = start.secsTo(end) / 3600
                if hours <= 0:
                    QMessageBox.warning(self, "Ошибка", "Время окончания должно быть позже начала.")
                    return

                total_salary = round(hourly_rate * hours, 2)

                self.db.execute("""
                    UPDATE shifts 
                    SET shift_start = %s, shift_end = %s, shift_salary = %s, employee_id = %s 
                    WHERE id = %s
                """, (start_time, end_time, total_salary, employee_id, shift_id))

                QMessageBox.information(self, "Обновлено", "Смена успешно обновлена.")
                self.load_shifts()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить редактирование:\n{e}")

    def delete_shift(self):
        shift_id = self.shifts_selector.currentData()
        if shift_id and QMessageBox.question(self, "Удаление", "Удалить выбранную смену?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM shifts WHERE id = %s", (shift_id,))
            QMessageBox.information(self, "Удалено", "Смена удалена.")
            self.load_shifts()


class EmployeeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.employee_selector = QComboBox()
        self.employee_selector.currentIndexChanged.connect(self.load_shifts)
        layout.addWidget(QLabel("Выберите сотрудника:"))
        layout.addWidget(self.employee_selector)

        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self.on_calendar_clicked)
        layout.addWidget(self.calendar)

        self.info_browser = QTextBrowser()
        layout.addWidget(QLabel("Смены и зарплата:"))
        layout.addWidget(self.info_browser)

        self.manage_button = QPushButton("Управление сменами")
        self.manage_button.clicked.connect(self.open_manage_shifts)
        layout.addWidget(self.manage_button)

        # Кнопка "Обновить"
        self.refresh_button = QPushButton("Обновить данные")
        self.refresh_button.clicked.connect(self.load_employees)
        layout.addWidget(self.refresh_button)

        self.load_employees()

    def load_employees(self):
        # Загружаем список сотрудников
        employees = self.db.fetch_all("SELECT id, first_name, last_name FROM employees")
        self.employee_selector.clear()
        self.employees_data = {}

        for emp in employees:
            full_name = f"{emp['first_name']} {emp['last_name']}"
            self.employee_selector.addItem(full_name, emp['id'])
            self.employees_data[emp['id']] = full_name

        if employees:
            self.load_shifts()

    def load_shifts(self):
        emp_id = self.employee_selector.currentData()
        if not emp_id:
            return

        shifts = self.db.fetch_all(""" 
            SELECT shift_date, shift_start, shift_end, shift_salary, employee_id
            FROM shifts 
            WHERE employee_id = %s 
            ORDER BY shift_date
        """, (emp_id,))

        self.info_browser.clear()
        self.info_browser.append(f"Смен в месяц: {len(shifts)}\n📅 Смены:")

        total = 0
        dates = []

        for shift in shifts:
            date = QDate.fromString(str(shift['shift_date']), "yyyy-MM-dd")
            dates.append(date)
            salary = shift['shift_salary'] or 0
            total += salary
            self.info_browser.append(
                f"— {date.toString('dd.MM.yyyy')} ({shift['shift_start']}–{shift['shift_end']}) — {salary:.2f} ₽"
            )

        self.info_browser.append(f"\n💰 Всего начислено: {total:.2f} ₽")
        self.highlight_calendar_days(dates)

    def highlight_calendar_days(self, dates):
        if dates:
            self.calendar.setSelectedDate(dates[-1])

    def on_calendar_clicked(self, date: QDate):
        emp_id = self.employee_selector.currentData()
        if not emp_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите сотрудника.")
            return

        shift_date = date.toString("yyyy-MM-dd")

        try:
            shift = self.db.fetch_one(
                "SELECT * FROM shifts WHERE employee_id = %s AND shift_date = %s",
                (emp_id, shift_date)
            )

            if shift:
                reply = QMessageBox.question(self, "Смена существует", "Смена уже существует. Изменить?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    dialog = EditShiftDialog(self, shift_data=shift, employees=self.employees_data)
                    if dialog.exec():
                        self._save_shift(dialog.get_data(), shift_date, existing_id=shift['id'])
            else:
                dialog = EditShiftDialog(self, employees=self.employees_data)
                if dialog.exec():
                    data = dialog.get_data()
                    if self.db.fetch_one("SELECT * FROM shifts WHERE shift_date = %s AND employee_id = %s",
                                         (shift_date, data[0])):

                        QMessageBox.warning(self, "Ошибка", "Этот сотрудник уже работает в этот день.")
                        return
                    self._save_shift(data, shift_date)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обработке смены:\n{e}")

    def _save_shift(self, data, shift_date, existing_id=None):
        employee_id, start_time, end_time, hourly_rate = data
        start = QTime.fromString(start_time, "HH:mm:ss")
        end = QTime.fromString(end_time, "HH:mm:ss")

        if not start.isValid() or not end.isValid() or start >= end:
            QMessageBox.warning(self, "Ошибка", "Некорректное время.")
            return

        hours = start.secsTo(end) / 3600
        total_salary = round(hourly_rate * hours, 2)

        if existing_id:
            self.db.execute("""
                UPDATE shifts
                SET shift_start = %s, shift_end = %s, shift_salary = %s, employee_id = %s
                WHERE id = %s
            """, (start_time, end_time, total_salary, employee_id, existing_id))
            QMessageBox.information(self, "Обновлено", "Смена обновлена.")
        else:
            self.db.execute("""
                INSERT INTO shifts (employee_id, shift_date, shift_start, shift_end, shift_salary)
                VALUES (%s, %s, %s, %s, %s)
            """, (employee_id, shift_date, start_time, end_time, total_salary))
            QMessageBox.information(self, "Добавлено", f"Смена на {shift_date} добавлена.")

        self.load_shifts()

    def open_manage_shifts(self):
        dialog = ManageShiftsDialog(self, db=self.db, employees=self.employees_data)
        if dialog.exec():
            self.load_shifts()

