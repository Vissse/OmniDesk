# UI/splash.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame, QApplication)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from core.config import COLORS, CURRENT_VERSION

class SplashScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        # Změna zde: Odstraněno Qt.WindowType.SplashScreen, přidáno Qt.WindowType.Window
        # Tím zajistíme, že se zobrazí ikona na panelu úloh (taskbaru)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_main']};
                border: 2px solid {COLORS['accent']};
                border-radius: 12px;
            }}
        """)
        
        inner_layout = QVBoxLayout(self.container)
        inner_layout.setContentsMargins(40, 50, 40, 40)
        
        lbl_title = QLabel("OmniDesk")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(f"color: {COLORS['fg']}; font-size: 26px; font-weight: bold; border: none; font-family: 'Segoe UI';")
        inner_layout.addWidget(lbl_title)
        
        lbl_ver = QLabel(f"Alpha version {CURRENT_VERSION}")
        lbl_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ver.setStyleSheet(f"color: {COLORS['accent']}; font-size: 13px; border: none; margin-bottom: 30px; font-family: 'Segoe UI';")
        inner_layout.addWidget(lbl_ver)
        
        self.lbl_status = QLabel("Inicializace...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 11px; border: none; font-family: 'Segoe UI';")
        inner_layout.addWidget(self.lbl_status)
        
        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_sidebar']};
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 3px;
            }}
        """)
        inner_layout.addWidget(self.progress)
        layout.addWidget(self.container)
        
        self.resize(480, 300)
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