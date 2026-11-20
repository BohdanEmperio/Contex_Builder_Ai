import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QComboBox, QCheckBox, QPlainTextEdit, QFileDialog,
    QMessageBox, QGridLayout, QAbstractItemView,
)
from core.models import ExportConfig, AI_MODEL_PRESETS
from core.scanner import ProjectScanner
from core.exporter import ReportExporter


class FilesTab(QWidget):
    def __init__(self, get_settings_fn):
        super().__init__()
        self.get_settings_fn = get_settings_fn
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("🔍 Выбор файлов")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        src_group = QGroupBox("Источник")
        src_layout = QVBoxLayout(src_group)

        row1 = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Директория для поиска файлов...")
        browse_btn = QPushButton("Обзор")
        browse_btn.setObjectName("BlueBtn")
        browse_btn.clicked.connect(self._browse_src)
        row1.addWidget(self.dir_input, 1)
        row1.addWidget(browse_btn)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Фильтр:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Расширения: .py, .js или часть имени")
        find_btn = QPushButton("🔍 Найти")
        find_btn.setObjectName("BlueBtn")
        find_btn.clicked.connect(self._find_files)
        row2.addWidget(self.filter_input, 1)
        row2.addWidget(find_btn)

        src_layout.addLayout(row1)
        src_layout.addLayout(row2)
        layout.addWidget(src_group)

        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        layout.addWidget(self.files_list, 1)

        exp_group = QGroupBox("Экспорт выбранных")
        exp_layout = QVBoxLayout(exp_group)

        grid = QGridLayout()
        grid.addWidget(QLabel("Имя файла:"), 0, 0)
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("Автоматическое имя с датой")
        grid.addWidget(self.filename_input, 0, 1)

        grid.addWidget(QLabel("Формат:"), 1, 0)
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["txt", "md"])
        grid.addWidget(self.fmt_combo, 1, 1)
        exp_layout.addLayout(grid)

        out_row = QHBoxLayout()
        self.out_input = QLineEdit()
        self.out_input.setPlaceholderText("Директория для сохранения...")
        out_browse = QPushButton("Обзор")
        out_browse.setObjectName("BlueBtn")
        out_browse.clicked.connect(self._browse_out)
        out_row.addWidget(self.out_input, 1)
        out_row.addWidget(out_browse)
        exp_layout.addLayout(out_row)

        self.tree_chk = QCheckBox("Включить дерево структуры")
        self.tree_chk.setChecked(True)
        exp_layout.addWidget(self.tree_chk)

        export_btn = QPushButton("💾 Создать отчёт")
        export_btn.setObjectName("GreenBtn")
        export_btn.clicked.connect(self._export_selected)
        exp_layout.addWidget(export_btn)

        layout.addWidget(exp_group)

        self.log_box = QPlainTextEdit()
        self.log_box.setObjectName("LogBox")
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(85)
        layout.addWidget(self.log_box)

    def _browse_src(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите директорию")
        if d:
            self.dir_input.setText(d)

    def _browse_out(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите директорию сохранения")
        if d:
            self.out_input.setText(d)

    def _find_files(self):
        d = self.dir_input.text().strip()
        if not d or not os.path.isdir(d):
            QMessageBox.warning(self, "Ошибка", "Укажите существующую директорию.")
            return
        settings = self.get_settings_fn()
        scanner = ProjectScanner(
            ignore_dirs=settings.get("ignore_dirs"),
            ignore_exts=settings.get("ignore_exts"),
        )
        matches = scanner.find_matching_files(d, self.filter_input.text().strip())
        self.files_list.clear()
        for rel in matches:
            self.files_list.addItem(QListWidgetItem(rel))
        self.log_box.appendPlainText(f"[*] Найдено файлов: {len(matches)}")

    def _export_selected(self):
        d = self.dir_input.text().strip()
        selected = {item.text() for item in self.files_list.selectedItems()}
        if not d or not selected:
            QMessageBox.warning(self, "Не выбрано", "Выберите хотя бы один файл в списке.")
            return

        settings = self.get_settings_fn()
        scanner = ProjectScanner(
            ignore_dirs=settings.get("ignore_dirs"),
            ignore_exts=settings.get("ignore_exts"),
        )
        scan_res = scanner.scan_directory(d, selected_rel_paths=selected)

        limit = settings.get("custom_token_limit") or AI_MODEL_PRESETS[
            "Gemini (безопасный чанк чата — 100 000 токенов)"
        ]
        out_dir = self.out_input.text().strip() or d
        est_parts = ReportExporter.estimate_parts_count(scan_res, limit)
        if est_parts > 1:
            chosen = QFileDialog.getExistingDirectory(
                self,
                f"Выбранные файлы превышают лимит ({est_parts} частей). Куда сохранить?",
                out_dir,
            )
            if not chosen:
                return
            out_dir = chosen
            self.out_input.setText(out_dir)

        cfg = ExportConfig(
            output_dir=out_dir,
            filename_base=self.filename_input.text().strip(),
            fmt=self.fmt_combo.currentText(),
            include_tree=self.tree_chk.isChecked(),
            censor_data=False,
            max_tokens_per_part=limit,
            ai_target_name="Выборочный экспорт",
            save_session=False,
        )
        try:
            created, total_parts = ReportExporter.export_report(scan_res, cfg)
            self.log_box.appendPlainText(
                f"[+] Экспорт ({total_parts} ч.), токены: ~{scan_res.total_tokens_gemini:,} Gemini / {scan_res.total_tokens_gpt:,} GPT"
            )
            for p in created:
                self.log_box.appendPlainText(f"    -> {p}")
            QMessageBox.information(self, "Готово", f"Создано файлов: {total_parts}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка экспорта", str(exc))