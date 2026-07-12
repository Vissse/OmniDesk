import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGridLayout, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QVariantAnimation
from PyQt6.QtGui import QPixmap, QPainter, QColor

from core.config import COLORS, CURRENT_VERSION, resource_path
from core.i18n import _, translator
from core.theme_manager import theme_manager
class ModuleCard(QFrame):
    """Moderní, minimalistická karta modulu s hover animací."""
    def __init__(self, icon_name, title_key, desc_key, parent=None):
        super().__init__(parent)
        self.title_key = title_key
        self.desc_key = desc_key
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
        
        self.icon_name = icon_name
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(24, 24)
        self.icon_lbl.setText("•")
            
        # Nadpis
        self.title_lbl = QLabel()
        
        top_layout.addWidget(self.icon_lbl)
        top_layout.addWidget(self.title_lbl)
        top_layout.addStretch()
        
        # --- SPODNÍ ŘÁDEK (Popis) ---
        self.desc_lbl = QLabel()
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        layout.addLayout(top_layout)
        layout.addWidget(self.desc_lbl)
        
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()
        
        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self._bg_color = QColor(COLORS['item_bg'])
        self.title_lbl.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['fg']}; background: transparent;")
        self.desc_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['sub_text']}; background: transparent; line-height: 1.3;")
        
        icon_path = resource_path(os.path.join("assets/images", self.icon_name))
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            colored = QPixmap(pix.size())
            colored.fill(Qt.GlobalColor.transparent)
            p = QPainter(colored)
            p.drawPixmap(0, 0, pix)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(colored.rect(), QColor(COLORS['fg']))
            p.end()
            self.icon_lbl.setPixmap(colored)
        else:
            self.icon_lbl.setStyleSheet(f"color: {COLORS['fg']}; font-weight: bold;")
        self.update()

    def retranslate_ui(self):
        self.title_lbl.setText(_(self.title_key))
        self.desc_lbl.setText(_(self.desc_key))
        
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


