import webbrowser
import subprocess
import os
import importlib
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QComboBox, QFrame, QMessageBox, 
                             QTextEdit, QDialog, QScrollArea, QCheckBox, QFileDialog)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QMouseEvent, QCursor

from core.config import COLORS, THEMES
from core.settings_manager import SettingsManager

# Pokus o import presets pro analýzu
try:
    import core.presets as presets
except ImportError:
    presets = None


# --- WORKER PRO KONTROLU A OPRAVU PRESETS ---
class PresetsCheckWorker(QThread):
    log_signal = pyqtSignal(str)     # Průběžný log
    finished = pyqtSignal(str)       # Finální report

    def run(self):
        if not presets:
            self.finished.emit("Chyba: Modul presets nebyl nalezen.")
            return

        self.log_signal.emit("Načítám definice aplikací z paměti...")
        
        apps_to_check = []
        seen_ids = set()

        # Posbíráme všechny aplikace k ověření
        for category_apps in presets.APP_CATEGORIES.values():
            for app in category_apps:
                if app["id"] not in seen_ids:
                    apps_to_check.append(app) # ZDE UKLÁDÁME ODKAZ NA SLOVNÍK V PAMĚTI
                    seen_ids.add(app["id"])

        total = len(apps_to_check)
        self.log_signal.emit(f"Nalezeno {total} unikátních aplikací ke kontrole.\n")

        changes = []
        errors = []

        for i, app in enumerate(apps_to_check):
            current_id = app["id"]
            app_name = app["name"]
            
            self.log_signal.emit(f"[{i+1}/{total}] Kontrola: {app_name} ({current_id})...")

            if not self.is_id_valid(current_id):
                self.log_signal.emit(f"   ⚠️ ID '{current_id}' nefunguje. Hledám opravu...")
                new_id = self.find_correct_id(app_name)
                
                if new_id and new_id != current_id:
                    self.log_signal.emit(f"   ✅ Nalezeno nové ID: {new_id}")
                    
                    if self.update_overrides_file(current_id, new_id):
                        # ZDE JE KOUZLO: Změníme ID rovnou v paměti. 
                        # Promítne se to okamžitě do celé aplikace, není potřeba reload!
                        app["id"] = new_id 
                        changes.append(f"OPRAVENO: {app_name}\n   Staré: {current_id}\n   Nové:  {new_id}")
                    else:
                        errors.append(f"CHYBA ZÁPISU: {app_name}")
                else:
                    errors.append(f"NENALEZENO: {app_name}")
                    self.log_signal.emit(f"   ❌ Nepodařilo se najít nové ID.")
            else:
                pass

        report = "=== VÝSLEDEK KONTROLY ===\n\n"
        if changes:
            report += f"✅ Bylo opraveno a uloženo do Dokumentů {len(changes)} ID:\n" + "\n".join(changes) + "\n\n"
        else:
            report += "✅ Všechna ID jsou platná. Žádné změny nebyly nutné.\n\n"
        
        if errors:
            report += f"⚠️ Problémy ({len(errors)}):\n" + "\n".join(errors)
            
        # Odstraněno importlib.reload(presets) - už není potřeba a naopak by to uškodilo
        self.finished.emit(report)

    def is_id_valid(self, app_id):
        try:
            cmd = f'winget show --id "{app_id}" --accept-source-agreements'
            result = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return result.returncode == 0
        except:
            return False

    def find_correct_id(self, app_name):
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

    def update_overrides_file(self, old_id, new_id):
        """Uloží mapování opraveného ID do JSONu v Dokumentech"""
        try:
            from core.presets import OVERRIDES_FILE
            import json
            import os
            
            overrides = {}
            # Pokud JSON už existuje, načteme ho, abychom nepřemazali starší opravy
            if os.path.exists(OVERRIDES_FILE):
                try:
                    with open(OVERRIDES_FILE, "r", encoding="utf-8") as f:
                        overrides = json.load(f)
                except:
                    pass
            
            # Zapíšeme si pravidlo "Když narazíš na old_id, použij new_id"
            overrides[old_id] = new_id
            
            # Uložíme aktualizovaný slovník
            with open(OVERRIDES_FILE, "w", encoding="utf-8") as f:
                json.dump(overrides, f, indent=4, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"Chyba zápisu do overrides jsonu: {e}")
            return False


