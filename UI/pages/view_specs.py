import sys
import os
import platform
import socket
import subprocess
import re
import csv
import io
import json
import datetime
import winreg # Modul pro spolehlivou detekci VRAM u AMD/NVIDIA

try:
    import wmi
except ImportError:
    print("Knihovna 'wmi' nenalezena. Nainstalujte ji pomocí: pip install wmi pywin32")
    sys.exit(1)

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QFrame, QStackedWidget, QScrollArea, QPushButton, 
                             QSizePolicy, QGraphicsOpacityEffect)
from PyQt6.QtCore import QThread, Qt, QSize, QVariantAnimation, QTimer, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPixmap, QPainter, QPainterPath

# --- KONFIGURACE A BARVY ---
from core.config import COLORS, resource_path
from core.i18n import _, translator
from core.theme_manager import theme_manager


# --- LOGIKA ZÍSKÁVÁNÍ DAT PC ---

def _run_ps(cmd):
    try:
        return subprocess.check_output(
            cmd, shell=True, timeout=5, stdin=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL, creationflags=0x08000000
        ).decode(errors='ignore').strip()
    except:
        return ""

def clean_disk_name(name):
    name = re.sub(r'\b(SSD|NVMe|HDD|USB)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\b\d+\s?[GT]B?\b', '', name, flags=re.IGNORECASE)
    return " ".join(name.split())

def get_market_size(real_gb):
    if real_gb >= 900: return f"{round(real_gb / 1000)} TB"
    standards = [120, 128, 240, 250, 256, 480, 500, 512, 960, 1000]
    closest = min(standards, key=lambda x: abs(x - real_gb))
    if abs(closest - real_gb) / closest < 0.10:
        if closest in [480, 500]: return "512 GB"
        if closest in [240, 250]: return "256 GB"
        if closest == 120: return "128 GB"
        return f"{closest} GB"
    return f"{real_gb} GB"

def format_wmi_date(raw_date):
    raw_date = str(raw_date).strip()
    formatted = "Neznámé"
    if len(raw_date) >= 8 and raw_date[:8].isdigit():
        formatted = f"{raw_date[6:8]}.{raw_date[4:6]}.{raw_date[0:4]}"
    elif "/Date(" in raw_date:
        match = re.search(r'\d+', raw_date)
        if match:
            timestamp = int(match.group()) / 1000
            d = datetime.datetime.fromtimestamp(timestamp)
            formatted = d.strftime('%d.%m.%Y')
    return formatted

def get_gpu_vendor_from_id(pnp_id):
    if not pnp_id: return ""
    match = re.search(r'SUBSYS_([0-9A-F]{8})', pnp_id, re.IGNORECASE)
    if match:
        subsys_id = match.group(1)[-4:].upper() 
        vendors = {
            "1043": "ASUS", "1462": "MSI", "1458": "GIGABYTE", "3842": "EVGA",
            "19DA": "ZOTAC", "1682": "XFX", "1DA2": "SAPPHIRE", "1849": "ASRock",
            "196E": "PNY", "10DE": "NVIDIA", "1002": "AMD", "1028": "DELL",
            "103C": "HP", "17AA": "Lenovo"
        }
        return vendors.get(subsys_id, "")
    return ""

def get_real_vram_from_registry():
    """ Přesné přečtení VRAM přeskočením 4GB limitu WMI """
    try:
        base_path = r"SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_path) as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    sub_key_name = winreg.EnumKey(key, i)
                    if sub_key_name == "Properties": continue
                    with winreg.OpenKey(key, sub_key_name) as sub_key:
                        try:
                            val, _ = winreg.QueryValueEx(sub_key, "HardwareInformation.QwMemorySize")
                            return int(val)
                        except FileNotFoundError:
                            pass
                except Exception:
                    continue
    except Exception:
        pass
    return 0

