import subprocess
import os
import ctypes  # PŘIDÁNO: Pro detekci administrátorských práv
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QProgressBar, QFrame, QLineEdit, QFileIconProvider,
                             QTextEdit, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QFileInfo, QTimer, QPropertyAnimation, QEasingCurve, QVariantAnimation, QRect
from PyQt6.QtGui import QColor, QPixmap, QPainter, QPainterPath

from core.config import COLORS, resource_path
from core.utils import find_app_icon_path, find_main_exe_in_folder
from UI.shared_widgets import AnimatedActionButton, IconDownloadWorker, add_vertical_separator

class ScanWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            cmd = "winget upgrade --include-unknown --accept-source-agreements"
            
            res = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo, encoding='utf-8', errors='replace')
            
            updates = []
            parsing = False
            lines = res.stdout.split('\n')
            
            for line in lines:
                clean_line = line.strip()
                if not clean_line: continue
                
                if "Name" in line and "Id" in line and "Version" in line: 
                    parsing = True
                    continue
                if not parsing or "----" in line: 
                    continue
                
                if "have an upgrade available" in clean_line or "upgrades available" in clean_line:
                    continue

                parts = clean_line.split()
                if len(parts) >= 4:
                    source = parts[-1]
                    new_ver = parts[-2]
                    
                    # Detekce posunu sloupců (přítomnost znaku '<')
                    if parts[-4] == '<':
                        curr_ver = f"{parts[-4]} {parts[-3]}"
                        app_id = parts[-5]
                        name_parts = parts[:-5]
                    else:
                        curr_ver = parts[-3]
                        app_id = parts[-4]
                        name_parts = parts[:-4]

                    name = " ".join(name_parts)
                    
                    # OCHRANA PROTI CHYBNÉMU PARSOVÁNÍ (jako např. ID="ad"):
                    # Winget ID standardně obsahuje tečku (Publisher.App) nebo je delší než 3 znaky.
                    # Pokud parsování vyhodí nesmysl, řádek přeskočíme.
                    if len(app_id) <= 2 or (not "." in app_id and app_id.islower()):
                        continue

                    if new_ver.lower() == "winget":
                         pass

                    updates.append({'name': name, 'id': app_id, 'current': curr_ver, 'new': new_ver})

            self.finished.emit(updates)
        except Exception as e: 
            self.error.emit(str(e))

class UpdateWorker(QThread):
    finished = pyqtSignal()
    log_signal = pyqtSignal(str)

    def __init__(self, app_ids=None, update_all=False):
        super().__init__()
        self.app_ids = app_ids or []
        self.update_all = update_all
        self.process = None 
        self.is_cancelled = False

    def run(self):
        cmd_base = [
            "winget", "upgrade", 
            "--silent", 
            "--disable-interactivity", 
            "--accept-package-agreements", 
            "--accept-source-agreements", 
            "--include-unknown",
            "--force",
            "--verbose"
        ]
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            if self.update_all:
                self.log_signal.emit("\n--- HROMADNÁ AKTUALIZACE VŠECH BALÍČKŮ ---")
                self._execute(cmd_base + ["--all", "--include-unknown"], startupinfo, is_spotify_or_user_app=False)
            else:
                for aid in self.app_ids:
                    if self.is_cancelled: break
                    self.log_signal.emit(f"\n--- AKTUALIZUJI: {aid} ---")
                    
                    # OPRAVA 1: Detekujeme, zda aktualizujeme Spotify nebo jinou problémovou "user-level" aplikaci
                    is_spotify = "spotify" in aid.lower()
                    
                    self._execute(cmd_base + ["--id", aid, "--exact"], startupinfo, is_spotify_or_user_app=is_spotify)
        except Exception as e:
            self.log_signal.emit(f"Kritická chyba: {str(e)}")
            
        self.finished.emit()

    def _execute(self, cmd, startupinfo, is_spotify_or_user_app=False):
        try:
            # OPRAVA 2: Kontrola, zda OmniDesk běží s právy Administrátora
            is_admin = False
            if os.name == 'nt':
                try:
                    is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
                except:
                    is_admin = False

            # Pokud jsme Admin a instalujeme aplikaci citlivou na kontext (např. Spotify),
            # shodíme Admin práva spuštěním přes explorer.exe
            if is_admin and is_spotify_or_user_app:
                # explorer.exe spustí winget v kontextu běžného přihlášeného uživatele
                cmd = ["explorer.exe"] + cmd
                
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace',
                startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                bufsize=1
            )
            
            # Pokud jsme použili explorer.exe, stdout se bohužel nedá streamovat (explorer hned skončí),
            # proto ošetříme čtení bezpečně.
            if self.process.stdout:
                for line in self.process.stdout:
                    if self.is_cancelled:
                        try: self.process.kill()
                        except: pass
                        break
                    clean_line = line.strip()
                    if clean_line:
                        self.log_signal.emit(clean_line)

            self.process.wait()
        except Exception as e:
            self.log_signal.emit(f"CHYBA PROCESU: {str(e)}")

    def kill_process(self):
        self.is_cancelled = True
        if self.process:
            try: self.process.kill() 
            except: pass


