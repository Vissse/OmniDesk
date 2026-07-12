import subprocess
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QLineEdit, 
                             QMessageBox, QFileIconProvider, QFrame, QProgressBar,
                             QCheckBox, QTextEdit)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QFileInfo, QTimer, QVariantAnimation, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QImage, QIcon, QPainter, QColor, QPainterPath

from core.workers import WingetListWorker
from core.config import COLORS, resource_path
from core.utils import find_app_icon_path, find_main_exe_in_folder
from core.theme_manager import theme_manager
from UI.shared_widgets import AnimatedActionButton, IconDownloadWorker, add_vertical_separator

class AppItemWidget(QWidget):
    def __init__(self, data, parent_page):
        super().__init__()
        self.data = data
        self.parent_page = parent_page
        
        self.setFixedHeight(55) 
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._bg_color = QColor("transparent")
        self._bar_height_factor = 0.0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 2, 20, 2)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.chk = QCheckBox()
        self.chk.setFixedWidth(24)
        self.chk.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk.setStyleSheet(f"""
            QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid {COLORS['sub_text']}; border-radius: 4px; background: transparent; }}
            QCheckBox::indicator:checked {{ background-color: {COLORS['accent']}; border-color: {COLORS['accent']}; image: url(check.png); }} 
        """)
        self.chk.stateChanged.connect(lambda state: self.parent_page.update_selection_ui())
        layout.addWidget(self.chk)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(28, 28)
        
        found_local = self.set_local_icon(data['name'], data['id'])
        if not found_local:
            if self.set_system_fallback_icon(data['name']): pass 
            else:
                self.icon_lbl.setText("📦")
                self.icon_lbl.setStyleSheet(f"font-size: 16px; color: {COLORS['sub_text']}; background: transparent;")
                self.dl_worker = IconDownloadWorker(data['id'])
                self.dl_worker.loaded.connect(self.set_downloaded_icon)
                self.dl_worker.start()
        
        layout.addWidget(self.icon_lbl)

        text_layout = QHBoxLayout()
        text_layout.setSpacing(15)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.name_lbl = QLabel(data['name'])
        self.id_lbl = QLabel(data['id'])
        
        text_layout.addWidget(self.name_lbl)
        text_layout.addWidget(self.id_lbl)
        text_layout.addStretch() 
        
        layout.addLayout(text_layout, stretch=1)

        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)
        
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

    def update_style(self):
        self.chk.setStyleSheet(f"""
            QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid {COLORS['sub_text']}; border-radius: 4px; background: transparent; }}
            QCheckBox::indicator:checked {{ background-color: {COLORS['accent']}; border-color: {COLORS['accent']}; image: url(check.png); }} 
        """)
        self.name_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLORS['fg']}; background: transparent;")
        self.id_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['sub_text']}; background: transparent;")

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
            if not self.chk.underMouse():
                self.chk.setChecked(not self.chk.isChecked())
        super().mousePressEvent(event)

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

    def set_local_icon(self, name, app_id):
        icon_path = find_app_icon_path(name, app_id)
        if icon_path and os.path.exists(icon_path):
            pix = QFileIconProvider().icon(QFileInfo(icon_path)).pixmap(24, 24)
            if not pix.isNull():
                self.icon_lbl.setPixmap(pix)
                self.icon_lbl.setStyleSheet("background: transparent;")
                return True
        return False

    def set_system_fallback_icon(self, name):
        n = name.lower()
        icon_name = None
        use_original = False
        
        if any(x in n for x in ["java", "jdk", "jre", "temurin"]): 
            icon_name = "java.png"
            use_original = True
        elif any(x in n for x in ["microsoft", "windows", "redist", "c++", ".net"]):
            icon_name = "windows.png"
            use_original = True
        elif any(x in n for x in ["driver", "nvidia", "amd", "intel"]): 
            icon_name = "circuitry-thin.png"
        
        if icon_name:
            path = resource_path(f"assets/images/{icon_name}")
            if os.path.exists(path):
                pix = QPixmap(path).scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                if not use_original:
                    p = QPainter(pix); p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                    p.fillRect(pix.rect(), QColor(COLORS['sub_text'])); p.end()
                self.icon_lbl.setPixmap(pix)
                return True
        return False

    def set_downloaded_icon(self, pixmap):
        scaled = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.icon_lbl.setPixmap(scaled); self.icon_lbl.setText("")

