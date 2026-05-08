import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QCheckBox, QFrame,
                             QDialog, QTabWidget, QComboBox, QFileDialog, QDialogButtonBox,
                             QScrollArea, QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor

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
    "🟩 Nvidia Nástroje": "assets/images/graphics-card-thin.png",
    "🎨 Média (Obraz, Zvuk, Video)": "assets/images/images-thin.png",
    "📄 Kancelářské aplikace": "assets/images/file-text-thin.png",
    "💽 Správa disků": "assets/images/disc-thin.png",
    "🛠️ Systémové nástroje (Utilities)": "assets/images/windows-logo-thin.png",
    "💻 Vývojářské nástroje": "assets/images/code-thin.png"
}

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


# --- WIDGET PRO KATALOG ---
class CompactAppWidget(QWidget):
    def __init__(self, data, parent_controller):
        super().__init__()
        self.data = data
        self.controller = parent_controller
        self.setFixedHeight(48)
        
        self.setStyleSheet(f"""
            QWidget#AppContainer {{
                background-color: transparent;
                border-radius: 8px;
            }}
            QWidget#AppContainer:hover {{
                background-color: {COLORS.get('item_hover', '#2d2d30')};
            }}
        """)
        self.setObjectName("AppContainer")
        
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
        
        self.btn_pick = QPushButton()
        self.btn_pick.setFixedSize(85, 28)
        self.btn_pick.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pick.clicked.connect(self.toggle_queue)
        layout.addWidget(self.btn_pick)

        self.is_queued = self.data['id'] in self.controller.queue_page.queue_data
        self.update_button_style()

    def update_button_style(self):
        if self.is_queued:
            self.btn_pick.setText("Zrušit")
            self.btn_pick.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS.get('accent', '#0078d4')};
                    border: 1px solid {COLORS.get('accent', '#0078d4')};
                    border-radius: 14px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS.get('accent', '#0078d4')};
                    color: white;
                }}
            """)
        else:
            self.btn_pick.setText("Přidat")
            self.btn_pick.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS.get('item_bg', '#3e3e42')};
                    color: white;
                    border: none;
                    border-radius: 14px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS.get('accent', '#0078d4')};
                }}
            """)

    def toggle_queue(self):
        self.is_queued = not self.is_queued
        self.update_button_style()
        
        if self.is_queued:
            self.controller.queue_page.add_to_queue(self.data, icon=self.icon_lbl.pixmap())
        else:
            self.controller.queue_page.remove_item_by_id(self.data['id'])
            
    def set_checked_state(self, is_checked):
        if self.is_queued != is_checked:
            self.is_queued = is_checked
            self.update_button_style()

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
        
        main_layout.addWidget(self.catalog_widget)

    # --- POMOCNÉ FUNKCE ---
    def filter_catalog(self):
        query = self.search_input.text().strip().lower()
        for cat in self.categories_ui:
            grid = cat['grid']
            
            # Zjištění, které aplikace mají být po vyhledání vidět
            visible_widgets = []
            for w in cat['widgets']:
                if query in w.data['name'].lower() or query in w.data['id'].lower():
                    w.show()
                    visible_widgets.append(w)
                else:
                    w.hide()
            
            # Skrytí všech aktuálních výplňových "dummy" widgetů, aby nám nedělaly neplechu
            for d in cat['dummies']:
                d.hide()
                
            num_apps = len(visible_widgets)
            
            # Pokud po vyfiltrování něco zbylo, přeskládáme to do mřížky odznova (reflow)
            if num_apps > 0:
                num_rows = (num_apps + 1) // 2 
                
                for idx, w in enumerate(visible_widgets):
                    col = idx // num_rows
                    row = idx % num_rows
                    grid.addWidget(w, row, col)
                
                # Výpočet, zda nám chybí položka do páru (abychom neroztahovali poslední appku)
                total_cells = num_rows * 2
                dummy_needed = total_cells - num_apps
                
                if dummy_needed > 0:
                    if not cat['dummies']:
                        cat['dummies'].append(QWidget())
                    d = cat['dummies'][0]
                    d.show()
                    grid.addWidget(d, num_rows - 1, 1)

            # Skrytí celého nadpisu a čáry, pokud v kategorii nic nevyhovuje vyhledávání
            if num_apps == 0:
                cat['header'].hide()
                cat['separator'].hide()
            else:
                cat['header'].show()
                cat['separator'].show()

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