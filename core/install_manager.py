import os
import shutil
import subprocess
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QProgressBar, QTextEdit, QPushButton, QWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QTextCursor

from core.config import COLORS
from core.settings_manager import SettingsManager

# --- PRACOVNÍ VLÁKNO (Instalace na pozadí) ---
class InstallationWorker(QThread):
    log_signal = pyqtSignal(str)          
    status_signal = pyqtSignal(str)        
    progress_signal = pyqtSignal(int)      
    finished_signal = pyqtSignal(list)     

    def __init__(self, install_list):
        super().__init__()
        self.install_list = install_list
        self.is_running = True
        self.settings = SettingsManager.load_settings()

    def run(self):
        failed_apps = []
        total = len(self.install_list)

        self.status_signal.emit("Aktualizace databáze Winget...")
        self.log_signal.emit("--- AKTUALIZACE ZDROJŮ WINGET ---\n")
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run('winget source update', shell=True, startupinfo=startupinfo, creationflags=0x08000000)
            self.log_signal.emit("Databáze úspěšně aktualizována.\n\n")
        except Exception as e:
            self.log_signal.emit(f"[VAROVÁNÍ] Aktualizace zdrojů selhala ({str(e)}), pokračuji...\n\n")

        self.log_signal.emit("--- ZAHAJUJI HROMADNOU INSTALACI ---\n")
        self.log_signal.emit(f"Konfigurace: Scope={self.settings.get('winget_scope', 'machine')}, Mode={self.settings.get('winget_mode', 'silent')}\n")

        for i, app_data in enumerate(self.install_list):
            if not self.is_running: break
            
            app_name = app_data['name']
            app_id = app_data['id'].strip()
            
            self.status_signal.emit(f"Kontrola: {app_name}")
            
            # --- 1. KONTROLA, ZDA UŽ JE APLIKACE NAINSTALOVÁNA ---
            is_installed = False
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                # Spustíme winget list pro konkrétní ID. 
                # Pokud winget aplikaci nenajde, vrátí chybový návratový kód (obvykle 1).
                check_cmd = f'winget list --id "{app_id}" --exact'
                check_process = subprocess.run(
                    check_cmd, shell=True, 
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    startupinfo=startupinfo, creationflags=0x08000000,
                    text=True, encoding='cp852', errors='ignore'
                )
                
                # Pokud je návratový kód 0, winget aplikaci v seznamu našel
                if check_process.returncode == 0:
                    is_installed = True
            except Exception as e:
                # Pokud kontrola selže z jiného důvodu, raději budeme předpokládat, že nainstalovaná není
                self.log_signal.emit(f"[VAROVÁNÍ] Nepodařilo se ověřit stav instalace pro {app_name}: {e}\n")

            if is_installed:
                self.log_signal.emit(f"[INFO] {app_name} ({app_id}) již je v počítači nainstalován. Přeskakuji...\n")
                self.progress_signal.emit(i + 1)
                continue # Skočí na další aplikaci v seznamu a tuto neinstaluje

            # --- 2. SAMOTNÁ INSTALACE (Pokud aplikace nebyla nalezena) ---
            self.status_signal.emit(f"Instaluji: {app_name}")
            self.log_signal.emit(f"\n> Instaluji: {app_name} ({app_id})...\n")

            def build_cmd(current_scope):
                args = [f'--id "{app_id}"']
                
                if self.settings.get("winget_mode", "silent") == "silent":
                    args.extend(['--silent', '--disable-interactivity'])
                else:
                    args.append('--interactive')

                if current_scope and current_scope != 'default':
                    args.append(f'--scope {current_scope}')

                custom_location = self.settings.get("winget_location", "")
                if custom_location:
                    args.append(f'--location "{custom_location}"')

                # DOPORUČENÍ: Pokud nechceš natvrdo vynucovat reinstalaci, 
                # měl bys mít winget_force v nastavení defaultně na False.
                if self.settings.get("winget_force", False):
                    args.append('--force')

                if self.settings.get("winget_agreements", True):
                    args.extend(['--accept-package-agreements', '--accept-source-agreements'])

                return f'winget install {" ".join(args)}'

            scope = self.settings.get("winget_scope", "machine")
            cmd = build_cmd(scope)

            try:
                # Spuštění prvního pokusu o instalaci
                process = subprocess.Popen(
                    cmd, shell=True, 
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                    text=True, encoding='cp852', errors='replace',
                    startupinfo=startupinfo, creationflags=0x08000000
                )

                for line in process.stdout:
                    if not self.is_running:
                        process.terminate()
                        break
                    clean_line = line.strip()
                    if not clean_line: continue
                    if any(x in clean_line for x in ['\\', '|', '/', '-', 'MB /', 'kB /', '%', '██']):
                        continue
                    self.log_signal.emit(clean_line + "\n")

                process.wait()

                # Fallback mechanismus pro scope (z předchozího řešení)
                if process.returncode != 0 and scope == "machine" and self.is_running:
                    self.log_signal.emit(f"[INFO] Instalace jako 'machine' selhala. Zkouším výchozí scope...\n")
                    cmd_retry = build_cmd("default")
                    
                    process_retry = subprocess.Popen(
                        cmd_retry, shell=True, 
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                        text=True, encoding='cp852', errors='replace',
                        startupinfo=startupinfo, creationflags=0x08000000
                    )
                    
                    for line in process_retry.stdout:
                        if not self.is_running:
                            process_retry.terminate()
                            break
                        clean_line = line.strip()
                        if not clean_line: continue
                        if any(x in clean_line for x in ['\\', '|', '/', '-', 'MB /', 'kB /', '%', '██']):
                            continue
                        self.log_signal.emit(clean_line + "\n")
                        
                    process_retry.wait()
                    return_code = process_retry.returncode
                else:
                    return_code = process.returncode

                if return_code == 0:
                    self.log_signal.emit(f"[OK] {app_name} úspěšně nainstalován.\n")
                    self.create_desktop_shortcut(app_name)
                else:
                    self.log_signal.emit(f"[CHYBA] Selhání instalace {app_name} (kód {return_code}).\n")
                    failed_apps.append(app_name)

            except Exception as e:
                self.log_signal.emit(f"[CHYBA] Kritická chyba: {str(e)}\n")
                failed_apps.append(app_name)

            self.progress_signal.emit(i + 1)

        if self.is_running:
            self.status_signal.emit("Probíhá úklid pracovní plochy...")
            self.clean_desktop_duplicates()

        self.finished_signal.emit(failed_apps)

    def create_desktop_shortcut(self, app_name):
        try:
            start_menu_paths = [
                os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs'),
                os.path.join(os.environ['PROGRAMDATA'], r'Microsoft\Windows\Start Menu\Programs')
            ]
            desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            
            search_terms = app_name.split()
            search_query = search_terms[0] if len(search_terms) > 0 else app_name
            
            found = False
            for path in start_menu_paths:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(".lnk") and search_query.lower() in file.lower():
                            src_file = os.path.join(root, file)
                            dst_file = os.path.join(desktop_path, file)
                            shutil.copy2(src_file, dst_file)
                            self.log_signal.emit(f"[INFO] Vytvořen zástupce na ploše: {file}\n")
                            found = True
                            break 
                    if found: break
                if found: break
        except Exception as e:
            self.log_signal.emit(f"[INFO] Zástupce nevytvořen: {e}\n")

    def clean_desktop_duplicates(self):
        self.log_signal.emit("\n--- ÚKLID PLOCHY ---\n")
        try:
            user_desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
            public_desktop = os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "Desktop")

            if not os.path.exists(user_desktop) or not os.path.exists(public_desktop):
                return

            for item in os.listdir(public_desktop):
                if item.endswith(".lnk"):
                    user_shortcut = os.path.join(user_desktop, item)
                    if os.path.exists(user_shortcut):
                        try:
                            os.remove(user_shortcut)
                            self.log_signal.emit(f"[INFO] Smazán duplikát zástupce: {item}\n")
                        except Exception as e:
                            self.log_signal.emit(f"[VAROVÁNÍ] Nepodařilo se smazat duplikát {item}: {e}\n")
        except Exception as e:
            self.log_signal.emit(f"[CHYBA] Při čištění plochy: {e}\n")

    def stop(self):
        self.is_running = False


