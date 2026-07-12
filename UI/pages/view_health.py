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
from core.i18n import _, translator
from core.theme_manager import theme_manager


from UI.components.health_components import PlayButton, ToolRowWidget
from UI.workers.command_worker import CommandWorker
from UI.dialogs.log_dialog import LogDialog

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
        
        self.lbl_head = QLabel()
        header_layout.addWidget(self.lbl_head)
        
        self.lbl_info = QLabel()
        header_layout.addWidget(self.lbl_info)
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(5)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        tools_container = QWidget()
        tools_layout = QVBoxLayout(tools_container)
        tools_layout.setSpacing(0)
        tools_layout.setContentsMargins(0, 0, 15, 0)

        # >> SEKCE: OPRAVY A DIAGNOSTIKA
        self._add_section_header(tools_layout, "h_sec_repair")
        self._add_tool(tools_layout, "magnifying-glass-thin.png", "SFC Scan", "h_tool_sfc", "sfc /scannow", "SFC Scan")
        self._add_tool(tools_layout, "first-aid-kit-thin.png", "DISM Check", "h_tool_dism1", "dism /online /cleanup-image /CheckHealth", "DISM Check")
        self._add_tool(tools_layout, "wrench-thin.png", "DISM Restore", "h_tool_dism2", "dism /online /cleanup-image /RestoreHealth", "DISM Restore")
        self._add_tool(tools_layout, "hard-drives-thin.png", "CHKDSK Scan", "h_tool_chkdsk", "chkdsk C: /scan", "Check Disk")
        self._add_tool(tools_layout, "shield-check-thin.png", "h_tool_sigverif_t", "h_tool_sigverif_d", "sigverif", "Sigverif", is_gui=True)
        self._add_tool(tools_layout, "arrows-clockwise-thin.png", "h_tool_wsreset_t", "h_tool_wsreset_d", "wsreset.exe & net stop wuauserv & net start wuauserv", "Service Reset")

        # >> SEKCE: ČIŠTĚNÍ A ÚDRŽBA
        self._add_section_header(tools_layout, "h_sec_maint")
        self._add_tool(tools_layout, "trash-thin.png", "Smazat Temp & Cache", "h_tool_temp", 'del /q/f/s %TEMP%\\* & del /q/f/s %WINDIR%\\Temp\\*', "Temp Cleaner")
        self._add_tool(tools_layout, "disc-thin.png", "Vyčištění Disku", "h_tool_disk", "cleanmgr.exe", "Disk Cleanup", is_gui=True)
        self._add_tool(tools_layout, "broom-thin.png", "WinSxS Cleanup", "h_tool_sxs", "dism /online /cleanup-image /StartComponentCleanup", "Component Cleanup") 

        # >> SEKCE: OPTIMALIZACE A SÍŤ
        self._add_section_header(tools_layout, "h_sec_opt")
        self._add_tool(tools_layout, "wifi-high-thin.png", "h_tool_netreset_t", "h_tool_netreset_d", "ipconfig /flushdns & ipconfig /registerdns & netsh winsock reset", "Network Reset")
        self._add_tool(tools_layout, "lightning-thin.png", "h_tool_power_t", "h_tool_power_d", "powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c & powercfg -h off", "Power & Hibernation")
        self._add_tool(tools_layout, "battery-full-thin.png", "Report Baterie", "h_tool_bat", "powercfg /batteryreport /output \"C:\\battery_report.html\"", "Battery Report")

        # >> SEKCE: POKROČILÉ NÁSTROJE
        self._add_section_header(tools_layout, "h_sec_adv")
        self._add_tool(tools_layout, "chris.png", "Chris Titus Tech Tool", "h_tool_ctt", 
                       "irm christitus.com/win | iex", "CTT Windows Tool", is_powershell=True)

        tools_layout.addStretch()
        self.scroll.setWidget(tools_container)
        main_layout.addWidget(self.scroll)

        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.lbl_head.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLORS['fg']};")
        self.lbl_info.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 14px;")
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }} 
            QWidget {{ background: transparent; }}
            QScrollBar:vertical {{ border: none; background-color: transparent; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background-color: {COLORS.get('accent', '#0078d4')}; min-height: 30px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {COLORS.get('accent_hover', '#1f8ad2')}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        if hasattr(self, 'section_headers'):
            for lbl, line in self.section_headers:
                lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-weight: bold; font-size: 10px; letter-spacing: 1px; margin-left: 5px;")
                line.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")

    def _add_section_header(self, layout, title):
        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(0, 10, 0, 5) 
        l.setSpacing(5)
        lbl = QLabel()
        lbl.setProperty("title_key", title) # Uchováme si klíč pro pozdější překlad
        lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-weight: bold; font-size: 10px; letter-spacing: 1px; margin-left: 5px;")
        l.addWidget(lbl)
        
        # We also need to add it to a list of section headers to update them later
        if not hasattr(self, 'section_headers'):
            self.section_headers = []
        line = QFrame()
        line.setFixedHeight(1)
        self.section_headers.append((lbl, line))
        l.addWidget(line)
        layout.addWidget(container)

    def _add_tool(self, layout, icon, title, desc, command, log_name, is_gui=False, is_powershell=False):
        widget = ToolRowWidget(icon, title, desc, command, log_name, self, is_gui, is_powershell)
        layout.addWidget(widget)

    def execute_tool(self, command, desc, is_gui, is_powershell=False):
        try:
            if is_gui:
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(None, "runas", command, "", None, 1)
            else:
                dialog = LogDialog(desc, self)
                dialog.show()
                dialog.start_command(command, is_powershell)

        except Exception as e:
            QMessageBox.critical(self, _("error_title"), _("error_launch").format(e=str(e)) if "error_launch" in translator._("error_launch") else f"Failed to launch tool: {str(e)}")

    def retranslate_ui(self):
        self.lbl_head.setText(_("h_title"))
        self.lbl_info.setText(_("h_desc"))
        
        if hasattr(self, 'section_headers'):
            for lbl, line in self.section_headers:
                lbl.setText(_(lbl.property("title_key")).upper())

     
