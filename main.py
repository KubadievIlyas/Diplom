import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtGui import QIcon
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

def main():
    app = QApplication(sys.argv)

    # Подключение стилей
    try:
        with open("assets/style.css", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("⚠️ Файл стилей не найден: assets/style.css")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
