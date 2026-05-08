import winreg
import os
import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QLineEdit, 
                             QMessageBox, QFileIconProvider, QFrame, QProgressBar)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QFileInfo, QTimer
from PyQt6.QtGui import QPixmap, QImage, QIcon, QPainter, QColor

# Importy z vašich modulů
from core.workers import WingetListWorker, UninstallWorker
from core.config import COLORS, resource_path
from UI.view_installer import HoverButton

# Import sjednocené logiky z updateru
from UI.view_updater import find_app_icon_path, IconDownloadWorker

# --- 1. WIDGET ŘÁDKU (Sjednocený s Updaterem) ---
class AppItemWidget(QWidget):
    def __init__(self, name, app_id, parent_view):
        super().__init__()
        self.app_id = app_id
        self.name = name
        self.parent_view = parent_view
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Sjednoceno s Updaterem
        layout.setSpacing(15)

        # Ikona
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(24, 24)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logika načítání ikon (stejná jako v Updateru)
        found_local = self.set_local_icon(name, app_id)
        if not found_local:
            if self.set_system_fallback_icon(name):
                pass 
            else:
                self.icon_lbl.setText("📦")
                self.icon_lbl.setStyleSheet("font-size: 16px; color: #777; background: transparent;")
                self.dl_worker = IconDownloadWorker(app_id)
                self.dl_worker.loaded.connect(self.set_downloaded_icon)
                self.dl_worker.start()
        
        layout.addWidget(self.icon_lbl)

        # Název aplikace
        self.name_lbl = QLabel(name)
        self.name_lbl.setStyleSheet("font-weight: bold; color: white; background: transparent;")
        layout.addWidget(self.name_lbl, stretch=1)

        # Tlačítko odinstalace (Stylizováno jako tlačítko v Updateru)
        self.btn_un = QPushButton("Odinstalovat")
        self.btn_un.setFixedWidth(100) 
        self.btn_un.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_un.setStyleSheet(f"""
            QPushButton {{ 
                background: transparent; 
                color: {COLORS['sub_text']}; 
                font-weight: bold; 
                border: 1px solid {COLORS['border']}; 
                border-radius: 4px; 
                padding: 4px; 
            }} 
            QPushButton:hover {{ 
                background: #ff4444; 
                color: white; 
                border-color: #ff4444;
            }}
        """)
        self.btn_un.clicked.connect(lambda: self.parent_view.confirm_uninstall(self.app_id))
        layout.addWidget(self.btn_un)

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

