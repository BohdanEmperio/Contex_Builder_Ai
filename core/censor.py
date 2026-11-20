import re


class DataCensor:
    """Маскирование чувствительных данных перед отправкой отчёта в ИИ."""

    PATTERNS = [
        (re.compile(r'(sk-[A-Za-z0-9\-_]{20,})'), '[REDACTED_OPENAI_KEY]'),
        (re.compile(r'(AIza[0-9A-Za-z\-_]{30,})'), '[REDACTED_GOOGLE_KEY]'),
        (re.compile(r'(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})'), '[REDACTED_GITHUB_TOKEN]'),
        (re.compile(r'(AKIA[0-9A-Z]{16})'), '[REDACTED_AWS_KEY]'),
        (
            re.compile(r'(?i)(password|passwd|pwd|secret|api_key|apikey|token|access_key)\s*([:=])\s*["\']?([^\s"\',;}{]+)["\']?'),
            r'\1\2 [REDACTED]'
        ),
        (re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'), '[REDACTED_EMAIL]'),
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        result = text
        for pattern, replacement in cls.PATTERNS:
            result = pattern.sub(replacement, result)
        return result