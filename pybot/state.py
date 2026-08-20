# -*- coding: utf-8 -*-
"""JSON-file state store for the bot.

Holds per-chat profiles (last callsign / grid square / language), in-flight
wizard sessions and the cached satellite catalog. All writes are atomic
(tmp file + os.replace) and guarded by a module-level lock.
"""

import json
import os
import threading
import time

_LOCK = threading.Lock()


def _load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


def _save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _ensure_sections(data):
    data.setdefault("profiles", {})
    data.setdefault("wizards", {})
    data.setdefault("catalog", {})
    return data


class Store:
    def __init__(self, path):
        self.path = path

    def _data(self):
        data = _load(self.path)
        return _ensure_sections(data)

    def _write(self, fn):
        with _LOCK:
            data = self._data()
            fn(data)
            _save(self.path, data)

    # ---- profiles ---------------------------------------------------

    def get_profile(self, chat_id):
        with _LOCK:
            return self._data()["profiles"].get(str(chat_id), {})

    def save_profile(self, chat_id, profile):
        def upd(data):
            data["profiles"][str(chat_id)] = profile

        self._write(upd)

    # ---- wizards ----------------------------------------------------

    def get_wizard(self, chat_id):
        with _LOCK:
            return self._data()["wizards"].get(str(chat_id))

    def save_wizard(self, wizard):
        def upd(data):
            data["wizards"][str(wizard["chat_id"])] = wizard

        self._write(upd)

    def clear_wizard(self, chat_id):
        def upd(data):
            data["wizards"].pop(str(chat_id), None)

        self._write(upd)

    # ---- catalog cache ----------------------------------------------

    def get_catalog(self):
        with _LOCK:
            entry = self._data()["catalog"]
        if not entry:
            return None
        if entry.get("ts", 0) + entry.get("ttl", 0) < time.time():
            return None
        return entry.get("data")

    def set_catalog(self, sats, ttl):
        def upd(data):
            data["catalog"] = {"ts": int(time.time()), "ttl": ttl, "data": sats}

        self._write(upd)