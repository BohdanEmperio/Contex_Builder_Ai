from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QSpinBox, QMessageBox,
)
from core.models import AppProfile, DEFAULT_IGNORE_DIRS, DEFAULT_IGNORE_EXTS
from core.profiles import ProfileManager


class SettingsTab(QWidget):
    def __init__(self, on_profile_applied_cb=None):
        super().__init__()
        self.profile_mgr = ProfileManager()
        self.on_profile_applied_cb = on_profile_applied_cb
        self._init_ui()
        self._refresh_profiles()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("⚙ Настройки и профили")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # --- Профили ---
        prof_group = QGroupBox("Профили")
        prof_layout = QVBoxLayout(prof_group)

        self.profiles_list = QListWidget()
        self.profiles_list.itemDoubleClicked.connect(self._load_selected_profile)
        prof_layout.addWidget(self.profiles_list)

        refresh_btn = QPushButton("🔄 Обновить список")
        refresh_btn.setObjectName("BlueBtn")
        refresh_btn.clicked.connect(self._refresh_profiles)
        prof_layout.addWidget(refresh_btn)

        limit_row = QHBoxLayout()
        limit_row.addWidget(QLabel("Свой лимит токенов (0 = из пресета):"))
        self.custom_limit_spin = QSpinBox()
        self.custom_limit_spin.setRange(0, 2_000_000)
        self.custom_limit_spin.setSingleStep(10_000)
        self.custom_limit_spin.setValue(0)
        limit_row.addWidget(self.custom_limit_spin)
        prof_layout.addLayout(limit_row)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Имя профиля:"))
        self.profile_name_input = QLineEdit()
        self.profile_name_input.setPlaceholderText("Название нового профиля")
        name_row.addWidget(self.profile_name_input, 1)
        prof_layout.addLayout(name_row)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить")
        save_btn.setObjectName("GreenBtn")
        save_btn.clicked.connect(self._save_profile)

        del_btn = QPushButton("🗑 Удалить")
        del_btn.setObjectName("RedBtn")
        del_btn.clicked.connect(self._delete_profile)

        btn_row.addWidget(save_btn)
        btn_row.addWidget(del_btn)
        prof_layout.addLayout(btn_row)

        layout.addWidget(prof_group, 1)

        # --- О программе ---
        about_group = QGroupBox("О программе")
        about_layout = QVBoxLayout(about_group)
        about_layout.addWidget(QLabel("📚 Context Builder AI v1.0.0"))
        about_layout.addWidget(
            QLabel("Инструмент для анализа объёма, подсчёта токенов ИИ и экспорта проектов с авто-разбиением")
        )
        about_layout.addWidget(QLabel("Python 3.12+ | PySide6 | tiktoken"))
        layout.addWidget(about_group)

        self.status_label = QLabel("Профилей: 0")
        self.status_label.setObjectName("TokenInfoBox")
        layout.addWidget(self.status_label)

    def get_settings(self) -> dict:
        return {
            "custom_token_limit": self.custom_limit_spin.value(),
            "ignore_dirs": set(DEFAULT_IGNORE_DIRS),
            "ignore_exts": set(DEFAULT_IGNORE_EXTS),
        }

    def _refresh_profiles(self):
        self.profiles_list.clear()
        names = self.profile_mgr.list_profiles()
        for name in names:
            self.profiles_list.addItem(QListWidgetItem(name))
        self.status_label.setText(f"Профилей: {len(names)}")

    def _save_profile(self):
        name = self.profile_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название профиля.")
            return
        prof = AppProfile(
            name=name,
            ai_preset="custom",
            max_tokens=self.custom_limit_spin.value(),
            default_format="txt",
            include_tree=True,
            censor_data=False,
            ignore_dirs=sorted(DEFAULT_IGNORE_DIRS),
            ignore_exts=sorted(DEFAULT_IGNORE_EXTS),
        )
        self.profile_mgr.save_profile(prof)
        self._refresh_profiles()

    def _load_selected_profile(self, item: QListWidgetItem):
        try:
            prof = self.profile_mgr.load_profile(item.text())
            self.custom_limit_spin.setValue(prof.max_tokens)
            self.profile_name_input.setText(prof.name)
            if self.on_profile_applied_cb:
                self.on_profile_applied_cb(prof)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка загрузки профиля", str(exc))

    def _delete_profile(self):
        item = self.profiles_list.currentItem()
        if not item:
            return
        self.profile_mgr.delete_profile(item.text())
        self._refresh_profiles()