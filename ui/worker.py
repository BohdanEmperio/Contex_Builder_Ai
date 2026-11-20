from typing import Callable, Any
from PySide6.QtCore import QThread, Signal


class TaskWorker(QThread):
    """Фоновый поток для длительных операций (сканирование / экспорт), чтобы GUI не зависал."""

    finished_ok = Signal(object)
    failed = Signal(str)
    log_msg = Signal(str)

    def __init__(self, fn: Callable[..., Any], *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished_ok.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))