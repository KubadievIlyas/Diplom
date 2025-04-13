from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox


class AddCategoryDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Добавить категорию")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Наименование категории:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_category)
        layout.addWidget(save_btn)

    def save_category(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название категории.")
            return

        self.db.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
        self.accept()
