import os
import requests
from urllib.parse import urlparse
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QCheckBox, QFrame,
                             QDialog, QTabWidget, QComboBox, QFileDialog, QDialogButtonBox,
                             QScrollArea, QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QPropertyAnimation, pyqtProperty, QEasingCurve, QRunnable, QThreadPool, QObject
from PyQt6.QtGui import QIcon, QPixmap, QImage, QPainter, QColor, QPainterPath

from core.config import COLORS
from core.config import resource_path

try:
    from core.presets import PRESETS, APP_CATEGORIES
except ImportError:
    PRESETS = {}
    APP_CATEGORIES = {}

CATEGORY_ICONS = {
    "🌐 Prohlížeče": "assets/images/globe-thin.png",
    "💬 Komunikace": "assets/images/chats-circle-thin.png",
    "🎮 Hry": "assets/images/game-controller-thin.png",
    "🎨 Grafika": "assets/images/image-thin.png",
    "🎬 Video": "assets/images/video-thin.png",
    "🎵 Audio": "assets/images/waveform-thin.png",
    "📄 Kancelář": "assets/images/file-text-thin.png",
    "📄 PDF": "assets/images/file-pdf-thin.png",
    "🛠️ Systémové nástroje": "assets/images/windows-logo-thin.png",
    "💻 Vývojářské nástroje": "assets/images/code-thin.png"
}

class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._position = 3.0  
        
        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setDuration(200) 
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad) 
        self.stateChanged.connect(self.setup_animation)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    def setup_animation(self, value):
        self.animation.stop()
        if self.isChecked():
            self.animation.setEndValue(23.0) 
        else:
            self.animation.setEndValue(3.0)  
        self.animation.start()

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg_color = QColor(COLORS['accent']) if self.isChecked() else QColor("#666666")
        
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        p.fillPath(path, bg_color)

        knob_color = QColor("#ffffff")
        p.setBrush(knob_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(self._position), 3, 18, 18) 
        p.end()