# --- DIALOG PRO VÝPIS LOGU ---
class LogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(600, 450)
        
        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        self.container.setGeometry(0, 0, 600, 450)
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

        # Horní lišta
        title_bar = QWidget()
        title_bar.setObjectName("TitleBar")
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet(f"""
            #TitleBar {{
                background-color: {COLORS['bg_sidebar']};
                border: 1px solid {COLORS['border']}; 
                border-top-left-radius: 7px; 
                border-top-right-radius: 7px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)

        lbl_title = QLabel("🔍 Kontrola Presets")
        lbl_title.setStyleSheet("color: white; font-weight: bold; border: none; font-size: 14px; background: transparent;")
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()

        btn_x = QPushButton("✕")
        btn_x.setFixedSize(30, 30)
        btn_x.clicked.connect(self.reject)
        btn_x.setStyleSheet(f"background: transparent; color: #888; border: none; font-size: 16px; font-weight: bold;")
        title_layout.addWidget(btn_x)
        main_layout.addWidget(title_bar)

        # Obsah
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet(f"background-color: {COLORS['input_bg']}; color: {COLORS['fg']}; border: 1px solid {COLORS['border']}; font-family: Consolas; border-radius: 4px;")
        content_layout.addWidget(self.log_area)

        self.btn_close = QPushButton("Zavřít")
        self.btn_close.setEnabled(False)
        self.btn_close.setFixedHeight(40)
        self.btn_close.setStyleSheet(f"background-color: {COLORS['accent']}; color: white; border: none; border-radius: 4px; font-weight: bold;")
        self.btn_close.clicked.connect(self.accept)
        content_layout.addWidget(self.btn_close)

        main_layout.addLayout(content_layout)
        self.old_pos = None

    def append_log(self, text):
        self.log_area.append(text)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def finish(self, report):
        self.log_area.append("\n" + "-"*40 + "\n")
        self.log_area.append(report)
        self.btn_close.setEnabled(True)
        self.btn_close.setText("Hotovo (Zavřít)")

    # Drag okna
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton: self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event: QMouseEvent): self.old_pos = None


# --- POMOCNÉ WIDGETY ---

class SectionHeader(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['sub_text']}; margin-top: 25px; margin-bottom: 10px;")

class Separator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet(f"background-color: {COLORS['border']}; margin-top: 15px; margin-bottom: 15px;")
        self.setFixedHeight(1)

class SettingRow(QWidget):
    def __init__(self, title, description, widget):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        
        text_layout = QVBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        lbl_desc = QLabel(description)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(f"font-size: 12px; color: {COLORS['sub_text']};")
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_desc)
        
        layout.addLayout(text_layout, stretch=1)
        layout.addSpacing(20)
        layout.addWidget(widget)

# --- HLAVNÍ STRÁNKA NASTAVENÍ ---

class SettingsPage(QWidget):
    def __init__(self, updater=None): 
        super().__init__()
        self.updater = updater 
        self.settings = SettingsManager.load_settings()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._style_scrollbar()

        # Obsah
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(40, 40, 40, 40)
        self.content_layout.setSpacing(5)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === ZAHÁJENÍ OBSAHU ===

        lbl_main = QLabel("Nastavení")
        lbl_main.setStyleSheet("font-size: 28px; font-weight: bold; color: white; margin-bottom: 20px;")
        self.content_layout.addWidget(lbl_main)

        # 1. SEKCE: PRESETS
        self.content_layout.addWidget(SectionHeader("Databáze aplikací"))
        btn_check_presets = QPushButton("Zkontrolovat správnost ID k instalaci aplikace")
        self._style_link_btn(btn_check_presets)
        btn_check_presets.clicked.connect(self.check_presets)
        
        self.content_layout.addWidget(SettingRow(
            "Validace ID aplikací", 
            "Ověří všechna ID v databázi a automaticky opraví neplatné.", 
            btn_check_presets
        ))
        self.content_layout.addWidget(Separator())

        # 2. SEKCE: VZHLED
        self.content_layout.addWidget(SectionHeader("Vzhled a Jazyk"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        current_theme = self.settings.get("theme", "Dark (Default)")
        self.theme_combo.setCurrentText(current_theme if current_theme in THEMES else "Dark (Default)")
        self.theme_combo.currentTextChanged.connect(self.save_theme)
        self._style_combo(self.theme_combo)
        self.content_layout.addWidget(SettingRow("Barevný motiv", "Vyberte si světlý nebo tmavý režim.", self.theme_combo))

        self.lang_combo = QComboBox()
        # Seznam jazyků
        european_languages = [
            "Čeština", "English", "Deutsch", "Slovenčina", "Polski", 
            "Français", "Español", "Italiano", "Português", "Nederlands", 
            "Dansk", "Svenska", "Norsk", "Suomi", "Magyar", "Română", 
            "Ελληνικά", "Русский", "Українська", "Hrvatski", "Slovenščina", 
            "Srpski", "Български", "Eesti", "Latviešu", "Lietuvių", "Türkçe"
        ]
        european_languages.sort() # Seřadit abecedně (A-Z)
        
        self.lang_combo.addItems(european_languages)
        
        # Nastavení aktuálního jazyka (pokud není v seznamu, defaultně Čeština)
        current_lang = self.settings.get("language", "Čeština")
        self.lang_combo.setCurrentText(current_lang)
        
        self.lang_combo.currentTextChanged.connect(self.save_lang)
        self._style_combo(self.lang_combo)
        
        self.content_layout.addWidget(SettingRow("Jazyk aplikace", "Změna se projeví po restartu.", self.lang_combo))
        self.content_layout.addWidget(Separator())

       # 3. SEKCE: SYSTÉM
        self.content_layout.addWidget(SectionHeader("Systém"))
        btn_update = QPushButton("Zkontrolovat aktualizace")
        self._style_link_btn(btn_update)
        
        if self.updater:
            # Pokud máme updater, připojíme ho (tlačítko zavolá logiku stahování)
            btn_update.clicked.connect(lambda: self.updater.check_for_updates(silent=False))
        else:
            # Pokud updater není (např. chyba inicializace), vypneme tlačítko
            btn_update.clicked.connect(lambda: QMessageBox.warning(self, "Chyba", "Modul aktualizací není dostupný."))
            btn_update.setEnabled(False)
            
        self.content_layout.addWidget(SettingRow("Aktualizace", "Zkontrolujte dostupnost nové verze.", btn_update))

        self.content_layout.addStretch()
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
        

    # --- STYLY A LOGIKA ---

    def _style_input(self, widget):
        widget.setStyleSheet(f"background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; padding: 10px; border-radius: 4px; color: white; font-family: Consolas;")

    def _style_button(self, btn):
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background-color: {COLORS['accent']}; color: white; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold; }} QPushButton:hover {{ background-color: {COLORS['accent_hover']}; }}")

    def _style_link_btn(self, btn):
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {COLORS['fg']}; border: none; text-align: left; }} QPushButton:hover {{ color: {COLORS['accent']}; text-decoration: underline; }}")

    def _style_combo(self, combo):
        combo.setFixedWidth(250)
        combo.setCursor(Qt.CursorShape.PointingHandCursor)
        combo.setStyleSheet(f"QComboBox {{ background-color: {COLORS['input_bg']}; color: white; border: 1px solid {COLORS['border']}; padding: 5px; border-radius: 4px; }} QComboBox::drop-down {{ border: none; }}")
        
    def _style_checkbox(self, chk):
        chk.setCursor(Qt.CursorShape.PointingHandCursor)
        # Checkbox styl (čtvereček)
        chk.setStyleSheet(f"""
            QCheckBox::indicator {{ width: 20px; height: 20px; border: 1px solid {COLORS['border']}; border-radius: 4px; background: {COLORS['input_bg']}; }}
            QCheckBox::indicator:checked {{ background: {COLORS['accent']}; image: url(check.png); border: 1px solid {COLORS['accent']}; }}
        """)

    def _style_scrollbar(self):
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{ background-color: transparent; border: none; }}
            QScrollBar:vertical {{ border: none; background-color: {COLORS['bg_main']}; width: 8px; margin: 0px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background-color: #444; min-height: 20px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS['accent']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        """)

    def check_presets(self):
        self.log_dialog = LogDialog(self)
        self.log_dialog.show()
        self.presets_worker = PresetsCheckWorker()
        self.presets_worker.log_signal.connect(self.log_dialog.append_log)
        self.presets_worker.finished.connect(self.log_dialog.finish)
        self.presets_worker.start()

    def save_theme(self, text):
        self.settings["theme"] = text
        SettingsManager.save_settings(self.settings)

    def save_lang(self, text):
        self.settings["language"] = text
        SettingsManager.save_settings(self.settings)