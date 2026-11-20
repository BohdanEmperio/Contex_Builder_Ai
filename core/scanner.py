import os
from typing import Set, Optional, List, Callable
from core.models import (
    FileEntry,
    ScanResult,
    DEFAULT_IGNORE_DIRS,
    DEFAULT_IGNORE_EXTS,
)
from core.tokenizer import TokenAnalyzer


class ProjectScanner:
    """Сканирование директории, чтение текстовых файлов и построение дерева."""

    MAX_SINGLE_FILE_BYTES = 5 * 1024 * 1024  # 5 МБ на один файл

    def __init__(
        self,
        ignore_dirs: Optional[Set[str]] = None,
        ignore_exts: Optional[Set[str]] = None,
    ):
        self.ignore_dirs = ignore_dirs if ignore_dirs is not None else set(DEFAULT_IGNORE_DIRS)
        self.ignore_exts = ignore_exts if ignore_exts is not None else set(DEFAULT_IGNORE_EXTS)

    @staticmethod
    def _is_binary(filepath: str) -> bool:
        try:
            with open(filepath, "rb") as f:
                chunk = f.read(8192)
            return b"\x00" in chunk
        except OSError:
            return True

    @staticmethod
    def _read_text(filepath: str) -> Optional[str]:
        for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
            try:
                with open(filepath, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except OSError:
                return None
        return None

    def scan_directory(
        self,
        root_dir: str,
        progress_cb: Optional[Callable[[str], None]] = None,
        selected_rel_paths: Optional[Set[str]] = None,
    ) -> ScanResult:
        root_dir = os.path.abspath(root_dir)
        result = ScanResult(root_dir=root_dir)
        collected_rel_paths: List[str] = []

        for current_root, dirs, files in os.walk(root_dir):
            dirs[:] = sorted(d for d in dirs if d not in self.ignore_dirs)
            files.sort()

            for filename in files:
                abs_path = os.path.join(current_root, filename)
                rel_path = os.path.relpath(abs_path, root_dir).replace("\\", "/")

                if selected_rel_paths is not None and rel_path not in selected_rel_paths:
                    continue

                _, ext = os.path.splitext(filename.lower())
                if ext in self.ignore_exts:
                    result.skipped_files.append(f"{rel_path} (игнорируемое расширение)")
                    continue

                try:
                    size_bytes = os.path.getsize(abs_path)
                except OSError:
                    result.skipped_files.append(f"{rel_path} (ошибка доступа)")
                    continue

                if size_bytes > self.MAX_SINGLE_FILE_BYTES:
                    result.skipped_files.append(f"{rel_path} (> 5 МБ)")
                    continue

                if self._is_binary(abs_path):
                    result.skipped_files.append(f"{rel_path} (бинарный файл)")
                    continue

                content = self._read_text(abs_path)
                if content is None:
                    result.skipped_files.append(f"{rel_path} (не удалось прочитать)")
                    continue

                if progress_cb:
                    progress_cb(f"Чтение: {rel_path}")

                t_gemini, t_gpt = TokenAnalyzer.count_tokens(content)
                lines_count = content.count("\n") + (1 if content else 0)
                chars_count = len(content)

                entry = FileEntry(
                    relative_path=rel_path,
                    absolute_path=abs_path,
                    size_bytes=size_bytes,
                    chars_count=chars_count,
                    lines_count=lines_count,
                    tokens_gemini=t_gemini,
                    tokens_gpt=t_gpt,
                    content=content,
                )
                result.files.append(entry)
                collected_rel_paths.append(rel_path)

                result.total_bytes += size_bytes
                result.total_chars += chars_count
                result.total_lines += lines_count
                result.total_tokens_gemini += t_gemini
                result.total_tokens_gpt += t_gpt

        result.tree_text = self.build_tree(os.path.basename(root_dir), collected_rel_paths)
        return result

    def find_matching_files(self, root_dir: str, filter_text: str) -> List[str]:
        """Поиск файлов для вкладки 'Файлы' по расширениям (.py, .js) или подстроке имени."""
        root_dir = os.path.abspath(root_dir)
        tokens = [t.strip().lower() for t in filter_text.replace(";", ",").split(",") if t.strip()]
        matches: List[str] = []

        for current_root, dirs, files in os.walk(root_dir):
            dirs[:] = sorted(d for d in dirs if d not in self.ignore_dirs)
            for filename in sorted(files):
                abs_path = os.path.join(current_root, filename)
                rel_path = os.path.relpath(abs_path, root_dir).replace("\\", "/")
                low_name = filename.lower()
                low_rel = rel_path.lower()

                if not tokens:
                    matches.append(rel_path)
                    continue

                matched = False
                for tok in tokens:
                    if tok.startswith(".") and low_name.endswith(tok):
                        matched = True
                        break
                    if tok in low_rel:
                        matched = True
                        break
                if matched:
                    matches.append(rel_path)
        return matches

    @staticmethod
    def build_tree(root_name: str, rel_paths: List[str]) -> str:
        tree_dict = {}
        for path in rel_paths:
            parts = path.split("/")
            curr = tree_dict
            for part in parts[:-1]:
                curr = curr.setdefault(part, {})
            curr[parts[-1]] = None

        lines = [f"{root_name}/"]

        def _walk(node: dict, prefix: str = ""):
            keys = sorted(node.keys(), key=lambda k: (node[k] is None, k.lower()))
            for idx, key in enumerate(keys):
                is_last = idx == len(keys) - 1
                connector = "└── " if is_last else "├── "
                val = node[key]
                if val is None:
                    lines.append(f"{prefix}{connector}{key}")
                else:
                    lines.append(f"{prefix}{connector}{key}/")
                    ext_prefix = "    " if is_last else "│   "
                    _walk(val, prefix + ext_prefix)

        _walk(tree_dict)
        return "\n".join(lines)