from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QMessageBox, QHBoxLayout, QProgressBar, QScrollArea, QGroupBox, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt
from decimal import Decimal
from database.db import Database

# Импортируем для доступа к фиксированным расходам
from ui.tab_settings import SettingsTab  # корректный путь

class CalculatorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Левая часть
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

        change_price_btn = QPushButton("Изменить цену")
        change_price_btn.clicked.connect(self.change_price)

        refresh_products_btn = QPushButton("Обновить список товаров")
        refresh_products_btn.clicked.connect(self.load_products)

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
        left_layout.addWidget(change_price_btn)
        left_layout.addWidget(refresh_products_btn)

        # Фиксированные расходы
        self.bank_fee_input = QLineEdit()
        self.nalog_input = QLineEdit()

        left_layout.addWidget(QLabel("Банковская комиссия (%)"))
        left_layout.addWidget(self.bank_fee_input)
        left_layout.addWidget(QLabel("Налог (%)"))
        left_layout.addWidget(self.nalog_input)

        save_fixed_btn = QPushButton("Сохранить комиссии и налоги")
        save_fixed_btn.clicked.connect(self.save_fixed_costs)
        left_layout.addWidget(save_fixed_btn)

        # Правая часть — справка
        info_layout = QVBoxLayout()
        info_group_box = QGroupBox("Как работают расчёты")
        info_group_box.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                color: #3C2C23;
            }
        """)

        info_text = QLabel("""
            <b>Учитываются:</b><br>
            - Цена продажи<br>
            - Себестоимость<br>
            - Прочие расходы<br>
            - Банковская комиссия и налог<br><br>
            <b>Не учитываются:</b><br>
            - Аренда<br>
            - Зарплаты<br>
            - Коммунальные услуги<br>
            """)
        info_text.setWordWrap(True)
        info_group_box.setLayout(QVBoxLayout())
        info_group_box.layout().addWidget(info_text)
        info_layout.addWidget(info_group_box)

        info_scroll = QScrollArea()
        info_scroll.setWidgetResizable(True)
        info_widget = QWidget()
        info_widget.setLayout(info_layout)
        info_scroll.setWidget(info_widget)

        layout.addLayout(left_layout, 3)
        layout.addWidget(info_scroll, 2)

        self.load_fixed_costs()
        self.apply_styles()

    def load_products(self):
        self.product_select.clear()
        products = self.db.fetch_all("SELECT id, name, price FROM products")
        self.products = {f"{p['name']} ({p['price']} ₽)": (p['id'], p['price']) for p in products}
        self.product_select.addItems(self.products.keys())

    def apply_styles(self):
        try:
            with open("assets/style.css", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("⚠️ Файл стилей не найден")

    def load_fixed_costs(self):
        fixed = self.db.fetch_one("SELECT * FROM fixed_costs WHERE id = 1")
        if fixed:
            self.bank_fee_input.setText(str(fixed["bank_fee"] * 100))
            self.nalog_input.setText(str(fixed["nalog"] * 100))
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить фиксированные издержки.")

    def save_fixed_costs(self):
        try:
            bank_fee_percent = Decimal(self.bank_fee_input.text().replace(',', '.')) / 100
            nalog_percent = Decimal(self.nalog_input.text().replace(',', '.')) / 100

            if bank_fee_percent < 0 or nalog_percent < 0:
                QMessageBox.warning(self, "Ошибка", "Значения не могут быть отрицательными.")
                return

            self.db.execute(
                "UPDATE fixed_costs SET bank_fee = %s, nalog = %s WHERE id = 1",
                (bank_fee_percent, nalog_percent)
            )

            QMessageBox.information(self, "Успех", "Фиксированные издержки обновлены.")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректные значения.")

    def calculate_profit(self):
        try:
            current_item = self.product_select.currentText()
            product_id, _ = self.products.get(current_item, (None, None))
            if not product_id:
                QMessageBox.warning(self, "Ошибка", "Выберите продукт.")
                return

            cost_price = Decimal(self.cost_input.text().replace(',', '.'))
            other_expenses = Decimal(self.other_expenses_input.text().replace(',', '.'))
            quantity = int(self.monthly_output_input.text())

            if quantity <= 0:
                QMessageBox.warning(self, "Ошибка", "Количество должно быть больше нуля.")
                return

            product = self.db.fetch_one("SELECT price FROM products WHERE id = %s", (product_id,))
            if not product:
                QMessageBox.critical(self, "Ошибка", "Продукт не найден.")
                return

            price = Decimal(product["price"])

            bank_fee = Decimal(self.bank_fee_input.text().replace(',', '.')) / 100
            nalog = Decimal(self.nalog_input.text().replace(',', '.')) / 100

            revenue = price * quantity
            total_variable_cost = (cost_price + other_expenses) * quantity
            total_fixed_cost = revenue * (bank_fee + nalog)
            total_cost = total_variable_cost + total_fixed_cost

            net_profit = revenue - total_cost
            profit_percent = (net_profit / revenue) * 100 if revenue > 0 else 0

            self.result_label.setText(
                f"Цена: {price:.2f} ₽ | Себестоимость + расходы: {(cost_price + other_expenses):.2f} ₽\n"
                f"Выручка: {revenue:.2f} ₽\n"
                f"Итоговая прибыль: {net_profit:.2f} ₽ ({profit_percent:.1f}%)"
            )
            self.update_progress_bar(profit_percent)

        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректные числовые значения.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

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
        current_item = self.product_select.currentText()
        product_id, _ = self.products.get(current_item, (None, None))

        if not product_id:
            QMessageBox.warning(self, "Ошибка", "Выберите продукт.")
            return

        dialog = ChangePriceDialog(product_id, self.db)
        dialog.exec()
        self.load_products()


class ChangePriceDialog(QDialog):
    def __init__(self, product_id, db):
        super().__init__()
        self.product_id = product_id
        self.db = db
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Изменить цену товара")
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

            self.db.execute("UPDATE products SET price = %s WHERE id = %s", (new_price, self.product_id))
            QMessageBox.information(self, "Успех", "Цена успешно обновлена.")
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректную цену.")
