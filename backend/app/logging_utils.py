import json
import logging
import sys
from datetime import datetime


_DEFAULT_ATTRS = {
    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
    'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
    'created', 'msecs', 'relativeCreated', 'thread', 'threadName', 'process',
    'processName'
}


class JsonFormatter(logging.Formatter):
    """Simple JSON formatter for application logs."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        log_entry = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry["stack_info"] = record.stack_info

        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _DEFAULT_ATTRS and not key.startswith('_')
        }
        if extras:
            log_entry.update(extras)

        return json.dumps(log_entry, ensure_ascii=False)


def configure_json_logging(app=None) -> None:
    """Configure root logger to emit JSON to stdout."""
    root_logger = logging.getLogger()
    if any(getattr(handler, "_json_logging", False) for handler in root_logger.handlers):
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler._json_logging = True  # type: ignore[attr-defined]

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    if app is not None:
        app.logger.handlers = root_logger.handlers
        app.logger.setLevel(root_logger.level)
