import webbrowser
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QMessageBox, QScrollArea)
from PyQt6.QtCore import Qt

from core.config import COLORS, THEMES, CURRENT_VERSION
from core.settings_manager import SettingsManager
from core.i18n import _, translator
from core.theme_manager import theme_manager

# Import našich animovaných widgetů ze sdíleného souboru (přidán add_vertical_separator)
from UI.shared_widgets import AnimatedActionButton, AnimatedComboBox, add_vertical_separator

# --- POMOCNÉ WIDGETY ---


from UI.components.settings_components import SectionHeader, Separator, SettingRow

class SettingsPage(QWidget):
    def __init__(self, updater=None): 
        super().__init__()
        self.updater = updater 
        self.settings = SettingsManager.load_settings()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll Area pro samotné nastavení
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)


        # Obsah nastavení
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(40, 40, 40, 40)
        self.content_layout.setSpacing(5)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === ZAHÁJENÍ OBSAHU ===

        self.lbl_main = QLabel()
        self.content_layout.addWidget(self.lbl_main)

        # --- 1. SEKCE: VZHLED ---
        self.content_layout.addWidget(SectionHeader("set_appearance"))
        
        self.theme_combo = AnimatedComboBox()
        self.theme_combo.setFixedWidth(250)
        self.theme_combo.currentIndexChanged.connect(self.save_theme)
        self.content_layout.addWidget(SettingRow("set_theme", "set_theme_desc", self.theme_combo))

        self.lang_combo = AnimatedComboBox()
        self.lang_combo.setFixedWidth(250)
        languages = ["Čeština", "English"]
        self.lang_combo.addItems(languages)
        current_lang = self.settings.get("language", "Čeština")
        self.lang_combo.setCurrentText(current_lang if current_lang in languages else "Čeština")
        self.lang_combo.currentTextChanged.connect(self.save_lang)
        self.content_layout.addWidget(SettingRow("set_lang", "set_lang_desc", self.lang_combo))
        
        self.content_layout.addWidget(Separator())

        # --- 2. SEKCE: SYSTÉM ---
        self.content_layout.addWidget(SectionHeader("set_system"))
        
        self.btn_update = AnimatedActionButton("", "assets/images/arrows-clockwise-thin.png")
        if self.updater:
            self.btn_update.clicked.connect(lambda: self.updater.check_for_updates(silent=False))
        else:
            self.btn_update.clicked.connect(lambda: QMessageBox.warning(self, _("error_title"), _("update_na")))
            self.btn_update.setEnabled(False)
            
        self.content_layout.addWidget(SettingRow("set_update", "set_update_desc", self.btn_update))

        # Odsazení, aby obsah neutíkal dolů
        self.content_layout.addStretch()
        self.scroll_area.setWidget(self.content_widget)
        
        # Přidáme hlavní scrollovací část do layoutu stránky
        main_layout.addWidget(self.scroll_area)

        # --- HORIZONTÁLNÍ PATIČKA (O aplikaci, Podpora, PayPal) ---
        self.footer_widget = QWidget()
        self.footer_widget.setObjectName("SettingsFooter")
        
        footer_layout = QHBoxLayout(self.footer_widget)
        footer_layout.setContentsMargins(40, 15, 40, 15)
        footer_layout.setSpacing(20)
        
        # Stretch zleva zajistí, že tlačítka budou uprostřed
        footer_layout.addStretch()

        # Tlačítko: O aplikaci
        self.btn_about = AnimatedActionButton("", "assets/images/info-thin.png")
        self.btn_about.clicked.connect(self.show_about_dialog)
        footer_layout.addWidget(self.btn_about)

        # --- Oddělovač ---
        add_vertical_separator(footer_layout)

        # Tlačítko: Podpora
        self.btn_email = AnimatedActionButton("", "assets/images/envelope-simple-thin.png")
        self.btn_email.clicked.connect(lambda: webbrowser.open("mailto:vit.sebestik@gmail.com?subject=OmniDesk - Podpora"))
        footer_layout.addWidget(self.btn_email)

        # --- Oddělovač ---
        add_vertical_separator(footer_layout)

        # Tlačítko: PayPal
        self.btn_paypal = AnimatedActionButton("", "assets/images/paypal-logo-thin.png")
        self.btn_paypal.clicked.connect(lambda: webbrowser.open("https://paypal.me/Vissse"))
        footer_layout.addWidget(self.btn_paypal)

        # Stretch zprava
        footer_layout.addStretch()

        # Přidáme patičku fixně úplně nakonec stránky (mimo ScrollArea)
        main_layout.addWidget(self.footer_widget)
        
        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()
        
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

    def retranslate_ui(self):
        self.lbl_main.setText(_("set_title"))
        self.btn_update.setText(_("set_btn_update"))
        self.btn_about.setText(_("set_btn_about"))
        self.btn_email.setText(_("set_btn_support"))
        self.btn_paypal.setText(_("set_btn_paypal"))
        
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        current_theme = self.settings.get("theme", "Dark")
        for key in THEMES.keys():
            t_name = _(f"theme_{key.lower()}")
            if t_name == f"theme_{key.lower()}":
                t_name = key
            self.theme_combo.addItem(t_name, key)
            if key == current_theme:
                self.theme_combo.setCurrentText(t_name)
        self.theme_combo.blockSignals(False)

    # --- STYLY A LOGIKA ---

    def update_style(self):
        self.content_widget.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        self.lbl_main.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLORS['fg']}; margin-bottom: 20px;")
        self.footer_widget.setStyleSheet(f"#SettingsFooter {{ background-color: {COLORS['bg_main']}; border-top: 1px solid {COLORS['border']}; }}")
        
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{ background-color: transparent; border: none; }}
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS['border']}; min-height: 20px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS['accent']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        """)

    def save_theme(self, index):
        if index >= 0:
            key = self.theme_combo.itemData(index)
            self.settings["theme"] = key
            SettingsManager.save_settings(self.settings)
            theme_manager.set_theme(key)

    def save_lang(self, text):
        self.settings["language"] = text
        SettingsManager.save_settings(self.settings)
        translator.set_language(text)

    def show_about_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(_("about_title"))
        
        msg.setText(f"<h3 style='color: {COLORS['fg']}; margin-bottom: 5px;'>OmniDesk</h3><p style='margin-top: 0px;'>v{CURRENT_VERSION}</p>")
        msg.setInformativeText(
            f"{_('about_desc1')}\n\n"
            f"{_('about_desc2')}\n\n"
            f"{_('about_author')} Vít Šebestík / Visse\n"
            f"© 2026 {_('about_rights')}"
        )
        
        try:
            from ctypes import windll, byref, c_int
            hwnd = msg.winId().__int__()
            windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(c_int(1)), 4)
            color_hex = COLORS['bg_main'].lstrip('#')
            r, g, b = int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16)
            dwm_color = (b << 16) | (g << 8) | r
            windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, byref(c_int(dwm_color)), 4)
            windll.dwmapi.DwmSetWindowAttribute(hwnd, 36, byref(c_int(0x00FFFFFF)), 4)
        except: pass
        
        # Stylování do motivu
        msg.setStyleSheet(f"""
            QMessageBox {{ background-color: {COLORS['bg_main']}; }}
            QLabel {{ color: {COLORS['sub_text']}; font-size: 13px; }}
            QPushButton {{ 
                background-color: {COLORS['item_bg']}; 
                color: {COLORS['fg']}; 
                border: 1px solid {COLORS['border']}; 
                padding: 6px 20px; 
                border-radius: 4px; 
                font-weight: bold;
            }}
            QPushButton:hover {{ 
                background-color: {COLORS['accent']}; 
                color: white; 
                border: 1px solid {COLORS['accent']};
            }}
        """)
        msg.exec()
