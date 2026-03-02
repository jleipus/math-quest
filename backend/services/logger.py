import json
import sys
from datetime import datetime, timezone
from threading import Lock

_lock = Lock()


def log(message: str, extra: dict | None = None) -> None:
    """Emit one structured log line to stdout.

    Args:
        message: Short human-readable description of the event.
        extra:   Optional dict of additional fields.
    """
    record: dict = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "msg": message,
    }
    if extra:
        for k, v in extra.items():
            record[k] = v

    line = json.dumps(record, ensure_ascii=False)
    with _lock:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
