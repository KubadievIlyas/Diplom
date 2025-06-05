import os
import pymysql
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QDateEdit, QFileDialog, QFormLayout
)
from PyQt6.QtCore import QDate, Qt, QBuffer, QIODevice, QByteArray
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath

# === Класс Database ===
class Database:
    def __init__(self):
        try:
            self.conn = pymysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="",
                database="coffee_shop",
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.conn.cursor()
            print("[DB] Подключение успешно.")
        except Exception as e:
            print(f"[DB] Ошибка подключения: {e}")
            self.conn = None

    def is_connected(self):
        return self.conn is not None

    def fetch_one(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()

# === Вспомогательная функция ===
def rounded_pixmap(pixmap, size=180):
    scaled = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                           Qt.TransformationMode.SmoothTransformation)
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()
    return result

# === Основной класс ===
class SettingsTab(QWidget):
    def __init__(self, user_id=None):
        super().__init__()
        self.user_id = user_id
        self.avatar_pixmap = None

        self.db = Database()
        if not self.db.is_connected():
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к базе данных.")
            return

        self.init_ui()

        if self.user_id:
            self.load_user_data()
            self.adjust_size_and_layout()

    def init_ui(self):
        self.setMinimumSize(700, 400)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(180, 180)
        self.avatar_label.setStyleSheet("""
            QLabel {
                border-radius: 90px; 
                background-color: #ddd; 
                border: 2px solid #bbb;
            }
        """)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setText("Нет фото")

        self.btn_upload_avatar = QPushButton("Загрузить фото")
        self.btn_upload_avatar.setFixedWidth(180)
        self.btn_upload_avatar.clicked.connect(self.upload_avatar)

        avatar_layout = QVBoxLayout()
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_layout.setSpacing(10)
        avatar_layout.addWidget(self.avatar_label)
        avatar_layout.addWidget(self.btn_upload_avatar)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignCenter)

        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()

        self.birth_date_input = QDateEdit()
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDisplayFormat("yyyy-MM-dd")
        self.birth_date_input.setDate(QDate.currentDate())

        self.status_input = QLineEdit()
        self.login_display = QLabel()
        self.login_display.setStyleSheet("font-weight: bold; color: #555;")

        form_layout.addRow("Имя:", self.first_name_input)
        form_layout.addRow("Фамилия:", self.last_name_input)
        form_layout.addRow("Дата рождения:", self.birth_date_input)
        form_layout.addRow("Статус:", self.status_input)
        form_layout.addRow("Логин:", self.login_display)

        self.save_btn = QPushButton("Сохранить изменения")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.save_btn.clicked.connect(self.save_user_data)

        self.change_pass_btn = QPushButton("Сменить пароль")
        self.change_pass_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.change_pass_btn)

        main_layout = QHBoxLayout()
        main_layout.addLayout(avatar_layout, 1)
        main_layout.addLayout(form_layout, 2)

        layout.addLayout(main_layout)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def adjust_size_and_layout(self):
        self.adjustSize()
        self.setMinimumSize(self.size())

    def load_user_data(self):
        try:
            user = self.db.fetch_one("SELECT * FROM employees WHERE id = %s", (self.user_id,))
            if not user:
                QMessageBox.warning(self, "Ошибка", "Пользователь не найден.")
                return

            self.first_name_input.setText(user.get('first_name', ''))
            self.last_name_input.setText(user.get('last_name', ''))
            self.status_input.setText(user.get('status', ''))
            self.login_display.setText(user.get('login', ''))

            birth_date = user.get('birth_date')
            if birth_date:
                qdate = QDate.fromString(str(birth_date), "yyyy-MM-dd")
                if qdate.isValid():
                    self.birth_date_input.setDate(qdate)

            photo_data = user.get('photo_path')
            if photo_data:
                image = QImage()
                image.loadFromData(photo_data)
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)
                    self.avatar_pixmap = pixmap
                    self.set_avatar(pixmap)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных:\n{e}")

    def save_user_data(self):
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        birth_date = self.birth_date_input.date().toString("yyyy-MM-dd")
        status = self.status_input.text().strip()

        if not first_name or not last_name:
            QMessageBox.warning(self, "Ошибка", "Имя и фамилия обязательны.")
            return

        try:
            photo_data = None
            if self.avatar_pixmap and not self.avatar_pixmap.isNull():
                image = self.avatar_pixmap.toImage()
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                image.save(buffer, "PNG")
                photo_data = byte_array.data()

            self.db.execute("""
                UPDATE employees 
                SET first_name = %s, last_name = %s, birth_date = %s, status = %s, photo_path = %s 
                WHERE id = %s
            """, (first_name, last_name, birth_date, status, photo_data, self.user_id))

            QMessageBox.information(self, "Готово", "Изменения сохранены.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения:\n{e}")

    def upload_avatar(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "", "Изображения (*.png *.jpg *.jpeg *.bmp)"
        )
        if not fname:
            return

        pixmap = QPixmap(fname)
        if pixmap.isNull():
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение.")
            return

        self.avatar_pixmap = pixmap
        self.set_avatar(pixmap)

    def set_avatar(self, pixmap):
        rounded = rounded_pixmap(pixmap, 180)
        self.avatar_label.setPixmap(rounded)

