from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox,
    QCalendarWidget, QTextBrowser, QMessageBox, QDialog, QFormLayout,
    QDialogButtonBox, QTimeEdit, QDoubleSpinBox
)
from PyQt6.QtCore import QDate, QTime
from database.db import Database


class EditShiftDialog(QDialog):
    def __init__(self, parent=None, shift_data=None, employees=None):
        super().__init__(parent)
        self.setWindowTitle("Изменить смену")

        # Поля для изменения данных смены
        self.employee_selector = QComboBox()
        self.start_time_edit = QTimeEdit()
        self.end_time_edit = QTimeEdit()
        self.hourly_rate_edit = QDoubleSpinBox()
        self.hourly_rate_edit.setMinimum(0)
        self.hourly_rate_edit.setMaximum(10000)
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

        # Заполняем комбобокс сотрудниками
        for emp_id, full_name in employees.items():
            self.employee_selector.addItem(full_name, emp_id)

        # Если переданы данные о смене, заполняем поля
        if shift_data:
            self.employee_selector.setCurrentIndex(
                self.employee_selector.findData(shift_data['employee_id'])
            )
            self.start_time_edit.setTime(QTime.fromString(shift_data['shift_start'], "HH:mm:ss"))
            self.end_time_edit.setTime(QTime.fromString(shift_data['shift_end'], "HH:mm:ss"))
            self.hourly_rate_edit.setValue(shift_data['shift_salary'] / self.calculate_hours(shift_data))

        self.shift_data = shift_data

    def get_data(self):
        return (
            self.employee_selector.currentData(),
            self.start_time_edit.time().toString("HH:mm:ss"),
            self.end_time_edit.time().toString("HH:mm:ss"),
            self.hourly_rate_edit.value()
        )

    def calculate_hours(self, shift):
        # Преобразуем строковое время в QTime
        start = QTime.fromString(shift['shift_start'], "HH:mm:ss")
        end = QTime.fromString(shift['shift_end'], "HH:mm:ss")

        # Вычисляем разницу во времени в часах
        hours = start.secsTo(end) / 3600
        return hours


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

        self.load_employees()

    def load_employees(self):
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
        self.info_browser.append(f"Смен в месяц: {len(shifts)}")
        self.info_browser.append("\n📅 Смены:")

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
                # Если смена существует, отображаем окно с возможностью редактировать
                employee_name = f"{self.employees_data[emp_id]}"

                # Проверка, что другие сотрудники не работают в этот день (пересечение)
                overlapping_shift = self.db.fetch_one(
                    "SELECT * FROM shifts WHERE shift_date = %s AND employee_id != %s",
                    (shift_date, emp_id)
                )
                if overlapping_shift:
                    QMessageBox.warning(self, "Ошибка", "В этот день уже есть другая смена.")
                    return

                message = f"В этот день уже выходит {employee_name}.\nИзменить данные смены?"
                reply = QMessageBox.question(self, "Смена существует", message,
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    dialog = EditShiftDialog(self, shift_data=shift, employees=self.employees_data)
                    if dialog.exec():
                        employee_id, start_time, end_time, hourly_rate = dialog.get_data()
                        start = QTime.fromString(start_time, "HH:mm:ss")
                        end = QTime.fromString(end_time, "HH:mm:ss")
                        hours = start.secsTo(end) / 3600
                        if hours <= 0:
                            QMessageBox.warning(self, "Ошибка", "Время окончания должно быть позже начала.")
                            return
                        total_salary = round(hourly_rate * hours, 2)

                        # Обновляем смену в базе данных
                        self.db.execute("""
                            UPDATE shifts
                            SET shift_start = %s, shift_end = %s, shift_salary = %s, employee_id = %s
                            WHERE id = %s
                        """, (start_time, end_time, total_salary, employee_id, shift['id']))
                        QMessageBox.information(self, "Обновлено", "Смена обновлена.")
                        self.load_shifts()

            else:
                # Если смены на выбранную дату нет, предлагаем добавить новую
                dialog = EditShiftDialog(self, employees=self.employees_data)
                if dialog.exec():
                    employee_id, start_time, end_time, hourly_rate = dialog.get_data()

                    # Проверка, что сотрудник не работает в этот день
                    overlapping_shift = self.db.fetch_one(
                        "SELECT * FROM shifts WHERE shift_date = %s AND employee_id = %s",
                        (shift_date, employee_id)
                    )
                    if overlapping_shift:
                        QMessageBox.warning(self, "Ошибка", "Этот сотрудник уже работает в этот день.")
                        return

                    start = QTime.fromString(start_time, "HH:mm:ss")
                    end = QTime.fromString(end_time, "HH:mm:ss")
                    hours = start.secsTo(end) / 3600
                    if hours <= 0:
                        QMessageBox.warning(self, "Ошибка", "Время окончания должно быть позже начала.")
                        return
                    total_salary = round(hourly_rate * hours, 2)

                    # Добавляем новую смену
                    self.db.execute("""
                        INSERT INTO shifts (employee_id, shift_date, shift_start, shift_end, shift_salary)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (employee_id, shift_date, start_time, end_time, total_salary))
                    QMessageBox.information(self, "Добавлено", f"Смена на {shift_date} добавлена.")
                    self.load_shifts()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обработке смены:\n{e}")
