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
from UI.view_installer import InstallationOptionsDialog
from UI.shared_widgets import AnimatedActionButton, add_vertical_separator
from UI.view_installer import InstallationOptionsDialog, HoverButton

class VersionFetchWorker(QThread):
    version_found = pyqtSignal(str)

    def __init__(self, app_id):
        super().__init__()
        self.app_id = app_id

    def run(self):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            cmd = ["winget", "show", "--id", self.app_id, "--exact", "--disable-interactivity", "--accept-source-agreements"]
            
            res = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                startupinfo=startupinfo, 
                encoding='utf-8', 
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            version = "Latest"
            for line in res.stdout.split('\n'):
                clean_line = line.strip()
                if clean_line.startswith("Version:") or clean_line.startswith("Verze:"):
                    version = clean_line.split(":", 1)[1].strip()
                    break
            
            self.version_found.emit(version)
        except Exception:
            self.version_found.emit("Neznámá")


class QueueRowWidget(QWidget):
    def __init__(self, data, parent_controller, queue_page_ref, cached_icon=None):
        super().__init__()
        self.data = data
        self.controller = parent_controller
        self.queue_page = queue_page_ref
        self.current_pixmap = cached_icon

        self.setFixedHeight(55)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._bg_color = QColor("transparent")
        self._bar_height_factor = 0.0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 2, 20, 2)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Ikonka aplikace
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(28, 28)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if cached_icon:
            self.set_icon(cached_icon)
        else:
            icon_path = data.get('icon_url')
            if icon_path and os.path.exists(icon_path):
                pix = QPixmap(icon_path).scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.icon_lbl.setPixmap(pix)
            else:
                self.icon_lbl.setText("📦") 
                self.icon_lbl.setStyleSheet("font-size: 16px; color: #888; border: none; background: transparent;")
        layout.addWidget(self.icon_lbl)

        # Texty (Název, oddělovač, verze)
        text_layout = QHBoxLayout()
        text_layout.setSpacing(8)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        name_lbl = QLabel(data['name'])
        name_lbl.setStyleSheet("font-weight: bold; color: white; font-size: 14px; background: transparent;")
        text_layout.addWidget(name_lbl)
        
        sep_lbl = QLabel("•")
        sep_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 14px; font-weight: bold; background: transparent;")
        text_layout.addWidget(sep_lbl)

        self.ver_lbl = QLabel(data.get('version', 'Načítání...'))
        self.ver_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 12px; background: transparent;")
        text_layout.addWidget(self.ver_lbl)

        text_layout.addStretch()
        layout.addLayout(text_layout, stretch=1)

        # Tlačítko pro odstranění (křížek) zarovnané doprava
        self.btn_remove = HoverButton("", "assets/images/x-thin.png", "sub_text", hover_style="danger")
        self.btn_remove.setFixedSize(28, 28)
        self.btn_remove.setIconSize(QSize(18, 18))
        self.btn_remove.setToolTip("Odebrat aplikaci z fronty")
        self.btn_remove.clicked.connect(self.remove_self)
        layout.addWidget(self.btn_remove)

        # Načítání verze na pozadí
        if data.get('version') in [None, "Latest", "Unknown", "Neznámá", "Načítání...", ""]:
            self.ver_lbl.setText("Načítání...")
            self.ver_worker = VersionFetchWorker(self.data['id'])
            self.ver_worker.version_found.connect(self.on_version_found)
            self.ver_worker.start()

        # Animace při najetí myší
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)

    def remove_self(self):
        self.queue_page.remove_item_by_id(self.data['id'])

    def on_version_found(self, version):
        self.ver_lbl.setText(version)
        self.data['version'] = version

    def set_icon(self, pixmap):
        self.current_pixmap = pixmap
        scaled = pixmap.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.icon_lbl.setPixmap(scaled)
        self.icon_lbl.setText("")

    def _animate_step(self, val):
        self._bar_height_factor = val
        target_bg = QColor(COLORS.get('item_hover', '#2d2d30'))
        self._bg_color = QColor(target_bg.red(), target_bg.green(), target_bg.blue(), int(255 * val))
        self.update()

    def enterEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Forward)
        self.anim.start()

    def leaveEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Backward)
        self.anim.start()

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
            p.setBrush(QColor(COLORS.get('accent', '#0078d4')))
            p.setPen(Qt.PenStyle.NoPen)
            h = rect.height() * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            
            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)
            p.setClipPath(path)
            p.drawRect(QRect(rect.x(), int(y), 4, int(h)))
            p.setClipping(False)


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
        top_bar = QWidget()
        top_bar.setStyleSheet(f"background-color: {COLORS['bg_main']}; border-bottom: 1px solid {COLORS['border']};")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 15, 20, 15)

        lbl_title = QLabel("Instalační fronta")
        lbl_title.setStyleSheet("font-size: 14pt; font-weight: bold; color: white; border: none;")
        top_layout.addWidget(lbl_title)
        top_layout.addSpacing(20)

        self.search_container = QFrame()
        self.search_container.setFixedWidth(500)
        self.search_container.setFixedHeight(38)
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS.get('accent', '#0078d4')}; }}")
        
        search_cont_layout = QHBoxLayout(self.search_container)
        search_cont_layout.setContentsMargins(10, 0, 5, 0)
        search_cont_layout.setSpacing(0)

        self.local_search_input = QLineEdit()
        self.local_search_input.setPlaceholderText("Hledat v seznamu fronty...")
        self.local_search_input.setStyleSheet("border: none; background: transparent; color: white; font-size: 10pt;")
        self.local_search_input.textChanged.connect(self.filter_queue)
        search_cont_layout.addWidget(self.local_search_input)
        
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
            cp.fillRect(colored_pix.rect(), QColor(COLORS.get('sub_text', '#a0a0a0')))
            cp.end()
            search_input_icon.setPixmap(colored_pix)
            
        search_cont_layout.addWidget(search_input_icon)
        top_layout.addWidget(self.search_container)
        top_layout.addStretch()
        main_layout.addWidget(top_bar)

        # --- AKCNI LISTA (DVOUŘÁDKOVÁ) ---
        action_bar = QWidget()
        action_bar.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        
        action_layout = QVBoxLayout(action_bar)
        action_layout.setContentsMargins(20, 10, 20, 10)
        action_layout.setSpacing(10)

        # PRVNÍ ŘÁDEK
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(5)

        self.btn_install_main = AnimatedActionButton(" Nainstalovat vše", "assets/images/download-simple-thin.png")
        self.btn_install_main.setEnabled(False)
        self.btn_install_main.clicked.connect(self.run_installation)
        row1_layout.addWidget(self.btn_install_main)
        
        add_vertical_separator(row1_layout)
        
        self.btn_settings_quick = AnimatedActionButton(" Nastavení instalace", "assets/images/gear-six-thin.png")
        self.btn_settings_quick.clicked.connect(self.open_options_dialog)
        row1_layout.addWidget(self.btn_settings_quick)
        
        row1_layout.addStretch()
        action_layout.addLayout(row1_layout)

        # DRUHÝ ŘÁDEK
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(5)

        self.btn_new = AnimatedActionButton(" Nová fronta", "assets/images/plus-thin.png")
        self.btn_new.clicked.connect(self.clear_queue)
        row2_layout.addWidget(self.btn_new)

        add_vertical_separator(row2_layout)

        self.btn_open = AnimatedActionButton(" Otevřít", "assets/images/folder-open-thin.png")
        self.btn_open.clicked.connect(self.load_from_json)
        row2_layout.addWidget(self.btn_open)

        add_vertical_separator(row2_layout)

        self.btn_save = AnimatedActionButton(" Uložit", "assets/images/floppy-disk-thin.png")
        self.btn_save.clicked.connect(self.save_to_json)
        row2_layout.addWidget(self.btn_save)

        add_vertical_separator(row2_layout)

        self.btn_ps1 = AnimatedActionButton(" Vytvořit instalační skript", "assets/images/terminal-window-thin.png")
        self.btn_ps1.clicked.connect(self.save_powershell_script)
        row2_layout.addWidget(self.btn_ps1)

        row2_layout.addStretch()
        action_layout.addLayout(row2_layout)

        main_layout.addWidget(action_bar)

        # --- SEZNAM APLIKACÍ ---
        h_sep = QFrame()
        h_sep.setFrameShape(QFrame.Shape.HLine)
        h_sep.setFixedHeight(1)
        h_sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        main_layout.addWidget(h_sep)

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
        
        self.update_selection_ui()

    def update_selection_ui(self):
        count = self.list_widget.count()
                
        if count > 0:
            self.btn_install_main.setText(f" Nainstalovat vše ({count})")
            self.btn_install_main.setEnabled(True)
        else:
            self.btn_install_main.setText(" Nainstalovat vše")
            self.btn_install_main.setEnabled(False)

    def run_installation(self):
        if not self.queue_data:
            QMessageBox.warning(self, "Prázdná fronta", "Nejdříve přidejte balíčky.")
            return
            
        selected = list(self.queue_data.values())
        InstallationDialog(selected, self).exec()

    def save_to_json(self):
        if not self.queue_data:
            QMessageBox.warning(self, "Prázdná fronta", "Není co uložit. Nejdřív přidejte balíčky.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Uložit frontu", "fronta.json", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f: 
                json.dump(list(self.queue_data.values()), f, indent=4, ensure_ascii=False)

    def save_powershell_script(self):
        if not self.queue_data:
            QMessageBox.warning(self, "Prázdná fronta", "Nelze vytvořit skript pro prázdnou frontu.")
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
        if self.queue_data and QMessageBox.question(self, "Nová fronta", "Opravdu chcete vyčistit celou frontu?") == QMessageBox.StandardButton.Yes:
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
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst soubor:\n{e}")

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