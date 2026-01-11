import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

_EVENTS_LOCK = threading.Lock()
_EVENTS_DIR = Path("backend/client_events")
_EVENTS_FILE = _EVENTS_DIR / "events.jsonl"


def record_client_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    _EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    stored: List[Dict[str, Any]] = []

    with _EVENTS_LOCK:
        with _EVENTS_FILE.open("a", encoding="utf-8") as handle:
            for event in events:
                event_id = event.get("event_id") or uuid.uuid4().hex
                received_at = datetime.utcnow()
                payload = dict(event)
                payload["event_id"] = event_id
                payload["received_at"] = f"{received_at.isoformat()}Z"
                handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
                stored.append({"event_id": event_id, "received_at": received_at})

    return stored
