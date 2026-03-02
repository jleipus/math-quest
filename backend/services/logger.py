import json
from datetime import datetime, timezone
from threading import Lock
from pathlib import Path

_lock = Lock()
_output_file: Path | None = None


def set_log_file(path: str | Path) -> None:
    global _output_file
    _output_file = Path(path)
    _output_file.parent.mkdir(parents=True, exist_ok=True)


def log(message: str, extra: dict | None = None) -> None:
    record: dict = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "msg": message,
    }
    if extra:
        record.update(extra)

    line = json.dumps(record, ensure_ascii=False) + "\n"
    with _lock:
        if _output_file:
            with open(_output_file, "a") as f:
                f.write(line)
