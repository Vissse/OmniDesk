import subprocess # Přidáno
import os
import ctypes
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QMessageBox,
                             QDialog, QTextEdit, QProgressBar)  
from PyQt6.QtCore import Qt, QVariantAnimation, QRect, QTimer, QThread, pyqtSignal, QProcess
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPainterPath

from core.config import COLORS
from core.config import resource_path
from core.i18n import _, translator
from core.theme_manager import theme_manager

class PlayButton(QPushButton):
    """Minimalistické tlačítko tvořené pouze ikonkou, které reaguje na najetí."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.icon_path = resource_path("assets/images/play-thin.png")
        self._hover = False
        self.setStyleSheet("background: transparent; border: none;")
        theme_manager.theme_changed.connect(self.update_style)

    def update_style(self):
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self._hover:
            p.setBrush(QColor(COLORS['item_hover']))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(self.rect())
            
        if os.path.exists(self.icon_path):
            pix = QPixmap(self.icon_path).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            colored_pix = QPixmap(pix.size())
            colored_pix.fill(Qt.GlobalColor.transparent)
            
            cp = QPainter(colored_pix)
            cp.drawPixmap(0, 0, pix)
            cp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            color = QColor(COLORS['accent']) if self._hover else QColor(COLORS['fg'])
            cp.fillRect(colored_pix.rect(), color)
            cp.end()
            
            x = (self.width() - 18) // 2
            y = (self.height() - 18) // 2
            p.drawPixmap(x, y, colored_pix)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()


class ToolRowWidget(QFrame):
    def __init__(self, icon_name, title_key, desc_key, command, log_desc_key, parent_view, is_gui=False, is_powershell=False):
        super().__init__()
        self.title_key = title_key
        self.desc_key = desc_key
        self.command = command
        self.log_desc_key = log_desc_key
        self.parent_view = parent_view
        self.is_gui = is_gui
        self.is_powershell = is_powershell
        self.setFixedHeight(55)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._bg_color = QColor("transparent")
        self._bar_height_factor = 0.0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 2, 20, 2)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # 1. IKONA
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(24, 24)
        
        # Cesta může být buď v images nebo v icons (pro chris.png)
        self.icon_name = icon_name
        potential_paths = [
            resource_path(os.path.join("assets/images", icon_name)),
            resource_path(os.path.join("assets/icons", icon_name))
        ]
        
        self.icon_path = next((p for p in potential_paths if os.path.exists(p)), None)
        
        if self.icon_path:
            pix = QPixmap(self.icon_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            # Pokud je to chris.png, nekreslíme ho jednobarevně, abychom zachovali barvy loga
            if "chris" in icon_name:
                self.icon_lbl.setPixmap(pix)
            else:
                colored_pix = QPixmap(pix.size())
                colored_pix.fill(Qt.GlobalColor.transparent)
                cp = QPainter(colored_pix)
                cp.drawPixmap(0, 0, pix)
                cp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                cp.fillRect(colored_pix.rect(), QColor(COLORS['sub_text']))
                cp.end()
                self.icon_lbl.setPixmap(colored_pix)
        
        layout.addWidget(self.icon_lbl)
        
        # 2. TEXTY
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.t_lbl = QLabel()
        self.d_lbl = QLabel()
        
        text_layout.addWidget(self.t_lbl)
        text_layout.addWidget(self.d_lbl)
        layout.addLayout(text_layout, stretch=1)
        
        # 3. PLAY TLAČÍTKO
        self.btn_run = PlayButton()
        self.btn_run.clicked.connect(self.run_tool)
        layout.addWidget(self.btn_run)
        
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()
        
        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.t_lbl.setStyleSheet(f"color: {COLORS['fg']}; font-size: 13px; font-weight: bold; background: transparent;")
        self.d_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 11px; background: transparent;")
        
        # Obnovení ikony, pokud není "chris"
        if "chris" not in self.icon_name and self.icon_path:
            pix = QPixmap(self.icon_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            colored_pix = QPixmap(pix.size())
            colored_pix.fill(Qt.GlobalColor.transparent)
            cp = QPainter(colored_pix)
            cp.drawPixmap(0, 0, pix)
            cp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            cp.fillRect(colored_pix.rect(), QColor(COLORS['sub_text']))
            cp.end()
            self.icon_lbl.setPixmap(colored_pix)
        
        self.update()

    def retranslate_ui(self):
        title = _(self.title_key)
        self.t_lbl.setText(title)
        self.d_lbl.setText(_(self.desc_key))
        self.btn_run.setToolTip(_("btn_run_tooltip").format(title=title) if "btn_run_tooltip" in translator._("btn_run_tooltip") else f"Run {title}")
        
        # Animace
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)
        
    def _animate_step(self, val):
        self._bar_height_factor = val
        target_bg = QColor(COLORS['item_hover'])
        self._bg_color = QColor(target_bg.red(), target_bg.green(), target_bg.blue(), int(255 * val))
        self.update()

    def enterEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Forward)
        self.anim.start()

    def leaveEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Backward)
        self.anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.run_tool()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        radius = 6
        
        if self._bg_color.alpha() > 0:
            p.setBrush(self._bg_color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, radius, radius)
            
        if self._bar_height_factor > 0:
            p.setBrush(QColor(COLORS['accent']))
            p.setPen(Qt.PenStyle.NoPen)
            h = rect.height() * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            
            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)
            p.setClipPath(path)
            p.drawRect(QRect(rect.x(), int(y), 4, int(h)))
            p.setClipping(False)
            
    def run_tool(self):
        self.parent_view.execute_tool(self.command, _(self.log_desc_key), self.is_gui, self.is_powershell)

