import subprocess
import os
import winreg
import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QLineEdit, 
                             QMessageBox, QFileIconProvider, QFrame, QProgressBar,
                             QCheckBox, QTextEdit)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QFileInfo, QTimer, QVariantAnimation, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QImage, QIcon, QPainter, QColor, QPainterPath

from core.workers import WingetListWorker
from core.config import COLORS, resource_path

# --- ANIMOVANÉ TLAČÍTKO PRO HORNÍ LIŠTU (S MODRÝM PROUŽKEM) ---
class AnimatedActionButton(QPushButton):
    def __init__(self, text, icon_path, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(34)
        self.icon_path = icon_path
        
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
            # Ponechána modrá barva (accent) dle zadání "stejně jako zbytek tlačítek"
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


# --- WORKER PRO STAHOVÁNÍ IKON ---
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

# --- VYLEPŠENÉ HLEDÁNÍ IKON V SYSTÉMU ---
def find_app_icon_path(app_name, app_id=None):
    clean_name = app_name.split(' (')[0].strip()
    search_names = [clean_name.lower()]
    if app_id and "." in app_id:
        publisher = app_id.split('.')[0].lower()
        if len(publisher) > 2: search_names.append(publisher)

    registry_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    roots = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
    found_install_loc = None

    for i, reg_path in enumerate(registry_paths):
        root = roots[i]
        try:
            with winreg.OpenKey(root, reg_path) as key:
                for j in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, j)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0].lower()
                                if any(s in display_name for s in search_names):
                                    try:
                                        display_icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                                        display_icon = display_icon.split(',')[0].strip('"')
                                        if os.path.exists(display_icon) and (display_icon.endswith('.exe') or display_icon.endswith('.ico')):
                                            return display_icon
                                    except: pass
                                    try:
                                        loc = winreg.QueryValueEx(subkey, "InstallLocation")[0].strip('"')
                                        if loc and os.path.exists(loc): found_install_loc = loc
                                    except: pass
                            except: continue
                    except: continue
        except: continue

    if found_install_loc:
        exe = find_main_exe_in_folder(found_install_loc)
        if exe: return exe

    try:
        app_paths_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, app_paths_key) as key:
            for j in range(winreg.QueryInfoKey(key)[0]):
                exe_name = winreg.EnumKey(key, j)
                if clean_name.replace(" ", "").lower() in exe_name.lower():
                    with winreg.OpenKey(key, exe_name) as subkey:
                        try:
                            path = winreg.QueryValue(subkey, None).strip('"')
                            if os.path.exists(path): return path
                        except: pass
    except: pass
    return None

def find_main_exe_in_folder(folder):
    best_exe = None; max_size = 0
    base_depth = folder.rstrip(os.sep).count(os.sep)
    try:
        for root, dirs, files in os.walk(folder):
            current_depth = root.rstrip(os.sep).count(os.sep)
            if current_depth - base_depth > 1: continue 
            for file in files:
                if file.lower().endswith(".exe"):
                    if any(x in file.lower() for x in ["unins", "helper", "crash", "update", "report", "setup"]): continue
                    full_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(full_path)
                        if "java.exe" in file.lower() or "javaw.exe" in file.lower(): return full_path
                        if size > max_size: max_size = size; best_exe = full_path
                    except: pass
    except: pass
    return best_exe


# --- ASYNCHRONNÍ WORKER PRO ODINSTALACI ---
class UninstallWorker(QThread):
    finished = pyqtSignal()
    log_signal = pyqtSignal(str)

    def __init__(self, app_ids):
        super().__init__()
        self.app_ids = app_ids
        self.process = None 
        self.is_cancelled = False

    def run(self):
        cmd_base = ["winget", "uninstall", "--silent", "--disable-interactivity", "--accept-source-agreements", "--verbose"]
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            for aid in self.app_ids:
                if self.is_cancelled: break
                self.log_signal.emit(f"\n--- ODINSTALUJI: {aid} ---")
                self._execute(cmd_base + ["--id", aid, "--exact"], startupinfo)
        except Exception as e:
            self.log_signal.emit(f"Kritická chyba: {str(e)}")
            
        self.finished.emit()

    def _execute(self, cmd, startupinfo):
        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace',
                startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                bufsize=1
            )
            for line in self.process.stdout:
                if self.is_cancelled:
                    self.process.kill()
                    break
                clean_line = line.strip()
                if clean_line:
                    self.log_signal.emit(clean_line)

            self.process.wait()
        except Exception as e:
            self.log_signal.emit(f"CHYBA PROCESU: {str(e)}")

    def kill_process(self):
        self.is_cancelled = True
        if self.process:
            try: self.process.kill() 
            except: pass


