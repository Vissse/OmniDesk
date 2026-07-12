import os
import json
import subprocess
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QMessageBox, QFileDialog, QFrame, QLineEdit)
from PyQt6.QtCore import Qt, QSize, QVariantAnimation, QRect, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QPainter, QPainterPath

from core.config import COLORS, resource_path
from core.theme_manager import theme_manager
from core.install_manager import InstallationDialog
from UI.pages.view_installer import InstallationOptionsDialog
from UI.shared_widgets import AnimatedActionButton, add_vertical_separator
from UI.pages.view_installer import InstallationOptionsDialog, HoverButton
from UI.workers.install_worker import VersionFetchWorker

class QueueRowWidget(QWidget):
    def __init__(self, data, parent_controller, queue_page_ref, cached_icon=None):
        super().__init__()
        self.data = data
        self.controller = parent_controller
        self.queue_page = queue_page_ref
        self.current_pixmap = cached_icon

        self.setFixedHeight(55)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._bg_color = QColor("transparent")
        self._bar_height_factor = 0.0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 2, 20, 2)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Ikonka aplikace
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(28, 28)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if cached_icon:
            self.set_icon(cached_icon)
        else:
            icon_path = data.get('icon_url')
            if icon_path and os.path.exists(icon_path):
                pix = QPixmap(icon_path).scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.icon_lbl.setPixmap(pix)
            else:
                self.icon_lbl.setText("📦") 
                self.icon_lbl.setStyleSheet(f"font-size: 16px; color: {COLORS['sub_text']}; border: none; background: transparent;")
        layout.addWidget(self.icon_lbl)

        # Texty (Název, oddělovač, verze)
        text_layout = QHBoxLayout()
        text_layout.setSpacing(8)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.name_lbl = QLabel(data['name'])
        text_layout.addWidget(self.name_lbl)
        
        self.sep_lbl = QLabel("•")
        text_layout.addWidget(self.sep_lbl)

        self.ver_lbl = QLabel(data.get('version', 'Načítání...'))
        text_layout.addWidget(self.ver_lbl)

        text_layout.addStretch()
        layout.addLayout(text_layout, stretch=1)

        # Tlačítko pro odstranění (křížek) zarovnané doprava
        self.btn_remove = HoverButton("", "assets/images/x-thin.png", "sub_text", hover_style="danger")
        self.btn_remove.setFixedSize(28, 28)
        self.btn_remove.setIconSize(QSize(18, 18))
        self.btn_remove.setToolTip("Odebrat aplikaci z fronty")
        self.btn_remove.clicked.connect(self.remove_self)
        layout.addWidget(self.btn_remove)

        # Načítání verze na pozadí
        if data.get('version') in [None, "Latest", "Unknown", "Neznámá", "Načítání...", ""]:
            self.ver_lbl.setText("Načítání...")
            self.ver_worker = VersionFetchWorker(self.data['id'])
            self.ver_worker.version_found.connect(self.on_version_found)
            self.ver_worker.start()

        # Animace při najetí myší
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)
        
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

    def update_style(self):
        self.name_lbl.setStyleSheet(f"font-weight: bold; color: {COLORS['fg']}; font-size: 14px; background: transparent;")
        self.sep_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 14px; font-weight: bold; background: transparent;")
        self.ver_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 12px; background: transparent;")

    def remove_self(self):
        self.queue_page.remove_item_by_id(self.data['id'])

    def on_version_found(self, version):
        self.ver_lbl.setText(version)
        self.data['version'] = version

    def set_icon(self, pixmap):
        self.current_pixmap = pixmap
        scaled = pixmap.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.icon_lbl.setPixmap(scaled)
        self.icon_lbl.setText("")

    def _animate_step(self, val):
        self._bar_height_factor = val
        target_bg = QColor(COLORS.get('item_hover', '#2d2d30'))
        self._bg_color = QColor(target_bg.red(), target_bg.green(), target_bg.blue(), int(255 * val))
        self.update()

    def enterEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Forward)
        self.anim.start()

    def leaveEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Backward)
        self.anim.start()

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
            p.setBrush(QColor(COLORS.get('accent', '#0078d4')))
            p.setPen(Qt.PenStyle.NoPen)
            h = rect.height() * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            
            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)
            p.setClipPath(path)
            p.drawRect(QRect(rect.x(), int(y), 4, int(h)))
            p.setClipping(False)


