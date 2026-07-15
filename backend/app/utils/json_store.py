import json
from pathlib import Path
from typing import Any


def ensure_json_file(path: Path, default: Any = None) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default if default is not None else []), encoding="utf-8")


def read_json(path: Path, default: Any = None) -> Any:
    ensure_json_file(path, default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default if default is not None else []


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