def get_pc_specs(progress_callback=None):
    def report(msg):
        if progress_callback: progress_callback(msg)

    os_name = f"Windows {platform.release()}"
    build = int(platform.version().split('.')[-1])
    os_name = "Windows 11" if build >= 22000 else "Windows 10"

    specs = {
        "cpu": "Neznámý Procesor", "cpu_details": {}, 
        "gpu": "Neznámá Grafika", "gpu_details": {}, 
        "ram": "0 GB", "ram_details": [], 
        "mobo": {"vendor": "", "product": "Neznámá Deska", "version": "", "serial": "", "bios": "", "uuid": ""},
        "storage": [], "os": os_name, "pc_name": socket.gethostname(),
        "monitors": []
    }
    
    try:
        c = wmi.WMI()
        
        # --- OS ---
        report(_("splash_os"))
        try:
            os_info = c.Win32_OperatingSystem()[0]
            specs["os"] = os_info.Caption.replace("Microsoft ", "").strip()
        except: pass

        # --- CPU ---
        report(_("splash_cpu"))
        try:
            cpu_info = c.Win32_Processor()[0]
            specs["cpu"] = cpu_info.Name.strip()
            
            speed_ghz = f"{cpu_info.MaxClockSpeed / 1000:.1f} GHz" if cpu_info.MaxClockSpeed else "N/A"
            l2 = f"{cpu_info.L2CacheSize // 1024} MB" if cpu_info.L2CacheSize else "N/A"
            l3 = f"{cpu_info.L3CacheSize // 1024} MB" if cpu_info.L3CacheSize else "N/A"
            
            virt_cmd = _run_ps('powershell "(Get-CimInstance Win32_Processor).VirtualizationFirmwareEnabled"')
            virt = "Zapnuta" if "True" in virt_cmd else ("Vypnuta" if "False" in virt_cmd else "Neznámá")
            
            specs["cpu_details"] = {
                "cores": f"{cpu_info.NumberOfCores} Jader / {cpu_info.NumberOfLogicalProcessors} Vláken",
                "speed": speed_ghz, "l2": l2, "l3": l3, "socket": cpu_info.SocketDesignation, "virt": virt
            }
        except: specs["cpu"] = "Chyba načítání CPU"

        # --- GPU ---
        report(_("splash_gpu"))
        try:
            for gpu in c.Win32_VideoController():
                g_name = gpu.Name
                subvendor = get_gpu_vendor_from_id(gpu.PNPDeviceID)
                if subvendor and subvendor not in g_name.upper():
                    g_name = f"{subvendor} {g_name}"

                vram_bytes = get_real_vram_from_registry()
                if vram_bytes > 0:
                    vram_final_gb = f"{round(vram_bytes / (1024**3))} GB"
                else:
                    vram_final_gb = "Neznámá"

                if ".0 GB" in vram_final_gb: vram_final_gb = vram_final_gb.replace(".0 GB", " GB")

                specs["gpu"] = g_name
                specs["gpu_details"] = {
                    "vram": vram_final_gb, 
                    "driver_ver": gpu.DriverVersion, 
                    "driver_date": format_wmi_date(gpu.DriverDate)
                }
                break 
        except: specs["gpu"] = "Chyba GPU"

        # --- Motherboard & BIOS ---
        report(_("splash_mobo"))
        try:
            mb = c.Win32_BaseBoard()[0]
            specs["mobo"]["vendor"] = mb.Manufacturer.strip()
            specs["mobo"]["product"] = mb.Product.strip()
            specs["mobo"]["version"] = mb.Version.strip()
            specs["mobo"]["serial"] = mb.SerialNumber.strip()
            
            sys_prod = c.Win32_ComputerSystemProduct()[0]
            specs["mobo"]["uuid"] = sys_prod.UUID

            bios = c.Win32_BIOS()[0]
            bios_date = format_wmi_date(bios.ReleaseDate)
            specs["mobo"]["bios"] = f"{bios.SMBIOSBIOSVersion} ({bios_date})"
        except: pass
        
        # --- RAM ---
        report(_("splash_ram"))
        try:
            total_ram_bytes = 0
            for ram in c.Win32_PhysicalMemory():
                cap = int(ram.Capacity)
                total_ram_bytes += cap
                manufacturer = ram.Manufacturer.strip() if ram.Manufacturer else "Unknown"
                part_num = ram.PartNumber.strip() if ram.PartNumber else "Unknown"
                speed = ram.Speed if ram.Speed else "Unknown"
                specs["ram_details"].append(f"{manufacturer} {part_num}\n{cap // (1024**3)} GB @ {speed} MHz")
            
            if total_ram_bytes > 0:
                specs["ram"] = f"{round(total_ram_bytes / (1024**3))} GB"
        except: specs["ram"] = "Chyba detekce RAM"

        # --- Monitory (s reálným EDID názvem) ---
        report(_("splash_monitors"))
        try:
            # WmiMonitorID čte skutečná EDID data, přeskočí ovladače jako "Generic PnP Monitor"
            c_mon = wmi.WMI(namespace=r"root\wmi")
            for m in c_mon.WmiMonitorID():
                if hasattr(m, 'UserFriendlyName') and m.UserFriendlyName is not None:
                    # Názvy jsou v poli ascii kódů, filtrujeme prázdné znaky (0)
                    name_chars = [chr(char_code) for char_code in m.UserFriendlyName if char_code > 0]
                    real_name = "".join(name_chars).strip()
                    if real_name:
                        specs["monitors"].append(real_name)
                        
            # Fallback pro případ, že WmiMonitorID nic nenajde
            if not specs["monitors"]:
                for monitor in c.Win32_PnPEntity(PNPClass="Monitor"):
                    name = monitor.Caption
                    # Filtrujeme "Obecný monitor PnP" atd.
                    if name and "Generic" not in name and "Obecný" not in name:
                        specs["monitors"].append(name)
        except: pass

        # --- Storage ---
        report(_("splash_storage"))
        try:
            ps_cmd = 'powershell "Get-PhysicalDisk | Select-Object FriendlyName, MediaType, BusType, SpindleSpeed, Size | ConvertTo-Json"'
            disks_raw = _run_ps(ps_cmd)
            
            if disks_raw:
                disks_data = json.loads(disks_raw)
                if isinstance(disks_data, dict): disks_data = [disks_data] 

                for d in disks_data:
                    name = d.get('FriendlyName', 'Unknown')
                    media_type = d.get('MediaType', 'Unspecified')
                    bus = d.get('BusType', 'Unknown')
                    spindle = d.get('SpindleSpeed', 0)
                    size_bytes = d.get('Size', 0)
                    
                    name_upper = name.upper()

                    if media_type == 'Unspecified' or not media_type:
                        if spindle and spindle > 0: media_type = 'HDD'
                        elif 'SSD' in name_upper or 'NVME' in name_upper: media_type = 'SSD'
                        elif 'HDD' in name_upper or ('HD' in name_upper and 'SSD' not in name_upper): media_type = 'HDD'
                        else: media_type = 'Neznámé'

                    if bus == 'USB':
                        if media_type == 'SSD' or 'SSD' in name_upper: media_type = 'Externí SSD'
                        elif media_type == 'HDD' or 'HDD' in name_upper: media_type = 'Externí HDD'
                        else: media_type = 'Flash disk'

                    if size_bytes:
                        real_gb = round(size_bytes / (1024**3))
                        specs["storage"].append({
                            "name": name, "type": media_type, "bus": "NVMe" if bus == "NVMe" else bus,
                            "real_size": f"{real_gb} GB", "market_size": get_market_size(real_gb)
                        })
        except: pass

        # Fallback to WMI if PowerShell failed to find any disks (e.g. on some laptops with Intel RST)
        if not specs["storage"]:
            try:
                wmi_conn = wmi.WMI()
                for disk in wmi_conn.Win32_DiskDrive():
                    name = disk.Model or 'Unknown Disk'
                    size_bytes = int(disk.Size) if disk.Size else 0
                    
                    name_upper = name.upper()
                    media_type = 'Neznámé'
                    if 'SSD' in name_upper or 'NVME' in name_upper: media_type = 'SSD'
                    elif 'HDD' in name_upper or 'HD' in name_upper: media_type = 'HDD'
                    else: media_type = 'Disk'
                    
                    bus = disk.InterfaceType or 'Unknown'
                    
                    if size_bytes:
                        real_gb = round(size_bytes / (1024**3))
                        specs["storage"].append({
                            "name": name, "type": media_type, "bus": bus,
                            "real_size": f"{real_gb} GB", "market_size": get_market_size(real_gb)
                        })
            except: pass

    except Exception as e:
        print(f"Kritická chyba WMI: {e}")
    
    report(_("splash_done"))
    return specs
    
