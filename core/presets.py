import os
import sys
import json
from pathlib import Path

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(current_dir)
    return os.path.join(base_path, relative_path)

CATALOG_FILE = get_resource_path(os.path.join("assets", "catalog.json"))
ICONS_DIR = get_resource_path(os.path.join("assets", "icons"))
DEFAULT_ICON = os.path.join(ICONS_DIR, "default-app.png")

APP_CATEGORIES = {}
PRESETS = {} # Můžeš si sem přidat logiku na presety, pokud je stále potřebuješ

# --- NAČTENÍ KATALOGU Z JSONU ---
if os.path.exists(CATALOG_FILE):
    try:
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            raw_catalog = json.load(f)

        for category_name, apps_list in raw_catalog.items():
            processed_apps = []
            for app_data in apps_list:
                # Ošetření ikony
                icon_path = os.path.join(ICONS_DIR, app_data.get("icon_name", ""))
                if not os.path.exists(icon_path):
                    icon_path = DEFAULT_ICON if os.path.exists(DEFAULT_ICON) else None

                processed_apps.append({
                    "name": app_data.get("name", "Neznámý název"),
                    "id": app_data.get("id", ""),
                    "website": app_data.get("website", ""),
                    "icon_url": icon_path,
                    "description": app_data.get("description", "Popis není k dispozici.")
                })
            
            APP_CATEGORIES[category_name] = processed_apps

    except Exception as e:
        print(f"DEBUG: Nelze načíst catalog.json: {e}")

# --- APLIKACE VLASTNÍCH OPRAV ID (OVERRIDES) ---
try:
    _docs_dir = Path.home() / "Documents" / "OmniDesk"
    OVERRIDES_FILE = str(_docs_dir / "preset_overrides.json")

    if os.path.exists(OVERRIDES_FILE):
        with open(OVERRIDES_FILE, "r", encoding="utf-8") as f:
            overrides = json.load(f)
        
        for category_apps in APP_CATEGORIES.values():
            for app in category_apps:
                if app["id"] in overrides:
                    app["id"] = overrides[app["id"]]
except Exception as e:
    print(f"DEBUG: Nelze načíst preset_overrides.json: {e}")