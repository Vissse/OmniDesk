import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QCheckBox, QFrame,
                             QDialog, QTabWidget, QComboBox, QFileDialog, QDialogButtonBox,
                             QScrollArea, QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QUrl, QVariantAnimation, QRect
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QDesktopServices, QPainterPath

from core.config import COLORS
from core.config import resource_path
from core.i18n import _, translator
from core.theme_manager import theme_manager
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

from UI.components.installer_components import HoverButton, QueueToggleButton, InstallationOptionsDialog, AppDetailPanel, CompactAppWidget

class InstallerPage(QWidget):
    def __init__(self, queue_page_ref):
        super().__init__()
        self.queue_page = queue_page_ref
        self.installation_options = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        self.top_bar = QWidget()
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 15, 20, 15)
        
        self.lbl_title = QLabel()
        top_layout.addWidget(self.lbl_title); top_layout.addSpacing(20)

        self.search_container = QFrame()
        self.search_container.setFixedWidth(700); self.search_container.setFixedHeight(38)
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS['accent']}; }}")
        search_cont_layout = QHBoxLayout(self.search_container)
        search_cont_layout.setContentsMargins(10, 0, 5, 0); search_cont_layout.setSpacing(0)

        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_catalog)
        
        self.btn_search = HoverButton("", "assets/images/magnifying-glass-thin.png", "fg")
        self.btn_search.setFixedSize(32, 32); self.btn_search.setIconSize(QSize(18, 18))
        self.btn_search.setStyleSheet("background: transparent; border: none; padding: 0;")

        search_cont_layout.addWidget(self.search_input); search_cont_layout.addWidget(self.btn_search)
        top_layout.addWidget(self.search_container); top_layout.addStretch()
        main_layout.addWidget(self.top_bar)

        self.action_bar = QWidget()
        action_layout = QHBoxLayout(self.action_bar)
        action_layout.setContentsMargins(20, 10, 20, 10); action_layout.setSpacing(10)

        self.btn_install_selection = AnimatedActionButton("", "assets/images/download-simple-thin.png")
        self.btn_install_selection.clicked.connect(self.run_install_from_bar)
        action_layout.addWidget(self.btn_install_selection)

        add_vertical_separator(action_layout)

        self.btn_settings_quick = AnimatedActionButton("", "assets/images/gear-six-thin.png")
        self.btn_settings_quick.clicked.connect(self.open_options_dialog)
        action_layout.addWidget(self.btn_settings_quick)
        
        action_layout.addStretch()

        self.btn_help = HoverButton("", "assets/images/question-thin.png", "sub_text")
        self.btn_help.setIconSize(QSize(20, 20)); self.btn_help.clicked.connect(self.show_help)
        action_layout.addWidget(self.btn_help)
        
        main_layout.addWidget(self.action_bar)

        self.h_sep = QFrame()
        self.h_sep.setFrameShape(QFrame.Shape.HLine)
        self.h_sep.setFixedHeight(1)
        main_layout.addWidget(self.h_sep)

        self.split_layout = QVBoxLayout()
        self.split_layout.setContentsMargins(0, 0, 0, 0)
        self.split_layout.setSpacing(0)

        self.catalog_widget = QWidget()
        catalog_layout = QVBoxLayout(self.catalog_widget)
        catalog_layout.setContentsMargins(30, 10, 30, 10)
        
        self.catalog_scroll = QScrollArea()
        self.catalog_scroll.setWidgetResizable(True)
        
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
        
                translated_name = _(f"cat_{clean_name}")
                if translated_name == f"cat_{clean_name}":
                    translated_name = clean_name
                    
                cat_lbl = QLabel(translated_name)
                
                header_layout.addWidget(cat_icon_lbl); header_layout.addWidget(cat_lbl); header_layout.addStretch()
                c_layout.addWidget(header_container)
                
                separator = QFrame(); separator.setFixedHeight(1)
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
                    # I zde přidáme rodiče
                    dummy = QWidget(self.catalog_widget) 
                    grid.addWidget(dummy, row, col)
                    cat_dummies.append(dummy)
                        
                c_layout.addLayout(grid)
                self.categories_ui.append({
                    'header': header_container, 
                    'separator': separator, 
                    'widgets': cat_widgets,
                    'grid': grid,              
                    'dummies': cat_dummies,
                    'cat_lbl': cat_lbl,
                    'clean_name': clean_name
                })
        else:
            lbl = QLabel("Pro zobrazení katalogu nastavte APP_CATEGORIES v presets.py")
            lbl.setStyleSheet(f"color: {COLORS['sub_text']};")
            c_layout.addWidget(lbl)
            
        c_layout.addStretch()
        self.catalog_scroll.setWidget(catalog_content)
        catalog_layout.addWidget(self.catalog_scroll)

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

        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.top_bar.setStyleSheet(f"background-color: {COLORS['bg_main']}; border-bottom: 1px solid {COLORS['border']};")
        self.lbl_title.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {COLORS['fg']}; border: none; outline: none;")
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS['accent']}; }}")
        self.search_input.setStyleSheet(f"border: none; background: transparent; color: {COLORS['fg']}; font-size: 10pt;")
        self.action_bar.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        self.h_sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        
        self.catalog_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: transparent; }}
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS.get('accent', '#0078d4')}; min-height: 30px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS.get('accent_hover', '#1f8ad2')}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)

        for cat in self.categories_ui:
            cat['cat_lbl'].setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['fg']};")
            cat['separator'].setStyleSheet(f"background-color: {COLORS['border']}; border: none;")

    def retranslate_ui(self):
        self.lbl_title.setText(_("in_title"))
        self.search_input.setPlaceholderText(_("in_search"))
        self.btn_install_selection.setText(_("in_btn_install_sel"))
        self.btn_settings_quick.setText(_("in_btn_settings"))
        self.btn_help.setText(_("in_btn_help"))
        
        for cat in self.categories_ui:
            clean = cat['clean_name']
            t_name = _(f"cat_{clean}")
            if t_name == f"cat_{clean}": t_name = clean
            cat['cat_lbl'].setText(t_name)
            
        if self.detail_panel.maximumHeight() > 0 and hasattr(self.detail_panel, 'data'):
            self.detail_panel.update_data(self.detail_panel.data)

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
                    # ZÁSADNÍ OPRAVA: Odstraníme skrytý widget z mřížky,
                    # aby QGridLayout přestal držet prázdné místo pro staré řádky.
                    grid.removeWidget(w)
            
            for d in cat['dummies']:
                d.hide()
                # ZÁSADNÍ OPRAVA i pro výplňové dummy widgety
                grid.removeWidget(d)
                
            num_apps = len(visible_widgets)
            
            if num_apps > 0:
                num_rows = (num_apps + 1) // 2 
                
                for idx, w in enumerate(visible_widgets):
                    col = idx // num_rows
                    row = idx % num_rows
                    # Přidáním do gridu si QGridLayout widget automaticky znovu převezme
                    grid.addWidget(w, row, col)
                
                total_cells = num_rows * 2
                dummy_needed = total_cells - num_apps
                
                if dummy_needed > 0:
                    if not cat['dummies']:
                        # Zde ponechán rodič (z předchozí opravy), aby nevznikal popup okno
                        cat['dummies'].append(QWidget(self.catalog_widget))
                    d = cat['dummies'][0]
                    # I dummy widgety nejprve přidáme do rozvržení a až pak zobrazíme
                    grid.addWidget(d, num_rows - 1, 1)
                    d.show()

            # DOPLŇKOVÁ OPRAVA: Pokud je kategorie zcela prázdná, zrušíme i její okraje
            if num_apps == 0:
                cat['header'].hide()
                cat['separator'].hide()
                grid.setContentsMargins(0, 0, 0, 0)
            else:
                cat['header'].show()
                cat['separator'].show()
                grid.setContentsMargins(0, 15, 0, 0)

    def refresh_catalog_checkboxes(self):
        for widget in self.catalog_widgets: widget.set_checked_state(widget.data['id'] in self.queue_page.queue_data)
            
    def refresh_checkboxes(self): self.refresh_catalog_checkboxes()

    def run_install_from_bar(self):
        if not self.queue_page.queue_data:
            QMessageBox.warning(self, _("in_empty_queue"), _("in_empty_queue_msg"))
            return
        self.queue_page.run_installation()

    def open_options_dialog(self):
        dlg = InstallationOptionsDialog(self, self.installation_options)
        if dlg.exec(): self.installation_options = dlg.get_options()

    def show_help(self):
        QMessageBox.information(self, _("in_btn_help").strip(), _("in_help_text"))
