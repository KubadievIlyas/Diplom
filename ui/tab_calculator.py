from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QMessageBox, QHBoxLayout, QProgressBar, QScrollArea, QGroupBox, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from database.db import Database
from decimal import Decimal

class CalculatorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Левая часть с калькулятором
        left_layout = QVBoxLayout()
        self.product_select = QComboBox()
        self.load_products()

        self.cost_input = QLineEdit()
        self.other_expenses_input = QLineEdit()
        self.monthly_output_input = QLineEdit()

        self.result_label = QLabel("")
        self.profit_bar = QProgressBar()
        self.profit_bar.setTextVisible(True)

        calculate_btn = QPushButton("Рассчитать прибыль")
        calculate_btn.clicked.connect(self.calculate_profit)

        # Кнопка для изменения цены
        change_price_btn = QPushButton("Изменить цену")
        change_price_btn.clicked.connect(self.change_price)

        left_layout.addWidget(QLabel("Выберите товар"))
        left_layout.addWidget(self.product_select)
        left_layout.addWidget(QLabel("Себестоимость (₽)"))
        left_layout.addWidget(self.cost_input)
        left_layout.addWidget(QLabel("Прочие расходы (на единицу, ₽)"))
        left_layout.addWidget(self.other_expenses_input)
        left_layout.addWidget(QLabel("Планируемое кол-во продаж в месяц"))
        left_layout.addWidget(self.monthly_output_input)
        left_layout.addWidget(calculate_btn)
        left_layout.addWidget(QLabel("Результаты:"))
        left_layout.addWidget(self.result_label)
        left_layout.addWidget(self.profit_bar)
        left_layout.addWidget(change_price_btn)  # Добавили кнопку изменения цены

        # Правая часть с информацией
        info_layout = QVBoxLayout()

        # Информационное окно
        info_group_box = QGroupBox()
        info_group_box.setTitle("Как работают расчёты")

        # Применим стиль к заголовку
        info_group_box.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                color: #3C2C23;
                text-align: center;
            }
        """)

        info_text = QLabel(
            """
            <b>В расчётах учитываются следующие данные:</b><br>
            - Цена продажи товара<br>
            - Себестоимость товара<br>
            - Прочие расходы на единицу товара<br>
            - Фиксированные расходы (банковская комиссия, налог)<br><br>

            <b>Не учитываются:</b><br>
            - Аренда<br>
            - Зарплата сотрудников<br>
            - Коммунальные услуги<br><br>

            <b>Рассчитываемая прибыль отображает только чистую прибыль с учётом данных факторов.</b>
            """
        )
        info_text.setWordWrap(True)  # Перенос текста

        # Применим стиль для текста
        info_text.setStyleSheet("""
            QLabel {
                background-color: #EBD3A5;
                padding: 15px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 16px;
                color: #3C2C23;
                border-radius: 8px;
                border: 2px solid #C08A5D;
            }
            QLabel b {
                font-weight: bold;
                color: #C08A5D;
            }
        """)

        info_layout.addWidget(info_group_box)
        info_group_box.setLayout(QVBoxLayout())
        info_group_box.layout().addWidget(info_text)

        # Увеличиваем пространство для информационного окна
        info_scroll_area = QScrollArea()
        info_scroll_area.setWidgetResizable(True)
        info_widget = QWidget()
        info_widget.setLayout(info_layout)
        info_scroll_area.setWidget(info_widget)

        # Добавляем правую панель с информацией
        layout.addLayout(left_layout, 3)
        layout.addWidget(info_scroll_area, 2)  # Увеличили размер правой панели

        # Применение стилей из файла CSS
        self.apply_styles()

    def load_products(self):
        products = self.db.fetch_all("SELECT id, name, price FROM products")
        self.products = {f"{p['name']} ({p['price']} ₽)": (p['id'], p['price']) for p in products}
        self.product_select.addItems(self.products.keys())

    def apply_styles(self):
        try:
            with open("assets/style.css", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("⚠️ Файл стилей не найден: assets/style.css")

    def calculate_profit(self):
        try:
            # Получаем выбранный продукт
            current_item = self.product_select.currentText()
            product_id, _ = self.products.get(current_item, (None, None))

            if not product_id:
                QMessageBox.warning(self, "Ошибка", "Выберите продукт.")
                return

            # Чтение введённых данных с приведением к Decimal
            cost_price = Decimal(self.cost_input.text().replace(',', '.'))
            other_expenses = Decimal(self.other_expenses_input.text().replace(',', '.'))
            quantity = int(self.monthly_output_input.text())

            if quantity <= 0:
                QMessageBox.warning(self, "Ошибка", "Количество должно быть больше нуля.")
                return

            # Получаем цену продажи
            product = self.db.fetch_one("SELECT price FROM products WHERE id = %s", (product_id,))
            if not product:
                QMessageBox.critical(self, "Ошибка", "Продукт не найден в базе.")
                return

            price = Decimal(product["price"])

            # Получаем фиксированные расходы
            fixed = self.db.fetch_one("SELECT * FROM fixed_costs WHERE id = 1")

            if not fixed:
                QMessageBox.critical(self, "Ошибка", "Фиксированные издержки не заданы.")
                return

            bank_fee = Decimal(fixed["bank_fee"])  # Преобразуем в Decimal
            tax = Decimal(fixed["nalog"])  # Преобразуем в Decimal

            # Расчёты
            total_fixed = (price * quantity) * (bank_fee + tax)
            full_cost = (cost_price + other_expenses) * quantity + total_fixed
            revenue = price * quantity
            net_profit = revenue - full_cost

            if revenue == 0:
                profit_percent = 0
            else:
                profit_percent = (net_profit / revenue) * 100

            # Вывод результатов
            self.result_label.setText(f"Прибыль: {net_profit:.2f} ₽ ({profit_percent:.1f}%)")
            self.update_progress_bar(profit_percent)

        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Проверьте корректность введённых чисел.")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"{str(e)}")

    def update_progress_bar(self, percent):
        self.profit_bar.setValue(int(percent))
        if percent < 20:
            self.profit_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
            self.profit_bar.setFormat("Низкая прибыль (%p%)")
        elif percent < 40:
            self.profit_bar.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
            self.profit_bar.setFormat("Средняя прибыль (%p%)")
        else:
            self.profit_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
            self.profit_bar.setFormat("Высокая прибыль (%p%)")

    def change_price(self):
        # Получаем выбранный продукт
        current_item = self.product_select.currentText()
        product_id, _ = self.products.get(current_item, (None, None))

        if not product_id:
            QMessageBox.warning(self, "Ошибка", "Выберите продукт.")
            return

        # Открываем диалог для изменения цены
        dialog = ChangePriceDialog(product_id, self.db)
        dialog.exec()

        # После изменения цены, обновляем данные
        self.load_products()

class ChangePriceDialog(QDialog):
    def __init__(self, product_id, db):
        super().__init__()
        self.product_id = product_id
        self.db = db
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Изменить цену товара")
        self.setModal(True)

        layout = QFormLayout(self)
        self.new_price_input = QLineEdit(self)
        layout.addRow("Новая цена (₽):", self.new_price_input)

        save_btn = QPushButton("Сохранить", self)
        save_btn.clicked.connect(self.save_price)
        cancel_btn = QPushButton("Отмена", self)
        cancel_btn.clicked.connect(self.reject)

        layout.addRow(save_btn, cancel_btn)

    def save_price(self):
        try:
            new_price = Decimal(self.new_price_input.text().replace(",", "."))
            if new_price <= 0:
                QMessageBox.warning(self, "Ошибка", "Цена должна быть больше нуля.")
                return

            # Обновляем цену в базе данных
            self.db.execute("UPDATE products SET price = %s WHERE id = %s", (new_price, self.product_id))

            # Закрываем диалог
            QMessageBox.information(self, "Успех", "Цена успешно обновлена.")
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректную цену.")
