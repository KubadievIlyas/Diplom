from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout,
    QLineEdit, QComboBox, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from database.db import Database
from ui.dialogs.edit_product_dialog import EditProductDialog
from ui.dialogs.add_category_dialog import AddCategoryDialog


class ProductTab(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_product = None
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        self.resize(1000, 600)

        # Левая панель с фильтрами и кнопками
        filter_layout = QVBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по названию...")

        self.category_filter = QComboBox()
        self.category_filter.addItem("Все категории")

        self.load_categories()

        self.search_input.textChanged.connect(self.update_product_list)
        self.category_filter.currentIndexChanged.connect(self.update_product_list)

        filter_layout.addWidget(QLabel("Поиск"))
        filter_layout.addWidget(self.search_input)

        filter_layout.addWidget(QLabel("Фильтр по категории"))
        filter_layout.addWidget(self.category_filter)

        # Кнопка добавления новой позиции
        add_btn = QPushButton("➕ Добавить позицию")
        add_btn.clicked.connect(self.add_product)
        filter_layout.addWidget(add_btn)

        # Кнопка добавления новой категории
        add_cat_btn = QPushButton("📂 Добавить категорию")
        add_cat_btn.clicked.connect(self.add_category)
        filter_layout.addWidget(add_cat_btn)

        # Кнопка обновления
        update_btn = QPushButton("🔄 Обновить")
        update_btn.clicked.connect(self.update_product_list)
        filter_layout.addWidget(update_btn)

        filter_layout.addStretch()
        main_layout.addLayout(filter_layout, 1)

        # Правая часть с карточками товаров
        self.product_area = QScrollArea()
        self.product_area.setWidgetResizable(True)
        self.product_container = QWidget()
        self.grid = QGridLayout(self.product_container)
        self.grid.setSpacing(20)
        self.product_area.setWidget(self.product_container)

        main_layout.addWidget(self.product_area, 4)

        self.update_product_list()

    def load_categories(self):
        self.category_filter.clear()
        self.category_filter.addItem("Все категории")
        categories = self.db.fetch_all("SELECT id, name FROM categories")
        for cat in categories:
            self.category_filter.addItem(cat['name'], cat['id'])

    def update_product_list(self):
        search = self.search_input.text().strip()
        category = self.category_filter.currentData()

        query = """
            SELECT p.*, u.name AS unit_name, c.name AS category_name 
            FROM products p 
            LEFT JOIN units u ON p.unit_id = u.id 
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 1
        """
        params = []

        if category and self.category_filter.currentIndex() != 0:
            query += " AND p.category_id = %s"
            params.append(category)

        if search:
            query += " AND p.name LIKE %s"
            params.append(f"%{search}%")

        products = self.db.fetch_all(query, params)

        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for i, prod in enumerate(products):
            self.grid.addWidget(self.create_product_card(prod), i // 3, i % 3)

    def create_product_card(self, product):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Фото
        if product['photo']:
            pixmap = QPixmap()
            pixmap.loadFromData(product['photo'])
            scaled = pixmap.scaledToWidth(150, Qt.TransformationMode.FastTransformation)
            img_label = QLabel()
            img_label.setPixmap(scaled)
            layout.addWidget(img_label)
        else:
            layout.addWidget(QLabel("Нет фото"))

        # Информация
        layout.addWidget(QLabel(f"<b>{product['name']}</b>"))
        layout.addWidget(QLabel(f"Категория: {product['category_name']}"))
        layout.addWidget(QLabel(f"Цена: {product['price']} ₽"))

        if product['weight_or_volume'] and product['unit_name']:
            layout.addWidget(QLabel(f"Объём/Вес: {product['weight_or_volume']} {product['unit_name']}"))

        if product['description']:
            layout.addWidget(QLabel(f"<i>{product['description']}</i>"))

        # Кнопка редактирования
        edit_btn = QPushButton("✏️ Редактировать")
        edit_btn.clicked.connect(lambda: self.edit_product(product['id']))
        layout.addWidget(edit_btn)

        return widget

    def edit_product(self, product_id):
        dialog = EditProductDialog(self.db, product_id, self)
        result = dialog.exec()
        if result:
            self.update_product_list()

    def add_product(self):
        dialog = EditProductDialog(self.db, parent=self)
        if dialog.exec():
            self.update_product_list()

    def add_category(self):
        dialog = AddCategoryDialog(self.db, self)
        if dialog.exec():
            self.load_categories()
            self.update_product_list()
