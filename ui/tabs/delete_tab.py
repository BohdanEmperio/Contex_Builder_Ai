import os
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QCheckBox, QPlainTextEdit, QFileDialog, QMessageBox,
    QAbstractItemView,
)
from core.exporter import ReportExporter


class DeleteTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("🗑 Удаление записей")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        dir_group = QGroupBox("Директория")
        dir_layout = QVBoxLayout(dir_group)

        row = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Директория с отчётами...")
        browse_btn = QPushButton("Обзор")
        browse_btn.setObjectName("BlueBtn")
        browse_btn.clicked.connect(self._browse)
        row.addWidget(self.dir_input, 1)
        row.addWidget(browse_btn)

        find_btn = QPushButton("🔍 Найти отчёты")
        find_btn.setObjectName("BlueBtn")
        find_btn.clicked.connect(self._find_reports)

        dir_layout.addLayout(row)
        dir_layout.addWidget(find_btn)
        layout.addWidget(dir_group)

        files_group = QGroupBox("Найденные файлы")
        files_layout = QVBoxLayout(files_group)

        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        files_layout.addWidget(self.files_list)

        self.del_session_chk = QCheckBox(
            f"Также удалить данные сессии ({ReportExporter.SESSION_DIR_NAME})"
        )
        files_layout.addWidget(self.del_session_chk)

        del_btn = QPushButton("🗑 Удалить выбранные")
        del_btn.setObjectName("RedBtn")
        del_btn.clicked.connect(self._delete_selected)
        files_layout.addWidget(del_btn)

        layout.addWidget(files_group, 1)

        self.log_box = QPlainTextEdit()
        self.log_box.setObjectName("LogBox")
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Лог операций...")
        layout.addWidget(self.log_box)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите директорию с отчётами")
        if d:
            self.dir_input.setText(d)

    def _find_reports(self):
        d = self.dir_input.text().strip()
        if not d or not os.path.isdir(d):
            QMessageBox.warning(self, "Ошибка", "Укажите существующую директорию.")
            return
        self.files_list.clear()
        found = 0
        for name in sorted(os.listdir(d)):
            if name.endswith((".txt", ".md")):
                full = os.path.join(d, name)
                if os.path.isfile(full):
                    self.files_list.addItem(QListWidgetItem(full))
                    found += 1
        self.log_box.appendPlainText(f"[*] Найдено файлов отчётов: {found}")

    def _delete_selected(self):
        selected = self.files_list.selectedItems()
        base_dir = self.dir_input.text().strip()
        if not selected and not self.del_session_chk.isChecked():
            QMessageBox.information(self, "Не выбрано", "Выберите файлы для удаления.")
            return

        for item in selected:
            path = item.text()
            try:
                os.remove(path)
                self.log_box.appendPlainText(f"[-] Удалён файл: {path}")
            except OSError as exc:
                self.log_box.appendPlainText(f"[!] Ошибка удаления {path}: {exc}")

        if self.del_session_chk.isChecked() and base_dir:
            s_dir = os.path.join(base_dir, ReportExporter.SESSION_DIR_NAME)
            if os.path.isdir(s_dir):
                shutil.rmtree(s_dir, ignore_errors=True)
                self.log_box.appendPlainText(f"[-] Удалена папка сессии: {s_dir}")

        self._find_reports()