# --- 2. STRÁNKA ODINSTALACE ---
class UninstallerPage(QWidget):
    def __init__(self):
        super().__init__()
        self.all_items = []
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        # HORNÍ LIŠTA (Sjednocená šířka search containeru)
        top_bar = QWidget()
        top_bar.setStyleSheet(f"background-color: {COLORS['bg_main']}; border-bottom: 1px solid {COLORS['border']};")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 15, 20, 15)

        lbl_title = QLabel("Odinstalace")
        lbl_title.setStyleSheet("font-size: 14pt; font-weight: bold; color: white; border: none;")
        top_layout.addWidget(lbl_title)
        top_layout.addSpacing(20)

        self.search_container = QFrame()
        self.search_container.setFixedWidth(500) # Sjednoceno s Updaterem
        self.search_container.setFixedHeight(38)
        self.search_container.setStyleSheet(f"QFrame {{ background-color: {COLORS['input_bg']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QFrame:focus-within {{ border: 1px solid {COLORS['accent']}; }}")
        s_layout = QHBoxLayout(self.search_container)
        s_layout.setContentsMargins(10, 0, 5, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Hledat v nainstalovaných aplikacích...")
        self.search_input.setStyleSheet("border: none; background: transparent; color: white; font-size: 10pt;")
        self.search_input.textChanged.connect(self.filter_items)

        self.btn_search_icon = HoverButton("", "assets/images/magnifying-glass-thin.png", "fg")
        self.btn_search_icon.setFixedSize(32, 32); self.btn_search_icon.setIconSize(QSize(18, 18))
        self.btn_search_icon.setStyleSheet("background: transparent; border: none;")

        s_layout.addWidget(self.search_input); s_layout.addWidget(self.btn_search_icon)
        top_layout.addWidget(self.search_container); top_layout.addStretch()
        main_layout.addWidget(top_bar)

        # PROGRESS BAR
        self.progress = QProgressBar()
        self.progress.setFixedHeight(2)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"QProgressBar {{ border: none; background: transparent; }} QProgressBar::chunk {{ background-color: {COLORS['accent']}; }}")
        self.progress.hide()
        main_layout.addWidget(self.progress)

        # ACTION BAR
        action_bar = QWidget()
        action_bar.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(20, 10, 20, 10)

        self.refresh_btn = QPushButton("  Načíst aplikace")
        self.refresh_btn.setIcon(QIcon(resource_path("assets/images/arrows-clockwise-thin.png")))
        self.refresh_btn.setFixedHeight(34); self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet(f"QPushButton {{ background-color: {COLORS['item_bg']}; color: white; border: 1px solid {COLORS['border']}; padding: 0 15px; border-radius: 6px; font-weight: bold; }} QPushButton:hover {{ border-color: {COLORS['accent']}; }}")
        self.refresh_btn.clicked.connect(self.load_apps)
        action_layout.addWidget(self.refresh_btn)
        
        action_layout.addStretch()
        self.status = QLabel("Připraveno."); self.status.setStyleSheet(f"color: {COLORS['sub_text']};")
        action_layout.addWidget(self.status)
        main_layout.addWidget(action_bar)

        # HLAVIČKA (Identická s Updaterem)
        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {COLORS['bg_sidebar']}; border-bottom: 1px solid {COLORS['border']};")
        h_layout = QHBoxLayout(header_widget)
        h_layout.setContentsMargins(35, 8, 35, 8) 
        h_layout.setSpacing(15)
        
        h_headers = [("", 24, 0), ("NÁZEV APLIKACE", 0, 1), ("AKCE", 100, 0)]
        for text, width, stretch in h_headers:
            lbl = QLabel(text); lbl.setStyleSheet("font-weight: bold; color: white; font-size: 9pt; border: none;")
            if width > 0: lbl.setFixedWidth(width)
            h_layout.addWidget(lbl, stretch=stretch)
        main_layout.addWidget(header_widget)

        # SEZNAM
        self.list_widget = QListWidget()
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{ 
                background-color: {COLORS['bg_main']}; 
                border: none; 
                outline: none; 
                padding: 0 30px; 
            }} 
            QListWidget::item {{ 
                border-bottom: 1px solid {COLORS['border']}; 
            }} 
            QListWidget::item:hover {{ 
                background-color: {COLORS['item_hover']}; 
            }}
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS.get('accent', '#0078d4')}; min-height: 30px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS.get('accent_hover', '#1f8ad2')}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        main_layout.addWidget(self.list_widget)

    def load_apps(self):
        self.list_widget.clear(); self.all_items = []
        self.refresh_btn.setEnabled(False); self.status.setText("Skenuji systém...")
        self.progress.setRange(0, 0); self.progress.show()
        
        self.worker = WingetListWorker()
        self.worker.finished.connect(self.on_loaded)
        self.worker.error.connect(lambda e: self.status.setText(f"Chyba: {e}"))
        self.worker.start()

    def on_loaded(self, apps):
        self.progress.hide()
        for app in apps:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 60)) # Výška sjednocena s Updaterem
            widget = AppItemWidget(app['name'], app['id'], self)
            self.list_widget.setItemWidget(item, widget)
            self.all_items.append((item, widget, app['name'].lower()))
        self.refresh_btn.setEnabled(True); self.status.setText(f"Nalezeno {len(apps)} aplikací.")

    def filter_items(self, text):
        t = text.lower()
        for item, widget, name in self.all_items: 
            item.setHidden(t not in name and t not in widget.app_id.lower())

    def confirm_uninstall(self, app_id):
        if QMessageBox.question(self, "Odinstalovat", f"Opravdu odinstalovat aplikaci?\nID: {app_id}") == QMessageBox.StandardButton.Yes:
            self.status.setText("Odinstalovávám..."); self.u_worker = UninstallWorker(app_id)
            self.u_worker.finished.connect(self.load_apps); self.u_worker.start()