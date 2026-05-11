# install_manager.py
import os
import shutil
import subprocess
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QProgressBar, QTextEdit, QPushButton, QWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QTextCursor

from core.config import COLORS
from core.settings_manager import SettingsManager # IMPORT NASTAVENÍ

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
        
        # Načtení nastavení uživatele
        self.settings = SettingsManager.load_settings()

    def run(self):
        failed_apps = []
        total = len(self.install_list)

        # 1. Aktualizace zdrojů
        self.status_signal.emit("Aktualizace databáze Winget...")
        self.log_signal.emit("--- AKTUALIZACE ZDROJŮ WINGET ---\n")
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run('winget source update', shell=True, startupinfo=startupinfo, creationflags=0x08000000)
            self.log_signal.emit(">>> Databáze úspěšně aktualizována.\n\n")
        except Exception as e:
            self.log_signal.emit(f"Warning: Aktualizace zdrojů selhala ({str(e)}), pokračuji...\n\n")

        self.log_signal.emit("--- ZAHAJUJI HROMADNOU INSTALACI ---\n")
        self.log_signal.emit(f"Konfigurace: Scope={self.settings.get('winget_scope', 'machine')}, Mode={self.settings.get('winget_mode', 'silent')}\n")

        # 2. Instalace aplikací
        for i, app_data in enumerate(self.install_list):
            if not self.is_running: break
            
            app_name = app_data['name']
            app_id = app_data['id'].strip()
            
            self.status_signal.emit(f"Instaluji: {app_name}")
            self.log_signal.emit(f"\n>>> Instaluji: {app_name} ({app_id})...\n")

            # --- DYNAMICKÉ SESTAVENÍ PŘÍKAZU PODLE NASTAVENÍ ---
            args = []
            
            # ID
            args.append(f'--id "{app_id}"')
            
            # Režim (Silent / Interactive)
            if self.settings.get("winget_mode", "silent") == "silent":
                args.append('--silent')
                args.append('--disable-interactivity')
            else:
                args.append('--interactive')

            # Scope (Machine / User)
            scope = self.settings.get("winget_scope", "machine")
            args.append(f'--scope {scope}')

            #NOVÉ: Location (Vlastní cesta)
            custom_location = self.settings.get("winget_location", "")
            if custom_location:
                # Cestu musíme obalit uvozovkami pro případ mezer
                args.append(f'--location "{custom_location}"')

            # Force
            if self.settings.get("winget_force", True):
                args.append('--force')

            # Agreements
            if self.settings.get("winget_agreements", True):
                args.append('--accept-package-agreements')
                args.append('--accept-source-agreements')

            # Finální příkaz
            cmd = f'winget install {" ".join(args)}'
            
            # Pro jistotu vypíšeme příkaz do logu (užitečné pro debug)
            # self.log_signal.emit(f"CMD: {cmd}\n") 

            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
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

                if process.returncode == 0:
                    self.log_signal.emit(f"✅ {app_name} úspěšně nainstalován.\n")
                    self.create_desktop_shortcut(app_name)
                else:
                    self.log_signal.emit(f"❌ Chyba při instalaci {app_name} (kód {process.returncode}).\n")
                    failed_apps.append(app_name)

            except Exception as e:
                self.log_signal.emit(f"❌ Kritická chyba: {str(e)}\n")
                failed_apps.append(app_name)

            self.progress_signal.emit(i + 1)

        self.finished_signal.emit(failed_apps)

    def create_desktop_shortcut(self, app_name):
        """Pokusí se najít nainstalovanou aplikaci a zkopírovat zástupce na plochu."""
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
                            self.log_signal.emit(f"➕ Vytvořen zástupce na ploše: {file}\n")
                            found = True
                            break 
                    if found: break
                if found: break
        except Exception as e:
            self.log_signal.emit(f"(Info: Zástupce nevytvořen: {e})\n")

    def stop(self):
        self.is_running = False


# --- DIALOGOVÉ OKNO (UI) - ZŮSTÁVÁ STEJNÉ JAKO PŘEDTÍM ---
class InstallationDialog(QDialog):
    def __init__(self, install_list, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(700, 550)
        self.old_pos = None

        self.install_list = install_list

        # --- HLAVNÍ KONTEJNER ---
        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        self.container.setGeometry(0, 0, 700, 550)
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
        
        lbl_icon = QLabel("🚀")
        lbl_icon.setStyleSheet("font-size: 16px; background: transparent; border: none;")
        lbl_title = QLabel("Průběh instalace")
        lbl_title.setStyleSheet("color: white; font-weight: bold; font-size: 14px; background: transparent; border: none;")
        
        title_layout.addWidget(lbl_icon)
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()

        main_layout.addWidget(title_bar)

        # --- 2. OBSAH ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(15)

        # Status Label
        self.lbl_status = QLabel("Příprava instalace...")
        self.lbl_status.setStyleSheet(f"color: {COLORS['accent']}; font-size: 16px; font-weight: bold;")
        content_layout.addWidget(self.lbl_status)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setRange(0, len(install_list))
        self.progress.setValue(0)
        self.progress.setFixedHeight(25)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['input_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                color: white;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['success']};
                border-radius: 3px;
            }}
        """)
        content_layout.addWidget(self.progress)

        # Log Area
        lbl_log = QLabel("Detailní výpis:")
        lbl_log.setStyleSheet("color: #888; margin-top: 10px;")
        content_layout.addWidget(lbl_log)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: #111; 
                color: #ccc; 
                border: 1px solid {COLORS['border']};
                font-family: Consolas, monospace;
                border-radius: 4px;
                padding: 5px;
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: #111;
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #444;
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS['accent']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        content_layout.addWidget(self.txt_log)

        # Tlačítko Zrušit/Zavřít
        self.btn_action = QPushButton("Zrušit instalaci")
        self.btn_action.setFixedSize(200, 45)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']}; color: white; border: none; 
                border-radius: 6px; font-weight: bold; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {COLORS['danger_hover']}; }}
        """)
        self.btn_action.clicked.connect(self.handle_button)
        
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addWidget(self.btn_action)
        btn_container.addStretch()
        content_layout.addLayout(btn_container)

        main_layout.addWidget(content_widget)

        # --- START VLÁKNA ---
        self.worker = InstallationWorker(install_list)
        self.worker.log_signal.connect(self.append_log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    # --- LOGIKA ---

    def append_log(self, text):
        self.txt_log.moveCursor(QTextCursor.MoveOperation.End)
        self.txt_log.insertPlainText(text)
        self.txt_log.moveCursor(QTextCursor.MoveOperation.End)

    def update_status(self, text):
        self.lbl_status.setText(text)

    def on_finished(self, failed_apps):
        if not failed_apps:
            self.lbl_status.setText("✅ HOTOVO! Vše nainstalováno.")
            self.lbl_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 16px; font-weight: bold;")
        else:
            self.lbl_status.setText(f"⚠️ Hotovo s chybami ({len(failed_apps)})")
            self.lbl_status.setStyleSheet("color: orange; font-size: 16px; font-weight: bold;")
            self.append_log(f"\nNepodařilo se nainstalovat: {', '.join(failed_apps)}")

        self.btn_action.setText("Zavřít")
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']}; color: white; border: none; 
                border-radius: 6px; font-weight: bold; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {COLORS['success_hover']}; }}
        """)
        self.worker = None # Cleanup

    def handle_button(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.append_log("\n!!! UŽIVATEL PŘERUŠIL INSTALACI !!!")
            self.worker.wait()
            self.close()
        else:
            self.close()

    # --- POSOUVÁNÍ OKNA ---
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