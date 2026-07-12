import os
from PyQt6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QApplication, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QVariantAnimation, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap, QPainter, QPainterPath

from core.config import COLORS, resource_path
from core.i18n import _, translator
from core.theme_manager import theme_manager

class SpecRow(QFrame):
    def __init__(self, title_key, value, parent_page=None):
        super().__init__()
        self.parent_page = parent_page
        self.title_key = title_key
        self.copy_text = str(value)
        self.setMinimumHeight(45)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._bar_height_factor = 0.0
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 5, 20, 5) 
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.t_lbl = QLabel()
        self.t_lbl.setFixedWidth(160)
        
        self.v_lbl = QLabel(str(value))
        self.v_lbl.setWordWrap(False)
        
        self.copy_icon = QLabel()
        self.op_effect = QGraphicsOpacityEffect(self.copy_icon)
        self.op_effect.setOpacity(0.0)
        self.copy_icon.setGraphicsEffect(self.op_effect)

        self.layout.addWidget(self.t_lbl)
        self.layout.addWidget(self.v_lbl)
        self.layout.addWidget(self.copy_icon)
        self.layout.addStretch() 
        
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)
        
        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.t_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 10px; font-weight: bold; background: transparent;")
        self.v_lbl.setStyleSheet(f"color: {COLORS['fg']}; font-size: 13px; font-weight: 500; background: transparent;")
        
        icon_path = resource_path("assets/images/copy-simple-thin.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            p = QPainter(pix)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(pix.rect(), QColor(COLORS['sub_text']))
            p.end()
            self.copy_icon.setPixmap(pix)

    def retranslate_ui(self):
        title_str = self.title_key
        if title_str.startswith("sp_slot ") or title_str.startswith("sp_display "):
            parts = title_str.split(" ")
            base = _(parts[0])
            self.t_lbl.setText(f"{base} {parts[1]}".upper())
        else:
            self.t_lbl.setText(_(title_str).upper())
        
    def _animate_step(self, val):
        self._bar_height_factor = val
        self.op_effect.setOpacity(val)
        
        c_start = QColor(COLORS['sub_text'])
        c_end = QColor("#cccccc")
        r = c_start.red() + (c_end.red() - c_start.red()) * val
        g = c_start.green() + (c_end.green() - c_start.green()) * val
        b = c_start.blue() + (c_end.blue() - c_start.blue()) * val
        self.t_lbl.setStyleSheet(f"color: rgb({int(r)}, {int(g)}, {int(b)}); font-size: 10px; font-weight: bold; background: transparent;")
        self.update()

    def enterEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Forward)
        self.anim.start()

    def leaveEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Backward)
        self.anim.start()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.parent_page:
            QApplication.clipboard().setText(self.copy_text)
            self.parent_page.show_copy_notification()

    def paintEvent(self, event):
        if self._bar_height_factor > 0:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = self.rect()
            p.setBrush(QColor(COLORS['accent']))
            p.setPen(Qt.PenStyle.NoPen)
            
            radius = 1
            w = 3
            h = 16 * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            x = 4 
            
            path = QPainterPath()
            path.addRoundedRect(int(x), int(y), w, int(h), radius, radius)
            p.drawPath(path)

class SpecGroup(QFrame):
    def __init__(self, parent_page=None):
        super().__init__()
        self.parent_page = parent_page
        self.setObjectName("specGroup")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(0)
        self.rows = []
        self.seps = []
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

    def update_style(self):
        self.setStyleSheet(f"#specGroup {{ background-color: {COLORS['item_bg']}; border-radius: 8px; }}")
        for sep in self.seps:
            sep.setStyleSheet(f"background-color: {COLORS['border']}; margin-left: 15px; margin-right: 15px;")

    def add_row(self, title, value):
        if self.rows:
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background-color: {COLORS['border']}; margin-left: 15px; margin-right: 15px;")
            self.layout.addWidget(sep)
            self.seps.append(sep)
            
        row = SpecRow(title, value, self.parent_page)
        self.layout.addWidget(row)
        self.rows.append(row)