class HoverButton(QPushButton):
    def __init__(self, text, icon_path, style_template, parent=None):
        super().__init__(text, parent)
        self.icon_path = resource_path(icon_path)
        self.style_template = style_template
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_colored_icon(False)

    def set_colored_icon(self, is_hover):
        if not os.path.exists(self.icon_path): return
        pixmap = QPixmap(self.icon_path)
        current_color = QColor(COLORS['accent']) if is_hover else QColor(
            COLORS['sub_text'] if "sub_text" in self.style_template else COLORS['fg']
        )
        colored_pixmap = QPixmap(pixmap.size())
        colored_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(colored_pixmap)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), current_color)
        painter.end()

        self.setIcon(QIcon(colored_pixmap))
        self.setStyleSheet(f"QPushButton {{ background: transparent; border: none; outline: none; color: {current_color.name()}; font-weight: bold; font-size: 10pt; padding: 5px; text-align: left; }}")

    def enterEvent(self, event):
        self.set_colored_icon(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.set_colored_icon(False)
        super().leaveEvent(event)


# --- POMOCNÉ TŘÍDY (WORKERS) ---

# Pro zpětnou kompatibilitu s QueuePage
class IconWorker(QThread):
    loaded = pyqtSignal(QImage) # OPRAVA: Odesíláme QImage místo QPixmap
    def __init__(self, app_id, website=None, preset_url=None):
        super().__init__()
        self.app_id = app_id; self.website = website; self.preset_url = preset_url

    def get_domain(self, url):
        try:
            if not url.startswith("http"): url = "https://" + url
            return urlparse(url).netloc
        except: return ""

    def run(self):
        if self.app_id:
            local_paths = [os.path.join("icons", f"{self.app_id}.png"), os.path.join("icons", f"{self.app_id.lower()}.png")]
            for path in local_paths:
                if os.path.exists(path):
                    image = QImage(path)
                    if not image.isNull():
                        self.loaded.emit(image); return

        if self.preset_url:
            if self._try_load_url(self.preset_url): return

        if self.app_id:
            clean_id = self.app_id; lower_id = self.app_id.lower(); dashed_id = lower_id.replace(".", "-")
            base_dash = "https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png"
            if self._try_load_url(f"{base_dash}/{dashed_id}.png"): return
            if self._try_load_url(f"{base_dash}/{lower_id}.png"): return
            base_uniget = "https://raw.githubusercontent.com/marticliment/UnigetUI/main/src/UnigetUI.PackageEngine/Assets/Packages"
            if self._try_load_url(f"{base_uniget}/{clean_id}.png"): return
            if self._try_load_url(f"{base_uniget}/{lower_id}.png"): return

        if self.website:
            domain = self.get_domain(self.website)
            if domain:
                if self._try_load_url(f"https://icons.duckduckgo.com/ip3/{domain}.ico"): return
                if self._try_load_url(f"https://www.google.com/s2/favicons?domain={domain}&sz=64"): return

    def _try_load_url(self, url):
        try:
            session = requests.Session(); session.headers.update({'User-Agent': 'Mozilla/5.0'})
            response = session.get(url, timeout=1.5, stream=True)
            if response.status_code == 200:
                data = response.content
                if len(data) > 50:
                    image = QImage(); image.loadFromData(data)
                    if not image.isNull():
                        self.loaded.emit(image); return True
        except Exception: pass
        return False

# Bezpečný Task pro QThreadPool
class IconTaskSignals(QObject):
    loaded = pyqtSignal(QImage) # OPRAVA: Odesíláme QImage

class IconWorkerTask(QRunnable):
    def __init__(self, app_id, website=None, preset_url=None):
        super().__init__()
        self.app_id = app_id; self.website = website; self.preset_url = preset_url
        self.signals = IconTaskSignals()

    def get_domain(self, url):
        try:
            if not url.startswith("http"): url = "https://" + url
            return urlparse(url).netloc
        except: return ""

    def run(self):
        if self.app_id:
            local_paths = [os.path.join("icons", f"{self.app_id}.png"), os.path.join("icons", f"{self.app_id.lower()}.png")]
            for path in local_paths:
                if os.path.exists(path):
                    image = QImage(path)
                    if not image.isNull():
                        self.signals.loaded.emit(image); return

        if self.preset_url:
            if self._try_load_url(self.preset_url): return

        if self.app_id:
            clean_id = self.app_id; lower_id = self.app_id.lower(); dashed_id = lower_id.replace(".", "-")
            base_dash = "https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png"
            if self._try_load_url(f"{base_dash}/{dashed_id}.png"): return
            if self._try_load_url(f"{base_dash}/{lower_id}.png"): return
            base_uniget = "https://raw.githubusercontent.com/marticliment/UnigetUI/main/src/UnigetUI.PackageEngine/Assets/Packages"
            if self._try_load_url(f"{base_uniget}/{clean_id}.png"): return
            if self._try_load_url(f"{base_uniget}/{lower_id}.png"): return

        if self.website:
            domain = self.get_domain(self.website)
            if domain:
                if self._try_load_url(f"https://icons.duckduckgo.com/ip3/{domain}.ico"): return
                if self._try_load_url(f"https://www.google.com/s2/favicons?domain={domain}&sz=64"): return

    def _try_load_url(self, url):
        try:
            session = requests.Session(); session.headers.update({'User-Agent': 'Mozilla/5.0'})
            response = session.get(url, timeout=1.5, stream=True)
            if response.status_code == 200:
                data = response.content
                if len(data) > 50:
                    image = QImage(); image.loadFromData(data)
                    if not image.isNull():
                        self.signals.loaded.emit(image); return True
        except Exception: pass
        return False

# --- DIALOG NASTAVENÍ ---
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

# --- KOMPAKTNÍ WIDGET PRO KATALOG ---
class CompactAppWidget(QWidget):
    def __init__(self, data, parent_controller):
        super().__init__()
        self.data = data
        self.controller = parent_controller
        self.setFixedHeight(38) 
        self.setStyleSheet("background-color: transparent;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 10, 5); layout.setSpacing(10)
        
        self.chk = ToggleSwitch()
        if self.data['id'] in self.controller.queue_page.queue_data:
            self.chk.setChecked(True)
            self.chk.position = 23.0
            
        self.chk.stateChanged.connect(self.toggle_queue)
        layout.addWidget(self.chk)
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(24, 24)
        
        local_icon_path = os.path.join("icons", f"{data['id']}.png")
        if os.path.exists(local_icon_path):
            pix = QPixmap(local_icon_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_lbl.setPixmap(pix)
        else:
            self.icon_lbl.setText("📦")
            self.icon_lbl.setStyleSheet("color: #888; font-size: 14px;")
            
            # Bezpečné vytvoření a start workeru ve fondu vláken
            self.icon_task = IconWorkerTask(data.get('id'), data.get('website'), data.get('icon_url'))
            self.icon_task.signals.loaded.connect(self.set_icon)
            QThreadPool.globalInstance().start(self.icon_task)
            
        layout.addWidget(self.icon_lbl)
        name_lbl = QLabel(data['name']); name_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: white;")
        layout.addWidget(name_lbl, stretch=1)

    def set_icon(self, image):
        # OPRAVA: Převedeme bezpečný QImage na QPixmap až tady, v hlavním grafickém vlákně
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.icon_lbl.setPixmap(scaled)
        self.icon_lbl.setText("")

    def toggle_queue(self, state):
        if state == 2: self.controller.queue_page.add_to_queue(self.data, icon=self.icon_lbl.pixmap())
        else: self.controller.queue_page.remove_item_by_id(self.data['id'])
            
    def set_checked_state(self, is_checked):
        self.chk.blockSignals(True)
        self.chk.setChecked(is_checked)
        self.chk.position = 23.0 if is_checked else 3.0
        self.chk.blockSignals(False)

# --- HLAVNÍ UI (InstallerPage) ---
class InstallerPage(QWidget):
    def __init__(self, queue_page_ref):
        super().__init__()
        self.queue_page = queue_page_ref
        self.installation_options = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        # A. HORNÍ VYHLEDÁVACÍ LIŠTA
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

        # B. ACTION BAR
        action_bar = QWidget()
        action_bar.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(20, 10, 20, 10); action_layout.setSpacing(10)

        split_container = QFrame()
        split_container.setFixedHeight(34)
        split_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['item_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:hover {{ border-color: {COLORS['accent']}; }}")
        split_layout = QHBoxLayout(split_container)
        split_layout.setContentsMargins(0, 0, 0, 0); split_layout.setSpacing(0)

        self.btn_install_selection = QPushButton("  Nainstalovat vybrané")
        self.btn_install_selection.setIcon(QIcon(resource_path("assets/images/download-simple-thin.png")))
        self.btn_install_selection.setFixedHeight(32)
        self.btn_install_selection.setStyleSheet(f"QPushButton {{ background: transparent; border: none; color: white; padding: 0 15px; font-weight: bold; font-size: 10pt; border-top-left-radius: 5px; border-bottom-left-radius: 5px; border-top-right-radius: 0px; border-bottom-right-radius: 0px; }} QPushButton:hover {{ background-color: {COLORS['item_hover']}; }}")
        self.btn_install_selection.clicked.connect(self.run_install_from_bar)

        mid_line = QFrame(); mid_line.setFixedWidth(1); mid_line.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")

        self.btn_settings_quick = QPushButton()
        self.btn_settings_quick.setFixedSize(32, 32)
        self.btn_settings_quick.setIcon(self.get_colored_icon_for_split("assets/images/gear-six-thin.png", COLORS['fg']))
        self.btn_settings_quick.setIconSize(QSize(18, 18))
        self.btn_settings_quick.setStyleSheet(f"QPushButton {{ background: transparent; border: none; border-top-right-radius: 5px; border-bottom-right-radius: 5px; border-top-left-radius: 0px; border-bottom-left-radius: 0px; }} QPushButton:hover {{ background-color: {COLORS['item_hover']}; }}")
        self.btn_settings_quick.clicked.connect(self.open_options_dialog)

        split_layout.addWidget(self.btn_install_selection)
        split_layout.addWidget(mid_line)
        split_layout.addWidget(self.btn_settings_quick)
        action_layout.addWidget(split_container)
        
        action_layout.addStretch()

        self.btn_help = HoverButton(" Nápověda", "assets/images/question-thin.png", "sub_text")
        self.btn_help.setIconSize(QSize(20, 20)); self.btn_help.clicked.connect(self.show_help)
        action_layout.addWidget(self.btn_help)
        
        main_layout.addWidget(action_bar)

        # C. KATALOG (ScrollArea)
        self.catalog_widget = QWidget()
        catalog_layout = QVBoxLayout(self.catalog_widget)
        catalog_layout.setContentsMargins(30, 10, 30, 10)
        
        catalog_scroll = QScrollArea()
        catalog_scroll.setWidgetResizable(True)
        catalog_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: transparent; }}
            QScrollBar:vertical {{ border: none; background-color: {COLORS['bg_main']}; width: 8px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background-color: #444; border-radius: 4px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS['accent']}; }}
        """)
        
        catalog_content = QWidget()
        catalog_content.setStyleSheet("background-color: transparent;")
        c_layout = QVBoxLayout(catalog_content)
        c_layout.setContentsMargins(0, 0, 15, 0)
        
        self.categories_ui = []
        self.catalog_widgets = [] 

        if APP_CATEGORIES:
            for cat_name, app_list in APP_CATEGORIES.items():
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
                
                grid = QGridLayout(); grid.setContentsMargins(0, 15, 0, 0); grid.setSpacing(10)
                
                cat_widgets = []
                col = 0; row = 0
                for app in app_list:
                    w = CompactAppWidget(app, self)
                    self.catalog_widgets.append(w)
                    cat_widgets.append(w)
                    grid.addWidget(w, row, col)
                    col += 1
                    if col > 1:
                        col = 0; row += 1
                        
                c_layout.addLayout(grid)
                self.categories_ui.append({'header': header_container, 'separator': separator, 'widgets': cat_widgets})
        else:
            lbl = QLabel("Pro zobrazení katalogu nastavte APP_CATEGORIES v presets.py")
            lbl.setStyleSheet("color: #888;")
            c_layout.addWidget(lbl)
            
        c_layout.addStretch()
        catalog_scroll.setWidget(catalog_content)
        catalog_layout.addWidget(catalog_scroll)
        
        main_layout.addWidget(self.catalog_widget)

    # --- POMOCNÉ FUNKCE ---
    def filter_catalog(self):
        query = self.search_input.text().strip().lower()
        for cat in self.categories_ui:
            visible_count = 0
            for w in cat['widgets']:
                if query in w.data['name'].lower() or query in w.data['id'].lower():
                    w.show(); visible_count += 1
                else: w.hide()
            if visible_count == 0:
                cat['header'].hide(); cat['separator'].hide()
            else:
                cat['header'].show(); cat['separator'].show()

    def refresh_catalog_checkboxes(self):
        for widget in self.catalog_widgets: widget.set_checked_state(widget.data['id'] in self.queue_page.queue_data)
            
    def refresh_checkboxes(self): self.refresh_catalog_checkboxes()

    def get_colored_icon_for_split(self, path, color_hex):
        full_path = resource_path(path)
        if not os.path.exists(full_path): return QIcon()
        pixmap = QPixmap(full_path)
        colored = QPixmap(pixmap.size()); colored.fill(Qt.GlobalColor.transparent)
        p = QPainter(colored); p.drawPixmap(0, 0, pixmap); p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn); p.fillRect(colored.rect(), QColor(color_hex)); p.end()
        return QIcon(colored)

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