# --- UI KOMPONENTY ---

from UI.components.spec_components import SpecRow, SpecGroup, DiskRow, AnimatedNavItem, AnimatedCard, MiniToast, InfoHeaderCard

class SpecsPage(QWidget):
    def __init__(self, data=None): 
        super().__init__()
        if data:
            self.specs = data
        else:
            self.specs = {
                "pc_name": "Neznámé", "os": "Neznámé", "cpu": "Neznámé", 
                "gpu": "Neznámé", "ram": "Neznámé", "cpu_details": {}, 
                "gpu_details": {}, "ram_details": [], 
                "mobo": {"vendor": "", "product": "", "bios": "", "serial": "", "uuid": ""},
                "storage": [], "monitors": []
            }
            
        self.nav_items = []
        self.init_ui() 
        self.toast = MiniToast(self)

    def show_copy_notification(self):
        self.toast.show()
        self.toast.raise_()
        QTimer.singleShot(1500, self.toast.hide)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(35, 30, 35, 30); main_layout.setSpacing(25)

        # Header
        header_row = QHBoxLayout()
        self.header_lbl = QLabel()
        self.header_lbl.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {COLORS['fg']};")
        
        header_row.addWidget(self.header_lbl); header_row.addStretch()
        main_layout.addLayout(header_row)

        top_bar = QHBoxLayout()
        top_bar.addWidget(InfoHeaderCard("desktop-thin.png", "sp_dev_name", self.specs.get('pc_name', 'Neznámé')))
        top_bar.addWidget(InfoHeaderCard("windows-logo-thin.png", "sp_os", self.specs.get('os', 'Neznámé')))
        top_bar.addWidget(InfoHeaderCard("circuitry-thin.png", "sp_arch", platform.machine()))
        top_bar.addStretch(); main_layout.addLayout(top_bar)

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(self.separator)

        content_layout = QHBoxLayout(); content_layout.setSpacing(25)

        self.sidebar_frame = QFrame(); self.sidebar_frame.setFixedWidth(210)
        sidebar_layout = QVBoxLayout(self.sidebar_frame); sidebar_layout.setContentsMargins(10, 15, 10, 15); sidebar_layout.setSpacing(5)

        # SEZNAM ZÁLOŽEK A IKONEK
        # Zkontroluj si, že tyto '.png' soubory existují v assets/images/
        sections = [
            ("sp_tab_sum", "squares-four-thin.png"), 
            ("sp_tab_cpu", "cpu-thin.png"),
            ("sp_tab_mb", "circuitry-thin.png"),
            ("sp_tab_gpu", "graphics-card-thin.png"),
            ("sp_tab_ram", "memory-thin.png"),
            ("sp_tab_disk", "hard-drives-thin.png"),
            ("sp_tab_mon", "monitor-thin.png")
        ]
        
        for i, (name, icon_name) in enumerate(sections):
            item = AnimatedNavItem(name, icon_name, i, self)
            item.clicked.connect(self.display_tab)
            sidebar_layout.addWidget(item)
            self.nav_items.append(item)
        
        sidebar_outer = QVBoxLayout(); sidebar_outer.addWidget(self.sidebar_frame); sidebar_outer.addStretch() 
        content_layout.addLayout(sidebar_outer)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_summary_page())
        self.stack.addWidget(self.create_cpu_page())
        self.stack.addWidget(self.create_mobo_page())
        self.stack.addWidget(self.create_gpu_page())
        self.stack.addWidget(self.create_ram_page())
        self.stack.addWidget(self.create_disk_page())
        self.stack.addWidget(self.create_monitors_page())
        content_layout.addWidget(self.stack)

        main_layout.addLayout(content_layout)
        self.display_tab(0)

        theme_manager.theme_changed.connect(self.update_style)
        self.update_style()

        translator.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def update_style(self):
        self.header_lbl.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {COLORS['fg']};")
        self.separator.setStyleSheet(f"background-color: {COLORS['border']}; min-height: 1px; max-height: 1px; border: none;")
        self.sidebar_frame.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_sidebar']}; border-radius: 12px; border: none; }}")
        self.stack.setStyleSheet("background: transparent;")
        
        if hasattr(self, 'empty_lbl'):
            self.empty_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 13px;")
            
        if hasattr(self, 'disk_head'):
            self.disk_head.setStyleSheet(f"background: {COLORS['item_bg']}; border-radius: 4px;")
            
        if hasattr(self, 'disk_header_lbls'):
            for lbl in self.disk_header_lbls:
                lbl.setStyleSheet(f"color: {COLORS['fg']}; font-size: 9px; font-weight: bold; border: none;")

    def retranslate_ui(self):
        self.header_lbl.setText(_("sp_title"))
        if hasattr(self, 'empty_lbl'):
            self.empty_lbl.setText(_("sp_no_monitors"))
        if hasattr(self, 'disk_header_lbls'):
            for lbl in self.disk_header_lbls:
                lbl.setText(_(lbl.property("title_key")).upper())

    def display_tab(self, idx):
        if idx == 2:
            w = self.stack.widget(2)
            self.stack.removeWidget(w)
            self.stack.insertWidget(2, self.create_mobo_page())
        self.stack.setCurrentIndex(idx)
        for i, item in enumerate(self.nav_items): item.set_active(i == idx)

    def create_mobo_page(self):
        m = self.specs.get('mobo', {})
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#scrollContent { background: transparent; }")
        
        content = QWidget()
        content.setObjectName("scrollContent")
        l = QVBoxLayout(content)
        l.setContentsMargins(0, 0, 10, 0)
        l.setSpacing(15)
        
        group = SpecGroup(self)
        group.add_row("sp_vendor", m.get('vendor', 'Neznámé'))
        group.add_row("sp_model", m.get('product', 'Neznámé'))
        group.add_row("sp_bios", m.get('bios', 'Neznámé'))
        group.add_row("sp_serial", m.get('serial', 'Neznámé'))
        if m.get('uuid'):
            group.add_row("sp_uuid", m.get('uuid'))
        l.addWidget(group)
        
        l.addStretch()
        scroll.setWidget(content)
        return scroll

    def create_cpu_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#scrollContent { background: transparent; }")
        content = QWidget()
        content.setObjectName("scrollContent")
        l = QVBoxLayout(content)
        l.setContentsMargins(0, 0, 10, 0)
        l.setSpacing(15)
        
        group = SpecGroup(self)
        details = self.specs.get("cpu_details", {})
        group.add_row("sp_model", self.specs.get('cpu', 'Neznámé'))
        
        if details:
            group.add_row("sp_cores", details.get('cores', 'N/A'))
            group.add_row("sp_freq", details.get('speed', 'N/A'))
            group.add_row("L2 Cache", details.get('l2', 'N/A'))
            group.add_row("L3 Cache", details.get('l3', 'N/A'))
            group.add_row("Socket", details.get('socket', 'N/A'))
            group.add_row("sp_virt", details.get('virt', 'N/A'))
        else:
            group.add_row("sp_arch", platform.machine())
            
        l.addWidget(group)
        l.addStretch()
        scroll.setWidget(content)
        return scroll

    def create_gpu_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#scrollContent { background: transparent; }")
        content = QWidget()
        content.setObjectName("scrollContent")
        l = QVBoxLayout(content)
        l.setContentsMargins(0, 0, 10, 0)
        l.setSpacing(15)
        
        group = SpecGroup(self)
        details = self.specs.get("gpu_details", {})
        group.add_row("sp_model", self.specs.get('gpu', 'Neznámé'))

        if details:
            group.add_row("sp_vram", details.get('vram', 'N/A'))
            group.add_row("sp_driver_ver", details.get('driver_ver', 'N/A'))
            group.add_row("sp_driver_date", details.get('driver_date', 'N/A'))
        
        l.addWidget(group)
        l.addStretch()
        scroll.setWidget(content)
        return scroll

    def create_ram_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#scrollContent { background: transparent; }")
        content = QWidget()
        content.setObjectName("scrollContent")
        l = QVBoxLayout(content)
        l.setContentsMargins(0, 0, 10, 0)
        l.setSpacing(15)

        group = SpecGroup(self)
        group.add_row("sp_total_cap", self.specs.get('ram', 'Neznámé'))
        
        for i, det in enumerate(self.specs.get('ram_details', [])):
            group.add_row(f"sp_slot {i+1}", det)

        l.addWidget(group)
        l.addStretch()
        scroll.setWidget(content)
        return scroll

    def create_monitors_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#scrollContent { background: transparent; }")
        content = QWidget()
        content.setObjectName("scrollContent")
        l = QVBoxLayout(content)
        l.setContentsMargins(0, 0, 10, 0)
        l.setSpacing(15)

        mons = self.specs.get('monitors', [])

        if mons:
            group = SpecGroup(self)
            for i, mon in enumerate(mons): 
                group.add_row(f"sp_display {i+1}", mon)
            l.addWidget(group)
        else:
            self.empty_lbl = QLabel()
            l.addWidget(self.empty_lbl)

        l.addStretch()
        scroll.setWidget(content)
        return scroll
    
    def create_summary_page(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(0,0,0,0); l.setSpacing(12)
        l.addWidget(AnimatedCard("sp_tab_cpu", self.specs.get('cpu', 'Neznámé'), self))
        
        gpu_label = self.specs.get('gpu', 'Neznámé')
        vram = self.specs.get('gpu_details', {}).get('vram', '')
        if vram and vram != "Neznámá":
            gpu_label += f" {vram}"
            
        l.addWidget(AnimatedCard("sp_tab_gpu", gpu_label, self))
        
        m_vendor = self.specs.get('mobo', {}).get('vendor', '')
        m_product = self.specs.get('mobo', {}).get('product', '')
        l.addWidget(AnimatedCard("sp_tab_mb", f"{m_vendor} {m_product}", self))
        
        l.addWidget(AnimatedCard("sp_tab_ram", self.specs.get('ram', 'Neznámé'), self))
        l.addStretch(); return page

    def create_disk_page(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(5)
        col_widths = [250, 80, 80, 90, 90] 
        
        self.disk_head = QFrame()
        h_lay = QHBoxLayout(self.disk_head)
        h_lay.setContentsMargins(15, 8, 25, 8) 
        h_lay.setSpacing(0)
        h_lay.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        titles = ["sp_disk_name", "sp_disk_type", "sp_disk_bus", "sp_disk_size", "sp_disk_real"]
        self.disk_header_lbls = []
        for i, t in enumerate(titles):
            lbl = QLabel()
            lbl.setProperty("title_key", t)
            lbl.setFixedWidth(col_widths[i])
            lbl.setStyleSheet(f"color: {COLORS['fg']}; font-size: 9px; font-weight: bold; border: none;")
            h_lay.addWidget(lbl)
            self.disk_header_lbls.append(lbl)
            
        h_lay.addStretch()
        l.addWidget(self.disk_head)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#scrollContent { background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        cont = QWidget()
        cont.setObjectName("scrollContent"); c_lay = QVBoxLayout(cont); c_lay.setSpacing(2); c_lay.setContentsMargins(0, 5, 0, 0); c_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        for d in self.specs.get('storage', []): 
            c_lay.addWidget(DiskRow(d, col_widths, self))
        
        c_lay.addStretch()
        scroll.setWidget(cont)
        l.addWidget(scroll)
        return page
