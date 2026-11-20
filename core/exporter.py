import os
import json
from datetime import datetime
from typing import List, Tuple
from core.models import ScanResult, ExportConfig, FileEntry
from core.censor import DataCensor
from core.tokenizer import TokenAnalyzer


class ReportExporter:
    """Формирование отчётов для ИИ, автоматическое разбиение по лимиту токенов и работа с сессиями."""

    SESSION_DIR_NAME = ".context_builder"
    SESSION_FILE_NAME = "session.json"

    @staticmethod
    def _format_file_block(entry: FileEntry, fmt: str, censor: bool) -> str:
        body = DataCensor.sanitize(entry.content) if censor else entry.content
        if fmt == "md":
            _, ext = os.path.splitext(entry.relative_path)
            lang = ext.lstrip(".").lower()
            return (
                f"### Файл: `{entry.relative_path}` "
                f"({entry.lines_count} строк | ~{entry.tokens_gemini} Gemini / {entry.tokens_gpt} GPT токенов)\n"
                f"```{lang}\n{body}\n```\n\n"
            )
        sep = "=" * 80
        return (
            f"{sep}\n"
            f"ФАЙЛ: {entry.relative_path} "
            f"({entry.lines_count} строк | ~{entry.tokens_gemini} Gemini / {entry.tokens_gpt} GPT токенов)\n"
            f"{sep}\n"
            f"{body}\n\n"
        )

    @staticmethod
    def _format_chunk_header(rel_path: str, part_idx: int, sub: str, fmt: str) -> str:
        if fmt == "md":
            _, ext = os.path.splitext(rel_path)
            lang = ext.lstrip(".").lower()
            return f"### Файл: `{rel_path}` (фрагмент {part_idx})\n```{lang}\n{sub}\n```\n\n"
        return f"--- ФАЙЛ: {rel_path} (фрагмент {part_idx}) ---\n{sub}\n\n"

    @classmethod
    def _split_oversized_entry(
        cls, entry: FileEntry, fmt: str, censor: bool, max_tokens: int
    ) -> List[str]:
        """Если один файл больше лимита — дробит по строкам, а слишком длинные строки — по символам."""
        body = DataCensor.sanitize(entry.content) if censor else entry.content
        lines = body.splitlines(keepends=True)
        chunks: List[str] = []
        buf: List[str] = []
        buf_tokens = 0
        part_idx = 1

        safe_limit = max(1000, int(max_tokens * 0.85))

        for line in lines:
            t_gem, t_gpt = TokenAnalyzer.count_tokens(line)
            t_line = max(t_gem, t_gpt)

            if t_line > safe_limit:
                if buf:
                    chunks.append(
                        cls._format_chunk_header(entry.relative_path, part_idx, "".join(buf), fmt)
                    )
                    buf = []
                    buf_tokens = 0
                    part_idx += 1

                pos = 0
                line_len = len(line)
                step = max(500, safe_limit * 2)
                while pos < line_len:
                    cur_step = min(step, line_len - pos)
                    piece = line[pos : pos + cur_step]
                    pg, pp = TokenAnalyzer.count_tokens(piece)
                    while max(pg, pp) > safe_limit and cur_step > 500:
                        cur_step = max(500, cur_step // 2)
                        piece = line[pos : pos + cur_step]
                        pg, pp = TokenAnalyzer.count_tokens(piece)
                    chunks.append(
                        cls._format_chunk_header(entry.relative_path, part_idx, piece, fmt)
                    )
                    part_idx += 1
                    pos += cur_step
                continue

            if buf and (buf_tokens + t_line > safe_limit):
                chunks.append(
                    cls._format_chunk_header(entry.relative_path, part_idx, "".join(buf), fmt)
                )
                buf = [line]
                buf_tokens = t_line
                part_idx += 1
            else:
                buf.append(line)
                buf_tokens += t_line

        if buf:
            chunks.append(
                cls._format_chunk_header(entry.relative_path, part_idx, "".join(buf), fmt)
            )
        return chunks

    @classmethod
    def estimate_parts_count(cls, scan_result: ScanResult, max_tokens: int) -> int:
        if max_tokens <= 0:
            return 1
        total_peak = max(scan_result.total_tokens_gemini, scan_result.total_tokens_gpt)
        effective_limit = max(1000, int(max_tokens * 0.90))
        if total_peak <= effective_limit:
            return 1

        parts = 1
        current = 0
        for f in scan_result.files:
            t = max(f.tokens_gemini, f.tokens_gpt)
            if t > effective_limit:
                if current > 0:
                    parts += 1
                    current = 0
                parts += (t // effective_limit)
            elif current + t > effective_limit:
                parts += 1
                current = t
            else:
                current += t
        return max(1, parts)

    @classmethod
    def export_report(
        cls, scan_result: ScanResult, config: ExportConfig
    ) -> Tuple[List[str], int]:
        """
        Создаёт один или несколько файлов отчёта, не превышая config.max_tokens_per_part.
        Возвращает: (список созданных файлов, количество частей).
        """
        os.makedirs(config.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = config.filename_base.strip() or f"ai_context_{timestamp}"
        ext = "md" if config.fmt == "md" else "txt"

        header_intro = (
            f"# КОНТЕКСТ ПРОЕКТА ДЛЯ ИИ\n"
            f"Корень проекта: {scan_result.root_dir}\n"
            f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Целевой лимит: {config.max_tokens_per_part:,} токенов ({config.ai_target_name})\n"
            f"Всего файлов: {len(scan_result.files)} | "
            f"Оценка токенов: ~{scan_result.total_tokens_gemini:,} (Gemini) / "
            f"{scan_result.total_tokens_gpt:,} (GPT cl100k)\n\n"
        )
        tree_block = ""
        if config.include_tree and scan_result.tree_text:
            if config.fmt == "md":
                tree_block = f"## Структура проекта\n```text\n{scan_result.tree_text}\n```\n\n"
            else:
                tree_block = f"СТРУКТУРА ПРОЕКТА:\n{scan_result.tree_text}\n\n"

        blocks: List[Tuple[str, int]] = []
        safe_limit = max(1000, int(config.max_tokens_per_part * 0.90))

        for entry in scan_result.files:
            block = cls._format_file_block(entry, config.fmt, config.censor_data)
            t_gem, t_gpt = TokenAnalyzer.count_tokens(block)
            block_tokens = max(t_gem, t_gpt)

            if block_tokens > safe_limit:
                sub_chunks = cls._split_oversized_entry(
                    entry, config.fmt, config.censor_data, config.max_tokens_per_part
                )
                for ch in sub_chunks:
                    cg, cp = TokenAnalyzer.count_tokens(ch)
                    blocks.append((ch, max(cg, cp)))
            else:
                blocks.append((block, block_tokens))

        preamble_t_gem, preamble_t_gpt = TokenAnalyzer.count_tokens(header_intro + tree_block)
        preamble_tokens = max(preamble_t_gem, preamble_t_gpt)

        parts_content: List[List[str]] = []
        current_part: List[str] = []
        current_tokens = preamble_tokens

        for block_text, block_tokens in blocks:
            if current_part and (current_tokens + block_tokens > safe_limit):
                parts_content.append(current_part)
                current_part = [block_text]
                current_tokens = 300 + block_tokens
            else:
                current_part.append(block_text)
                current_tokens += block_tokens

        if current_part or not parts_content:
            parts_content.append(current_part)

        total_parts = len(parts_content)
        created_files: List[str] = []

        for idx, chunk_list in enumerate(parts_content, start=1):
            if total_parts == 1:
                out_name = f"{base_name}.{ext}"
                part_header = header_intro + tree_block
            else:
                out_name = f"{base_name}_part_{idx}_of_{total_parts}.{ext}"
                ai_instruction = (
                    f"[ИНСТРУКЦИЯ ДЛЯ ИИ: Это часть {idx} из {total_parts}. "
                    f"Прими этот фрагмент в контекст. "
                    + (
                        "Жди следующие части и пока не начинай финальный разбор.]\n\n"
                        if idx < total_parts
                        else "Это последняя часть. Теперь у тебя есть весь проект — можешь анализировать.]\n\n"
                    )
                )
                part_header = ai_instruction + (header_intro + tree_block if idx == 1 else "")

            out_path = os.path.join(config.output_dir, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(part_header)
                f.writelines(chunk_list)
            created_files.append(out_path)

        if config.save_session:
            cls.save_session(scan_result, config.output_dir)

        return created_files, total_parts

    @classmethod
    def save_session(cls, scan_result: ScanResult, target_dir: str) -> str:
        session_dir = os.path.join(target_dir, cls.SESSION_DIR_NAME)
        os.makedirs(session_dir, exist_ok=True)
        session_file = os.path.join(session_dir, cls.SESSION_FILE_NAME)

        data = {
            "root_dir": scan_result.root_dir,
            "tree_text": scan_result.tree_text,
            "total_bytes": scan_result.total_bytes,
            "total_chars": scan_result.total_chars,
            "total_lines": scan_result.total_lines,
            "total_tokens_gemini": scan_result.total_tokens_gemini,
            "total_tokens_gpt": scan_result.total_tokens_gpt,
            "files": [
                {
                    "relative_path": f.relative_path,
                    "absolute_path": f.absolute_path,
                    "size_bytes": f.size_bytes,
                    "chars_count": f.chars_count,
                    "lines_count": f.lines_count,
                    "tokens_gemini": f.tokens_gemini,
                    "tokens_gpt": f.tokens_gpt,
                    "content": f.content,
                }
                for f in scan_result.files
            ],
        }
        with open(session_file, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
        return session_file

    @classmethod
    def load_session(cls, directory: str) -> ScanResult:
        direct_file = os.path.join(directory, cls.SESSION_FILE_NAME)
        nested_file = os.path.join(directory, cls.SESSION_DIR_NAME, cls.SESSION_FILE_NAME)
        session_file = direct_file if os.path.isfile(direct_file) else nested_file

        if not os.path.isfile(session_file):
            raise FileNotFoundError(
                f"Файл сессии {cls.SESSION_FILE_NAME} не найден в указанной директории."
            )

        with open(session_file, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        files = [FileEntry(**item) for item in data.get("files", [])]
        return ScanResult(
            root_dir=data["root_dir"],
            files=files,
            tree_text=data.get("tree_text", ""),
            total_bytes=data.get("total_bytes", 0),
            total_chars=data.get("total_chars", 0),
            total_lines=data.get("total_lines", 0),
            total_tokens_gemini=data.get("total_tokens_gemini", 0),
            total_tokens_gpt=data.get("total_tokens_gpt", 0),
        )