class DiskRow(QFrame):
    def __init__(self, disk_data, col_widths, parent_page):
        super().__init__()
        self.parent_page = parent_page
        self.data = disk_data
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(45)
        
        clean_name = self.data['name']
        self.copy_text = f"{clean_name} {self.data['type']} {self.data['market_size']}"
        
        self._bg_color = QColor("transparent")
        self._bar_height_factor = 0.0 
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 25, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.add_column(clean_name, col_widths[0], f"color: {COLORS['fg']}; font-weight: 500;")
        self.add_column(self.data['type'], col_widths[1], f"color: {COLORS['sub_text']};")
        self.add_column(self.data['bus'], col_widths[2], f"color: {COLORS['sub_text']};")
        self.add_column(self.data['market_size'], col_widths[3], f"color: {COLORS['fg']}; font-weight: bold;")
        self.add_column(self.data['real_size'], col_widths[4], f"color: {COLORS['sub_text']};")

        self.layout.addStretch()
        
        self.copy_icon = QLabel()
        self.op_effect = QGraphicsOpacityEffect(self.copy_icon)
        self.op_effect.setOpacity(0.0)
        self.copy_icon.setGraphicsEffect(self.op_effect)
        
        self.layout.addWidget(self.copy_icon)
        
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)

    def add_column(self, text, width, style_base):
        lbl = QLabel(text)
        lbl.setFixedWidth(width)
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        lbl.setProperty("style_base", style_base)
        self.layout.addWidget(lbl)

    def update_style(self):
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.property("style_base"):
                style = widget.property("style_base")
                # Need to update colors dynamically for columns
                color = COLORS['fg'] if "fg" in style else COLORS['sub_text']
                font_weight = "bold" if "bold" in style else ("500" if "500" in style else "normal")
                widget.setStyleSheet(f"background: transparent; border: none; color: {color}; font-weight: {font_weight};")

        icon_path = resource_path("assets/images/copy-simple-thin.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            p = QPainter(pix)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(pix.rect(), QColor(COLORS['sub_text']))
            p.end()
            self.copy_icon.setPixmap(pix)

    def _animate_step(self, val):
        self._bar_height_factor = val 
        self.op_effect.setOpacity(val) 
        
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
        if event.button() == Qt.MouseButton.LeftButton and self.parent_page:
            QApplication.clipboard().setText(self.copy_text)
            self.parent_page.show_copy_notification()
            
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        radius = 4
        
        if self._bg_color.alpha() > 0:
            p.setBrush(self._bg_color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, radius, radius)
            
        if getattr(self, '_bar_height_factor', 0) > 0:
            p.setBrush(QColor(COLORS['accent']))
            p.setPen(Qt.PenStyle.NoPen)
            
            h = rect.height() * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            
            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)
            p.setClipPath(path)
            
            p.drawRect(QRect(rect.x(), int(y), 4, int(h)))
            p.setClipping(False)

