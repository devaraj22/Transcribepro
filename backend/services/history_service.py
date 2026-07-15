import uuid
from datetime import datetime, timezone
from typing import Dict, List

from ..app.core.config import settings
from ..app.utils.json_store import read_json, write_json


def get_history() -> List[Dict]:
    return read_json(settings.HISTORY_FILE, default=[])


def append_history(entry: Dict) -> Dict:
    history = get_history()
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": entry.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    history.insert(0, entry)
    history = history[: settings.HISTORY_LIMIT]
    write_json(settings.HISTORY_FILE, history)
    return entry
