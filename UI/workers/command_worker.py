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

class CommandWorker(QThread):
    """
    Speciální vlákno, které čte výstup z Windows příkazů BAJT PO BAJTU.
    Zabrání zamrznutí a obejde zasekávání procent u SFC/DISM.
    """
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, command, is_powershell):
        super().__init__()
        self.command = command
        self.is_powershell = is_powershell

    def run(self):
        # Nastavení příkazu
        if self.is_powershell:
            cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", self.command]
        else:
            cmd = self.command.split() # Rozdělí 'sfc /scannow' na ['sfc', '/scannow']

        try:
            # CREATE_NO_WINDOW skryje otravné černé okno konzole
            CREATE_NO_WINDOW = 0x08000000
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                creationflags=CREATE_NO_WINDOW
            )

            buffer = ""
            while True:
                # ČTEME PŘESNĚ 1 ZNAK (Bajt) - Žádné čekání na konec řádku!
                char_bytes = process.stdout.read(1)
                
                # Pokud už nejsou data a proces skončil, ukončíme smyčku
                if not char_bytes and process.poll() is not None:
                    break
                    
                if not char_bytes:
                    continue

                # Převod bajtu na text
                try:
                    char = char_bytes.decode('cp852', errors='ignore')
                except:
                    char = char_bytes.decode('utf-8', errors='ignore')

                buffer += char

                # JAKMILE NARAZÍME NA PROCENTO, OKAMŽITĚ HO ZPRACUJEME
                if char == '%':
                    match = re.search(r'(\d+)\s*%$', buffer)
                    if match:
                        self.progress_signal.emit(int(match.group(1)))

                # Jakmile narazíme na odřádkování nebo návrat vozíku (\r nebo \n)
                if char in ['\r', '\n']:
                    clean_line = buffer.strip()
                    if clean_line:
                        self.log_signal.emit(clean_line)
                    buffer = "" # Vyprázdníme buffer pro další řádek

            process.wait()
            self.finished_signal.emit()

        except Exception as e:
            self.log_signal.emit(f"Kritická chyba běhu: {str(e)}")
            self.finished_signal.emit()


