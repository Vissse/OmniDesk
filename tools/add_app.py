import subprocess
import json
import sys
import os
import re

# Získáme absolutní cestu ke složce, kde leží tento skript (tools)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Skočíme o úroveň výš do kořenové složky projektu (OmniDesk)
BASE_DIR = os.path.dirname(SCRIPT_DIR)
# Sestavíme přesnou cestu ke katalogu
CATALOG_PATH = os.path.join(BASE_DIR, "assets", "catalog.json")

# Mapování Winget tagů na tvé kategorie
CATEGORY_MAP = {
    "browser": "🌐 Prohlížeče",
    "web": "🌐 Prohlížeče",
    "chat": "💬 Komunikace",
    "messaging": "💬 Komunikace",
    "game": "🎮 Hry",
    "gaming": "🎮 Hry",
    "media": "🎨 Média (Obraz, Zvuk, Video)",
    "video": "🎨 Média (Obraz, Zvuk, Video)",
    "audio": "🎨 Média (Obraz, Zvuk, Video)",
    "office": "📄 Kancelářské aplikace",
    "document": "📄 Kancelářské aplikace",
    "disk": "💽 Správa disků",
    "utility": "🛠️ Systémové nástroje (Utilities)",
    "tool": "🛠️ Systémové nástroje (Utilities)",
    "development": "💻 Vývojářské nástroje",
    "coding": "💻 Vývojářské nástroje"
}
DEFAULT_CATEGORY = "🛠️ Systémové nástroje (Utilities)"

def get_winget_info(app_id):
    print(f"Získávám informace z Wingetu pro ID: {app_id}...")
    
    # Nastavíme kódování na utf-8, abychom zamezili problémům s diakritikou
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    result = subprocess.run(
        f'winget show --id "{app_id}" --accept-source-agreements',
        capture_output=True, text=True, shell=True, env=env, encoding='utf-8', errors='replace'
    )
    
    output = result.stdout
    
    # Rychlý regex parsing dat z Winget výpisu
    name_match = re.search(r"Found (.*?)\s+\[", output)
    url_match = re.search(r"(?:Publisher Url|Homepage):\s+(.*)", output)
    desc_match = re.search(r"Description:\s+(.*)", output)
    tags_match = re.search(r"Tags:\s+(.*)", output)

    name = name_match.group(1).strip() if name_match else app_id.split(".")[-1]
    url = url_match.group(1).strip() if url_match else ""
    desc = desc_match.group(1).strip() if desc_match else "Popis není k dispozici."
    tags = tags_match.group(1).lower().split(",") if tags_match else []

    # Odhad kategorie
    category = DEFAULT_CATEGORY
    for tag in tags:
        tag = tag.strip()
        if tag in CATEGORY_MAP:
            category = CATEGORY_MAP[tag]
            break

    return {
        "name": name,
        "id": app_id,
        "website": url,
        "icon_name": f"{app_id}.png",
        "description": desc
    }, category

def add_to_catalog(app_data, category):
    # Načtení stávajícího katalogu
    if os.path.exists(CATALOG_PATH):
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    else:
        catalog = {}

    # Přidání kategorie, pokud neexistuje
    if category not in catalog:
        catalog[category] = []

    # Kontrola duplicit
    if any(app["id"] == app_data["id"] for app in catalog[category]):
        print(f"⚠️ Aplikace {app_data['id']} už v kategorii '{category}' existuje!")
        return

    catalog[category].append(app_data)

    # Seřazení podle abecedy (volitelné, ale dělá v tom pořádek)
    catalog[category] = sorted(catalog[category], key=lambda x: x["name"].lower())

    # Uložení
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Přidáno: {app_data['name']} do kategorie '{category}'!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Použití: python add_app.py <WingetID>")
        sys.exit(1)
        
    target_id = sys.argv[1]
    app_info, inferred_category = get_winget_info(target_id)
    add_to_catalog(app_info, inferred_category)
