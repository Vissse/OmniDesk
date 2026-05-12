import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QCheckBox, QFrame,
                             QDialog, QTabWidget, QComboBox, QFileDialog, QDialogButtonBox,
                             QScrollArea, QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QUrl, QVariantAnimation, QRect
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QDesktopServices, QPainterPath

from core.config import COLORS
from core.config import resource_path
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
                icon_color = QColor("white")
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
            icon_color = QColor("white")
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
        self.setWindowTitle("Možnosti instalace")
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
        self.chk_admin = QCheckBox("Spustit jako správce")
        self.chk_interactive = QCheckBox("Interaktivní instalace")
        self.chk_hash = QCheckBox("Přeskočit kontrolní součet")
        layout_gen.addWidget(self.chk_admin); layout_gen.addWidget(self.chk_interactive); layout_gen.addWidget(self.chk_hash)
        layout_gen.addSpacing(10); line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setStyleSheet(f"background-color: {COLORS['border']}; border: none;"); layout_gen.addWidget(line)
        layout_gen.addSpacing(10); lbl_ver = QLabel("Verze:")
        self.combo_version = QComboBox(); self.combo_version.addItems(["Poslední (Latest)", "Zeptat se při instalaci"])
        layout_gen.addWidget(lbl_ver); layout_gen.addWidget(self.combo_version)
        self.chk_ignore_updates = QCheckBox("Ignorovat budoucí aktualizace tohoto balíčku")
        layout_gen.addWidget(self.chk_ignore_updates); layout_gen.addStretch()
        self.tabs.addTab(tab_general, "Obecné / Verze")

        tab_arch = QWidget(); layout_arch = QVBoxLayout(tab_arch)
        layout_arch.setContentsMargins(20, 20, 20, 20); layout_arch.setSpacing(15)
        lbl_arch = QLabel("Architektura:")
        self.combo_arch = QComboBox(); self.combo_arch.addItems(["Výchozí", "x64", "x86", "arm64"])
        layout_arch.addWidget(lbl_arch); layout_arch.addWidget(self.combo_arch)
        lbl_scope = QLabel("Rozsah instalace:")
        self.combo_scope = QComboBox(); self.combo_scope.addItems(["Výchozí (User/Machine)", "User (Pouze pro mě)", "Machine (Pro všechny)"])
        layout_arch.addWidget(lbl_scope); layout_arch.addWidget(self.combo_scope)
        lbl_path = QLabel("Umístění instalace:"); path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(); self.path_edit.setPlaceholderText("Nenastaveno nebo neznámo (Výchozí)")
        btn_path = QPushButton("Vybrat"); btn_path.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_path.clicked.connect(self.select_path); btn_path.setStyleSheet(f"background: {COLORS['item_bg']}; color: {COLORS['accent']}; border: none; font-weight: bold;")
        path_layout.addWidget(self.path_edit); path_layout.addWidget(btn_path)
        layout_arch.addWidget(lbl_path); layout_arch.addLayout(path_layout); layout_arch.addStretch()
        self.tabs.addTab(tab_arch, "Architektura a umístění")

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
        d = QFileDialog.getExistingDirectory(self, "Vybrat složku pro instalaci")
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
        
        self.lbl_title = QLabel("Název")
        self.lbl_title.setStyleSheet(f"font-weight: bold; font-size: 18px; color: {COLORS['fg']};")
        
        self.lbl_id = QLabel("ID")
        self.lbl_id.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 12px; font-family: Consolas, monospace;")
        
        self.current_url = ""
        self.btn_web = HoverButton("", "assets/images/globe-thin.png", "accent", hover_style="accent_hover")
        self.btn_web.setFixedSize(24, 24)
        self.btn_web.setIconSize(QSize(20, 20))
        self.btn_web.setToolTip("Otevřít webové stránky")
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
            QScrollBar:vertical {{ border: none; background: transparent; width: 4px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: #555555; border-radius: 2px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background: {COLORS.get('accent', '#0078d4')}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; border: none; background: transparent; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; border: none; }}
        """)
        desc_container = QWidget()
        desc_container.setStyleSheet("background: transparent;")
        desc_layout = QVBoxLayout(desc_container)
        desc_layout.setContentsMargins(0, 5, 20, 0)
        
        self.lbl_desc = QLabel("Zde se zobrazí popis aplikace.")
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

    def update_data(self, data):
        self.lbl_title.setText(data.get('name', 'Neznámá aplikace'))
        self.lbl_id.setText(data.get('id', 'Neznámé ID'))
        self.lbl_desc.setText(data.get('description', 'Tato aplikace zatím nemá k dispozici podrobný popis.'))

        icon_path = data.get('icon_url')
        if icon_path and os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_icon.setPixmap(pix)
        else:
            self.lbl_icon.setText("📦")
            self.lbl_icon.setStyleSheet("font-size: 64px; color: #555; background: transparent;")

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
            self.icon_lbl.setStyleSheet("color: #888; font-size: 16px; background: transparent;")
            
        layout.addWidget(self.icon_lbl)
        
        name_lbl = QLabel(data['name'])
        name_lbl.setStyleSheet("font-size: 14px; font-weight: 500; color: white; background: transparent;")
        layout.addWidget(name_lbl, stretch=1)
        
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

class InstallerPage(QWidget):
    def __init__(self, queue_page_ref):
        super().__init__()
        self.queue_page = queue_page_ref
        self.installation_options = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setStyleSheet(f"background-color: {COLORS['bg_main']}; border-bottom: 1px solid {COLORS['border']};")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 15, 20, 15)
        
        lbl_title = QLabel("Katalog aplikací")
        lbl_title.setStyleSheet("font-size: 14pt; font-weight: bold; color: white; border: none; outline: none;")
        top_layout.addWidget(lbl_title); top_layout.addSpacing(20)

        self.search_container = QFrame()
        self.search_container.setFixedWidth(700); self.search_container.setFixedHeight(38)
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS['accent']}; }}")
        search_cont_layout = QHBoxLayout(self.search_container)
        search_cont_layout.setContentsMargins(10, 0, 5, 0); search_cont_layout.setSpacing(0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Hledat v katalogu...")
        self.search_input.setStyleSheet("border: none; background: transparent; color: white; font-size: 10pt;")
        self.search_input.textChanged.connect(self.filter_catalog)
        
        self.btn_search = HoverButton("", "assets/images/magnifying-glass-thin.png", "fg")
        self.btn_search.setFixedSize(32, 32); self.btn_search.setIconSize(QSize(18, 18))
        self.btn_search.setStyleSheet("background: transparent; border: none; padding: 0;")

        search_cont_layout.addWidget(self.search_input); search_cont_layout.addWidget(self.btn_search)
        top_layout.addWidget(self.search_container); top_layout.addStretch()
        main_layout.addWidget(top_bar)

        action_bar = QWidget()
        action_bar.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(20, 10, 20, 10); action_layout.setSpacing(10)

        self.btn_install_selection = AnimatedActionButton(" Nainstalovat vybrané", "assets/images/download-simple-thin.png")
        self.btn_install_selection.clicked.connect(self.run_install_from_bar)
        action_layout.addWidget(self.btn_install_selection)

        add_vertical_separator(action_layout)

        self.btn_settings_quick = AnimatedActionButton(" Nastavení instalace", "assets/images/gear-six-thin.png")
        self.btn_settings_quick.clicked.connect(self.open_options_dialog)
        action_layout.addWidget(self.btn_settings_quick)
        
        action_layout.addStretch()

        self.btn_help = HoverButton(" Nápověda", "assets/images/question-thin.png", "sub_text")
        self.btn_help.setIconSize(QSize(20, 20)); self.btn_help.clicked.connect(self.show_help)
        action_layout.addWidget(self.btn_help)
        
        main_layout.addWidget(action_bar)

        h_sep = QFrame()
        h_sep.setFrameShape(QFrame.Shape.HLine)
        h_sep.setFixedHeight(1)
        h_sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        main_layout.addWidget(h_sep)

        self.split_layout = QVBoxLayout()
        self.split_layout.setContentsMargins(0, 0, 0, 0)
        self.split_layout.setSpacing(0)

        self.catalog_widget = QWidget()
        catalog_layout = QVBoxLayout(self.catalog_widget)
        catalog_layout.setContentsMargins(30, 10, 30, 10)
        
        catalog_scroll = QScrollArea()
        catalog_scroll.setWidgetResizable(True)
        catalog_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: transparent; }}
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS.get('accent', '#0078d4')}; min-height: 30px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS.get('accent_hover', '#1f8ad2')}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        
        catalog_content = QWidget()
        catalog_content.setStyleSheet("background-color: transparent;")
        c_layout = QVBoxLayout(catalog_content)
        c_layout.setContentsMargins(0, 0, 15, 0)
        
        self.categories_ui = []
        self.catalog_widgets = [] 

        if APP_CATEGORIES:
            for cat_name, app_list in APP_CATEGORIES.items():
                sorted_apps = sorted(app_list, key=lambda x: x['name'].lower())
                
                header_container = QWidget(); header_layout = QHBoxLayout(header_container)
                header_layout.setContentsMargins(0, 25, 0, 5); header_layout.setSpacing(10)
                
                cat_icon_lbl = QLabel(); cat_icon_lbl.setFixedSize(20, 20)
                icon_file = CATEGORY_ICONS.get(cat_name, "")
                
                if icon_file:
                    icon_path = resource_path(icon_file) 
                    if os.path.exists(icon_path):
                        pix = QPixmap(icon_path).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        cat_icon_lbl.setPixmap(pix)
                
                clean_name = cat_name.split(' ', 1)[1] if ' ' in cat_name and len(cat_name) > 0 and not cat_name[0].isalnum() else cat_name
                cat_lbl = QLabel(clean_name); cat_lbl.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['fg']};")
                
                header_layout.addWidget(cat_icon_lbl); header_layout.addWidget(cat_lbl); header_layout.addStretch()
                c_layout.addWidget(header_container)
                
                separator = QFrame(); separator.setFixedHeight(1)
                separator.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
                c_layout.addWidget(separator)
                
                grid = QGridLayout()
                grid.setContentsMargins(0, 15, 0, 0)
                grid.setHorizontalSpacing(30)
                grid.setVerticalSpacing(5)
                grid.setColumnStretch(0, 1)
                grid.setColumnStretch(1, 1)
                
                cat_widgets = []
                cat_dummies = [] 
                
                num_apps = len(sorted_apps)
                num_rows = (num_apps + 1) // 2 
                
                for idx, app in enumerate(sorted_apps):
                    w = CompactAppWidget(app, self)
                    self.catalog_widgets.append(w)
                    cat_widgets.append(w)
                    
                    col = idx // num_rows
                    row = idx % num_rows
                    grid.addWidget(w, row, col)
                
                total_cells = num_rows * 2
                for empty_idx in range(num_apps, total_cells):
                    col = empty_idx // num_rows
                    row = empty_idx % num_rows
                    dummy = QWidget() 
                    grid.addWidget(dummy, row, col)
                    cat_dummies.append(dummy) 
                        
                c_layout.addLayout(grid)
                self.categories_ui.append({
                    'header': header_container, 
                    'separator': separator, 
                    'widgets': cat_widgets,
                    'grid': grid,              
                    'dummies': cat_dummies    
                })
        else:
            lbl = QLabel("Pro zobrazení katalogu nastavte APP_CATEGORIES v presets.py")
            lbl.setStyleSheet("color: #888;")
            c_layout.addWidget(lbl)
            
        c_layout.addStretch()
        catalog_scroll.setWidget(catalog_content)
        catalog_layout.addWidget(catalog_scroll)

        self.split_layout.addWidget(self.catalog_widget, stretch=1)

        self.detail_panel = AppDetailPanel(self)
        self.detail_panel.btn_close.clicked.connect(self.hide_app_details)
        self.split_layout.addWidget(self.detail_panel)

        main_layout.addLayout(self.split_layout, stretch=1)

        self.panel_anim_group = QParallelAnimationGroup()
        self.anim_min = QPropertyAnimation(self.detail_panel, b"minimumHeight")
        self.anim_max = QPropertyAnimation(self.detail_panel, b"maximumHeight")
        self.anim_min.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim_max.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.panel_anim_group.addAnimation(self.anim_min)
        self.panel_anim_group.addAnimation(self.anim_max)

    def show_app_details(self, data):
        self.detail_panel.update_data(data)
        if self.detail_panel.maximumHeight() == 0:
            self.anim_min.setDuration(350)
            self.anim_max.setDuration(350)
            self.anim_min.setStartValue(0)
            self.anim_min.setEndValue(160)
            self.anim_max.setStartValue(0)
            self.anim_max.setEndValue(160)
            self.panel_anim_group.start()

    def hide_app_details(self):
        self.anim_min.setDuration(350)
        self.anim_max.setDuration(350)
        self.anim_min.setStartValue(160)
        self.anim_min.setEndValue(0)
        self.anim_max.setStartValue(160)
        self.anim_max.setEndValue(0)
        self.panel_anim_group.start()

    def filter_catalog(self):
        query = self.search_input.text().strip().lower()
        for cat in self.categories_ui:
            grid = cat['grid']
            
            visible_widgets = []
            for w in cat['widgets']:
                if query in w.data['name'].lower() or query in w.data['id'].lower():
                    w.show()
                    visible_widgets.append(w)
                else:
                    w.hide()
            
            for d in cat['dummies']:
                d.hide()
                
            num_apps = len(visible_widgets)
            
            if num_apps > 0:
                num_rows = (num_apps + 1) // 2 
                
                for idx, w in enumerate(visible_widgets):
                    col = idx // num_rows
                    row = idx % num_rows
                    grid.addWidget(w, row, col)
                
                total_cells = num_rows * 2
                dummy_needed = total_cells - num_apps
                
                if dummy_needed > 0:
                    if not cat['dummies']:
                        cat['dummies'].append(QWidget())
                    d = cat['dummies'][0]
                    d.show()
                    grid.addWidget(d, num_rows - 1, 1)

            if num_apps == 0:
                cat['header'].hide()
                cat['separator'].hide()
            else:
                cat['header'].show()
                cat['separator'].show()

    def refresh_catalog_checkboxes(self):
        for widget in self.catalog_widgets: widget.set_checked_state(widget.data['id'] in self.queue_page.queue_data)
            
    def refresh_checkboxes(self): self.refresh_catalog_checkboxes()

    def run_install_from_bar(self):
        if not self.queue_page.queue_data:
            QMessageBox.warning(self, "Prázdná fronta", "Vyberte nejprve balíčky z katalogu.")
            return
        self.queue_page.run_installation()

    def open_options_dialog(self):
        dlg = InstallationOptionsDialog(self, self.installation_options)
        if dlg.exec(): self.installation_options = dlg.get_options()

    def show_help(self):
        QMessageBox.information(self, "Nápověda", "Vyberte aplikace z katalogu pomocí tlačítek. Výběr se automaticky přidá do fronty. K dispozici je také lokální vyhledávací pole nahoře pro rychlé filtrování.")