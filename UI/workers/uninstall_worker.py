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
from UI.shared_widgets import AnimatedActionButton, IconDownloadWorker, add_vertical_separator

class UninstallWorker(QThread):
    finished = pyqtSignal()
    log_signal = pyqtSignal(str)

    def __init__(self, app_ids):
        super().__init__()
        self.app_ids = app_ids
        self.process = None 
        self.is_cancelled = False

    def run(self):
        cmd_base = ["winget", "uninstall", "--silent", "--disable-interactivity", "--accept-source-agreements", "--verbose"]
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            for aid in self.app_ids:
                if self.is_cancelled: break
                self.log_signal.emit(f"\n--- ODINSTALUJI: {aid} ---")
                self._execute(cmd_base + ["--id", aid, "--exact"], startupinfo)
        except Exception as e:
            self.log_signal.emit(f"Kritická chyba: {str(e)}")
            
        self.finished.emit()

    def _execute(self, cmd, startupinfo):
        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace',
                startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                bufsize=1
            )
            for line in self.process.stdout:
                if self.is_cancelled:
                    self.process.kill()
                    break
                clean_line = line.strip()
                if clean_line:
                    self.log_signal.emit(clean_line)

            self.process.wait()
        except Exception as e:
            self.log_signal.emit(f"CHYBA PROCESU: {str(e)}")

    def kill_process(self):
        self.is_cancelled = True
        if self.process:
            try: self.process.kill() 
            except: pass

