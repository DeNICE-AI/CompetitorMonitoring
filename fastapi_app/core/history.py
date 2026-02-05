import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException

from fastapi_app.core.config import HISTORY_PATH


def _read_history(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="History file is corrupted") from exc


def _write_history(path: Path, items: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(items, file, ensure_ascii=False, indent=2)


def save_history(entry: Dict[str, Any]) -> None:
    history = _read_history(HISTORY_PATH)
    entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
    history.append(entry)
    history = history[-10:]
    _write_history(HISTORY_PATH, history)


def get_history() -> List[Dict[str, Any]]:
    return _read_history(HISTORY_PATH)
