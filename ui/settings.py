import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "user_settings.json")

DEFAULT_SETTINGS = {
    "theme_name": "Blue",
    "mode": "Light",
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            return {
                "theme_name": data.get("theme_name", DEFAULT_SETTINGS["theme_name"]),
                "mode": data.get("mode", DEFAULT_SETTINGS["mode"]),
            }
    except (json.JSONDecodeError, OSError):
        return DEFAULT_SETTINGS.copy()

def save_settings(theme_name, mode):
    data = {"theme_name": theme_name, "mode": mode}
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f)
    except OSError:
        pass