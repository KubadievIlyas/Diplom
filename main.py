import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QDialog, QLabel, QProgressBar, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QTimer

from auth import AuthDialog

from ui.tab_products import ProductTab
from ui.tab_calculator import CalculatorTab
from ui.tab_employees import EmployeeTab
from ui.tab_settings import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.setWindowTitle("Coffee Shop Manager")
        self.resize(1500, 800)
        self.setWindowIcon(QIcon("assets/icon.png"))

        tabs = QTabWidget()
        tabs.addTab(ProductTab(), "📦 Продукты")
        tabs.addTab(CalculatorTab(), "💰 Калькулятор")
        tabs.addTab(EmployeeTab(), "👨‍💼 Сотрудники")
        tabs.addTab(SettingsTab(user_id=user_id), "⚙️ Настройки")  # <-- передаём user_id
        self.setCentralWidget(tabs)



class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Загрузка")
        self.setFixedSize(400, 150)

        layout = QVBoxLayout(self)

        self.title_label = QLabel("Загрузка приложения...", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def update_progress(self, value):
        self.progress_bar.setValue(value)


def main():
    app = QApplication(sys.argv)

    try:
        with open("assets/style.css", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("⚠️ Файл стилей не найден: assets/style.css")

    auth_dialog = AuthDialog()
    if auth_dialog.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    user_id = auth_dialog.user_id  # <-- получаем id авторизованного пользователя

    splash = SplashScreen()
    splash.show()

    window = MainWindow(user_id=user_id)  # <-- передаём в MainWindow

    progress = 0

    def update_splash():
        nonlocal progress
        progress += 5
        splash.update_progress(progress)
        if progress >= 100:
            splash.close()
            window.show()
        else:
            QTimer.singleShot(100, update_splash)

    QTimer.singleShot(100, update_splash)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
