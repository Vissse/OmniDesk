import subprocess
import os
import ctypes  # PŘIDÁNO: Pro detekci administrátorských práv
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QProgressBar, QFrame, QLineEdit, QFileIconProvider,
                             QTextEdit, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QFileInfo, QTimer, QPropertyAnimation, QEasingCurve, QVariantAnimation, QRect
from PyQt6.QtGui import QColor, QPixmap, QPainter, QPainterPath

from core.config import COLORS, resource_path
from core.utils import find_app_icon_path, find_main_exe_in_folder
from core.i18n import _, translator
from core.theme_manager import theme_manager
from UI.shared_widgets import AnimatedActionButton, IconDownloadWorker, add_vertical_separator


from UI.workers.update_worker import ScanWorker, UpdateWorker
from UI.components.updater_components import UpdateRowWidget

class UpdaterPage(QWidget):
    scan_finished_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.all_updates = [] 
        self.active_workers = []
        self.current_worker = None 

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        self.top_bar = QWidget()
        top_l = QHBoxLayout(self.top_bar); top_l.setContentsMargins(20, 15, 20, 15)
        
        self.lbl_title = QLabel()
        top_l.addWidget(self.lbl_title); top_l.addSpacing(20)

        self.search_container = QFrame()
        self.search_container.setFixedWidth(500); self.search_container.setFixedHeight(38)
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS['accent']}; }}")
        
        sl = QHBoxLayout(self.search_container); sl.setContentsMargins(10, 0, 5, 0); sl.setSpacing(0)
        
        self.search_in = QLineEdit()
        self.search_input_icon = QLabel()
        self.search_input_icon.setFixedSize(32, 32)
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
        main_layout.addWidget(self.top_bar)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(2); self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"QProgressBar {{ background: transparent; border: none; }} QProgressBar::chunk {{ background-color: {COLORS['accent']}; }}")
        self.progress.hide()
        main_layout.addWidget(self.progress)

        self.act_bar = QWidget()
        al = QHBoxLayout(self.act_bar)
        al.setContentsMargins(20, 10, 20, 10)
        al.setSpacing(10)

        self.btn_scan = AnimatedActionButton("", "assets/images/arrows-clockwise-thin.png")
        self.btn_scan.clicked.connect(self.scan_updates)
        al.addWidget(self.btn_scan)

        add_vertical_separator(al)

        self.btn_up_sel = AnimatedActionButton("", "assets/images/download-simple-thin.png")
        self.btn_up_sel.setEnabled(False)
        self.btn_up_sel.clicked.connect(self.run_update_selected)
        al.addWidget(self.btn_up_sel)

        add_vertical_separator(al)

        self.btn_up_all = AnimatedActionButton("", "assets/images/download-simple-thin.png")
        self.btn_up_all.setEnabled(False)
        self.btn_up_all.clicked.connect(self.run_update_all)
        al.addWidget(self.btn_up_all)
        
        al.addStretch()
        self.status_lbl = QLabel()
        self.status_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 10pt;")
        al.addWidget(self.status_lbl)
        main_layout.addWidget(self.act_bar)

        self.h_sep = QFrame()
        self.h_sep.setFrameShape(QFrame.Shape.HLine)
        self.h_sep.setFixedHeight(1)
        main_layout.addWidget(self.h_sep)

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
        ccl = QVBoxLayout(self.console_container); ccl.setContentsMargins(15, 8, 15, 8); ccl.setSpacing(5)
        hl = QHBoxLayout(); self.con_title = QLabel()
        
        self.btn_cancel = QPushButton(); self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.cancel_current_process)
        self.btn_cancel.setStyleSheet(f"QPushButton {{ background: {COLORS['bg_main']}; color: {COLORS.get('danger', '#ff5555')}; border: 1px solid {COLORS.get('danger', '#ff5555')}; border-radius: 4px; padding: 2px 10px; font-size: 10px; font-weight: bold; }} QPushButton:hover {{ background: {COLORS.get('danger', '#ff5555')}; color: {COLORS['fg']}; }}")
        
        btn_close = QPushButton("✕"); btn_close.setFixedSize(20, 20); btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(f"QPushButton {{ background: transparent; color: {COLORS['sub_text']}; border: none; font-weight: bold; font-size: 12px; }} QPushButton:hover {{ color: {COLORS['fg']}; }}")
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
        self.con_progress.setStyleSheet(f"QProgressBar {{ border: none; background: {COLORS['item_bg']}; border-radius: 1px; }} QProgressBar::chunk {{ background-color: {COLORS['accent']}; border-radius: 1px; }}")
        self.con_progress.setRange(0, 0); ccl.addWidget(self.con_progress)
        
        main_layout.addWidget(self.console_container)
        self.anim = QPropertyAnimation(self.console_container, b"maximumHeight"); self.anim.setDuration(400); self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.top_bar.setStyleSheet(f"background-color: {COLORS['bg_main']}; border-bottom: 1px solid {COLORS['border']};")
        self.lbl_title.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {COLORS['fg']}; border: none;")
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS['accent']}; }}")
        self.search_in.setStyleSheet(f"border: none; color: {COLORS['fg']}; background: transparent; font-size: 10pt;")
        
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
            
        self.progress.setStyleSheet(f"QProgressBar {{ background: transparent; border: none; }} QProgressBar::chunk {{ background-color: {COLORS['accent']}; }}")
        self.act_bar.setStyleSheet(f"background: {COLORS['bg_main']};")
        self.status_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 10pt;")
        self.h_sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        
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
        
        self.console_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_sidebar']}; border-top-left-radius: 12px; border-top-right-radius: 12px; border-top: 1px solid {COLORS['border']}; }}")
        self.con_title.setStyleSheet(f"color: {COLORS['fg']}; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; background: transparent;")
        
        self.console_out.setStyleSheet(f"""
            QTextEdit {{ background: transparent; color: {COLORS['fg']}; border: none; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; }} 
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS.get('accent', '#0078d4')}; min-height: 30px; border-radius: 4px; }}
        """)
        
        self.con_progress.setStyleSheet(f"QProgressBar {{ border: none; background: {COLORS['item_bg']}; border-radius: 1px; }} QProgressBar::chunk {{ background-color: {COLORS['accent']}; border-radius: 1px; }}")

    def retranslate_ui(self):
        self.lbl_title.setText(_("up_title"))
        self.search_in.setPlaceholderText(_("up_search"))
        self.btn_scan.setText(_("up_scan"))
        self.btn_cancel.setText(_("up_cancel"))
        self.con_title.setText(_("up_progress_title"))
        
        if not self.active_workers:
            if not self.all_updates:
                self.status_lbl.setText(_("up_status_ready") if self.btn_scan.isEnabled() else _("up_all_updated"))
            else:
                self.status_lbl.setText(_("up_status_found").format(count=len(self.all_updates)))
        
        self.update_selection_ui()
        if self.all_updates:
            self.btn_up_all.setText(_("up_update_all_c").format(count=len(self.all_updates)))
        else:
            self.btn_up_all.setText(_("up_update_all"))

    def scan_updates(self):
        self.list_widget.clear(); self.all_updates = []; self.btn_scan.setEnabled(False)
        
        self.btn_up_sel.setEnabled(False)
        self.btn_up_sel.setText(_("up_update_sel"))
        
        self.btn_up_all.setEnabled(False)
        self.btn_up_all.setText(_("up_update_all"))

        self.status_lbl.setText(_("up_status_scan")); self.progress.setRange(0, 0); self.progress.show()
        self.worker = ScanWorker(); self.worker.finished.connect(self.on_scan_done); self.worker.error.connect(lambda e: self.on_scan_done([])); self.worker.start()

    def on_scan_done(self, updates):
        updates.sort(key=lambda x: x['name'].lower())
        self.progress.hide(); self.btn_scan.setEnabled(True); self.all_updates = updates
        self.render_list(updates); self.scan_finished_signal.emit(updates)
        
        if updates: 
            self.status_lbl.setText(_("up_status_found").format(count=len(updates)))
            self.btn_up_all.setEnabled(True)
            self.btn_up_all.setText(_("up_update_all_c").format(count=len(updates)))
        else: 
            self.status_lbl.setText(_("up_status_uptodate"))

    def render_list(self, updates):
        self.list_widget.clear()
        for u in updates:
            item = QListWidgetItem(self.list_widget); item.setSizeHint(QSize(0, 55))
            self.list_widget.setItemWidget(item, UpdateRowWidget(u, self))
        if not updates:
            item = QListWidgetItem(self.list_widget); item.setSizeHint(QSize(0, 100))
            l = QLabel(_("up_all_updated")); l.setAlignment(Qt.AlignmentFlag.AlignCenter); l.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 14px;")
            self.list_widget.setItemWidget(item, l)
        self.update_selection_ui()

    def filter_updates(self, txt):
        f = [u for u in self.all_updates if txt.lower() in u['name'].lower()]
        self.render_list(f)

    def update_selection_ui(self):
        count = 0
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            # OPRAVA 3: Kontrolujeme, že se jedná o UpdateRowWidget a ne o fallback QLabel při vyhledávání
            if isinstance(widget, UpdateRowWidget) and hasattr(widget, 'chk') and widget.chk.isChecked():
                count += 1
                
        if count > 0:
            self.btn_up_sel.setText(_("up_update_sel_c").format(count=count))
            self.btn_up_sel.setEnabled(True)
        else:
            self.btn_up_sel.setText(_("up_update_sel"))
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
            self.current_worker.kill_process(); self.append_log("--- " + _("up_status_canceled") + " ---")
            self.status_lbl.setText(_("up_status_canceled")); self.con_progress.hide(); self.btn_cancel.hide()
            QTimer.singleShot(1500, self.hide_console)

    def on_update_finished(self, worker, name):
        if worker == self.current_worker:
            self.append_log("--- " + _("up_status_done") + " ---"); self.status_lbl.setText(_("up_status_done"))
            self.con_progress.hide(); self.btn_cancel.hide(); self.scan_updates()
            QTimer.singleShot(3000, self.hide_console)
        self.cleanup_worker(worker)

    def run_update(self, app_ids, name):
        if not app_ids: return
        self.show_console(f"{_('up_progress_title')}: {name}"); self.append_log(f"{_('up_status_updating').format(name=name)}")
        self.status_lbl.setText(_("up_status_updating").format(name=name))
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
        self.show_console(_("up_progress_title")); self.append_log(_("up_status_mass"))
        self.status_lbl.setText(_("up_status_mass")); self.list_widget.setEnabled(False)
        w = UpdateWorker(update_all=True); self.active_workers.append(w); self.current_worker = w
        w.log_signal.connect(self.append_log)
        
        # OPRAVA 4: Sloučení do jedné přehledné lambda funkce, aby se předešlo duplicitám signálů
        w.finished.connect(lambda: [self.list_widget.setEnabled(True), self.on_update_finished(w, "Vše")])
        w.start()
