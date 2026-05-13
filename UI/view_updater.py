import subprocess
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QProgressBar, QFrame, QLineEdit, QFileIconProvider,
                             QTextEdit, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QFileInfo, QTimer, QPropertyAnimation, QEasingCurve, QVariantAnimation, QRect
from PyQt6.QtGui import QColor, QPixmap, QPainter, QPainterPath

from core.config import COLORS, resource_path
from core.utils import find_app_icon_path, find_main_exe_in_folder
from UI.shared_widgets import AnimatedActionButton, IconDownloadWorker, add_vertical_separator

class ScanWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            cmd = "winget upgrade --include-unknown --accept-source-agreements"
            
            res = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo, encoding='utf-8', errors='replace')
            
            updates = []
            parsing = False
            lines = res.stdout.split('\n')
            
            for line in lines:
                clean_line = line.strip()
                if not clean_line: continue
                
                if "Name" in line and "Id" in line and "Version" in line: 
                    parsing = True
                    continue
                if not parsing or "----" in line: 
                    continue
                
                if "have an upgrade available" in clean_line or "upgrades available" in clean_line:
                    continue

                parts = clean_line.split()
                
                if len(parts) >= 4:
                    source = parts[-1]
                    new_ver = parts[-2]
                    
                    if parts[-4] == '<':
                        curr_ver = f"{parts[-4]} {parts[-3]}"
                        app_id = parts[-5]
                        name_parts = parts[:-5]
                    else:
                        curr_ver = parts[-3]
                        app_id = parts[-4]
                        name_parts = parts[:-4]

                    name = " ".join(name_parts)
                    
                    if new_ver.lower() == "winget":
                         pass

                    updates.append({'name': name, 'id': app_id, 'current': curr_ver, 'new': new_ver})

            self.finished.emit(updates)
        except Exception as e: 
            self.error.emit(str(e))

class UpdateWorker(QThread):
    finished = pyqtSignal()
    log_signal = pyqtSignal(str)

    def __init__(self, app_ids=None, update_all=False):
        super().__init__()
        self.app_ids = app_ids or []
        self.update_all = update_all
        self.process = None 
        self.is_cancelled = False

    def run(self):
        cmd_base = ["winget", "upgrade", "--silent", "--disable-interactivity", "--accept-package-agreements", "--accept-source-agreements", "--verbose"]
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            if self.update_all:
                self.log_signal.emit("\n--- HROMADNÁ AKTUALIZACE VŠECH BALÍČKŮ ---")
                self._execute(cmd_base + ["--all", "--include-unknown"], startupinfo)
            else:
                for aid in self.app_ids:
                    if self.is_cancelled: break
                    self.log_signal.emit(f"\n--- AKTUALIZUJI: {aid} ---")
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


