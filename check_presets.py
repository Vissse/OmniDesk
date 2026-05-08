import os
import sys
import subprocess
import re
import importlib.util

# Cesta k presets.py (předpokládáme, že skript běží v kořenové složce projektu)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRESETS_PATH = os.path.join(BASE_DIR, "core", "presets.py")

def load_presets():
    if not os.path.exists(PRESETS_PATH):
        print(f"❌ Chyba: Soubor presets nenalezen na {PRESETS_PATH}")
        return None
        
    spec = importlib.util.spec_from_file_location("presets", PRESETS_PATH)
    presets_module = importlib.util.module_from_spec(spec)
    sys_modules_backup = sys.modules.copy()
    try:
        spec.loader.exec_module(presets_module)
        return presets_module.APP_CATEGORIES
    except Exception as e:
        print(f"❌ Chyba při čtení presets.py: {e}")
        return None
    finally:
        sys.modules = sys_modules_backup

def is_id_valid(app_id):
    """Zkontroluje, jestli Winget dané ID rozpoznává"""
    try:
        cmd = f'winget show --id "{app_id}" --accept-source-agreements'
        result = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except:
        return False

def find_correct_id(app_name):
    """Pokusí se dohledat správné ID podle názvu aplikace"""
    try:
        cmd = f'winget search --name "{app_name}" --source winget --accept-source-agreements -n 1'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding='cp852', errors='replace')
        lines = result.stdout.split('\n')
        data_started = False
        for line in lines:
            if line.startswith("---"):
                data_started = True
                continue
            if data_started and line.strip():
                ids = re.findall(r'\b[a-zA-Z0-9-]+\.[a-zA-Z0-9\.-]+\b', line)
                if ids:
                    return ids[0]
        return None
    except:
        return None

def update_presets_file(old_id, new_id):
    """Přepíše zdrojový kód presets.py s novým ID a ZÁROVEŇ opraví odkaz na ikonu!"""
    try:
        with open(PRESETS_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 1. Řetězce pro nahrazení samotného ID
        old_id_str = f'"id": "{old_id}"'
        new_id_str = f'"id": "{new_id}"'
        
        # 2. Řetězce pro nahrazení názvu souboru s ikonou (uvnitř get_icon("..."))
        old_icon_str = f'"{old_id}.png"'
        new_icon_str = f'"{new_id}.png"'
        
        if old_id_str in content:
            # Nahradíme ID
            content = content.replace(old_id_str, new_id_str)
            # Nahradíme ikonu
            content = content.replace(old_icon_str, new_icon_str)
            
            with open(PRESETS_PATH, "w", encoding="utf-8") as f:
                f.write(content)
            return True
            
        return False
    except Exception as e:
        print(f"   ❌ Chyba zápisu do presets.py: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 NAČÍTÁM DATABÁZI Z PRESETS.PY")
    print("=" * 60)
    
    categories = load_presets()
    if not categories:
        return

    apps_to_check = []
    seen_ids = set()
    
    for category_apps in categories.values():
        for app in category_apps:
            if app["id"] not in seen_ids:
                apps_to_check.append(app)
                seen_ids.add(app["id"])

    total = len(apps_to_check)
    print(f"📦 Nalezeno {total} unikátních aplikací ke kontrole.\n")

    changes = []
    errors = []

    for i, app in enumerate(apps_to_check):
        current_id = app["id"]
        app_name = app["name"]
        
        print(f"[{i+1}/{total}] Kontrola: {app_name} ({current_id})...")

        if not is_id_valid(current_id):
            print(f"   ⚠️ Neplatné ID: '{current_id}'. Hledám správné...")
            new_id = find_correct_id(app_name)
            
            if new_id and new_id != current_id:
                print(f"   ✅ Nalezeno nové ID: {new_id}")
                if update_presets_file(current_id, new_id):
                    changes.append(f"{app_name} | {current_id} -> {new_id} (Včetně ikony)")
                    print("   💾 Zapsáno do presets.py")
                else:
                    errors.append(f"{app_name} - Nelze zapsat do presets.py")
            else:
                errors.append(f"{app_name} (Staré ID: {current_id})")
                print("   ❌ Nepodařilo se najít žádné funkční ID.")

    # Finální výpis
    print("\n" + "=" * 60)
    print("VÝSLEDEK KONTROLY")
    print("=" * 60)
    
    if changes:
        print(f"✅ Bylo úspěšně opraveno a přepsáno {len(changes)} aplikací:\n")
        for c in changes:
            print(f"  - {c}")
    else:
        print("✅ Všechna ID jsou platná. Žádné změny v kódu nebyly nutné.")
        
    if errors:
        print(f"\n⚠️ Nepodařilo se najít řešení pro tyto aplikace ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
            
    print("\nHOTOVO.")

if __name__ == "__main__":
    main()