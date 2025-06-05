from PyQt6.QtWidgets import (
    QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QDialog, QApplication
)
from database.db import Database  # путь к вашему классу Database
from ui.tab_settings import SettingsTab  # импорт вкладки настроек

class AuthDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.setFixedSize(300, 250)
        self.user_id = None  # ← Храним id пользователя после авторизации
        self.init_ui()

        try:
            self.db = Database()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка подключения", f"Не удалось подключиться к базе:\n{e}")
            self.db = None
            self.reject()

    def init_ui(self):
        layout = QVBoxLayout()

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.check_credentials)

        self.change_pass_button = QPushButton("Сменить пароль")
        self.change_pass_button.clicked.connect(self.change_password_dialog)

        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.login_input)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.change_pass_button)

        self.setLayout(layout)

    def check_credentials(self):
        if self.db is None:
            QMessageBox.critical(self, "Ошибка", "Нет подключения к базе данных.")
            return

        login = self.login_input.text().strip()
        password = self.password_input.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль.")
            return

        user = self.db.fetch_one("SELECT * FROM employees WHERE login = %s", (login,))
        if user is None:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден.")
            return

        stored_password = user['password']
        if password == stored_password:
            self.user_id = user['id']  # ← Сохраняем ID пользователя
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный пароль.")

    def change_password_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Сменить пароль")
        dialog.setFixedSize(300, 270)

        layout = QVBoxLayout()

        old_pass_input = QLineEdit()
        old_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        old_pass_input.setPlaceholderText("Старый пароль")

        new_pass_input = QLineEdit()
        new_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        new_pass_input.setPlaceholderText("Новый пароль")

        confirm_pass_input = QLineEdit()
        confirm_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_pass_input.setPlaceholderText("Подтвердите новый пароль")

        confirm_button = QPushButton("Обновить пароль")

        def update_password():
            login = self.login_input.text().strip()
            old_password = old_pass_input.text().strip()
            new_password = new_pass_input.text().strip()
            confirm_password = confirm_pass_input.text().strip()

            if not login:
                QMessageBox.warning(dialog, "Ошибка", "Введите логин в основном окне.")
                return

            user = self.db.fetch_one("SELECT * FROM employees WHERE login = %s", (login,))
            if user is None:
                QMessageBox.warning(dialog, "Ошибка", "Пользователь не найден.")
                return

            stored_password = user['password']
            if old_password != stored_password:
                QMessageBox.warning(dialog, "Ошибка", "Старый пароль неверен.")
                return

            if new_password != confirm_password:
                QMessageBox.warning(dialog, "Ошибка", "Новые пароли не совпадают.")
                return

            if len(new_password) < 4:
                QMessageBox.warning(dialog, "Ошибка", "Пароль должен содержать минимум 4 символа.")
                return

            try:
                self.db.execute("UPDATE employees SET password = %s WHERE login = %s", (new_password, login))
                QMessageBox.information(dialog, "Успех", "Пароль успешно обновлён.")
                dialog.accept()
            except Exception as err:
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить пароль:\n{err}")

        confirm_button.clicked.connect(update_password)

        layout.addWidget(QLabel("Введите старый пароль:"))
        layout.addWidget(old_pass_input)
        layout.addWidget(QLabel("Новый пароль:"))
        layout.addWidget(new_pass_input)
        layout.addWidget(QLabel("Подтверждение пароля:"))
        layout.addWidget(confirm_pass_input)
        layout.addWidget(confirm_button)

        dialog.setLayout(layout)
        dialog.exec()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    dlg = AuthDialog()
    if dlg.exec() == QDialog.DialogCode.Accepted:
        user_id = dlg.user_id
        if user_id:
            settings_tab = SettingsTab(user_id=user_id)
            settings_tab.show()
            sys.exit(app.exec())
        else:
            QMessageBox.critical(None, "Ошибка", "Не удалось определить ID пользователя.")
    else:
        print("Авторизация отменена или неудачна.")
    sys.exit(0)
