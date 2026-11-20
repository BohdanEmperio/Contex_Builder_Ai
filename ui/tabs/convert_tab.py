import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QPlainTextEdit,
    QFileDialog, QMessageBox, QGridLayout,
)
from core.models import ScanResult, ExportConfig, AI_MODEL_PRESETS
from core.exporter import ReportExporter


class ConvertTab(QWidget):
    def __init__(self, get_settings_fn):
        super().__init__()
        self.get_settings_fn = get_settings_fn
        self.loaded_session: ScanResult | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("🔄 Конвертация")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # --- Источник сессии ---
        src_group = QGroupBox("Источник сессии")
        src_layout = QVBoxLayout(src_group)

        row = QHBoxLayout()
        self.session_dir_input = QLineEdit()
        self.session_dir_input.setPlaceholderText("Директория с сохранённой сессией...")
        browse_btn = QPushButton("Обзор")
        browse_btn.setObjectName("BlueBtn")
        browse_btn.clicked.connect(self._browse_session)
        row.addWidget(self.session_dir_input, 1)
        row.addWidget(browse_btn)

        load_btn = QPushButton("📁 Загрузить сессию")
        load_btn.setObjectName("BlueBtn")
        load_btn.clicked.connect(self._load_session)

        src_layout.addLayout(row)
        src_layout.addWidget(load_btn)
        layout.addWidget(src_group)

        # --- Параметры конвертации ---
        param_group = QGroupBox("Параметры конвертации")
        param_layout = QVBoxLayout(param_group)

        grid = QGridLayout()
        grid.addWidget(QLabel("Целевой формат:"), 0, 0)
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["txt", "md"])
        grid.addWidget(self.fmt_combo, 0, 1)

        grid.addWidget(QLabel("Имя файла:"), 1, 0)
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("Автоматическое имя с датой")
        grid.addWidget(self.filename_input, 1, 1)

        grid.addWidget(QLabel("Лимит ИИ (часть):"), 2, 0)
        self.ai_limit_combo = QComboBox()
        for name in AI_MODEL_PRESETS:
            self.ai_limit_combo.addItem(name)
        grid.addWidget(self.ai_limit_combo, 2, 1)
        param_layout.addLayout(grid)

        out_row = QHBoxLayout()
        self.out_dir_input = QLineEdit()
        self.out_dir_input.setPlaceholderText("Директория для сохранения...")
        out_browse = QPushButton("Обзор")
        out_browse.setObjectName("BlueBtn")
        out_browse.clicked.connect(self._browse_out)
        out_row.addWidget(self.out_dir_input, 1)
        out_row.addWidget(out_browse)
        param_layout.addLayout(out_row)

        self.tree_chk = QCheckBox("Включить дерево структуры")
        self.tree_chk.setChecked(True)
        param_layout.addWidget(self.tree_chk)

        conv_btn = QPushButton("🔄 Конвертировать")
        conv_btn.setObjectName("GreenBtn")
        conv_btn.clicked.connect(self._convert)
        param_layout.addWidget(conv_btn)

        layout.addWidget(param_group)

        self.log_box = QPlainTextEdit()
        self.log_box.setObjectName("LogBox")
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Лог операций...")
        layout.addWidget(self.log_box, 1)

    def _browse_session(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите директорию с сессией")
        if d:
            self.session_dir_input.setText(d)

    def _browse_out(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите директорию для сохранения")
        if d:
            self.out_dir_input.setText(d)

    def _load_session(self):
        d = self.session_dir_input.text().strip()
        if not d or not os.path.isdir(d):
            QMessageBox.warning(self, "Ошибка", "Укажите корректную директорию с сессией.")
            return
        try:
            self.loaded_session = ReportExporter.load_session(d)
            self.log_box.appendPlainText(
                f"[+] Сессия загружена: {len(self.loaded_session.files)} файлов, "
                f"~{self.loaded_session.total_tokens_gemini:,} токенов Gemini."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка загрузки", str(exc))

    def _convert(self):
        if not self.loaded_session:
            QMessageBox.warning(self, "Нет сессии", "Сначала загрузите сохранённую сессию.")
            return
        out_dir = self.out_dir_input.text().strip() or self.session_dir_input.text().strip()
        preset_name = self.ai_limit_combo.currentText()
        custom_limit = self.get_settings_fn().get("custom_token_limit", 0)
        limit = custom_limit if custom_limit > 0 else AI_MODEL_PRESETS.get(preset_name, 100_000)

        est_parts = ReportExporter.estimate_parts_count(self.loaded_session, limit)
        if est_parts > 1:
            chosen = QFileDialog.getExistingDirectory(
                self,
                f"Объём превышает лимит (будет {est_parts} частей). Куда сохранить?",
                out_dir,
            )
            if not chosen:
                return
            out_dir = chosen
            self.out_dir_input.setText(out_dir)

        cfg = ExportConfig(
            output_dir=out_dir,
            filename_base=self.filename_input.text().strip(),
            fmt=self.fmt_combo.currentText(),
            include_tree=self.tree_chk.isChecked(),
            censor_data=False,
            max_tokens_per_part=limit,
            ai_target_name=preset_name,
            save_session=False,
        )
        try:
            created, total_parts = ReportExporter.export_report(self.loaded_session, cfg)
            self.log_box.appendPlainText(f"[+] Конвертация завершена. Создано частей: {total_parts}")
            for p in created:
                self.log_box.appendPlainText(f"    -> {p}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка конвертации", str(exc))