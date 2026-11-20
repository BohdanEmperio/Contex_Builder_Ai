import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QPlainTextEdit,
    QFileDialog, QMessageBox, QGridLayout,
)
from core.models import ScanResult, ExportConfig, AI_MODEL_PRESETS
from core.scanner import ProjectScanner
from core.exporter import ReportExporter
from ui.worker import TaskWorker


class ScanTab(QWidget):
    def __init__(self, get_settings_fn):
        super().__init__()
        self.get_settings_fn = get_settings_fn
        self.current_scan: ScanResult | None = None
        self.worker: TaskWorker | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("📁 Сканирование и запись")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # --- Группа Источник ---
        src_group = QGroupBox("Источник")
        src_layout = QVBoxLayout(src_group)

        path_row = QHBoxLayout()
        self.src_input = QLineEdit()
        self.src_input.setPlaceholderText("Путь к директории для сканирования...")
        self.src_browse_btn = QPushButton("Обзор")
        self.src_browse_btn.setObjectName("BlueBtn")
        self.src_browse_btn.clicked.connect(self._choose_source_dir)
        path_row.addWidget(self.src_input, 1)
        path_row.addWidget(self.src_browse_btn)

        self.scan_btn = QPushButton("🔍 Сканировать")
        self.scan_btn.setObjectName("BlueBtn")
        self.scan_btn.clicked.connect(self._start_scan)

        src_layout.addLayout(path_row)
        src_layout.addWidget(self.scan_btn)
        layout.addWidget(src_group)

        # --- Блок анализа объёма и токенов ---
        self.analysis_label = QLabel(
            "Анализ объёма: выполните сканирование для расчёта размера и токенов ИИ (Gemini / GPT)."
        )
        self.analysis_label.setObjectName("TokenInfoBox")
        self.analysis_label.setWordWrap(True)
        layout.addWidget(self.analysis_label)

        # --- Группа Экспорт ---
        exp_group = QGroupBox("Экспорт")
        exp_layout = QVBoxLayout(exp_group)

        grid = QGridLayout()
        grid.addWidget(QLabel("Имя файла:"), 0, 0)
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("Автоматическое имя с датой")
        grid.addWidget(self.filename_input, 0, 1)

        grid.addWidget(QLabel("Формат:"), 1, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["txt", "md"])
        grid.addWidget(self.format_combo, 1, 1)

        grid.addWidget(QLabel("Лимит ИИ (часть):"), 2, 0)
        self.ai_limit_combo = QComboBox()
        for name in AI_MODEL_PRESETS:
            self.ai_limit_combo.addItem(name)
        self.ai_limit_combo.currentIndexChanged.connect(self._update_analysis_banner)
        grid.addWidget(self.ai_limit_combo, 2, 1)

        exp_layout.addLayout(grid)

        out_row = QHBoxLayout()
        self.out_input = QLineEdit()
        self.out_input.setPlaceholderText("Директория для сохранения (по умолчанию — сканируемая)...")
        self.out_browse_btn = QPushButton("Обзор")
        self.out_browse_btn.setObjectName("BlueBtn")
        self.out_browse_btn.clicked.connect(self._choose_output_dir)
        out_row.addWidget(self.out_input, 1)
        out_row.addWidget(self.out_browse_btn)
        exp_layout.addLayout(out_row)

        chk_row = QHBoxLayout()
        self.tree_chk = QCheckBox("Включить дерево структуры")
        self.tree_chk.setChecked(True)
        self.censor_chk = QCheckBox("Цензура данных")
        chk_row.addWidget(self.tree_chk)
        chk_row.addWidget(self.censor_chk)
        chk_row.addStretch()
        exp_layout.addLayout(chk_row)

        self.export_btn = QPushButton("💾 Создать отчёт")
        self.export_btn.setObjectName("GreenBtn")
        self.export_btn.clicked.connect(self._create_report)
        exp_layout.addWidget(self.export_btn)

        layout.addWidget(exp_group)

        # --- Лог операций ---
        self.log_box = QPlainTextEdit()
        self.log_box.setObjectName("LogBox")
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Лог операций...")
        layout.addWidget(self.log_box, 1)

    def log(self, text: str):
        self.log_box.appendPlainText(text)

    def _choose_source_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите директорию для сканирования")
        if d:
            self.src_input.setText(d)

    def _choose_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите директорию для сохранения отчёта")
        if d:
            self.out_input.setText(d)

    def _get_selected_limit(self) -> tuple[str, int]:
        preset_name = self.ai_limit_combo.currentText()
        settings_limit = self.get_settings_fn().get("custom_token_limit", 0)
        if settings_limit > 0:
            return f"Пользовательский лимит ({settings_limit:,})", settings_limit
        return preset_name, AI_MODEL_PRESETS.get(preset_name, 100_000)

    def _start_scan(self):
        root_dir = self.src_input.text().strip()
        if not root_dir or not os.path.isdir(root_dir):
            QMessageBox.warning(self, "Ошибка", "Укажите существующую директорию для сканирования.")
            return

        settings = self.get_settings_fn()
        scanner = ProjectScanner(
            ignore_dirs=settings.get("ignore_dirs"),
            ignore_exts=settings.get("ignore_exts"),
        )
        self.scan_btn.setEnabled(False)
        self.log(f"[*] Запуск сканирования: {root_dir}")

        self.worker = TaskWorker(scanner.scan_directory, root_dir)
        self.worker.finished_ok.connect(self._on_scan_finished)
        self.worker.failed.connect(self._on_worker_error)
        self.worker.start()

    def _on_scan_finished(self, result: ScanResult):
        self.scan_btn.setEnabled(True)
        self.current_scan = result
        self._update_analysis_banner()
        self.log(
            f"[+] Сканирование завершено: файлов={len(result.files)}, "
            f"пропущено={len(result.skipped_files)}, "
            f"размер={result.total_bytes / 1024:.1f} КБ, "
            f"токенов ~{result.total_tokens_gemini:,} (Gemini) / {result.total_tokens_gpt:,} (GPT)"
        )

    def _on_worker_error(self, msg: str):
        self.scan_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.log(f"[!] Ошибка: {msg}")
        QMessageBox.critical(self, "Ошибка", msg)

    def _update_analysis_banner(self):
        if not self.current_scan:
            return
        res = self.current_scan
        _, limit = self._get_selected_limit()
        est_parts = ReportExporter.estimate_parts_count(res, limit)
        size_kb = res.total_bytes / 1024.0

        if est_parts > 1:
            status = (
                f"<span style='color:#f38ba8; font-weight:bold;'>"
                f"ПРЕВЫШЕНИЕ ЛИМИТА ({limit:,} токенов)! Отчёт будет разделён на ~{est_parts} частей.</span>"
            )
        else:
            status = (
                f"<span style='color:#a6e3a1; font-weight:bold;'>"
                f"Вмещается в 1 файл (лимит: {limit:,} токенов).</span>"
            )

        self.analysis_label.setText(
            f"<b>Файлов:</b> {len(res.files)} | <b>Строк:</b> {res.total_lines:,} | "
            f"<b>Объём:</b> {size_kb:.1f} КБ ({res.total_chars:,} симв.)<br>"
            f"<b>Токены ИИ:</b> ~{res.total_tokens_gemini:,} (Gemini) | "
            f"{res.total_tokens_gpt:,} (GPT cl100k)<br>"
            f"{status}"
        )

    def _create_report(self):
        if not self.current_scan:
            QMessageBox.warning(self, "Нет данных", "Сначала выполните сканирование директории.")
            return
        if not self.current_scan.files:
            QMessageBox.warning(self, "Пусто", "Не найдено текстовых файлов для отчёта.")
            return

        preset_name, limit = self._get_selected_limit()
        est_parts = ReportExporter.estimate_parts_count(self.current_scan, limit)
        out_dir = self.out_input.text().strip() or self.current_scan.root_dir

        if est_parts > 1:
            reply = QMessageBox.question(
                self,
                "Превышение лимита токенов ИИ",
                f"Объём проекта (~{self.current_scan.total_tokens_gemini:,} токенов Gemini / "
                f"{self.current_scan.total_tokens_gpt:,} GPT) превышает лимит {limit:,} токенов.\n\n"
                f"Отчёт будет автоматически разделён на ~{est_parts} частей.\n"
                f"Выбрать папку для сохранения частей отчёта?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                chosen = QFileDialog.getExistingDirectory(
                    self, "Выберите директорию для сохранения частей отчёта", out_dir
                )
                if not chosen:
                    return
                out_dir = chosen
                self.out_input.setText(out_dir)

        cfg = ExportConfig(
            output_dir=out_dir,
            filename_base=self.filename_input.text().strip(),
            fmt=self.format_combo.currentText(),
            include_tree=self.tree_chk.isChecked(),
            censor_data=self.censor_chk.isChecked(),
            max_tokens_per_part=limit,
            ai_target_name=preset_name,
            save_session=True,
        )

        self.export_btn.setEnabled(False)
        self.log(f"[*] Формирование отчёта в: {out_dir}")
        self.worker = TaskWorker(ReportExporter.export_report, self.current_scan, cfg)
        self.worker.finished_ok.connect(self._on_export_finished)
        self.worker.failed.connect(self._on_worker_error)
        self.worker.start()

    def _on_export_finished(self, result):
        self.export_btn.setEnabled(True)
        created_files, total_parts = result
        self.log(f"[+] Готово! Создано файлов: {total_parts}")
        for p in created_files:
            self.log(f"    -> {p}")
        QMessageBox.information(
            self,
            "Отчёт создан",
            f"Успешно сформировано частей: {total_parts}.\n"
            f"Папка: {os.path.dirname(created_files[0])}",
        )