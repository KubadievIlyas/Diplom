import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QSplashScreen, QLabel, QProgressBar, QVBoxLayout, \
    QWidget
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QTimer

from ui.tab_products import ProductTab
from ui.tab_calculator import CalculatorTab
from ui.tab_employees import EmployeeTab
from ui.tab_settings import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coffee Shop Manager")
        self.resize(1500, 800)
        self.setWindowIcon(QIcon("assets/icon.png"))

        # Вкладки
        tabs = QTabWidget()
        tabs.addTab(ProductTab(), "📦 Продукты")
        tabs.addTab(CalculatorTab(), "💰 Калькулятор")
        tabs.addTab(EmployeeTab(), "👨‍💼 Сотрудники")
        tabs.addTab(SettingsTab(), "⚙️ Настройки")
        self.setCentralWidget(tabs)


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()

        # Настроим размеры окна загрузки
        self.setWindowTitle("Загрузка")
        self.setFixedSize(400, 150)

        # Создаем вертикальный layout
        layout = QVBoxLayout(self)

        # Заголовок
        self.title_label = QLabel("Загрузка приложения...", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Прогресс-бар
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Устанавливаем layout для окна
        self.setLayout(layout)

    def update_progress(self, value):
        """Обновляет значение прогресса на баре"""
        self.progress_bar.setValue(value)
        if value == 100:
            self.close()  # Закрыть экран загрузки, когда прогресс завершен.


def main():
    app = QApplication(sys.argv)

    # Загружаем изображение для экрана загрузки
    splash = SplashScreen()
    splash.show()

    # Подключение стилей
    try:
        with open("assets/style.css", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("⚠️ Файл стилей не найден: assets/style.css")

    # Инициализация основного окна
    window = MainWindow()

    # Таймер для обновления прогресса
    progress = 0

    def update_splash():
        nonlocal progress
        progress += 5
        splash.update_progress(progress)
        if progress >= 100:
            window.show()  # Показываем основное окно
        else:
            QTimer.singleShot(100, update_splash)  # Через 100 мс обновляем прогресс

    # Запускаем обновление прогресса
    QTimer.singleShot(100, update_splash)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