class AnimatedNavItem(QFrame):
    clicked = pyqtSignal(int)
    def __init__(self, text_key, icon_name, index, parent=None):
        super().__init__(parent)
        self.text_key = text_key
        self.index = index
        self.active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(45)
        self._bg_color = QColor("transparent")
        self._bar_height_factor = 0.0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 10, 0)
        layout.setSpacing(12)
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(16, 16)
        self.icon_name = icon_name
        
        self.label = QLabel()
        
        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.label)
        layout.addStretch()
        
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(250)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)
        
        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.label.setStyleSheet(f"color: {COLORS['fg'] if self.active else COLORS['sub_text']}; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        
        if self.active:
            self._bg_color = QColor(COLORS['item_bg'])
            
        path = resource_path(f"assets/images/{self.icon_name}")
        if os.path.exists(path):
            raw_pix = QPixmap(path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            self.pix_normal = raw_pix.copy()
            p = QPainter(self.pix_normal)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(self.pix_normal.rect(), QColor(COLORS['sub_text']))
            p.end()
            
            self.pix_active = raw_pix.copy()
            p = QPainter(self.pix_active)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(self.pix_active.rect(), QColor(COLORS['fg']))
            p.end()
            
            self.icon_lbl.setPixmap(self.pix_active if self.active else self.pix_normal)
            
        self.update()

    def retranslate_ui(self):
        self.label.setText(_(self.text_key))
        
    def set_active(self, active): 
        self.active = active
        self._animate_step(1.0 if active else 0.0)
        
    def _animate_step(self, val):
        if not self.active:
            target_bg = QColor(COLORS['item_hover'])
            self._bg_color = QColor(target_bg.red(), target_bg.green(), target_bg.blue(), int(255 * val))
            self._bar_height_factor = val
            
            is_highlighted = val > 0.5
            self.label.setStyleSheet(f"color: {COLORS['fg'] if is_highlighted else COLORS['sub_text']}; font-size: 13px; font-weight: 500; border: none; background: transparent;")
            if not self.pix_active.isNull():
                self.icon_lbl.setPixmap(self.pix_active if is_highlighted else self.pix_normal)
        else:
            self._bg_color = QColor(COLORS['item_bg'])
            self._bar_height_factor = 1.0
            self.label.setStyleSheet(f"color: {COLORS['fg']}; font-size: 13px; font-weight: 500; border: none; background: transparent;")
            if not self.pix_active.isNull():
                self.icon_lbl.setPixmap(self.pix_active)
        self.update()
        
    def enterEvent(self, event): 
        if not self.active: self.anim.setDirection(QVariantAnimation.Direction.Forward); self.anim.start()
        
    def leaveEvent(self, event): 
        if not self.active: self.anim.setDirection(QVariantAnimation.Direction.Backward); self.anim.start()
        
    def mousePressEvent(self, event): 
        self.clicked.emit(self.index)
        
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        radius = 8
        if self._bg_color.alpha() > 0:
            p.setBrush(self._bg_color); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(rect, radius, radius)
        if self._bar_height_factor > 0:
            p.setBrush(QColor(COLORS['accent'])); p.setPen(Qt.PenStyle.NoPen)
            h = rect.height() * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)
            p.setClipPath(path); p.drawRect(QRect(0, int(y), 4, int(h))); p.setClipping(False)

class AnimatedCard(QFrame):
    def __init__(self, title_key, value, parent_page=None):
        super().__init__()
        self.title_key = title_key
        self.parent_page = parent_page 
        self.copy_text = str(value)
        self.setCursor(Qt.CursorShape.PointingHandCursor) 
        self.setFixedHeight(65) 
        self._bg_color = QColor(COLORS['item_bg'])
        self._bar_height_factor = 0.0 
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 15, 10)
        layout.setSpacing(2) 
        
        self.t_lbl = QLabel()
        self.v_lbl = QLabel(str(value))
        self.v_lbl.setWordWrap(False) 
        
        self.copy_icon = QLabel()
        self.op_effect = QGraphicsOpacityEffect(self.copy_icon)
        self.op_effect.setOpacity(0.0)
        self.copy_icon.setGraphicsEffect(self.op_effect)

        v_layout = QHBoxLayout()
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(8)
        v_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        v_layout.addWidget(self.v_lbl)
        v_layout.addWidget(self.copy_icon)
        v_layout.addStretch() 
        
        layout.addWidget(self.t_lbl)
        layout.addLayout(v_layout)
        layout.addStretch()
        
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)
        
        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.t_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 10px; font-weight: bold; background:transparent;")
        self.v_lbl.setStyleSheet(f"color: {COLORS['fg']}; font-size: 13px; font-weight: 500; background:transparent;")
        
        # Obnovení barvy pozadí podle nového motivu (pokud není zrovna animováno hoverem)
        self._bg_color = QColor(COLORS['item_bg'])
        
        icon_path = resource_path("assets/images/copy-simple-thin.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            p = QPainter(pix)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(pix.rect(), QColor(COLORS['sub_text']))
            p.end()
            self.copy_icon.setPixmap(pix)
            
        self.update()

    def retranslate_ui(self):
        self.t_lbl.setText(_(self.title_key).upper())
        
    def _animate_step(self, val):
        start_bg = QColor(COLORS['item_bg'])
        end_bg = QColor(COLORS['item_hover'])
        r = start_bg.red() + (end_bg.red() - start_bg.red()) * val
        g = start_bg.green() + (end_bg.green() - start_bg.green()) * val
        b = start_bg.blue() + (end_bg.blue() - start_bg.blue()) * val
        self._bg_color = QColor(int(r), int(g), int(b))
        self._bar_height_factor = val
        
        self.op_effect.setOpacity(val) 
        
        c_start = QColor(COLORS['sub_text'])
        c_end = QColor("#cccccc")
        tr = c_start.red() + (c_end.red() - c_start.red()) * val
        tg = c_start.green() + (c_end.green() - c_start.green()) * val
        tb = c_start.blue() + (c_end.blue() - c_start.blue()) * val
        self.t_lbl.setStyleSheet(f"color: rgb({int(tr)}, {int(tg)}, {int(tb)}); font-size: 10px; font-weight: bold; background:transparent;")
            
        self.update()
        
    def enterEvent(self, event): 
        self.anim.setDirection(QVariantAnimation.Direction.Forward)
        self.anim.start()
        
    def leaveEvent(self, event): 
        self.anim.setDirection(QVariantAnimation.Direction.Backward)
        self.anim.start()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.parent_page:
            QApplication.clipboard().setText(self.copy_text)
            self.parent_page.show_copy_notification()
        
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        radius = 8
        
        p.setBrush(self._bg_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, radius, radius)
        
        if self._bar_height_factor > 0:
            p.setBrush(QColor(COLORS['accent']))
            h = rect.height() * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            path = QPainterPath()
            path.addRoundedRect(0, 0, rect.width(), rect.height(), radius, radius)
            p.setClipPath(path)
            p.drawRect(QRect(0, int(y), 4, int(h)))
            p.setClipping(False)

class MiniToast(QLabel):
    def __init__(self, parent):
        super().__init__("", parent)
        self.hide()
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()
        translator.language_changed.connect(self.retranslate_ui)

    def update_style(self):
        self.setStyleSheet(f"background: {COLORS['accent']}; color: white; padding: 5px 15px; border-radius: 4px; font-weight: bold;")

    def retranslate_ui(self):
        self.setText(_("sp_copied"))
        self.adjustSize()

class InfoHeaderCard(QFrame):
    def __init__(self, icon_name, title_key, value):
        super().__init__()
        self.title_key = title_key
        self.setStyleSheet("background-color: transparent; border: none;")
        
        l = QHBoxLayout(self)
        l.setContentsMargins(5, 8, 15, 8) 
        
        self.icon_name = icon_name
        self.icon_lbl = QLabel()
        l.addWidget(self.icon_lbl)
        
        v_l = QVBoxLayout()
        v_l.setSpacing(0)
        
        self.t = QLabel()
        self.v = QLabel(value)
        
        v_l.addWidget(self.t)
        v_l.addWidget(self.v)
        l.addLayout(v_l)

        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.t.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 9px; font-weight: bold; border: none;")
        self.v.setStyleSheet(f"color: {COLORS['fg']}; font-size: 13px; font-weight: bold; border: none;")
        
        path = resource_path(f"assets/images/{self.icon_name}")
        if os.path.exists(path):
            pix = QPixmap(path).scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            p = QPainter(pix)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(pix.rect(), QColor(COLORS['fg'])) 
            p.end()
            self.icon_lbl.setPixmap(pix)

    def retranslate_ui(self):
        self.t.setText(_(self.title_key).upper())