class UpdateRowWidget(QWidget):
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
        self.chk.stateChanged.connect(self.parent_page.update_selection_ui)
        layout.addWidget(self.chk)

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

        text_layout = QHBoxLayout()
        text_layout.setSpacing(10)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        name_lbl = QLabel(data['name'])
        name_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: white; background: transparent;")
        
        curr_lbl = QLabel(data['current'])
        curr_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['sub_text']}; background: transparent;")
        
        self.sep_lbl = QLabel()
        self.sep_lbl.setFixedSize(16, 16)
        arrow_path = resource_path("assets/images/right-arrow-thin.png")
        if not os.path.exists(arrow_path):
            arrow_path = resource_path("assets/images/arrow-right-thin.png")
            
        if os.path.exists(arrow_path):
            pix = QPixmap(arrow_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            colored_pix = QPixmap(pix.size())
            colored_pix.fill(Qt.GlobalColor.transparent)
            cp = QPainter(colored_pix)
            cp.drawPixmap(0, 0, pix)
            cp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            cp.fillRect(colored_pix.rect(), QColor(COLORS['sub_text'])) 
            cp.end()
            self.sep_lbl.setPixmap(colored_pix)
        else:
            self.sep_lbl.setText("→")
            self.sep_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['sub_text']}; background: transparent;")
        
        new_lbl = QLabel(data['new'])
        new_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['accent']}; background: transparent;")

        text_layout.addWidget(name_lbl)
        text_layout.addSpacing(5)
        text_layout.addWidget(curr_lbl)
        text_layout.addWidget(self.sep_lbl)
        text_layout.addWidget(new_lbl)
        text_layout.addStretch() 
        
        layout.addLayout(text_layout, stretch=1)

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
        if not icon_path:
            names_to_try = [name]
            if app_id and "." in app_id: names_to_try.append(app_id.split('.')[0])
            for n in names_to_try:
                common_paths = [
                    os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), n),
                    os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), n),
                    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", n)
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        found_exe = find_main_exe_in_folder(path)
                        if found_exe: icon_path = found_exe; break
                if icon_path: break
                        
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
        
        is_teams = "teams" in n
        
        if any(x in n for x in ["java", "jdk", "jre", "temurin", "oracle"]): 
            icon_name = "java.png"
            use_original = True
        elif any(x in n for x in ["microsoft", "windows", "redist", "c++", ".net"]) and not is_teams:
            icon_name = "windows.png"
            use_original = True
        elif any(x in n for x in ["driver", "realtek", "nvidia", "amd", "intel"]): 
            icon_name = "circuitry-thin.png"
        elif "sdk" in n: 
            icon_name = "code-thin.png"
        
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


