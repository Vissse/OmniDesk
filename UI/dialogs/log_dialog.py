import subprocess # Přidáno
import os
import ctypes
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QMessageBox,
                             QDialog, QTextEdit, QProgressBar)  
from PyQt6.QtCore import Qt, QVariantAnimation, QRect, QTimer, QThread, pyqtSignal, QProcess
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPainterPath

from core.config import COLORS
from core.config import resource_path

class LogDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Nástroj: {title}")
        self.resize(750, 450)
        self.setModal(False)
        
        # Načtení barev z tvé konfigurace
        sidebar_color = COLORS.get('bg_sidebar', '#252526')
        main_color = COLORS.get('bg_main', '#1e1e1e')
        self.accent_color = COLORS.get('accent', '#007acc')
        accent_hover = COLORS.get('accent_hover', '#1f8ad2')
        border_color = COLORS.get('border', '#3e3e42')

        # Vynucení barvy horní lišty Windows
        QTimer.singleShot(50, lambda: self._apply_custom_titlebar_color(sidebar_color))

        self.setStyleSheet(f"background-color: {main_color};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- TEXTOVÉ POLE PRO LOGY ---
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        
        # Nastylování okna a profi scrollbaru
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                font-family: Consolas, monospace;
                font-size: 13px;
                background-color: {COLORS['input_bg']};
                color: {COLORS['fg']};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 10px;
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['input_bg']};
                width: 10px;
                border-left: 1px solid {border_color};
            }}
            QScrollBar::handle:vertical {{
                background-color: {border_color};
                min-height: 20px;
                border-radius: 4px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.accent_color};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        layout.addWidget(self.text_edit)

        # --- SPODNÍ LIŠTA S TLAČÍTKEM ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_close = QPushButton("Zavřít", self)
        self.btn_close.setEnabled(False)
        self.btn_close.setFixedSize(120, 35)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent_color};
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {accent_hover};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['border']};
                color: {COLORS['sub_text']};
            }}
        """)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)

        # --- INICIALIZACE PROCESU ---
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyRead.connect(self.handle_ready_read)
        self.process.finished.connect(self.process_finished)

    def _apply_custom_titlebar_color(self, hex_color):
        try:
            import ctypes
            hex_str = hex_color.lstrip('#')
            r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
            colorref = (b << 16) | (g << 8) | r
            hwnd = int(self.winId())
            DWMWA_CAPTION_COLOR = 35
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(ctypes.c_int(colorref)), ctypes.sizeof(ctypes.c_int)
            )
        except Exception as e:
            print(f"Chyba obarvení lišty: {e}")

    def start_command(self, command, is_powershell):
        self.text_edit.append(f"<span style='color:{self.accent_color}; font-weight:bold;'>> Spouštím: {command}</span><br>")
        
        if is_powershell:
            self.process.start("powershell.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command])
        else:
            self.process.start("cmd.exe", ["/c", command])

    def handle_ready_read(self):
        data = self.process.readAll().data()
        try:
            text = data.decode('cp852', errors='replace')
        except:
            text = data.decode('utf-8', errors='replace')

        if not text:
            return

        # Upravíme tvrdé návraty vozíku (\r), které CMD používá pro přepisování stejného řádku
        # Zabráníme tím tomu, aby se text slil do jednoho nepřehledného bloku
        clean_text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Plynulé přidání textu do GUI bez zbytečných prázdných řádků
        for line in clean_text.split('\n'):
            line_stripped = line.strip()
            if line_stripped:
                # Ochrana před brutálním spamem stejných procentuálních řádků
                # Pokud je to stejný řádek s procenty jako ten předchozí, přeskočíme ho
                if line_stripped.endswith("%") and line_stripped in self.text_edit.toPlainText()[-200:]:
                    continue
                self.text_edit.append(line_stripped)
                
        self.text_edit.ensureCursorVisible()

    def process_finished(self):
        self.text_edit.append(f"<br><span style='color:{self.accent_color}; font-weight:bold;'>> Proces dokončen.</span>")
        self.text_edit.ensureCursorVisible()
        self.btn_close.setEnabled(True)