# --- DIALOGOVÉ OKNO (UI) ---
class InstallationDialog(QDialog):
    def __init__(self, install_list, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(700, 520)
        self.old_pos = None

        self.install_list = install_list

        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        self.container.setGeometry(0, 0, 700, 520)
        self.container.setStyleSheet(f"""
            #MainContainer {{
                background-color: {COLORS['bg_main']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(1, 1, 1, 1) 
        main_layout.setSpacing(0)

        # --- 1. HORNÍ LIŠTA ---
        title_bar = QWidget()
        title_bar.setObjectName("TitleBar")
        title_bar.setFixedHeight(45)
        title_bar.setStyleSheet(f"""
            #TitleBar {{
                background-color: {COLORS['bg_sidebar']};
                border-bottom: 1px solid {COLORS['border']};
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
            }}
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        
        lbl_title = QLabel(_("inst_prog_title"))
        lbl_title.setStyleSheet("color: white; font-weight: 500; font-size: 13px; background: transparent; border: none;")
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()
        main_layout.addWidget(title_bar)

        # --- 2. OBSAH ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 20, 30, 25)
        content_layout.setSpacing(15)

        self.lbl_status = QLabel("Příprava instalace...")
        self.lbl_status.setStyleSheet(f"color: {COLORS['accent']}; font-size: 15px; font-weight: 500;")
        content_layout.addWidget(self.lbl_status)

        self.progress = QProgressBar()
        self.progress.setRange(0, len(install_list))
        self.progress.setValue(0)
        self.progress.setFixedHeight(6) # Tenčí pruh
        self.progress.setTextVisible(False) # Skryté procento pro minimalismus
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['input_bg']};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 3px;
            }}
        """)
        content_layout.addWidget(self.progress)

        lbl_log = QLabel("Detailní výpis")
        lbl_log.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 11px; margin-top: 5px;")
        content_layout.addWidget(lbl_log)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_sidebar']}; 
                color: {COLORS['sub_text']}; 
                border: 1px solid {COLORS['border']};
                font-family: Consolas, monospace;
                font-size: 11px;
                border-radius: 6px;
                padding: 10px;
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: transparent;
                width: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #555;
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS['accent']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        content_layout.addWidget(self.txt_log, stretch=1)

        # Minimalistické tlačítko
        self.btn_action = QPushButton("Zrušit instalaci")
        self.btn_action.setFixedSize(140, 36)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; 
                color: {COLORS['danger']}; 
                border: 1px solid {COLORS['danger']}; 
                border-radius: 4px; 
                font-weight: 500; 
                font-size: 12px;
            }}
            QPushButton:hover {{ 
                background-color: {COLORS['danger']}; 
                color: white; 
            }}
        """)
        self.btn_action.clicked.connect(self.handle_button)
        
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addWidget(self.btn_action)
        content_layout.addLayout(btn_container)

        main_layout.addWidget(content_widget)

        # --- START VLÁKNA ---
        self.worker = InstallationWorker(install_list)
        self.worker.log_signal.connect(self.append_log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def append_log(self, text):
        self.txt_log.moveCursor(QTextCursor.MoveOperation.End)
        self.txt_log.insertPlainText(text)
        self.txt_log.moveCursor(QTextCursor.MoveOperation.End)

    def update_status(self, text):
        self.lbl_status.setText(text)

    def on_finished(self, failed_apps):
        if not failed_apps:
            self.lbl_status.setText("Dokončeno. Vše nainstalováno.")
            self.lbl_status.setStyleSheet(f"color: {COLORS.get('success', '#4cc71a')}; font-size: 15px; font-weight: 500;")
        else:
            self.lbl_status.setText(f"Dokončeno s chybami ({len(failed_apps)})")
            self.lbl_status.setStyleSheet("color: #eab308; font-size: 15px; font-weight: 500;")
            self.append_log(f"\nNepodařilo se nainstalovat: {', '.join(failed_apps)}")

        self.btn_action.setText("Zavřít")
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; 
                color: {COLORS['fg']}; 
                border: 1px solid {COLORS['border']}; 
                border-radius: 4px; 
                font-weight: 500; 
                font-size: 12px;
            }}
            QPushButton:hover {{ 
                background-color: {COLORS['item_bg']}; 
            }}
        """)
        self.worker = None

    def handle_button(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.append_log("\n[INFO] Uživatel přerušil instalaci.")
            self.worker.wait()
            self.close()
        else:
            self.close()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.old_pos = None
