import json
import os
import hashlib
from typing import Optional, Dict, Any

DEFAULT_STATE_PATH = os.path.join(os.path.dirname(__file__), "buyer_state.json")


def _hash_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


class BuyerStateStore:
    def __init__(self, path: Optional[str] = None):
        self.path = path or DEFAULT_STATE_PATH
        self.state: Dict[str, Any] = {}
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.state = json.load(f)
        except FileNotFoundError:
            self.state = {}
        except json.JSONDecodeError:
            self.state = {}

    def save(self):
        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self.path)

    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        return self.state.setdefault(thread_id, {})

    def mark_seen_message(self, thread_id: str, message_text: str):
        entry = self.get_thread(thread_id)
        entry["last_message_hash"] = _hash_text(message_text)
        self.state[thread_id] = entry
        self.save()

    def mark_replied_to_message(self, thread_id: str, message_text: str):
        """Mark that we've replied to this specific buyer message."""
        entry = self.get_thread(thread_id)
        entry["last_replied_hash"] = _hash_text(message_text)
        entry["last_message_hash"] = _hash_text(message_text)
        self.state[thread_id] = entry
        self.save()

    def has_new_message(self, thread_id: str, message_text: str) -> bool:
        entry = self.get_thread(thread_id)
        prev = entry.get("last_message_hash")
        return prev != _hash_text(message_text)
    
    def needs_reply(self, thread_id: str, message_text: str) -> bool:
        """Check if this buyer message needs a reply (hasn't been replied to yet)."""
        entry = self.get_thread(thread_id)
        last_replied = entry.get("last_replied_hash")
        current_hash = _hash_text(message_text)
        return last_replied != current_hash

    def set_buyer_name(self, thread_id: str, name: str):
        entry = self.get_thread(thread_id)
        entry["buyer_name"] = name
        self.state[thread_id] = entry
        self.save()

    def set_item_id(self, thread_id: str, item_id: Optional[int]):
        entry = self.get_thread(thread_id)
        if item_id is None:
            entry.pop("item_id", None)
        else:
            entry["item_id"] = item_id
        self.state[thread_id] = entry
        self.save()

    def get_item_id(self, thread_id: str) -> Optional[int]:
        entry = self.get_thread(thread_id)
        return entry.get("item_id")
