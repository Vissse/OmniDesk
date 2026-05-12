import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGridLayout, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QVariantAnimation
from PyQt6.QtGui import QPixmap, QPainter, QColor

from core.config import COLORS, CURRENT_VERSION, resource_path

class ModuleCard(QFrame):
    """Moderní, minimalistická karta modulu s hover animací."""
    def __init__(self, icon_name, title, desc, parent=None):
        super().__init__(parent)
        self.setFixedHeight(115)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Výchozí barvy pro animaci
        self._bg_color = QColor(COLORS['item_bg'])
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        
        # --- HORNÍ ŘÁDEK (Ikona + Nadpis) ---
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Ikona
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(24, 24)
        icon_path = resource_path(os.path.join("assets/images", icon_name))
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            colored = QPixmap(pix.size())
            colored.fill(Qt.GlobalColor.transparent)
            p = QPainter(colored)
            p.drawPixmap(0, 0, pix)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(colored.rect(), QColor(COLORS['fg']))
            p.end()
            icon_lbl.setPixmap(colored)
        else:
            icon_lbl.setText("•")
            icon_lbl.setStyleSheet(f"color: {COLORS['fg']}; font-weight: bold;")
            
        # Nadpis
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['fg']}; background: transparent;")
        
        top_layout.addWidget(icon_lbl)
        top_layout.addWidget(title_lbl)
        top_layout.addStretch()
        
        # --- SPODNÍ ŘÁDEK (Popis) ---
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['sub_text']}; background: transparent; line-height: 1.3;")
        
        layout.addLayout(top_layout)
        layout.addWidget(desc_lbl)
        
        # --- ANIMACE ---
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)

    def _animate_step(self, val):
        c_start = QColor(COLORS['item_bg'])
        c_end = QColor(COLORS['item_hover'])
        r = c_start.red() + (c_end.red() - c_start.red()) * val
        g = c_start.green() + (c_end.green() - c_start.green()) * val
        b = c_start.blue() + (c_end.blue() - c_start.blue()) * val
        self._bg_color = QColor(int(r), int(g), int(b))
        self.update()

    def enterEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Forward)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Backward)
        self.anim.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(0, 0, -1, -1)
        radius = 8
        
        # Vykreslení pozadí a jemného rámečku
        p.setBrush(self._bg_color)
        p.setPen(QColor(COLORS['border']))
        p.drawRoundedRect(rect, radius, radius)
        p.end()


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll Area pro případ menšího okna
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ border: none; background-color: {COLORS['bg_main']}; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: #444; min-height: 20px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS['accent']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        
        content_widget = QWidget()
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
            
        lbl_welcome = QLabel(f"Vítejte, {user}")
        lbl_welcome.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        
        lbl_intro = QLabel("Toto je váš centrální rozcestník pro správu systému a aplikací.")
        lbl_intro.setStyleSheet(f"font-size: 14px; color: {COLORS['sub_text']};")
        
        header_layout.addWidget(lbl_welcome)
        header_layout.addWidget(lbl_intro)
        content_layout.addLayout(header_layout)

        # --- 2. MŘÍŽKA MODULŮ ---
        grid = QGridLayout()
        grid.setSpacing(20)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        
        modules = [
            ("package-thin.png", "Katalog aplikací", "Procházejte a instalujte nový software čistě a bez zbytečného klikání."),
            ("tray-arrow-down-thin.png", "Instalační fronta", "Hromadná, tichá instalace a automatická konfigurace vybraných programů."),
            ("arrows-clockwise-thin.png", "Aktualizace", "Udržujte svůj systém v bezpečí pomocí hromadných aktualizací zastaralých verzí."),
            ("trash-simple-thin.png", "Odinstalace", "Rychlé a čisté odstranění nepotřebného softwaru ze systému."),
            ("heartbeat-thin.png", "Údržba PC", "Sada diagnostických nástrojů, opravy systémových chyb a čištění disku."),
            ("desktop-thin.png", "Specifikace HW", "Detailní přehled o hardwaru, komponentách a úložištích vašeho počítače.")
        ]
        
        # Automatické rozestavení do 2 sloupců
        for index, (icon, title, desc) in enumerate(modules):
            row = index // 2
            col = index % 2
            grid.addWidget(ModuleCard(icon, title, desc, self), row, col)

        content_layout.addLayout(grid)
        content_layout.addStretch()
        
        # --- 3. FOOTER ---
        lbl_footer = QLabel(f"OmniDesk v{CURRENT_VERSION} • Moderní správce systému")
        lbl_footer.setStyleSheet(f"color: {COLORS['border']}; font-size: 11px; font-weight: bold;")
        lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(lbl_footer)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)