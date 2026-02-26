import json
import os
from datetime import datetime, timezone
from threading import Lock

_lock = Lock()


def log_llm_request(path: str, entry: dict) -> None:
    """Append a JSON log entry to the LLM request log file.

    Args:
        path: Absolute or relative path to the log file.
        entry: Dict with request/response fields to record.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    record = {"ts": datetime.now(timezone.utc).isoformat(), **entry}
    line = json.dumps(record, ensure_ascii=False)
    with _lock:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
