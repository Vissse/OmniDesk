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
from core.i18n import _, translator
from core.theme_manager import theme_manager
from UI.shared_widgets import AnimatedActionButton, IconDownloadWorker, add_vertical_separator


from UI.workers.uninstall_worker import UninstallWorker
from UI.components.uninstaller_components import AppItemWidget

class UninstallerPage(QWidget):
    def __init__(self):
        super().__init__()
        self.all_items = []
        self.active_workers = []
        self.current_worker = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        self.top_bar = QWidget()
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 15, 20, 15)

        self.lbl_title = QLabel()
        top_layout.addWidget(self.lbl_title)
        top_layout.addSpacing(20)

        self.search_container = QFrame()
        self.search_container.setFixedWidth(500)
        self.search_container.setFixedHeight(38)
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS['accent']}; }}")
        
        s_layout = QHBoxLayout(self.search_container)
        s_layout.setContentsMargins(10, 0, 5, 0)
        s_layout.setSpacing(0)

        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_items)
        s_layout.addWidget(self.search_input)

        self.search_input_icon = QLabel()
        self.search_input_icon.setFixedSize(32, 32)
        self.search_input_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
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
            
        s_layout.addWidget(self.search_input_icon)
        top_layout.addWidget(self.search_container)
        top_layout.addStretch()
        main_layout.addWidget(self.top_bar)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(2)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"QProgressBar {{ border: none; background: transparent; }} QProgressBar::chunk {{ background-color: {COLORS['accent']}; }}")
        self.progress.hide()
        main_layout.addWidget(self.progress)

        self.act_bar = QWidget()
        action_layout = QHBoxLayout(self.act_bar)
        action_layout.setContentsMargins(20, 10, 20, 10)
        action_layout.setSpacing(10)

        self.refresh_btn = AnimatedActionButton("", "assets/images/arrows-clockwise-thin.png")
        self.refresh_btn.clicked.connect(self.load_apps)
        action_layout.addWidget(self.refresh_btn)

        add_vertical_separator(action_layout)

        self.btn_un_sel = AnimatedActionButton("", "assets/images/trash-thin.png")
        self.btn_un_sel.setEnabled(False)
        self.btn_un_sel.clicked.connect(self.run_uninstall_selected)
        action_layout.addWidget(self.btn_un_sel)
        
        action_layout.addStretch()
        self.status = QLabel()
        self.status.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 10pt;")
        action_layout.addWidget(self.status)
        main_layout.addWidget(self.act_bar)

        self.h_sep = QFrame()
        self.h_sep.setFrameShape(QFrame.Shape.HLine)
        self.h_sep.setFixedHeight(1)
        main_layout.addWidget(self.h_sep)

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

        self.console_container = QFrame()
        self.console_container.setMaximumHeight(0)
        ccl = QVBoxLayout(self.console_container); ccl.setContentsMargins(15, 8, 15, 8); ccl.setSpacing(5)
        
        hl = QHBoxLayout(); self.con_title = QLabel()
        
        self.btn_cancel = QPushButton(); self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
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
        btn_close.setStyleSheet(f"QPushButton {{ background: transparent; color: {COLORS['sub_text']}; border: none; font-weight: bold; font-size: 12px; }} QPushButton:hover {{ color: {COLORS['fg']}; }}")
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
        self.search_input.setStyleSheet(f"border: none; background: transparent; color: {COLORS['fg']}; font-size: 10pt;")
        
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
            
        self.progress.setStyleSheet(f"QProgressBar {{ border: none; background: transparent; }} QProgressBar::chunk {{ background-color: {COLORS['accent']}; }}")
        self.act_bar.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        self.status.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 10pt;")
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
        
        self.console_out.setStyleSheet(f"""
            QTextEdit {{ background: transparent; color: {COLORS['fg']}; border: none; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; }} 
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 6px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS.get('accent', '#0078d4')}; border-radius: 3px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS.get('accent_hover', '#1f8ad2')}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        
        self.con_progress.setStyleSheet(f"QProgressBar {{ border: none; background: {COLORS['item_bg']}; border-radius: 1px; }} QProgressBar::chunk {{ background-color: {COLORS['accent']}; border-radius: 1px; }}")

    def retranslate_ui(self):
        self.lbl_title.setText(_("un_title"))
        self.search_input.setPlaceholderText(_("un_search"))
        self.refresh_btn.setText(_("un_load"))
        self.btn_cancel.setText(_("up_cancel"))
        self.con_title.setText(_("un_progress_title"))
        
        if not self.active_workers:
            if not self.all_items:
                self.status.setText(_("up_status_ready"))
            else:
                self.status.setText(_("un_status_found").format(count=len(self.all_items)))
                
        self.update_selection_ui()

    def set_app_locked(self, locked):
        main_win = self.window()
        if hasattr(main_win, 'sidebar_container'):
            main_win.sidebar_container.setEnabled(not locked)

    def load_apps(self):
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        self.list_widget.clear(); self.all_items = []
        self.refresh_btn.setEnabled(False)
        self.btn_un_sel.setEnabled(False); self.btn_un_sel.setText(_("un_uninstall_sel"))
        self.status.setText(_("un_status_scan"))
        self.progress.setRange(0, 0); self.progress.show()
        
        self.set_app_locked(True)
        
        self.worker = WingetListWorker()
        self.worker.finished.connect(self.on_loaded)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_error(self, e):
        from PyQt6.QtWidgets import QApplication
        QApplication.restoreOverrideCursor()
        
        self.status.setText(f"Chyba: {e}")
        self.progress.hide()
        self.refresh_btn.setEnabled(True)
        self.set_app_locked(False)

    def on_loaded(self, apps):
        self.progress.hide()
        
        from PyQt6.QtCore import QCoreApplication
        for i, app in enumerate(apps):
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 55))
            data = {'name': app['name'], 'id': app['id']}
            widget = AppItemWidget(data, self)
            self.list_widget.setItemWidget(item, widget)
            self.all_items.append((item, widget, app['name'].lower()))
            
            if i % 10 == 0:
                QCoreApplication.processEvents()
                
        self.refresh_btn.setEnabled(True)
        self.status.setText(_("un_status_found").format(count=len(apps)))
        self.set_app_locked(False)
        
        from PyQt6.QtWidgets import QApplication
        QApplication.restoreOverrideCursor()

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
            self.btn_un_sel.setText(_("un_uninstall_sel_c").format(count=count))
            self.btn_un_sel.setEnabled(True)
        else:
            self.btn_un_sel.setText(_("un_uninstall_sel"))
            self.btn_un_sel.setEnabled(False)

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
            self.current_worker.kill_process(); self.append_log("--- " + _("up_status_canceled") + " ---")
            self.status.setText(_("up_status_canceled")); self.con_progress.hide(); self.btn_cancel.hide()
            QTimer.singleShot(1500, self.hide_console)

    def on_uninstall_finished(self, worker):
        if worker == self.current_worker:
            self.append_log("--- " + _("up_status_done") + " ---"); self.status.setText(_("up_status_done"))
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
        
        self.show_console(_("un_progress_title")); self.append_log(f"{_('un_status_uninstalling')}")
        self.status.setText(_("un_status_uninstalling"))
        self.list_widget.setEnabled(False)
        
        w = UninstallWorker(app_ids=selected_ids); self.active_workers.append(w); self.current_worker = w
        w.log_signal.connect(self.append_log); w.finished.connect(lambda: self.list_widget.setEnabled(True)); w.finished.connect(lambda: self.on_uninstall_finished(w)); w.start()