# --- WIDGET ŘÁDKU S APLIKACÍ ---
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

        # 1. Checkbox (modrý)
        self.chk = QCheckBox()
        self.chk.setFixedWidth(24)
        self.chk.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk.setStyleSheet(f"""
            QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid {COLORS['sub_text']}; border-radius: 4px; background: transparent; }}
            QCheckBox::indicator:checked {{ background-color: {COLORS['accent']}; border-color: {COLORS['accent']}; image: url(check.png); }} 
        """)
        self.chk.stateChanged.connect(self.parent_page.update_selection_ui)
        layout.addWidget(self.chk)

        # 2. Ikona
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(28, 28)
        
        found_local = self.set_local_icon(data['name'], data['id'])
        if not found_local:
            if self.set_system_fallback_icon(data['name']): pass 
            else:
                self.icon_lbl.setText("📦")
                self.icon_lbl.setStyleSheet("font-size: 16px; color: #777; background: transparent;")
                self.dl_worker = IconDownloadWorker(data['id'])
                self.dl_worker.loaded.connect(self.set_downloaded_icon)
                self.dl_worker.start()
        
        layout.addWidget(self.icon_lbl)

        # 3. Texty vedle sebe 
        text_layout = QHBoxLayout()
        text_layout.setSpacing(15)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        name_lbl = QLabel(data['name'])
        name_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: white; background: transparent;")
        
        id_lbl = QLabel(data['id'])
        id_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['sub_text']}; background: transparent;")

        text_layout.addWidget(name_lbl)
        text_layout.addWidget(id_lbl)
        text_layout.addStretch() 
        
        layout.addLayout(text_layout, stretch=1)

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


