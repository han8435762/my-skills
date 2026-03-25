import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "synced_ids.json")


def _load():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def _save(ids):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids), f, ensure_ascii=False)


def is_synced(message_id):
    return message_id in _load()


def mark_synced(message_id):
    ids = _load()
    ids.add(message_id)
    _save(ids)
