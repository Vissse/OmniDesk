import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QCheckBox, QFrame,
                             QDialog, QTabWidget, QComboBox, QFileDialog, QDialogButtonBox,
                             QScrollArea, QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QUrl, QVariantAnimation, QRect
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QDesktopServices, QPainterPath

from core.config import COLORS
from core.i18n import _, translator
from core.config import resource_path
from core.theme_manager import theme_manager
from UI.shared_widgets import AnimatedActionButton, add_vertical_separator

try:
    from core.presets import PRESETS, APP_CATEGORIES
except ImportError:
    PRESETS = {}
    APP_CATEGORIES = {}

CATEGORY_ICONS = {
    "🌐 Prohlížeče": "assets/images/globe-thin.png",
    "💬 Komunikace": "assets/images/chats-circle-thin.png",
    "🎮 Hry": "assets/images/game-controller-thin.png",
    "🟩 Nvidia Nástroje": "assets/images/graphics-card-thin.png",
    "🎨 Média (Obraz, Zvuk, Video)": "assets/images/images-thin.png",
    "📄 Kancelářské aplikace": "assets/images/file-text-thin.png",
    "💽 Správa disků": "assets/images/disc-thin.png",
    "🛠️ Systémové nástroje (Utilities)": "assets/images/windows-logo-thin.png",
    "💻 Vývojářské nástroje": "assets/images/code-thin.png"
}

