import webbrowser
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QMessageBox, QScrollArea)
from PyQt6.QtCore import Qt

from core.config import COLORS, THEMES, CURRENT_VERSION
from core.settings_manager import SettingsManager

# Import našich animovaných widgetů ze sdíleného souboru (přidán add_vertical_separator)
from UI.shared_widgets import AnimatedActionButton, AnimatedComboBox, add_vertical_separator

from core.i18n import _, translator
from core.theme_manager import theme_manager

# --- POMOCNÉ WIDGETY ---

class SectionHeader(QLabel):
    def __init__(self, text_key):
        super().__init__()
        self.text_key = text_key
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()
        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['sub_text']}; margin-top: 25px; margin-bottom: 10px;")

    def retranslate_ui(self):
        self.setText(_(self.text_key))

class Separator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()
        
    def update_style(self):
        self.setStyleSheet(f"background-color: {COLORS['border']}; margin-top: 15px; margin-bottom: 15px;")

class SettingRow(QWidget):
    def __init__(self, title_key, desc_key, widget):
        super().__init__()
        self.title_key = title_key
        self.desc_key = desc_key
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        
        text_layout = QVBoxLayout()
        self.lbl_title = QLabel()
        self.lbl_desc = QLabel()
        self.lbl_desc.setWordWrap(True)
        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_desc)
        
        layout.addLayout(text_layout, stretch=1)
        layout.addSpacing(20)
        layout.addWidget(widget)

        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.lbl_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLORS['fg']};")
        self.lbl_desc.setStyleSheet(f"font-size: 12px; color: {COLORS['sub_text']};")

    def retranslate_ui(self):
        self.lbl_title.setText(_(self.title_key))
        self.lbl_desc.setText(_(self.desc_key))

# --- HLAVNÍ STRÁNKA NASTAVENÍ ---
