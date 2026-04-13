"""
Preset Manager – Laden, Speichern und Verwalten von benutzerdefinierten Presets.

Custom Presets werden als JSON-Dateien im Ordner 'user_presets/' gespeichert.
"""

import json
import os
from pathlib import Path
from typing import Optional

from presets.builtin import BUILTIN_PRESETS, DEFAULT_PARAMS


USER_PRESETS_DIR = Path(__file__).parent.parent.parent / "user_presets"


def ensure_user_presets_dir() -> None:
    USER_PRESETS_DIR.mkdir(parents=True, exist_ok=True)


def load_all_presets() -> list[dict]:
    """Gibt alle Presets zurück: Built-in zuerst, dann User-Presets."""
    presets = list(BUILTIN_PRESETS)
    presets += load_user_presets()
    return presets


def load_user_presets() -> list[dict]:
    """Lädt alle benutzerdefinierten Presets aus dem user_presets/-Ordner."""
    ensure_user_presets_dir()
    user_presets = []
    for path in sorted(USER_PRESETS_DIR.glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                preset = json.load(f)
            # Fehlende Parameter mit Defaults auffüllen
            preset.setdefault("params", {})
            for key, val in DEFAULT_PARAMS.items():
                preset["params"].setdefault(key, val)
            preset.setdefault("icon", "⭐")
            preset.setdefault("is_custom", True)
            user_presets.append(preset)
        except (json.JSONDecodeError, OSError):
            pass
    return user_presets


def save_user_preset(preset: dict) -> bool:
    """Speichert ein Custom-Preset als JSON-Datei. Gibt True bei Erfolg zurück."""
    ensure_user_presets_dir()
    safe_name = "".join(c for c in preset["id"] if c.isalnum() or c in "_-")
    path = USER_PRESETS_DIR / f"{safe_name}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(preset, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def delete_user_preset(preset_id: str) -> bool:
    """Löscht ein Custom-Preset. Gibt True bei Erfolg zurück."""
    safe_name = "".join(c for c in preset_id if c.isalnum() or c in "_-")
    path = USER_PRESETS_DIR / f"{safe_name}.json"
    try:
        if path.exists():
            path.unlink()
        return True
    except OSError:
        return False


def is_builtin(preset_id: str) -> bool:
    """Gibt True zurück wenn das Preset ein eingebautes (unveränderliches) Preset ist."""
    return any(p["id"] == preset_id for p in BUILTIN_PRESETS)


def get_preset_by_id(preset_id: str) -> Optional[dict]:
    """Sucht ein Preset anhand seiner ID in allen Presets."""
    for p in load_all_presets():
        if p["id"] == preset_id:
            return p
    return None
