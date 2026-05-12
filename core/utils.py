import os
import winreg

def find_main_exe_in_folder(folder):
    best_exe = None
    max_size = 0
    base_depth = folder.rstrip(os.sep).count(os.sep)
    try:
        for root, dirs, files in os.walk(folder):
            current_depth = root.rstrip(os.sep).count(os.sep)
            if current_depth - base_depth > 1: continue 
            for file in files:
                if file.lower().endswith(".exe"):
                    if any(x in file.lower() for x in ["unins", "helper", "crash", "update", "report", "setup"]): continue
                    full_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(full_path)
                        if "java.exe" in file.lower() or "javaw.exe" in file.lower(): return full_path
                        if size > max_size: 
                            max_size = size
                            best_exe = full_path
                    except: pass
    except: pass
    return best_exe

def find_app_icon_path(app_name, app_id=None):
    clean_name = app_name.split(' (')[0].strip()
    search_names = [clean_name.lower()]
    if app_id and "." in app_id:
        publisher = app_id.split('.')[0].lower()
        if len(publisher) > 2: search_names.append(publisher)

    registry_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    roots = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
    found_install_loc = None

    for i, reg_path in enumerate(registry_paths):
        root = roots[i]
        try:
            with winreg.OpenKey(root, reg_path) as key:
                for j in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, j)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0].lower()
                                if any(s in display_name for s in search_names):
                                    try:
                                        display_icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                                        display_icon = display_icon.split(',')[0].strip('"')
                                        if os.path.exists(display_icon) and (display_icon.endswith('.exe') or display_icon.endswith('.ico')):
                                            return display_icon
                                    except: pass
                                    try:
                                        loc = winreg.QueryValueEx(subkey, "InstallLocation")[0].strip('"')
                                        if loc and os.path.exists(loc): found_install_loc = loc
                                    except: pass
                            except: continue
                    except: continue
        except: continue

    if found_install_loc:
        exe = find_main_exe_in_folder(found_install_loc)
        if exe: return exe

    try:
        app_paths_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, app_paths_key) as key:
            for j in range(winreg.QueryInfoKey(key)[0]):
                exe_name = winreg.EnumKey(key, j)
                if clean_name.replace(" ", "").lower() in exe_name.lower():
                    with winreg.OpenKey(key, exe_name) as subkey:
                        try:
                            path = winreg.QueryValue(subkey, None).strip('"')
                            if os.path.exists(path): return path
                        except: pass
    except: pass
    return None