class HoverButton(QPushButton):
    def __init__(self, text, icon_path, style_template, parent=None, hover_style="accent"):
        super().__init__(text, parent)
        self.icon_path = resource_path(icon_path)
        self.style_template = style_template
        self.hover_style = hover_style
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._padding = "0px" if not text.strip() else "5px"
        self.set_colored_icon(False)

    def set_colored_icon(self, is_hover):
        if not os.path.exists(self.icon_path): return
        pixmap = QPixmap(self.icon_path)
        
        if is_hover:
            current_color = QColor(COLORS.get(self.hover_style, COLORS['accent']))
        else:
            if "sub_text" in self.style_template:
                current_color = QColor(COLORS['sub_text'])
            elif "accent" in self.style_template:
                current_color = QColor(COLORS['accent'])
            elif "danger" in self.style_template:
                current_color = QColor(COLORS['danger'])
            else:
                current_color = QColor(COLORS['fg'])
                
        colored_pixmap = QPixmap(pixmap.size())
        colored_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(colored_pixmap)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), current_color)
        painter.end()

        self.setIcon(QIcon(colored_pixmap))
        self.setStyleSheet(f"QPushButton {{ background: transparent; border: none; outline: none; color: {current_color.name()}; font-weight: bold; font-size: 10pt; padding: {self._padding}; text-align: left; }}")

    def enterEvent(self, event):
        self.set_colored_icon(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.set_colored_icon(False)
        super().leaveEvent(event)

class QueueToggleButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover = False
        self.is_queued = False
        
        self.icon_plus = resource_path("assets/images/plus.png")
        if not os.path.exists(self.icon_plus):
            self.icon_plus = resource_path("assets/images/plus-thin.png")
            
        self.icon_minus = resource_path("assets/images/minus.png")
        if not os.path.exists(self.icon_minus):
            self.icon_minus = resource_path("assets/images/minus-thin.png")

    def set_queued(self, state):
        self.is_queued = state
        self.setToolTip("Odebrat z fronty" if state else "Přidat do fronty")
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2) 
        
        if self.is_queued:
            danger_color = QColor(COLORS.get('danger', '#ff4444'))
            
            if self._hover:
                bg_color = danger_color
                border_color = danger_color
                icon_color = QColor(COLORS['fg'])
            else:
                bg_color = QColor("transparent")
                border_color = danger_color
                icon_color = danger_color
            current_icon = self.icon_minus
        else:
            if self._hover:
                bg_color = QColor(COLORS.get('accent', '#0078d4'))
                border_color = bg_color
            else:
                bg_color = QColor(COLORS.get('item_bg', '#3e3e42'))
                border_color = QColor("transparent")
            icon_color = QColor(COLORS['fg'])
            current_icon = self.icon_plus
            
        if bg_color.alpha() > 0:
            p.setBrush(bg_color)
        else:
            p.setBrush(Qt.BrushStyle.NoBrush)
            
        if border_color.alpha() > 0 and border_color != QColor("transparent"):
            p.setPen(border_color)
        else:
            p.setPen(Qt.PenStyle.NoPen)
            
        p.drawEllipse(rect)
        
        if os.path.exists(current_icon):
            pix = QPixmap(current_icon).scaled(14, 14, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            colored_pix = QPixmap(pix.size())
            colored_pix.fill(Qt.GlobalColor.transparent)
            
            cp = QPainter(colored_pix)
            cp.drawPixmap(0, 0, pix)
            cp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            cp.fillRect(colored_pix.rect(), icon_color)
            cp.end()
            
            x = (self.width() - 14) // 2
            y = (self.height() - 14) // 2
            p.drawPixmap(x, y, colored_pix)


class InstallationOptionsDialog(QDialog):
    def __init__(self, parent=None, current_options=None):
        super().__init__(parent)
        self.setWindowTitle(_("inst_opt_title"))
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_main']}; color: {COLORS['fg']}; }}
            QTabWidget::pane {{ border: 1px solid {COLORS['border']}; }}
            QTabBar::tab {{ background: {COLORS['bg_sidebar']}; color: {COLORS['sub_text']}; padding: 8px 15px; margin-right: 2px; }}
            QTabBar::tab:selected {{ background: {COLORS['item_bg']}; color: {COLORS['fg']}; border-top: 2px solid {COLORS['accent']}; }}
            QLabel {{ color: {COLORS['fg']}; font-size: 10pt; }}
            QCheckBox {{ color: {COLORS['fg']}; font-size: 10pt; spacing: 8px; }}
            QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid {COLORS['border']}; border-radius: 4px; }}
            QCheckBox::indicator:checked {{ background-color: {COLORS['accent']}; border-color: {COLORS['accent']}; image: url(check.png); }}
            QComboBox {{ background: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; padding: 5px; color: {COLORS['fg']}; border-radius: 4px; }}
            QLineEdit {{ background: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; padding: 5px; color: {COLORS['fg']}; border-radius: 4px; }}
        """)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        tab_general = QWidget(); layout_gen = QVBoxLayout(tab_general)
        layout_gen.setContentsMargins(20, 20, 20, 20); layout_gen.setSpacing(15)
        self.chk_admin = QCheckBox(_("inst_opt_admin"))
        self.chk_interactive = QCheckBox(_("inst_opt_interactive"))
        self.chk_hash = QCheckBox(_("inst_opt_hash"))
        layout_gen.addWidget(self.chk_admin); layout_gen.addWidget(self.chk_interactive); layout_gen.addWidget(self.chk_hash)
        layout_gen.addSpacing(10); line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setStyleSheet(f"background-color: {COLORS['border']}; border: none;"); layout_gen.addWidget(line)
        layout_gen.addSpacing(10); lbl_ver = QLabel(_("inst_opt_ver"))
        self.combo_version = QComboBox(); self.combo_version.addItems([_("inst_opt_latest"), _("inst_opt_ask")])
        layout_gen.addWidget(lbl_ver); layout_gen.addWidget(self.combo_version)
        self.chk_ignore_updates = QCheckBox(_("inst_opt_ignore"))
        layout_gen.addWidget(self.chk_ignore_updates); layout_gen.addStretch()
        self.tabs.addTab(tab_general, _("inst_opt_tab_gen"))

        tab_arch = QWidget(); layout_arch = QVBoxLayout(tab_arch)
        layout_arch.setContentsMargins(20, 20, 20, 20); layout_arch.setSpacing(15)
        lbl_arch = QLabel(_("inst_opt_arch"))
        self.combo_arch = QComboBox(); self.combo_arch.addItems([_("inst_opt_default"), "x64", "x86", "arm64"])
        layout_arch.addWidget(lbl_arch); layout_arch.addWidget(self.combo_arch)
        lbl_scope = QLabel(_("inst_opt_scope"))
        self.combo_scope = QComboBox(); self.combo_scope.addItems([_("inst_opt_scope_def"), _("inst_opt_scope_user"), _("inst_opt_scope_mach")])
        layout_arch.addWidget(lbl_scope); layout_arch.addWidget(self.combo_scope)
        lbl_path = QLabel(_("inst_opt_path")); path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(); self.path_edit.setPlaceholderText(_("inst_opt_path_def"))
        btn_path = QPushButton(_("inst_opt_btn_sel")); btn_path.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_path.clicked.connect(self.select_path); btn_path.setStyleSheet(f"background: {COLORS['item_bg']}; color: {COLORS['accent']}; border: none; font-weight: bold;")
        path_layout.addWidget(self.path_edit); path_layout.addWidget(btn_path)
        layout_arch.addWidget(lbl_path); layout_arch.addLayout(path_layout); layout_arch.addStretch()
        self.tabs.addTab(tab_arch, _("inst_opt_tab_arch"))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if current_options:
            self.chk_admin.setChecked(current_options.get("admin", False))
            self.chk_interactive.setChecked(current_options.get("interactive", False))
            self.chk_hash.setChecked(current_options.get("hash", False))
            self.combo_arch.setCurrentText(current_options.get("arch", "Výchozí"))
            self.path_edit.setText(current_options.get("path", ""))

    def select_path(self):
        d = QFileDialog.getExistingDirectory(self, _("inst_opt_sel_dir"))
        if d: self.path_edit.setText(d)

    def get_options(self):
        return { "admin": self.chk_admin.isChecked(), "interactive": self.chk_interactive.isChecked(), "hash": self.chk_hash.isChecked(), "version": self.combo_version.currentText(), "arch": self.combo_arch.currentText(), "scope": self.combo_scope.currentText(), "path": self.path_edit.text() }


class AppDetailPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(0) 
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_sidebar']};
                border-top: 1px solid {COLORS['border']};
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(30, 20, 20, 20)
        self.layout.setSpacing(25)

        self.lbl_icon = QLabel()
        self.lbl_icon.setFixedSize(100, 100)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_icon, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        title_id_layout = QHBoxLayout()
        title_id_layout.setSpacing(10)
        
        self.lbl_title = QLabel(_("inst_name"))
        self.lbl_title.setStyleSheet(f"font-weight: bold; font-size: 18px; color: {COLORS['fg']};")
        
        self.lbl_id = QLabel(_("inst_id"))
        self.lbl_id.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 12px; font-family: Consolas, monospace;")
        
        self.current_url = ""
        self.btn_web = HoverButton("", "assets/images/globe-thin.png", "accent", hover_style="accent_hover")
        self.btn_web.setFixedSize(24, 24)
        self.btn_web.setIconSize(QSize(20, 20))
        self.btn_web.setToolTip(_("inst_tt_web"))
        self.btn_web.clicked.connect(self.open_website)
        
        title_id_layout.addWidget(self.lbl_title)
        title_id_layout.addWidget(self.lbl_id)
        title_id_layout.addWidget(self.btn_web) 
        title_id_layout.addStretch()
        
        text_layout.addLayout(title_id_layout)

        scroll_desc = QScrollArea()
        scroll_desc.setWidgetResizable(True)
        scroll_desc.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ border: none; background: transparent; width: 6px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: {COLORS['border']}; border-radius: 2px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background: {COLORS.get('accent', '#0078d4')}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; border: none; background: transparent; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; border: none; }}
        """)
        desc_container = QWidget()
        desc_container.setStyleSheet("background: transparent;")
        desc_layout = QVBoxLayout(desc_container)
        desc_layout.setContentsMargins(0, 5, 20, 0)
        
        self.lbl_desc = QLabel(_("inst_def_desc"))
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.lbl_desc.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 13px; line-height: 1.4;")
        
        desc_layout.addWidget(self.lbl_desc)
        desc_layout.addStretch()
        scroll_desc.setWidget(desc_container)
        
        text_layout.addWidget(scroll_desc, stretch=1)
        self.layout.addLayout(text_layout, stretch=1)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_close = HoverButton("", "assets/images/x-thin.png", "sub_text", hover_style="danger")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setIconSize(QSize(20, 20))
        self.btn_close.setToolTip("Zavřít panel")
        
        right_layout.addWidget(self.btn_close, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        right_layout.addStretch()
        
        self.layout.addLayout(right_layout)

        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

    def update_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_sidebar']};
                border-top: 1px solid {COLORS['border']};
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        self.lbl_title.setStyleSheet(f"font-weight: bold; font-size: 18px; color: {COLORS['fg']};")
        self.lbl_id.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 12px; font-family: Consolas, monospace;")
        self.lbl_desc.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 13px; line-height: 1.4;")

    def update_data(self, data):
        self.data = data
        self.lbl_title.setText(data.get('name', 'Neznámá aplikace'))
        self.lbl_id.setText(data.get('id', 'Neznámé ID'))
        
        if translator.current_lang == "Čeština":
            desc = data.get('description_cs', data.get('description', 'Tato aplikace zatím nemá k dispozici podrobný popis.'))
        else:
            desc = data.get('description_en', data.get('description', 'No description available for this app.'))
            
        self.lbl_desc.setText(desc)

        icon_path = data.get('icon_url')
        if icon_path and os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_icon.setPixmap(pix)
        else:
            self.lbl_icon.setText("📦")
            self.lbl_icon.setStyleSheet(f"font-size: 64px; color: {COLORS['sub_text']}; background: transparent;")

        website = data.get('website', '')
        self.current_url = website
        if website:
            self.btn_web.show()
        else:
            self.btn_web.hide()

    def open_website(self):
        if self.current_url:
            QDesktopServices.openUrl(QUrl(self.current_url))


class CompactAppWidget(QWidget):
    def __init__(self, data, parent_controller):
        super().__init__()
        self.data = data
        self.controller = parent_controller
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setObjectName("AppContainer")
        self.setStyleSheet("background: transparent;")
        
        self._bg_color = QColor("transparent")
        self._bar_height_factor = 0.0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(28, 28)
        icon_path = data.get('icon_url')
        
        if icon_path and os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_lbl.setPixmap(pix)
        else:
            self.icon_lbl.setText("📦")
        self.icon_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 16px; background: transparent;")
            
        layout.addWidget(self.icon_lbl)
        
        self.name_lbl = QLabel(data['name'])
        layout.addWidget(self.name_lbl, stretch=1)
        
        self.btn_pick = QueueToggleButton()
        self.btn_pick.clicked.connect(self.toggle_queue)
        layout.addWidget(self.btn_pick)

        self.is_queued = self.data['id'] in self.controller.queue_page.queue_data
        self.btn_pick.set_queued(self.is_queued)

        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)

        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

    def update_style(self):
        self.name_lbl.setStyleSheet(f"font-size: 14px; font-weight: 500; color: {COLORS['fg']}; background: transparent;")

    def _animate_step(self, val):
        self._bar_height_factor = val
        target_bg = QColor(COLORS.get('item_hover', '#2d2d30'))
        self._bg_color = QColor(target_bg.red(), target_bg.green(), target_bg.blue(), int(255 * val))
        self.update()

    def enterEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Forward)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Backward)
        self.anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.controller.show_app_details(self.data)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        radius = 8 
        
        if self._bg_color.alpha() > 0:
            p.setBrush(self._bg_color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, radius, radius)
            
        if self._bar_height_factor > 0:
            p.setBrush(QColor(COLORS.get('accent', '#0078d4')))
            p.setPen(Qt.PenStyle.NoPen)
            
            h = rect.height() * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            
            from PyQt6.QtGui import QPainterPath
            from PyQt6.QtCore import QRect
            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)
            p.setClipPath(path)
            
            p.drawRect(QRect(rect.x(), int(y), 4, int(h)))
            p.setClipping(False)

    def toggle_queue(self):
        self.is_queued = not self.is_queued
        self.btn_pick.set_queued(self.is_queued)
        
        if self.is_queued:
            self.controller.queue_page.add_to_queue(self.data, icon=self.icon_lbl.pixmap())
        else:
            self.controller.queue_page.remove_item_by_id(self.data['id'])
            
    def set_checked_state(self, is_checked):
        if self.is_queued != is_checked:
            self.is_queued = is_checked
            self.btn_pick.set_queued(self.is_queued)

