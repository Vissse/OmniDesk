import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame, 
                             QApplication, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor

from core.config import COLORS, CURRENT_VERSION, resource_path
from core.i18n import _

class SplashScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        # Ponecháno jako Window pro zobrazení na hlavním panelu
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15) # Větší okraj pro stín
        
        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_main']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        
        # Přidání moderního vrženého stínu
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.container.setGraphicsEffect(shadow)
        
        inner_layout = QVBoxLayout(self.container)
        inner_layout.setContentsMargins(40, 45, 40, 40)
        inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- IKONA ---
        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("border: none; background: transparent;")
        
        icon_path = resource_path("assets/icons/program_icon.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_lbl.setPixmap(pix)
        else:
            self.icon_lbl.setText("⚙️")
            self.icon_lbl.setStyleSheet("font-size: 50px; border: none; background: transparent;")
            
        inner_layout.addWidget(self.icon_lbl)
        inner_layout.addSpacing(15)
        
        # --- NADPIS ---
        lbl_title = QLabel("OmniDesk")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(f"color: {COLORS['fg']}; font-size: 28px; font-weight: bold; border: none; letter-spacing: 1px;")
        inner_layout.addWidget(lbl_title)
        
        # --- VERZE (Nyní decentní šedá) ---
        lbl_ver = QLabel(f"v{CURRENT_VERSION}")
        lbl_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ver.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 12px; font-weight: 500; border: none;")
        inner_layout.addWidget(lbl_ver)
        
        inner_layout.addStretch()
        
        # --- STATUS TEXT ---
        self.lbl_status = QLabel(_("splash_init"))
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 11px; border: none;")
        inner_layout.addWidget(self.lbl_status)
        inner_layout.addSpacing(8)
        
        # --- PROGRESS BAR (Tenčí a modernější) ---
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_sidebar']};
                border-radius: 2px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 2px;
            }}
        """)
        inner_layout.addWidget(self.progress)
        layout.addWidget(self.container)
        
        self.resize(460, 320)
        self.center_on_screen()
        
    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            int((screen.width() - size.width()) / 2),
            int((screen.height() - size.height()) / 2)
        )

    def update_progress(self, value, text):
        self.progress.setValue(value)
        self.lbl_status.setText(text)
        
        if value >= 100:
            QTimer.singleShot(500, self.finish_loading)

    def finish_loading(self):
        self.close()
        self.finished.emit()
