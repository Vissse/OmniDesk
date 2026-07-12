import os
import json
import subprocess
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QMessageBox, QFileDialog, QFrame, QLineEdit)
from PyQt6.QtCore import Qt, QSize, QVariantAnimation, QRect, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QPainter, QPainterPath

from core.config import COLORS, resource_path
from core.install_manager import InstallationDialog
from core.theme_manager import theme_manager
from core.i18n import _, translator
from UI.shared_widgets import AnimatedActionButton, add_vertical_separator
from UI.pages.view_installer import InstallationOptionsDialog, HoverButton


from UI.workers.install_worker import VersionFetchWorker
from UI.components.queue_components import QueueRowWidget

class QueuePage(QWidget):
    def __init__(self):
        super().__init__()
        self.queue_data = {} 
        self.installer_page_ref = None
        self.installation_options = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- HORNI LISTA ---
        self.top_bar = QWidget()
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 15, 20, 15)

        self.lbl_title = QLabel()
        top_layout.addWidget(self.lbl_title)
        top_layout.addSpacing(20)

        self.search_container = QFrame()
        self.search_container.setFixedWidth(500)
        self.search_container.setFixedHeight(38)
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS.get('accent', '#0078d4')}; }}")
        
        search_cont_layout = QHBoxLayout(self.search_container)
        search_cont_layout.setContentsMargins(10, 0, 5, 0)
        search_cont_layout.setSpacing(0)

        self.local_search_input = QLineEdit()
        self.local_search_input.textChanged.connect(self.filter_queue)
        search_cont_layout.addWidget(self.local_search_input)
        
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
            cp.fillRect(colored_pix.rect(), QColor(COLORS.get('sub_text', '#a0a0a0')))
            cp.end()
            self.search_input_icon.setPixmap(colored_pix)
            
        search_cont_layout.addWidget(self.search_input_icon)
        top_layout.addWidget(self.search_container)
        top_layout.addStretch()
        main_layout.addWidget(self.top_bar)

        # --- AKCNI LISTA (DVOUŘÁDKOVÁ) ---
        self.action_bar = QWidget()
        
        action_layout = QVBoxLayout(self.action_bar)
        action_layout.setContentsMargins(20, 10, 20, 10)
        action_layout.setSpacing(10)

        # PRVNÍ ŘÁDEK
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(5)

        self.btn_install_main = AnimatedActionButton("", "assets/images/download-simple-thin.png")
        self.btn_install_main.setEnabled(False)
        self.btn_install_main.clicked.connect(self.run_installation)
        row1_layout.addWidget(self.btn_install_main)
        
        add_vertical_separator(row1_layout)
        
        self.btn_settings_quick = AnimatedActionButton("", "assets/images/gear-six-thin.png")
        self.btn_settings_quick.clicked.connect(self.open_options_dialog)
        row1_layout.addWidget(self.btn_settings_quick)
        
        row1_layout.addStretch()
        action_layout.addLayout(row1_layout)

        # DRUHÝ ŘÁDEK
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(5)

        self.btn_new = AnimatedActionButton("", "assets/images/plus-thin.png")
        self.btn_new.clicked.connect(self.clear_queue)
        row2_layout.addWidget(self.btn_new)

        add_vertical_separator(row2_layout)

        self.btn_open = AnimatedActionButton("", "assets/images/folder-open-thin.png")
        self.btn_open.clicked.connect(self.load_from_json)
        row2_layout.addWidget(self.btn_open)

        add_vertical_separator(row2_layout)

        self.btn_save = AnimatedActionButton("", "assets/images/floppy-disk-thin.png")
        self.btn_save.clicked.connect(self.save_to_json)
        row2_layout.addWidget(self.btn_save)

        add_vertical_separator(row2_layout)

        self.btn_ps1 = AnimatedActionButton("", "assets/images/terminal-window-thin.png")
        self.btn_ps1.clicked.connect(self.save_powershell_script)
        row2_layout.addWidget(self.btn_ps1)

        row2_layout.addStretch()
        action_layout.addLayout(row2_layout)

        main_layout.addWidget(self.action_bar)

        # --- SEZNAM APLIKACÍ ---
        self.h_sep = QFrame()
        self.h_sep.setFrameShape(QFrame.Shape.HLine)
        self.h_sep.setFixedHeight(1)
        main_layout.addWidget(self.h_sep)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{ background-color: {COLORS['bg_main']}; border: none; outline: none; padding: 10px 20px; }} 
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
        
        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.top_bar.setStyleSheet(f"background-color: {COLORS['bg_main']}; border-bottom: 1px solid {COLORS['border']};")
        self.lbl_title.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {COLORS['fg']}; border: none;")
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS.get('accent', '#0078d4')}; }}")
        self.local_search_input.setStyleSheet(f"border: none; background: transparent; color: {COLORS['fg']}; font-size: 10pt;")
        
        icon_path_search = resource_path("assets/images/magnifying-glass-thin.png")
        if os.path.exists(icon_path_search):
            pix_s = QPixmap(icon_path_search).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            colored_pix = QPixmap(pix_s.size())
            colored_pix.fill(Qt.GlobalColor.transparent)
            cp = QPainter(colored_pix)
            cp.drawPixmap(0, 0, pix_s)
            cp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            cp.fillRect(colored_pix.rect(), QColor(COLORS.get('sub_text', '#a0a0a0')))
            cp.end()
            self.search_input_icon.setPixmap(colored_pix)
            
        self.action_bar.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        self.h_sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        self.list_widget.setStyleSheet(f"""
            QListWidget {{ background-color: {COLORS['bg_main']}; border: none; outline: none; padding: 10px 20px; }} 
            QListWidget::item {{ border-bottom: 1px solid transparent; padding: 0px; }} 
            QListWidget::item:hover {{ background: transparent; }}
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS.get('accent', '#0078d4')}; min-height: 30px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS.get('accent_hover', '#1f8ad2')}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)

    def retranslate_ui(self):
        self.lbl_title.setText(_("qu_title"))
        self.local_search_input.setPlaceholderText(_("qu_search"))
        self.btn_settings_quick.setText(_("in_btn_settings"))
        self.btn_new.setText(_("qu_btn_new"))
        self.btn_open.setText(_("qu_btn_open"))
        self.btn_save.setText(_("qu_btn_save"))
        self.btn_ps1.setText(_("qu_btn_ps1"))
        self.update_selection_ui()

    def update_selection_ui(self):
        count = self.list_widget.count()
                
        if count > 0:
            self.btn_install_main.setText(_("qu_btn_install_all_c").format(count=count))
            self.btn_install_main.setEnabled(True)
        else:
            self.btn_install_main.setText(_("qu_btn_install_all"))
            self.btn_install_main.setEnabled(False)

    def run_installation(self):
        if not self.queue_data:
            QMessageBox.warning(self, _("in_empty_queue"), _("in_empty_queue_msg"))
            return
            
        selected = list(self.queue_data.values())
        InstallationDialog(selected, self).exec()

    def save_to_json(self):
        if not self.queue_data:
            QMessageBox.warning(self, _("in_empty_queue"), _("qu_empty_save_msg"))
            return
        path, _ = QFileDialog.getSaveFileName(self, "Uložit frontu", "fronta.json", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f: 
                json.dump(list(self.queue_data.values()), f, indent=4, ensure_ascii=False)

    def save_powershell_script(self):
        if not self.queue_data:
            QMessageBox.warning(self, _("in_empty_queue"), _("qu_empty_ps1_msg"))
            return
        path, _ = QFileDialog.getSaveFileName(self, "Vytvořit skript", "install.ps1", "PowerShell (*.ps1)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Winget Auto-Install\n")
                for app in self.queue_data.values():
                    f.write(f"winget install --id '{app['id']}' -e --accept-source-agreements --accept-package-agreements\n")

    def filter_queue(self, text):
        search_text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, QueueRowWidget):
                item.setHidden(search_text not in widget.data['name'].lower() and search_text not in widget.data['id'].lower())

    def clear_queue(self):
        if self.queue_data and QMessageBox.question(self, _("qu_btn_new").strip(), _("qu_clear_q")) == QMessageBox.StandardButton.Yes:
            self.queue_data.clear()
            self.list_widget.clear()
            self.update_selection_ui()
            if self.installer_page_ref: 
                self.installer_page_ref.refresh_checkboxes()

    def load_from_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Načíst frontu", "", "JSON (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f: 
                    apps = json.load(f)
                self.queue_data.clear()
                self.list_widget.clear()
                for app in apps: 
                    self.add_to_queue(app)
                self.update_selection_ui()
                if self.installer_page_ref: 
                    self.installer_page_ref.refresh_checkboxes()
            except Exception as e: 
                QMessageBox.critical(self, "Error", _("qu_err_load").format(e=e))

    def add_to_queue(self, data, icon=None):
        app_id = data['id']
        if app_id in self.queue_data: 
            return
            
        self.queue_data[app_id] = data
        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(QSize(0, 55))
        item.setData(Qt.ItemDataRole.UserRole, app_id)
        widget = QueueRowWidget(data, self, self, cached_icon=icon)
        self.list_widget.setItemWidget(item, widget)
        
        self.update_selection_ui()
        if self.installer_page_ref: 
            self.installer_page_ref.refresh_checkboxes()

    def remove_item_by_id(self, app_id):
        if app_id in self.queue_data: 
            del self.queue_data[app_id]
            
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == app_id:
                self.list_widget.takeItem(i)
                break
                
        self.update_selection_ui()
        if self.installer_page_ref: 
            self.installer_page_ref.refresh_checkboxes()

    def open_options_dialog(self):
        dlg = InstallationOptionsDialog(self, self.installation_options)
        if dlg.exec(): 
            self.installation_options = dlg.get_options()

    def set_installer_ref(self, ref): 
        self.installer_page_ref = ref
