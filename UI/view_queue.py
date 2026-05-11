import os
import json
import subprocess
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QMessageBox, QFileDialog, QFrame, QLineEdit, QCheckBox)
from PyQt6.QtCore import Qt, QSize, QVariantAnimation, QRect, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QPainterPath

from core.config import COLORS, resource_path
from core.install_manager import InstallationDialog
from UI.view_installer import InstallationOptionsDialog

# --- WORKER PRO ZJIŠTĚNÍ VERZE BALÍČKU ---
class VersionFetchWorker(QThread):
    version_found = pyqtSignal(str)

    def __init__(self, app_id):
        super().__init__()
        self.app_id = app_id

    def run(self):
        try:
            # Neviditelné spuštění příkazu winget
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
                # Zjištění verze (funguje pro český "Verze:" i anglický "Version:" systém)
                if clean_line.startswith("Version:") or clean_line.startswith("Verze:"):
                    version = clean_line.split(":", 1)[1].strip()
                    break
            
            self.version_found.emit(version)
        except Exception:
            self.version_found.emit("Neznámá")


# --- ANIMOVANÉ TLAČÍTKO PRO HORNÍ LIŠTU ---
class AnimatedActionButton(QPushButton):
    def __init__(self, text, icon_path, parent=None, bar_align="left", hover_color="accent"):
        super().__init__(text, parent)
        self.setFixedHeight(34)
        self.icon_path = icon_path
        self.bar_align = bar_align
        self.hover_color = hover_color
        
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
            p.setBrush(QColor(COLORS.get(self.hover_color, COLORS['accent'])))
            p.setPen(Qt.PenStyle.NoPen)
            h = rect.height() * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            
            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)
            p.setClipPath(path)
            
            if self.bar_align == "right":
                p.drawRect(QRect(rect.right() - 4, int(y), 4, int(h)))
            else:
                p.drawRect(QRect(rect.x(), int(y), 4, int(h)))
                
            p.setClipping(False)
            
        p.end()
        super().paintEvent(event)


# --- WIDGET ŘÁDKU FRONTY ---
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
        
        # 1. Checkbox
        self.chk = QCheckBox()
        self.chk.setFixedWidth(24)
        self.chk.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk.setStyleSheet(f"""
            QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid {COLORS['sub_text']}; border-radius: 4px; background: transparent; }}
            QCheckBox::indicator:checked {{ background-color: {COLORS['accent']}; border-color: {COLORS['accent']}; image: url(check.png); }} 
        """)
        
        self.chk.setChecked(True)
        self.chk.stateChanged.connect(self.queue_page.update_selection_ui)
        layout.addWidget(self.chk)

        # 2. Ikona
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

        # 3. Texty (Název • Verze) nalepené zleva
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

        text_layout.addStretch() # Natlačí všechny texty bezpečně doleva
        layout.addLayout(text_layout, stretch=1)

        # Spuštění zjišťování verze na pozadí, pokud není verze pevně dána
        if data.get('version') in [None, "Latest", "Unknown", "Neznámá", "Načítání...", ""]:
            self.ver_lbl.setText("Načítání...")
            self.ver_worker = VersionFetchWorker(self.data['id'])
            self.ver_worker.version_found.connect(self.on_version_found)
            self.ver_worker.start()

        # Animace po najetí
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)

    def on_version_found(self, version):
        self.ver_lbl.setText(version)
        self.data['version'] = version # Uložíme verzi pro Instalaci / Uložení do souboru

    def set_icon(self, pixmap):
        self.current_pixmap = pixmap
        scaled = pixmap.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.icon_lbl.setPixmap(scaled)
        self.icon_lbl.setText("")

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


