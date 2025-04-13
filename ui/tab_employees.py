from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class EmployeeTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel("Управление сотрудниками и сменами")
        layout.addWidget(label)
