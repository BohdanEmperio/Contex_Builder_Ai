from typing import Tuple

try:
    import tiktoken
    _TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")
except Exception:
    _TIKTOKEN_ENC = None


class TokenAnalyzer:
    """Подсчёт токенов для GPT (tiktoken cl100k_base) и оценка для Gemini."""

    @staticmethod
    def count_tokens(text: str) -> Tuple[int, int]:
        """
        Возвращает кортеж: (tokens_gemini_est, tokens_gpt).
        Для Gemini: базовая оценка ~4 символа на токен для латиницы/кода;
        для кириллицы/многобайтовых символов плотность выше (~2.2 символа на токен).
        """
        if not text:
            return 0, 0

        if _TIKTOKEN_ENC is not None:
            tokens_gpt = len(_TIKTOKEN_ENC.encode(text, disallowed_special=()))
        else:
            tokens_gpt = max(1, len(text) // 4)

        non_ascii = sum(1 for ch in text if ord(ch) > 127)
        ascii_chars = len(text) - non_ascii
        gemini_est = int((ascii_chars / 4.0) + (non_ascii / 2.2))
        tokens_gemini = max(1, gemini_est)

        return tokens_gemini, tokens_gpt