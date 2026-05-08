import webbrowser
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QFrame, QMessageBox, 
                             QScrollArea, QCheckBox, QFileDialog)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QMouseEvent, QCursor

from core.config import COLORS, THEMES
from core.settings_manager import SettingsManager

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

        # 1. SEKCE: VZHLED
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

        # 2. SEKCE: SYSTÉM
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

    def save_theme(self, text):
        self.settings["theme"] = text
        SettingsManager.save_settings(self.settings)

    def save_lang(self, text):
        self.settings["language"] = text
        SettingsManager.save_settings(self.settings)