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
from UI.pages.view_installer import InstallationOptionsDialog
from UI.shared_widgets import AnimatedActionButton, add_vertical_separator
from UI.pages.view_installer import InstallationOptionsDialog, HoverButton

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


