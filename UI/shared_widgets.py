import os
import requests
from PyQt6.QtWidgets import QPushButton, QFrame, QComboBox, QListView
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QVariantAnimation, QRect, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPainterPath, QImage
from core.config import COLORS, resource_path
from core.theme_manager import theme_manager

class AnimatedSidebarButton(QPushButton):
    def __init__(self, text, icon_path, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(48)
        self.icon_path = icon_path
        self.active = False
        self._bg_color = QColor("transparent")
        self._bar_height_factor = 0.0
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(250)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)
        theme_manager.theme_changed.connect(lambda: self.update_visuals())
        self.update_visuals()

    def set_active(self, active):
        self.active = active
        self._bar_height_factor = 1.0 if active else 0.0
        self._bg_color = QColor(COLORS['item_bg']) if active else QColor("transparent")
        self.update_visuals()
        self.update()

    def _animate_step(self, val):
        if not self.active:
            self._bar_height_factor = val
            target_bg = QColor(COLORS['item_hover'])
            self._bg_color = QColor(target_bg.red(), target_bg.green(), target_bg.blue(), int(255 * val))
            self.update_visuals(val > 0.5)
        self.update()

    def update_visuals(self, hover=False):
        is_highlighted = self.active or hover
        color_hex = COLORS['fg'] if is_highlighted else COLORS['sub_text']
        
        if self.active:
            self._bg_color = QColor(COLORS['item_bg'])
        
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent; 
                border: none; 
                text-align: left; 
                padding-left: 20px; 
                font-weight: 500; 
                color: {color_hex};
            }}
        """)
        
        # Zbarvení ikony podle stavu tlačítka
        icon_color_hex = COLORS['accent'] if self.active else color_hex
        full_icon_path = resource_path(self.icon_path)
        if os.path.exists(full_icon_path):
            pix = QPixmap(full_icon_path)
            if not pix.isNull():
                canvas = QPixmap(pix.size())
                canvas.fill(Qt.GlobalColor.transparent)
                p = QPainter(canvas)
                p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                p.drawPixmap(0, 0, pix)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                p.fillRect(canvas.rect(), QColor(icon_color_hex))
                p.end()
                self.setIcon(QIcon(canvas))
            self.setIconSize(QSize(24, 24))
            
        self.update()

    def enterEvent(self, event):
        if not self.active:
            self.anim.setDirection(QVariantAnimation.Direction.Forward)
            self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.active:
            self.anim.setDirection(QVariantAnimation.Direction.Backward)
            self.anim.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Odsazení odpovídá položkám v QListWidget
        rect = self.rect().adjusted(10, 2, -10, -2)
        radius = 6

        # Vykreslení hover pozadí
        if self._bg_color.alpha() > 0:
            p.setBrush(self._bg_color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, radius, radius)

        # Vykreslení aktivního modrého proužku
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

        # UKONČENÍ KRESLENÍ ZABRÁNÍ PÁDU!
        p.end()
        
        super().paintEvent(event)

class AnimatedActionButton(QPushButton):
    def __init__(self, text, icon_path, parent=None, bar_align="left", hover_color="accent"):
        super().__init__(text, parent)
        self.setFixedHeight(34)
        self.icon_path = icon_path
        self.bar_align = bar_align
        self.hover_color = hover_color
        
        self._bg_color = QColor("transparent")
        self._bar_height_factor = 0.0
        
        self.setStyleSheet(f"""
            QPushButton {{ 
                background: transparent; 
                color: {COLORS['fg']}; 
                border: none; 
                padding: 0 15px; 
                font-weight: bold; 
                font-size: 10pt; 
                text-align: left;
            }}
            QPushButton:disabled {{ 
                color: {COLORS['sub_text']}; 
            }}
        """)
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)
        theme_manager.theme_changed.connect(self.update_visual_state)
        self.update_visual_state()

    def get_colored_icon(self, color_hex):
        full_path = resource_path(self.icon_path)
        if not os.path.exists(full_path): return QIcon()
        pixmap = QPixmap(full_path)
        colored = QPixmap(pixmap.size())
        colored.fill(Qt.GlobalColor.transparent)
        p = QPainter(colored)
        p.drawPixmap(0, 0, pixmap)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(colored.rect(), QColor(color_hex))
        p.end()
        return QIcon(colored)

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.update_visual_state()

    def update_visual_state(self):
        self.setStyleSheet(f"""
            QPushButton {{ 
                background: transparent; 
                color: {COLORS['fg']}; 
                border: none; 
                padding: 0 15px; 
                font-weight: bold; 
                font-size: 10pt; 
                text-align: left;
            }}
            QPushButton:disabled {{ 
                color: {COLORS['sub_text']}; 
            }}
        """)
        if self.isEnabled():
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            if self.icon_path:
                self.setIcon(self.get_colored_icon(COLORS['fg']))
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            if self.icon_path:
                self.setIcon(self.get_colored_icon(COLORS['sub_text']))
            self.anim.stop()
            self._bar_height_factor = 0.0
            self._bg_color = QColor("transparent")
        self.update()

    def _animate_step(self, val):
        self._bar_height_factor = val
        target_bg = QColor(COLORS['item_hover'])
        self._bg_color = QColor(target_bg.red(), target_bg.green(), target_bg.blue(), int(255 * val))
        self.update()

    def enterEvent(self, event):
        if self.isEnabled():
            self.anim.setDirection(QVariantAnimation.Direction.Forward)
            self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.isEnabled():
            self.anim.setDirection(QVariantAnimation.Direction.Backward)
            self.anim.start()
        else:
            self._bar_height_factor = 0.0
            self._bg_color = QColor("transparent")
            self.update()
        super().leaveEvent(event)

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
            p.setBrush(QColor(COLORS.get(self.hover_color, COLORS['accent'])))
            p.setPen(Qt.PenStyle.NoPen)
            h = rect.height() * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            
            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)
            p.setClipPath(path)
            
            if self.bar_align == "right":
                p.drawRect(QRect(rect.right() - 4, int(y), 4, int(h)))
            else:
                p.drawRect(QRect(rect.x(), int(y), 4, int(h)))
                
            p.setClipping(False)
            
        p.end()
        super().paintEvent(event)

class IconDownloadWorker(QThread):
    loaded = pyqtSignal(QPixmap)

    def __init__(self, app_id):
        super().__init__()
        self.app_id = app_id

    def run(self):
        if not self.app_id: return
        clean_id = self.app_id
        lower_id = self.app_id.lower()
        dashed_id = lower_id.replace(".", "-")
        urls = [
            f"https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/{dashed_id}.png",
            f"https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/{lower_id}.png",
            f"https://raw.githubusercontent.com/marticliment/UnigetUI/main/src/UnigetUI.PackageEngine/Assets/Packages/{clean_id}.png",
            f"https://raw.githubusercontent.com/marticliment/UnigetUI/main/src/UnigetUI.PackageEngine/Assets/Packages/{lower_id}.png"
        ]
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        for url in urls:
            try:
                response = session.get(url, timeout=1.5, stream=True)
                if response.status_code == 200:
                    data = response.content
                    if len(data) > 50:
                        image = QImage(); image.loadFromData(data)
                        if not image.isNull():
                            pixmap = QPixmap.fromImage(image)
                            self.loaded.emit(pixmap); return
            except: pass

class VerticalSeparator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFixedWidth(1)
        self.setFixedHeight(18)
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()
    def update_style(self):
        self.setStyleSheet(f"background: {COLORS['border']}; border: none;")

def add_vertical_separator(layout):
    sep = VerticalSeparator()
    layout.addWidget(sep)

class AnimatedComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._bg_color = QColor(COLORS['input_bg'])
        self._bar_height_factor = 0.0
        
        # Nastavení QListView umožňuje stylovat vyjížděcí menu
        view = QListView()
        view.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setView(view)
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

    def update_style(self):
        self._bg_color = QColor(COLORS["input_bg"])
        # Zrušíme výchozí pozadí/rámeček combo boxu - budeme ho kreslit sami v paintEvent
        self.setStyleSheet(f"""
            QComboBox {{ 
                background: transparent; 
                color: {COLORS['fg']}; 
                border: none; 
                padding: 5px 15px; 
                font-weight: bold;
            }} 
            QComboBox::drop-down {{ 
                border: none; 
                width: 30px; 
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_main']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 34px;
                padding-left: 10px;
                color: {COLORS['fg']};
                border-left: 3px solid transparent;
                font-weight: bold;
            }}
            QComboBox QAbstractItemView::item:hover, 
            QComboBox QAbstractItemView::item:selected {{
                background-color: {COLORS['item_hover']};
                color: {COLORS['fg']};
                border-left: 3px solid {COLORS['accent']};
            }}
        """)
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)

    def _animate_step(self, val):
        self._bar_height_factor = val
        c_start = QColor(COLORS['input_bg'])
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
        
        rect = self.rect()
        radius = 4
        
        # Vykreslení pozadí boxu
        p.setBrush(self._bg_color)
        p.setPen(QColor(COLORS['border']))
        p.drawRoundedRect(rect.adjusted(0, 0, -1, -1), radius, radius)
        
        # Vykreslení animovaného proužku na levé straně!
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
            
        p.end()
        super().paintEvent(event)