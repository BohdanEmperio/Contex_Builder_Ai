from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget,
)
from ui.tabs.scan_tab import ScanTab
from ui.tabs.convert_tab import ConvertTab
from ui.tabs.delete_tab import DeleteTab
from ui.tabs.files_tab import FilesTab
from ui.tabs.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Context Builder AI")
        self.resize(980, 780)
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(6)

        self.settings_tab = SettingsTab()
        self.scan_tab = ScanTab(self.settings_tab.get_settings)
        self.convert_tab = ConvertTab(self.settings_tab.get_settings)
        self.delete_tab = DeleteTab()
        self.files_tab = FilesTab(self.settings_tab.get_settings)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.scan_tab)
        self.stack.addWidget(self.convert_tab)
        self.stack.addWidget(self.delete_tab)
        self.stack.addWidget(self.files_tab)
        self.stack.addWidget(self.settings_tab)

        nav_items = [
            ("📁 Сканирование", 0),
            ("🔄 Конвертация", 1),
            ("🗑 Удаление", 2),
            ("🔍 Файлы", 3),
            ("⚙ Настройки", 4),
        ]

        self.nav_buttons: list[QPushButton] = []
        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("NavBtn")
            btn.clicked.connect(lambda _=False, i=idx: self._switch_tab(i))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        nav_layout.addStretch()
        root_layout.addLayout(nav_layout)
        root_layout.addWidget(self.stack, 1)

        self._switch_tab(0)

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)