# --- HLAVNÍ STRÁNKA FRONTY ---
class QueuePage(QWidget):
    def __init__(self):
        super().__init__()
        self.queue_data = {} 
        self.installer_page_ref = None
        self.installation_options = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === A. HORNÍ LIŠTA ===
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
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS['accent']}; }}")
        
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
            cp.fillRect(colored_pix.rect(), QColor(COLORS['sub_text']))
            cp.end()
            search_input_icon.setPixmap(colored_pix)
            
        search_cont_layout.addWidget(search_input_icon)
        top_layout.addWidget(self.search_container)
        top_layout.addStretch()
        main_layout.addWidget(top_bar)

        # === B. ACTION BAR ===
        action_bar = QWidget()
        action_bar.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(20, 10, 20, 10)
        action_layout.setSpacing(5)

        install_group = QHBoxLayout()
        install_group.setSpacing(0)
        
        self.btn_install_main = AnimatedActionButton(" Nainstalovat vybrané", "assets/images/download-simple-thin.png")
        self.btn_install_main.setEnabled(False)
        self.btn_install_main.clicked.connect(self.run_installation)
        install_group.addWidget(self.btn_install_main)
        
        sep_inner = QFrame()
        sep_inner.setFrameShape(QFrame.Shape.VLine)
        sep_inner.setFixedWidth(1)
        sep_inner.setFixedHeight(18)
        sep_inner.setStyleSheet(f"background: {COLORS['border']}; border: none; margin: 0 5px;")
        install_group.addWidget(sep_inner)
        
        # Animace opravena na default zleva
        self.btn_settings_quick = AnimatedActionButton(" Nastavení", "assets/images/gear-six-thin.png")
        self.btn_settings_quick.clicked.connect(self.open_options_dialog)
        install_group.addWidget(self.btn_settings_quick)
        
        action_layout.addLayout(install_group)
        self.add_separator(action_layout)

        self.btn_new = AnimatedActionButton(" Nová", "assets/images/plus-thin.png")
        self.btn_new.clicked.connect(self.clear_queue)
        action_layout.addWidget(self.btn_new)

        self.btn_open = AnimatedActionButton(" Otevřít", "assets/images/folder-open-thin.png")
        self.btn_open.clicked.connect(self.load_from_json)
        action_layout.addWidget(self.btn_open)

        self.btn_save = AnimatedActionButton(" Uložit", "assets/images/floppy-disk-thin.png")
        self.btn_save.clicked.connect(self.save_to_json)
        action_layout.addWidget(self.btn_save)

        self.add_separator(action_layout)

        self.btn_ps1 = AnimatedActionButton(" Skript", "assets/images/terminal-window-thin.png")
        self.btn_ps1.clicked.connect(self.save_powershell_script)
        action_layout.addWidget(self.btn_ps1)

        self.add_separator(action_layout)

        self.btn_remove_selected = AnimatedActionButton(" Odebrat vybrané", "assets/images/trash-thin.png", hover_color="danger")
        self.btn_remove_selected.setEnabled(False)
        self.btn_remove_selected.clicked.connect(self.remove_selected_items)
        action_layout.addWidget(self.btn_remove_selected)

        action_layout.addStretch()
        main_layout.addWidget(action_bar)

        h_sep = QFrame()
        h_sep.setFrameShape(QFrame.Shape.HLine)
        h_sep.setFixedHeight(1)
        h_sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        main_layout.addWidget(h_sep)

        # === C. SEZNAM ===
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

    # --- LOGIKA ---
    def add_separator(self, layout):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(18)
        sep.setStyleSheet(f"background: {COLORS['border']}; border: none;")
        layout.addWidget(sep)

    def update_selection_ui(self):
        count = 0
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(widget, QueueRowWidget) and widget.chk.isChecked():
                count += 1
                
        if count > 0:
            self.btn_install_main.setText(f" Nainstalovat vybrané ({count})")
            self.btn_install_main.setEnabled(True)
            self.btn_remove_selected.setText(f" Odebrat vybrané ({count})")
            self.btn_remove_selected.setEnabled(True)
        else:
            self.btn_install_main.setText(" Nainstalovat vybrané")
            self.btn_install_main.setEnabled(False)
            self.btn_remove_selected.setText(" Odebrat vybrané")
            self.btn_remove_selected.setEnabled(False)

    def remove_selected_items(self):
        if not self.queue_data:
            QMessageBox.warning(self, "Prázdná fronta", "V seznamu nejsou žádné balíčky k odebrání.")
            return
            
        to_remove = []
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(widget, QueueRowWidget) and widget.chk.isChecked():
                to_remove.append(widget.data['id'])
                
        if not to_remove:
            QMessageBox.information(self, "Žádný výběr", "Nejdříve zaškrtněte balíčky k odebrání.")
            return
            
        for app_id in to_remove:
            self.remove_item_by_id(app_id)
            
        self.update_selection_ui()

    def run_installation(self):
        if not self.queue_data:
            QMessageBox.warning(self, "Prázdná fronta", "Nejdříve přidejte balíčky.")
            return
            
        selected = []
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(widget, QueueRowWidget) and widget.chk.isChecked():
                selected.append(widget.data)
                
        if not selected:
            QMessageBox.information(self, "Žádný výběr", "Označte alespoň jeden balíček, který chcete nainstalovat.")
            return
            
        InstallationDialog(selected, self).exec()

    def save_to_json(self):
        if not self.queue_data:
            QMessageBox.warning(self, "Prázdná fronta", "Není co uložit. Nejdřív přidejte balíčky.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Uložit frontu", "fronta.json", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f: json.dump(list(self.queue_data.values()), f, indent=4, ensure_ascii=False)

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
            if self.installer_page_ref: self.installer_page_ref.refresh_checkboxes()

    def load_from_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Načíst frontu", "", "JSON (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f: apps = json.load(f)
                self.queue_data.clear(); self.list_widget.clear()
                for app in apps: self.add_to_queue(app)
                self.update_selection_ui()
                if self.installer_page_ref: self.installer_page_ref.refresh_checkboxes()
            except: pass

    def add_to_queue(self, data, icon=None):
        app_id = data['id']
        if app_id in self.queue_data: return
        self.queue_data[app_id] = data
        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(QSize(0, 55))
        item.setData(Qt.ItemDataRole.UserRole, app_id)
        widget = QueueRowWidget(data, self, self, cached_icon=icon)
        self.list_widget.setItemWidget(item, widget)
        
        self.update_selection_ui()
        if self.installer_page_ref: self.installer_page_ref.refresh_checkboxes()

    def remove_item_by_id(self, app_id):
        if app_id in self.queue_data: del self.queue_data[app_id]
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == app_id:
                self.list_widget.takeItem(i)
                break
                
        self.update_selection_ui()
        if self.installer_page_ref: self.installer_page_ref.refresh_checkboxes()

    def open_options_dialog(self):
        dlg = InstallationOptionsDialog(self, self.installation_options)
        if dlg.exec(): self.installation_options = dlg.get_options()

    def set_installer_ref(self, ref): 
        self.installer_page_ref = ref