from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox, QLabel, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from database.db import Database
from decimal import Decimal
import pandas as pd
import os
import subprocess


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        layout.addWidget(QLabel("<h2>Настройки фиксированных данных</h2>"))

        # Форма для ввода данных
        self.form_layout = QFormLayout()

        # Поля для ввода данных (банковская комиссия и налог в процентах)
        self.bank_fee_input = QLineEdit()
        self.nalog_input = QLineEdit()

        self.form_layout.addRow("Банковская комиссия (%)", self.bank_fee_input)
        self.form_layout.addRow("Налог (%)", self.nalog_input)

        # Кнопка для сохранения
        save_btn = QPushButton("Сохранить изменения")
        save_btn.clicked.connect(self.save_settings)

        # Кнопка для экспорта данных о продукции
        export_products_btn = QPushButton("Экспортировать продукцию в Excel")
        export_products_btn.clicked.connect(self.export_products_to_excel)

        # Кнопка для экспорта данных о сменах
        export_shifts_btn = QPushButton("Экспортировать смены в Excel")
        export_shifts_btn.clicked.connect(self.export_shifts_to_excel)

        layout.addLayout(self.form_layout)
        layout.addWidget(save_btn)
        layout.addWidget(export_products_btn)
        layout.addWidget(export_shifts_btn)

        # Загружаем текущие данные
        self.load_settings()

    def load_settings(self):
        # Загружаем текущие фиксированные расходы из базы данных
        settings = self.db.fetch_one("SELECT * FROM fixed_costs WHERE id = 1")

        if settings:
            # Устанавливаем значения в поля для ввода
            self.bank_fee_input.setText(str(settings['bank_fee'] * 100))  # Отображаем в процентах
            self.nalog_input.setText(str(settings['nalog'] * 100))  # Отображаем в процентах
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить настройки.")

    def save_settings(self):
        try:
            # Получаем данные из полей ввода и преобразуем в проценты
            bank_fee_percent = Decimal(self.bank_fee_input.text().replace(',', '.')) / 100
            nalog_percent = Decimal(self.nalog_input.text().replace(',', '.')) / 100

            # Проверяем на корректность
            if bank_fee_percent < 0 or nalog_percent < 0:
                QMessageBox.warning(self, "Ошибка", "Значения не могут быть отрицательными.")
                return

            # Сохраняем данные в базу
            self.db.execute(
                "UPDATE fixed_costs SET bank_fee = %s, nalog = %s WHERE id = 1",
                (bank_fee_percent, nalog_percent)
            )

            QMessageBox.information(self, "Успех", "Настройки успешно обновлены.")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите корректные значения.")

    def export_products_to_excel(self):
        try:
            # Экспортируем данные о продукции
            query = """
                SELECT p.name AS product_name,
                       c.name AS category_name,
                       p.price,
                       u.name AS unit_name,
                       p.weight_or_volume
                FROM products p
                JOIN categories c ON p.category_id = c.id
                JOIN units u ON p.unit_id = u.id
            """
            products = self.db.fetch_all(query)

            if not products:
                QMessageBox.warning(self, "Ошибка", "Нет данных о продукции для экспорта.")
                return

            # Создаем DataFrame из полученных данных
            df = pd.DataFrame(products)

            # Заменим заголовки столбцов на русские
            df.columns = ['Название продукции', 'Категория', 'Цена', 'Единица измерения', 'Вес/Объем']

            # Открываем диалог для выбора местоположения и имени файла
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Excel Files (*.xlsx)")

            if file_path:
                # Сохраняем DataFrame в файл Excel
                df.to_excel(file_path, index=False, engine='openpyxl')
                QMessageBox.information(self, "Успех", "Данные о продукции успешно экспортированы в Excel.")

                # Открываем файл после экспорта
                self.open_file(file_path)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте данных: {str(e)}")

    def export_shifts_to_excel(self):
        try:
            query = """
                SELECT e.first_name,
                       e.last_name,
                       e.position,
                       s.shift_date,
                       TIME_FORMAT(s.shift_start, '%%H:%%i') AS shift_start,
                       TIME_FORMAT(s.shift_end, '%%H:%%i') AS shift_end,
                       s.shift_salary
                FROM shifts s
                JOIN employees e ON s.employee_id = e.id
                ORDER BY s.shift_date DESC
            """

            shifts = self.db.fetch_all(query)

            if not shifts:
                QMessageBox.warning(self, "Ошибка", "Нет данных о сменах для экспорта.")
                return

            df = pd.DataFrame(shifts)

            df.columns = ['Имя', 'Фамилия', 'Должность', 'Дата смены', 'Начало смены', 'Конец смены',
                          'Зарплата за смену']

            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Excel Files (*.xlsx)")

            if file_path:
                df.to_excel(file_path, index=False, engine='openpyxl')
                QMessageBox.information(self, "Успех", "Данные о сменах успешно экспортированы в Excel.")
                self.open_file(file_path)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте смен: {str(e)}")

    def open_file(self, file_path):
        try:
            # Открыть файл с помощью системного приложения
            if os.name == 'nt':  # Для Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # Для macOS и Linux
                subprocess.run(['open', file_path] if sys.platform == 'darwin' else ['xdg-open', file_path])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {str(e)}")
