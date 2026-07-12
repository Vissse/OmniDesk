import os
import json
import sys
from pathlib import Path

CURRENT_VERSION = "1.0.14"

try:
    _docs_dir = Path.home() / "Documents" / "OmniDesk"
    _docs_dir.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE = str(_docs_dir / "user_settings.json")
    OUTPUT_FILE = str(_docs_dir / "install_apps.bat")
except Exception:
    SETTINGS_FILE = "user_settings.json"
    OUTPUT_FILE = "install_apps.bat"

# --- 1. DEFINICE TÉMAT ---
# Musí obsahovat všechny klíče, které používají nové PyQt views
THEMES = {
    "Dark": {
        "bg_main": "#1e1e1e",
        "bg_sidebar": "#252526",
        "fg": "#ffffff",
        "sub_text": "#888888",
        "input_bg": "#3c3c3c",
        "accent": "#007acc",       # VS Code Blue
        "accent_hover": "#1f8ad2",
        "danger": "#d83b01",
        "danger_hover": "#e84a1b", # PŘIDÁNO: Světlejší červená pro hover
        "success": "#107c10",
        "success_hover": "#138913",# PŘIDÁNO: Světlejší zelená pro hover
        "item_bg": "#2d2d30",
        "item_hover": "#3e3e42",
        "border": "#3e3e42"
    },
    "Light": {
        "bg_main": "#f8f9fa",      # Světle šedé pozadí hlavní plochy
        "bg_sidebar": "#ffffff",   # Bílé pozadí levého menu
        "fg": "#212529",           # Tmavě šedý/černý text
        "sub_text": "#6c757d",     # Světlejší šedý text
        "input_bg": "#ffffff",
        "accent": "#0d6efd",       # Výraznější modrá
        "accent_hover": "#0b5ed7",
        "danger": "#dc3545",
        "danger_hover": "#bb2d3b",
        "success": "#198754",
        "success_hover": "#157347",
        "item_bg": "#ffffff",      # Bílé pozadí karet a prvků
        "item_hover": "#e9ecef",   # Jemná šedá po přejetí
        "border": "#dee2e6"        # Zřetelné jemné okraje
    }
}

# --- 2. NAČTENÍ AKTIVNÍHO TÉMATU ---
# Inicializujeme prázdný slovník, který se naplní z THEMES
COLORS = THEMES["Dark"].copy()


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- DEFINICE CESTY K IKONÁM ---
ICONS_DIR = resource_path(os.path.join("assets", "icons"))

# Pokud existuje nastavení, pokusíme se načíst uložené téma
try:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            saved_theme = data.get("theme", "Dark")
            
            # Fallback pro staré názvy témat
            if saved_theme == "Notion Light": saved_theme = "Light"
            
            if saved_theme in THEMES:
                COLORS = THEMES[saved_theme].copy()
except Exception:
    pass