class UpdaterPage(QWidget):
    scan_finished_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.all_updates = [] 
        self.active_workers = []
        self.current_worker = None 

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setStyleSheet(f"background-color: {COLORS['bg_main']}; border-bottom: 1px solid {COLORS['border']};")
        top_l = QHBoxLayout(top_bar); top_l.setContentsMargins(20, 15, 20, 15)
        
        lbl_title = QLabel("Aktualizace")
        lbl_title.setStyleSheet("font-size: 14pt; font-weight: bold; color: white; border: none;")
        top_l.addWidget(lbl_title); top_l.addSpacing(20)

        self.search_container = QFrame()
        self.search_container.setFixedWidth(500); self.search_container.setFixedHeight(38)
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS['accent']}; }}")
        
        sl = QHBoxLayout(self.search_container); sl.setContentsMargins(10, 0, 5, 0); sl.setSpacing(0)
        
        self.search_in = QLineEdit()
        self.search_input_icon = QLabel()
        self.search_input_icon.setFixedSize(32, 32)
        self.search_in.setPlaceholderText("Hledat v aktualizacích...")
        self.search_in.setStyleSheet("border: none; color: white; background: transparent; font-size: 10pt;")
        self.search_in.textChanged.connect(self.filter_updates)
        sl.addWidget(self.search_in)
        
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
            self.search_input_icon.setPixmap(colored_pix)
            
        self.search_input_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sl.addWidget(self.search_input_icon)
        
        top_l.addWidget(self.search_container); top_l.addStretch()
        main_layout.addWidget(top_bar)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(2); self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"QProgressBar {{ background: transparent; border: none; }} QProgressBar::chunk {{ background-color: {COLORS['accent']}; }}")
        self.progress.hide()
        main_layout.addWidget(self.progress)

        act_bar = QWidget()
        act_bar.setStyleSheet(f"background: {COLORS['bg_main']};")
        al = QHBoxLayout(act_bar)
        al.setContentsMargins(20, 10, 20, 10)
        al.setSpacing(10)

        self.btn_scan = AnimatedActionButton(" Skenovat", "assets/images/arrows-clockwise-thin.png")
        self.btn_scan.clicked.connect(self.scan_updates)
        al.addWidget(self.btn_scan)

        add_vertical_separator(al)

        self.btn_up_sel = AnimatedActionButton(" Aktualizovat vybrané", "assets/images/download-simple-thin.png")
        self.btn_up_sel.setEnabled(False)
        self.btn_up_sel.clicked.connect(self.run_update_selected)
        al.addWidget(self.btn_up_sel)

        add_vertical_separator(al)

        self.btn_up_all = AnimatedActionButton(" Aktualizovat vše", "assets/images/download-simple-thin.png")
        self.btn_up_all.setEnabled(False)
        self.btn_up_all.clicked.connect(self.run_update_all)
        al.addWidget(self.btn_up_all)
        
        al.addStretch()
        self.status_lbl = QLabel("Připraveno"); self.status_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 10pt;")
        al.addWidget(self.status_lbl)
        main_layout.addWidget(act_bar)

        h_sep = QFrame()
        h_sep.setFrameShape(QFrame.Shape.HLine)
        h_sep.setFixedHeight(1)
        h_sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        main_layout.addWidget(h_sep)

        self.list_widget = QListWidget()
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
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        main_layout.addWidget(self.list_widget)

        self.console_container = QFrame(); self.console_container.setMaximumHeight(0)
        self.console_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_sidebar']}; border-top-left-radius: 12px; border-top-right-radius: 12px; border-top: 1px solid #333; }}")
        ccl = QVBoxLayout(self.console_container); ccl.setContentsMargins(15, 8, 15, 8); ccl.setSpacing(5)
        hl = QHBoxLayout(); self.con_title = QLabel("PRŮBĚH INSTALACE")
        self.con_title.setStyleSheet(f"color: white; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; background: transparent;")
        
        self.btn_cancel = QPushButton("Zrušit"); self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.cancel_current_process)
        self.btn_cancel.setStyleSheet("QPushButton { background: #333; color: #ff5555; border: 1px solid #ff5555; border-radius: 4px; padding: 2px 10px; font-size: 10px; font-weight: bold; } QPushButton:hover { background: #ff5555; color: white; }")
        
        btn_close = QPushButton("✕"); btn_close.setFixedSize(20, 20); btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("QPushButton { background: transparent; color: #777; border: none; font-weight: bold; font-size: 12px; } QPushButton:hover { color: white; }")
        btn_close.clicked.connect(self.hide_console)
        
        hl.addWidget(self.con_title); hl.addStretch(); hl.addWidget(self.btn_cancel); hl.addSpacing(10); hl.addWidget(btn_close)
        ccl.addLayout(hl)
        
        self.console_out = QTextEdit(); self.console_out.setReadOnly(True)
        self.console_out.setStyleSheet(f"""
            QTextEdit {{ background: transparent; color: #ccc; border: none; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; }} 
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS.get('accent', '#0078d4')}; min-height: 30px; border-radius: 4px; }}
        """)
        ccl.addWidget(self.console_out)
        
        self.con_progress = QProgressBar(); self.con_progress.setFixedHeight(3); self.con_progress.setTextVisible(False)
        self.con_progress.setStyleSheet(f"QProgressBar {{ border: none; background: #222; border-radius: 1px; }} QProgressBar::chunk {{ background-color: {COLORS['accent']}; border-radius: 1px; }}")
        self.con_progress.setRange(0, 0); ccl.addWidget(self.con_progress)
        
        main_layout.addWidget(self.console_container)
        self.anim = QPropertyAnimation(self.console_container, b"maximumHeight"); self.anim.setDuration(400); self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def scan_updates(self):
        self.list_widget.clear(); self.all_updates = []; self.btn_scan.setEnabled(False)
        
        self.btn_up_sel.setEnabled(False)
        self.btn_up_sel.setText(" Aktualizovat vybrané")
        
        self.btn_up_all.setEnabled(False)
        self.btn_up_all.setText(" Aktualizovat vše")

        self.status_lbl.setText("Hledám aktualizace..."); self.progress.setRange(0, 0); self.progress.show()
        self.worker = ScanWorker(); self.worker.finished.connect(self.on_scan_done); self.worker.error.connect(lambda e: self.on_scan_done([])); self.worker.start()

    def on_scan_done(self, updates):
        updates.sort(key=lambda x: x['name'].lower())
        self.progress.hide(); self.btn_scan.setEnabled(True); self.all_updates = updates
        self.render_list(updates); self.scan_finished_signal.emit(updates)
        
        if updates: 
            self.status_lbl.setText(f"Nalezeno {len(updates)} aktualizací")
            self.btn_up_all.setEnabled(True)
            self.btn_up_all.setText(f" Aktualizovat vše ({len(updates)})")
        else: 
            self.status_lbl.setText("Vše aktuální")

    def render_list(self, updates):
        self.list_widget.clear()
        for u in updates:
            item = QListWidgetItem(self.list_widget); item.setSizeHint(QSize(0, 55))
            self.list_widget.setItemWidget(item, UpdateRowWidget(u, self))
        if not updates:
            item = QListWidgetItem(self.list_widget); item.setSizeHint(QSize(0, 100))
            l = QLabel("Všechny aplikace jsou aktuální"); l.setAlignment(Qt.AlignmentFlag.AlignCenter); l.setStyleSheet("color: #666; font-size: 14px;"); self.list_widget.setItemWidget(item, l)
        self.update_selection_ui()

    def filter_updates(self, txt):
        f = [u for u in self.all_updates if txt.lower() in u['name'].lower()]
        self.render_list(f)

    def update_selection_ui(self):
        count = 0
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(widget, UpdateRowWidget) and widget.chk.isChecked():
                count += 1
                
        if count > 0:
            self.btn_up_sel.setText(f" Aktualizovat vybrané ({count})")
            self.btn_up_sel.setEnabled(True)
        else:
            self.btn_up_sel.setText(" Aktualizovat vybrané")
            self.btn_up_sel.setEnabled(False)

    def append_log(self, text):
        color = "#cccccc"
        if "Chyba" in text or "Fail" in text or "error" in text.lower(): color = "#ff5555"
        elif "Success" in text or "Successfully" in text: color = "#55ff55"
        elif "Downloading" in text: color = "#55ffff"
        elif "Installing" in text: color = "#ffff55"
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
            self.status_lbl.setText("Zrušeno"); self.con_progress.hide(); self.btn_cancel.hide()
            QTimer.singleShot(1500, self.hide_console)

    def on_update_finished(self, worker, name):
        if worker == self.current_worker:
            self.append_log(f"--- Operace dokončena ---"); self.status_lbl.setText("Hotovo")
            self.con_progress.hide(); self.btn_cancel.hide(); self.scan_updates()
            QTimer.singleShot(3000, self.hide_console)
        self.cleanup_worker(worker)

    def run_update(self, app_ids, name):
        if not app_ids: return
        self.show_console(f"AKTUALIZACE: {name}"); self.append_log(f"Připravuji aktualizaci pro: {name}...")
        self.status_lbl.setText(f"Aktualizuji: {name}...")
        w = UpdateWorker(app_ids=app_ids); self.active_workers.append(w); self.current_worker = w
        w.log_signal.connect(self.append_log); w.finished.connect(lambda: self.on_update_finished(w, name)); w.start()

    def run_update_selected(self):
        selected_ids = []
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(widget, UpdateRowWidget) and widget.chk.isChecked():
                selected_ids.append(widget.data['id'])
                
        if not selected_ids: return
        self.run_update(selected_ids, f"Vybrané aplikace ({len(selected_ids)})")

    def run_update_all(self):
        self.show_console("HROMADNÁ AKTUALIZACE"); self.append_log("Spouštím aktualizaci všech balíčků...")
        self.status_lbl.setText("Probíhá hromadná aktualizace..."); self.list_widget.setEnabled(False)
        w = UpdateWorker(update_all=True); self.active_workers.append(w); self.current_worker = w
        w.log_signal.connect(self.append_log); w.finished.connect(lambda: self.list_widget.setEnabled(True)); w.finished.connect(lambda: self.on_update_finished(w, "Vše")); w.start()