# --- 4. HLAVNÍ STRÁNKA (UninstallerPage) ---
class UninstallerPage(QWidget):
    def __init__(self):
        super().__init__()
        self.all_items = []
        self.active_workers = []
        self.current_worker = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        # A. HORNÍ LIŠTA S VYPRACOVANÝM HLEDÁNÍM
        top_bar = QWidget()
        top_bar.setStyleSheet(f"background-color: {COLORS['bg_main']}; border-bottom: 1px solid {COLORS['border']};")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 15, 20, 15)

        lbl_title = QLabel("Odinstalace")
        lbl_title.setStyleSheet("font-size: 14pt; font-weight: bold; color: white; border: none;")
        top_layout.addWidget(lbl_title)
        top_layout.addSpacing(20)

        self.search_container = QFrame()
        self.search_container.setFixedWidth(500)
        self.search_container.setFixedHeight(38)
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS['accent']}; }}")
        
        s_layout = QHBoxLayout(self.search_container)
        s_layout.setContentsMargins(10, 0, 5, 0)
        s_layout.setSpacing(0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Hledat v nainstalovaných aplikacích...")
        self.search_input.setStyleSheet("border: none; background: transparent; color: white; font-size: 10pt;")
        self.search_input.textChanged.connect(self.filter_items)
        s_layout.addWidget(self.search_input)

        search_input_icon = QLabel()
        search_input_icon.setFixedSize(32, 32)
        search_input_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_path_search = resource_path("assets/images/magnifying-glass-thin.png")
        if os.path.exists(icon_path_search):
            pix_s = QPixmap(icon_path_search).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            colored_pix = QPixmap(pix_s.size())
            colored_pix.fill(Qt.GlobalColor.transparent)
            cp = QPainter(colored_pix)
            cp.drawPixmap(0, 0, pix_s)
            cp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            cp.fillRect(colored_pix.rect(), QColor(COLORS['sub_text']))
            cp.end()
            search_input_icon.setPixmap(colored_pix)
            
        s_layout.addWidget(search_input_icon)
        top_layout.addWidget(self.search_container)
        top_layout.addStretch()
        main_layout.addWidget(top_bar)

        # B. PROGRESS BAR
        self.progress = QProgressBar()
        self.progress.setFixedHeight(2)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"QProgressBar {{ border: none; background: transparent; }} QProgressBar::chunk {{ background-color: {COLORS['accent']}; }}")
        self.progress.hide()
        main_layout.addWidget(self.progress)

        # C. ACTION BAR (Sjednocený layout s Updaterem)
        act_bar = QWidget()
        act_bar.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        action_layout = QHBoxLayout(act_bar)
        action_layout.setContentsMargins(20, 10, 20, 10)
        action_layout.setSpacing(10)

        self.refresh_btn = AnimatedActionButton(" Načíst aplikace", "assets/images/arrows-clockwise-thin.png")
        self.refresh_btn.clicked.connect(self.load_apps)
        action_layout.addWidget(self.refresh_btn)

        self.add_separator(action_layout)

        self.btn_un_sel = AnimatedActionButton(" Odinstalovat vybrané", "assets/images/trash-thin.png")
        self.btn_un_sel.setEnabled(False)
        self.btn_un_sel.clicked.connect(self.run_uninstall_selected)
        action_layout.addWidget(self.btn_un_sel)
        
        action_layout.addStretch()
        self.status = QLabel("Připraveno.")
        self.status.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 10pt;")
        action_layout.addWidget(self.status)
        main_layout.addWidget(act_bar)

        # VODOROVNÁ ČÁRA PŘES CELOU ŠÍŘKU
        h_sep = QFrame()
        h_sep.setFrameShape(QFrame.Shape.HLine)
        h_sep.setFixedHeight(1)
        h_sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        main_layout.addWidget(h_sep)

        # D. SEZNAM BEZ HLAVIČKY
        self.list_widget = QListWidget()
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{ background: {COLORS['bg_main']}; border: none; outline: none; padding: 10px 20px; }} 
            QListWidget::item {{ border-bottom: 1px solid transparent; padding: 0px; }} 
            QListWidget::item:hover {{ background: transparent; }} 
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS.get('accent', '#0078d4')}; min-height: 30px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS.get('accent_hover', '#1f8ad2')}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        main_layout.addWidget(self.list_widget)

        # E. KONZOLE 
        self.console_container = QFrame()
        self.console_container.setMaximumHeight(0)
        self.console_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_sidebar']}; border-top-left-radius: 12px; border-top-right-radius: 12px; border-top: 1px solid #333; }}")
        ccl = QVBoxLayout(self.console_container); ccl.setContentsMargins(15, 8, 15, 8); ccl.setSpacing(5)
        
        hl = QHBoxLayout(); self.con_title = QLabel("PRŮBĚH ODINSTALACE")
        self.con_title.setStyleSheet(f"color: white; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; background: transparent;")
        
        # Modernizované tlačítko Zrušit (ghost red button)
        self.btn_cancel = QPushButton("Zrušit"); self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.cancel_current_process)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{ 
                background: transparent; 
                color: {COLORS.get('danger', '#ff5555')}; 
                border: 1px solid {COLORS.get('danger', '#ff5555')}; 
                border-radius: 6px; 
                padding: 4px 16px; 
                font-size: 11px; 
                font-weight: bold; 
            }} 
            QPushButton:hover {{ 
                background: {COLORS.get('danger', '#ff5555')}; 
                color: white; 
            }}
        """)
        
        btn_close = QPushButton("✕"); btn_close.setFixedSize(20, 20); btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("QPushButton { background: transparent; color: #777; border: none; font-weight: bold; font-size: 12px; } QPushButton:hover { color: white; }")
        btn_close.clicked.connect(self.hide_console)
        
        hl.addWidget(self.con_title); hl.addStretch(); hl.addWidget(self.btn_cancel); hl.addSpacing(10); hl.addWidget(btn_close)
        ccl.addLayout(hl)
        
        self.console_out = QTextEdit(); self.console_out.setReadOnly(True)
        self.console_out.setStyleSheet(f"""
            QTextEdit {{ background: transparent; color: #ccc; border: none; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; }} 
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 6px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS.get('accent', '#0078d4')}; border-radius: 3px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS.get('accent_hover', '#1f8ad2')}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        ccl.addWidget(self.console_out)
        
        self.con_progress = QProgressBar(); self.con_progress.setFixedHeight(3); self.con_progress.setTextVisible(False)
        self.con_progress.setStyleSheet(f"QProgressBar {{ border: none; background: #222; border-radius: 1px; }} QProgressBar::chunk {{ background-color: {COLORS['accent']}; border-radius: 1px; }}")
        self.con_progress.setRange(0, 0); ccl.addWidget(self.con_progress)
        
        main_layout.addWidget(self.console_container)
        self.anim = QPropertyAnimation(self.console_container, b"maximumHeight"); self.anim.setDuration(400); self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def add_separator(self, layout):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(18)
        sep.setStyleSheet(f"background: {COLORS['border']}; border: none;")
        layout.addWidget(sep)

    def load_apps(self):
        self.list_widget.clear(); self.all_items = []
        self.refresh_btn.setEnabled(False)
        self.btn_un_sel.setEnabled(False); self.btn_un_sel.setText(" Odinstalovat vybrané")
        self.status.setText("Skenuji systém...")
        self.progress.setRange(0, 0); self.progress.show()
        
        self.worker = WingetListWorker()
        self.worker.finished.connect(self.on_loaded)
        self.worker.error.connect(lambda e: self.status.setText(f"Chyba: {e}"))
        self.worker.start()

    def on_loaded(self, apps):
        self.progress.hide()
        for app in apps:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 55))
            data = {'name': app['name'], 'id': app['id']}
            widget = AppItemWidget(data, self)
            self.list_widget.setItemWidget(item, widget)
            self.all_items.append((item, widget, app['name'].lower()))
        self.refresh_btn.setEnabled(True); self.status.setText(f"Nalezeno {len(apps)} aplikací.")

    def filter_items(self, text):
        t = text.lower()
        for item, widget, name in self.all_items: 
            item.setHidden(t not in name and t not in widget.data['id'].lower())

    def update_selection_ui(self):
        count = 0
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(widget, AppItemWidget) and widget.chk.isChecked():
                count += 1
                
        if count > 0:
            self.btn_un_sel.setText(f" Odinstalovat vybrané ({count})")
            self.btn_un_sel.setEnabled(True)
        else:
            self.btn_un_sel.setText(" Odinstalovat vybrané")
            self.btn_un_sel.setEnabled(False)

    # --- KONZOLOVÁ LOGIKA ---
    def append_log(self, text):
        color = "#cccccc"
        if "Chyba" in text or "Fail" in text or "error" in text.lower(): color = "#ff5555"
        elif "Success" in text or "Successfully" in text: color = "#55ff55"
        elif "Uninstalling" in text: color = "#ffaa00"
        elif "Zrušeno" in text: color = "#ff5555"
        self.console_out.append(f'<span style="color:{color}">{text}</span>')
        self.console_out.verticalScrollBar().setValue(self.console_out.verticalScrollBar().maximum())

    def cleanup_worker(self, worker):
        if worker in self.active_workers: self.active_workers.remove(worker)
        if self.current_worker == worker: self.current_worker = None

    def show_console(self, title):
        self.con_title.setText(title.upper()); self.console_out.clear(); self.con_progress.show(); self.btn_cancel.show()
        self.anim.stop(); self.anim.setStartValue(self.console_container.height()); self.anim.setEndValue(160); self.anim.start()

    def hide_console(self):
        self.anim.stop(); self.anim.setStartValue(self.console_container.height()); self.anim.setEndValue(0); self.anim.start()

    def cancel_current_process(self):
        if self.current_worker:
            self.current_worker.kill_process(); self.append_log("--- Operace Zrušena uživatelem ---")
            self.status.setText("Zrušeno"); self.con_progress.hide(); self.btn_cancel.hide()
            QTimer.singleShot(1500, self.hide_console)

    def on_uninstall_finished(self, worker):
        if worker == self.current_worker:
            self.append_log(f"--- Operace dokončena ---"); self.status.setText("Hotovo")
            self.con_progress.hide(); self.btn_cancel.hide(); self.load_apps()
            QTimer.singleShot(3000, self.hide_console)
        self.cleanup_worker(worker)

    def run_uninstall_selected(self):
        selected_ids = []
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(widget, AppItemWidget) and widget.chk.isChecked():
                selected_ids.append(widget.data['id'])
                
        if not selected_ids: return
        
        self.show_console("HROMADNÁ ODINSTALACE"); self.append_log(f"Připravuji odinstalaci pro {len(selected_ids)} aplikací...")
        self.status.setText(f"Odinstalovávám...")
        self.list_widget.setEnabled(False)
        
        w = UninstallWorker(app_ids=selected_ids); self.active_workers.append(w); self.current_worker = w
        w.log_signal.connect(self.append_log); w.finished.connect(lambda: self.list_widget.setEnabled(True)); w.finished.connect(lambda: self.on_uninstall_finished(w)); w.start()