import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGridLayout, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QVariantAnimation
from PyQt6.QtGui import QPixmap, QPainter, QColor

from core.config import COLORS, CURRENT_VERSION, resource_path
from core.i18n import _, translator
from core.theme_manager import theme_manager

from UI.components.home_components import ModuleCard

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll Area pro případ menšího okna
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        
        content_widget = QWidget()
        content_widget.setObjectName("homeContainer")
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(45, 50, 45, 40)
        content_layout.setSpacing(35)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # --- 1. HEADER ---
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        try: 
            user = os.getlogin()
        except: 
            user = "Uživatel"
            
        self.lbl_welcome = QLabel()
        
        self.lbl_intro = QLabel()

        
        header_layout.addWidget(self.lbl_welcome)
        header_layout.addWidget(self.lbl_intro)
        content_layout.addLayout(header_layout)

        # --- 2. MŘÍŽKA MODULŮ ---
        grid = QGridLayout()
        grid.setSpacing(20)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        
        modules = [
            ("package-thin.png", "nav_catalog", "home_desc_catalog"),
            ("tray-arrow-down-thin.png", "nav_queue", "home_desc_queue"),
            ("arrows-clockwise-thin.png", "nav_updates", "home_desc_updates"),
            ("trash-simple-thin.png", "nav_uninstall", "home_desc_uninstall"),
            ("heartbeat-thin.png", "nav_health", "home_desc_health"),
            ("desktop-thin.png", "nav_specs", "home_desc_specs")
        ]
        
        # Automatické rozestavení do 2 sloupců
        for index, (icon, title, desc) in enumerate(modules):
            row = index // 2
            col = index % 2
            grid.addWidget(ModuleCard(icon, title, desc, self), row, col)

        content_layout.addLayout(grid)
        content_layout.addStretch()
        
        # --- 3. FOOTER ---
        self.lbl_footer = QLabel()
        self.lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.lbl_footer)

        self.scroll.setWidget(content_widget)
        main_layout.addWidget(self.scroll)

        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QWidget#homeContainer {{ background: transparent; }}
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS['border']}; min-height: 20px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS['accent']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        self.lbl_welcome.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {COLORS['fg']};")
        self.lbl_intro.setStyleSheet(f"font-size: 14px; color: {COLORS['sub_text']};")
        self.lbl_footer.setStyleSheet(f"color: {COLORS['border']}; font-size: 11px; font-weight: bold;")

    def retranslate_ui(self):
        try: user = os.getlogin()
        except: user = "User"
        self.lbl_welcome.setText(_("home_welcome").format(user=user))
        self.lbl_intro.setText(_("home_intro"))
        self.lbl_footer.setText(_("home_footer").format(ver=CURRENT_VERSION))
