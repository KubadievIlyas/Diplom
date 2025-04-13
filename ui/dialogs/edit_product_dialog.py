from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QHBoxLayout,
    QMessageBox, QFileDialog
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class EditProductDialog(QDialog):
    def __init__(self, db, product_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.product_id = product_id
        self.setWindowTitle("Редактировать товар" if product_id else "Добавить товар")
        self.setMinimumWidth(400)
        self.photo_data = None

        self.init_ui()
        if self.product_id:
            self.load_product()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.category_input = QComboBox()
        self.price_input = QLineEdit()
        self.weight_input = QLineEdit()
        self.unit_input = QComboBox()
        self.description_input = QTextEdit()

        # Фото
        self.photo_label = QLabel("Фото не выбрано")
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_btn = QPushButton("📷 Загрузить фото")
        photo_btn.clicked.connect(self.load_photo)

        # Загрузка категорий и единиц
        self.load_categories()
        self.load_units()

        layout.addWidget(QLabel("Название"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Категория"))
        layout.addWidget(self.category_input)
        layout.addWidget(QLabel("Цена (₽)"))
        layout.addWidget(self.price_input)
        layout.addWidget(QLabel("Вес / Объём"))
        layout.addWidget(self.weight_input)
        layout.addWidget(QLabel("Единица измерения"))
        layout.addWidget(self.unit_input)
        layout.addWidget(QLabel("Описание"))
        layout.addWidget(self.description_input)

        layout.addWidget(photo_btn)
        layout.addWidget(self.photo_label)

        # Кнопки сохранить / удалить
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self.save_product)


        if self.product_id:
            delete_btn = QPushButton("🗑 Удалить")
            delete_btn.clicked.connect(self.delete_product)
            btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        btn_layout.addWidget(save_btn)
    def load_categories(self):
        self.category_input.clear()
        categories = self.db.fetch_all("SELECT id, name FROM categories")
        for cat in categories:
            self.category_input.addItem(cat['name'], cat['id'])

    def load_units(self):
        self.unit_input.clear()
        units = self.db.fetch_all("SELECT id, name FROM units")
        for unit in units:
            self.unit_input.addItem(unit['name'], unit['id'])

    def load_product(self):
        product = self.db.fetch_one("SELECT * FROM products WHERE id = %s", (self.product_id,))
        if product:
            self.name_input.setText(product['name'])
            self.price_input.setText(str(product['price']))
            self.weight_input.setText(str(product['weight_or_volume'] or ""))
            self.description_input.setPlainText(product['description'] or "")

            # Фото
            if product['photo']:
                pixmap = QPixmap()
                pixmap.loadFromData(product['photo'])
                self.photo_label.setPixmap(pixmap.scaledToWidth(150))
                self.photo_data = product['photo']

            # Установим значения в combobox
            index = self.category_input.findData(product['category_id'])
            if index >= 0:
                self.category_input.setCurrentIndex(index)

            index = self.unit_input.findData(product['unit_id'])
            if index >= 0:
                self.unit_input.setCurrentIndex(index)

    def load_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите фото", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            with open(file_path, 'rb') as file:
                self.photo_data = file.read()
            pixmap = QPixmap()
            pixmap.loadFromData(self.photo_data)
            self.photo_label.setPixmap(pixmap.scaledToWidth(150))

    def save_product(self):
        name = self.name_input.text().strip()
        category_id = self.category_input.currentData()
        unit_id = self.unit_input.currentData()
        description = self.description_input.toPlainText().strip()
        try:
            price = float(self.price_input.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Неверный формат цены")
            return
        try:
            weight = float(self.weight_input.text()) if self.weight_input.text() else None
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Неверный формат веса/объема")
            return

        if not name or not category_id:
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля")
            return

        if self.product_id:
            self.db.execute("""
                UPDATE products SET name=%s, category_id=%s, price=%s, 
                weight_or_volume=%s, unit_id=%s, description=%s, photo=%s 
                WHERE id=%s
            """, (name, category_id, price, weight, unit_id, description, self.photo_data, self.product_id))
        else:
            self.db.execute("""
                INSERT INTO products (name, category_id, price, weight_or_volume, unit_id, description, photo)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, category_id, price, weight, unit_id, description, self.photo_data))

        self.accept()

    def delete_product(self):
        confirm = QMessageBox.question(
            self,
            "Удаление",
            "Вы действительно хотите удалить эту позицию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM products WHERE id = %s", (self.product_id,))
            self.accept()
