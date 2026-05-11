import subprocess
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QVariantAnimation, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPainterPath

from core.config import COLORS
from core.config import resource_path

class PlayButton(QPushButton):
    """Minimalistické tlačítko tvořené pouze ikonkou, které reaguje na najetí."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.icon_path = resource_path("assets/images/play-thin.png")
        self._hover = False
        self.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self._hover:
            p.setBrush(QColor(COLORS['item_hover']))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(self.rect())
            
        if os.path.exists(self.icon_path):
            pix = QPixmap(self.icon_path).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            colored_pix = QPixmap(pix.size())
            colored_pix.fill(Qt.GlobalColor.transparent)
            
            cp = QPainter(colored_pix)
            cp.drawPixmap(0, 0, pix)
            cp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            color = QColor(COLORS['accent']) if self._hover else QColor(COLORS['fg'])
            cp.fillRect(colored_pix.rect(), color)
            cp.end()
            
            x = (self.width() - 18) // 2
            y = (self.height() - 18) // 2
            p.drawPixmap(x, y, colored_pix)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()


class ToolRowWidget(QFrame):
    def __init__(self, icon_name, title, desc, command, log_desc, parent_view, is_gui=False, is_powershell=False):
        super().__init__()
        self.command = command
        self.log_desc = log_desc
        self.parent_view = parent_view
        self.is_gui = is_gui
        self.is_powershell = is_powershell
        self.setFixedHeight(55)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._bg_color = QColor("transparent")
        self._bar_height_factor = 0.0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 2, 20, 2)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # 1. IKONA
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(24, 24)
        
        # Cesta může být buď v images nebo v icons (pro chris.png)
        potential_paths = [
            resource_path(os.path.join("assets/images", icon_name)),
            resource_path(os.path.join("assets/icons", icon_name))
        ]
        
        icon_path = next((p for p in potential_paths if os.path.exists(p)), None)
        
        if icon_path:
            pix = QPixmap(icon_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            # Pokud je to chris.png, nekreslíme ho jednobarevně, abychom zachovali barvy loga
            if "chris" in icon_name:
                self.icon_lbl.setPixmap(pix)
            else:
                colored_pix = QPixmap(pix.size())
                colored_pix.fill(Qt.GlobalColor.transparent)
                cp = QPainter(colored_pix)
                cp.drawPixmap(0, 0, pix)
                cp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                cp.fillRect(colored_pix.rect(), QColor(COLORS['sub_text']))
                cp.end()
                self.icon_lbl.setPixmap(colored_pix)
        
        layout.addWidget(self.icon_lbl)
        
        # 2. TEXTY
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.t_lbl = QLabel(title)
        self.t_lbl.setStyleSheet(f"color: {COLORS['fg']}; font-size: 13px; font-weight: bold; background: transparent;")
        
        self.d_lbl = QLabel(desc)
        self.d_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 11px; background: transparent;")
        
        text_layout.addWidget(self.t_lbl)
        text_layout.addWidget(self.d_lbl)
        layout.addLayout(text_layout, stretch=1)
        
        # 3. PLAY TLAČÍTKO
        self.btn_run = PlayButton()
        self.btn_run.setToolTip(f"Spustit {title}")
        self.btn_run.clicked.connect(self.run_tool)
        layout.addWidget(self.btn_run)
        
        # Animace
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)
        
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
            self.run_tool()

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
            
    def run_tool(self):
        self.parent_view.execute_tool(self.command, self.log_desc, self.is_gui, self.is_powershell)

class HealthCheckPage(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 25, 40, 25)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        
        lbl_head = QLabel("Kontrola stavu PC")
        lbl_head.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        header_layout.addWidget(lbl_head)
        
        lbl_info = QLabel("Nástroje pro diagnostiku, čištění a optimalizaci systému.")
        lbl_info.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 14px;")
        header_layout.addWidget(lbl_info)
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(5)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }} 
            QWidget {{ background: transparent; }}
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS.get('accent', '#0078d4')}; min-height: 30px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS.get('accent_hover', '#1f8ad2')}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        
        tools_container = QWidget()
        tools_layout = QVBoxLayout(tools_container)
        tools_layout.setSpacing(0)
        tools_layout.setContentsMargins(0, 0, 15, 0)

        # >> SEKCE: OPRAVY SYSTÉMU
        self._add_section_header(tools_layout, "Opravy Systému")
        self._add_tool(tools_layout, "magnifying-glass-thin.png", "SFC Scan", "Kontrola a automatická oprava poškozených systémových souborů.", "sfc /scannow", "SFC Scan")
        self._add_tool(tools_layout, "hard-drives-thin.png", "CHKDSK Scan", "Rychlá kontrola chyb na disku C: (režim pouze pro čtení).", "chkdsk C: /scan", "Check Disk")
        self._add_tool(tools_layout, "first-aid-kit-thin.png", "DISM Check", "Diagnostika obrazu Windows pro zjištění možného poškození.", "dism /online /cleanup-image /CheckHealth", "DISM Check")
        self._add_tool(tools_layout, "wrench-thin.png", "DISM Restore", "Stáhne a opraví systémové soubory pomocí Windows Update.", "dism /online /cleanup-image /RestoreHealth", "DISM Restore")

        # >> SEKCE: ÚDRŽBA
        self._add_section_header(tools_layout, "Správa a Údržba")
        self._add_tool(tools_layout, "trash-thin.png", "Smazat Temp", "Bezpečně vymaže dočasné soubory zpomalující systém.", 'del /q/f/s %TEMP%\\*', "Temp Cleaner")
        self._add_tool(tools_layout, "disc-thin.png", "Vyčištění Disku", "Otevře nativní nástroj Windows pro uvolnění místa.", "cleanmgr.exe", "Disk Cleanup", is_gui=True)
        self._add_tool(tools_layout, "battery-full-thin.png", "Report Baterie", "Uloží podrobný HTML report o stavu baterie na disk C:.", "powercfg /batteryreport /output \"C:\\battery_report.html\"", "Battery Report")
        self._add_tool(tools_layout, "broom-thin.png", "WinSxS Cleanup", "Hloubkové čištění starých aktualizací pro výraznou úsporu místa.", "dism /online /cleanup-image /StartComponentCleanup", "Component Cleanup") 

        # >> SEKCE: POKROČILÉ NÁSTROJE
        self._add_section_header(tools_layout, "Pokročilé Nástroje")
        self._add_tool(tools_layout, "chris.png", "Chris Titus Tech Tool", "Komplexní utilita pro debloat, instalaci aplikací a optimalizaci Windows.", 
                       "irm christitus.com/win | iex", "CTT Windows Tool", is_powershell=True)

        tools_layout.addStretch()
        scroll.setWidget(tools_container)
        main_layout.addWidget(scroll)

    def _add_section_header(self, layout, title):
        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(0, 10, 0, 5) 
        l.setSpacing(5)
        lbl = QLabel(title.upper())
        lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-weight: bold; font-size: 10px; letter-spacing: 1px; margin-left: 5px;")
        l.addWidget(lbl)
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        l.addWidget(line)
        layout.addWidget(container)

    def _add_tool(self, layout, icon, title, desc, command, log_name, is_gui=False, is_powershell=False):
        widget = ToolRowWidget(icon, title, desc, command, log_name, self, is_gui, is_powershell)
        layout.addWidget(widget)

    def execute_tool(self, command, desc, is_gui, is_powershell=False):
        try:
            import ctypes
            
            # Pomocná funkce pro spuštění jako správce
            def run_as_admin(cmd, params=""):
                # ShellExecuteEx s parametrem 'runas' vyvolá UAC dialog
                ctypes.windll.shell32.ShellExecuteW(None, "runas", cmd, params, None, 1)

            if is_gui:
                # Pro GUI nástroje (jako cleanmgr)
                run_as_admin(command)
            elif is_powershell:
                # Pro CTT Tool a PowerShell skripty
                ps_params = f"-NoProfile -ExecutionPolicy Bypass -Command \"{command}\""
                run_as_admin("powershell.exe", ps_params)
            else:
                # Pro klasické CMD příkazy (SFC, DISM)
                # Obalíme to do cmd /k, aby okno zůstalo otevřené a uživatel viděl výsledek
                cmd_with_resize = f'mode con: cols=100 lines=30 && color 0A && echo --- SPUSTENO JAKO SPRAVCE: {desc} --- && {command}'
                run_as_admin("cmd.exe", f'/k "{cmd_with_resize}"')

        except Exception as e:
            QMessageBox.critical(self, "Chyba spuštění", f"Nepodařilo se spustit nástroj jako správce: {str(e)}")