from dataclasses import dataclass, field
from typing import List, Dict


AI_MODEL_PRESETS: Dict[str, int] = {
    "Gemini (безопасный чанк чата — 100 000 токенов)": 100_000,
    "Gemini Web / Pro (лимит контекста — 900 000 токенов)": 900_000,
    "GPT-4o / ChatGPT (безопасный чанк — 60 000 токенов)": 60_000,
    "Claude 3.5/3.7 Sonnet (чанк — 120 000 токенов)": 120_000,
    "Компактный чат (32 000 токенов)": 32_000,
    "Малый лимит (16 000 токенов)": 16_000,
}

DEFAULT_IGNORE_DIRS = {
    ".git", ".svn", ".hg", "__pycache__", "node_modules",
    "venv", ".venv", "env", ".idea", ".vscode", "dist",
    "build", ".context_builder", ".pytest_cache", ".mypy_cache",
}

DEFAULT_IGNORE_EXTS = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".obj", ".o",
    ".pyc", ".pyo", ".pyd", ".png", ".jpg", ".jpeg", ".gif",
    ".bmp", ".ico", ".webp", ".svg", ".mp3", ".mp4", ".wav",
    ".avi", ".mov", ".zip", ".rar", ".7z", ".tar", ".gz",
    ".pdf", ".docx", ".xlsx", ".db", ".sqlite", ".sqlite3",
}


@dataclass
class FileEntry:
    relative_path: str
    absolute_path: str
    size_bytes: int
    chars_count: int
    lines_count: int
    tokens_gemini: int
    tokens_gpt: int
    content: str


@dataclass
class ScanResult:
    root_dir: str
    files: List[FileEntry] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    tree_text: str = ""
    total_bytes: int = 0
    total_chars: int = 0
    total_lines: int = 0
    total_tokens_gemini: int = 0
    total_tokens_gpt: int = 0


@dataclass
class ExportConfig:
    output_dir: str
    filename_base: str
    fmt: str  # "txt" или "md"
    include_tree: bool
    censor_data: bool
    max_tokens_per_part: int
    ai_target_name: str
    save_session: bool = True


@dataclass
class AppProfile:
    name: str
    ai_preset: str
    max_tokens: int
    default_format: str
    include_tree: bool
    censor_data: bool
    ignore_dirs: List[str]
    ignore_exts: List[str]