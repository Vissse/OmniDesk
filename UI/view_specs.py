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
try:
    from core.config import COLORS, resource_path
except ImportError:
    COLORS = {
        'bg': '#121212', 'bg_sidebar': '#1e1e1e', 'item_bg': '#252525', 
        'item_hover': '#333333', 'accent': '#3498db', 'fg': '#ffffff', 
        'sub_text': '#aaaaaa', 'border': '#333333', 'success': '#2ecc71'
    }
    def resource_path(p): return p

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
        report("Zjišťuji verzi operačního systému...")
        try:
            os_info = c.Win32_OperatingSystem()[0]
            specs["os"] = os_info.Caption.replace("Microsoft ", "").strip()
        except: pass

        # --- CPU ---
        report("Zjišťuji procesor (CPU)...")
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
        report("Zjišťuji grafickou kartu (GPU)...")
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
        report("Zjišťuji základní desku...")
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
        report("Zjišťuji operační paměť (RAM)...")
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
        report("Zjišťuji monitory...")
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
        report("Zjišťuji disky a úložiště...")
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

    except Exception as e:
        print(f"Kritická chyba WMI: {e}")
    
    report("Dokončuji načítání...")
    return specs
    
# --- UI KOMPONENTY ---

class SpecRow(QFrame):
    def __init__(self, title, value, parent_page=None):
        super().__init__()
        self.parent_page = parent_page
        self.copy_text = str(value)
        self.setMinimumHeight(45)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._bar_height_factor = 0.0
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 5, 20, 5) 
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.t_lbl = QLabel(str(title).upper())
        self.t_lbl.setFixedWidth(160)
        self.t_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 10px; font-weight: bold; background: transparent;")
        
        self.v_lbl = QLabel(str(value))
        self.v_lbl.setWordWrap(False)
        self.v_lbl.setStyleSheet(f"color: {COLORS['fg']}; font-size: 13px; font-weight: 500; background: transparent;")
        
        self.copy_icon = QLabel()
        icon_path = resource_path("assets/images/copy-simple-thin.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            p = QPainter(pix)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(pix.rect(), QColor(COLORS['sub_text']))
            p.end()
            self.copy_icon.setPixmap(pix)
            
        self.op_effect = QGraphicsOpacityEffect(self.copy_icon)
        self.op_effect.setOpacity(0.0)
        self.copy_icon.setGraphicsEffect(self.op_effect)
        
        self.layout.addWidget(self.t_lbl)
        self.layout.addWidget(self.v_lbl)
        self.layout.addWidget(self.copy_icon)
        self.layout.addStretch() 
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)
        
    def _animate_step(self, val):
        self._bar_height_factor = val
        self.op_effect.setOpacity(val)
        
        c_start = QColor(COLORS['sub_text'])
        c_end = QColor("#cccccc")
        r = c_start.red() + (c_end.red() - c_start.red()) * val
        g = c_start.green() + (c_end.green() - c_start.green()) * val
        b = c_start.blue() + (c_end.blue() - c_start.blue()) * val
        self.t_lbl.setStyleSheet(f"color: rgb({int(r)}, {int(g)}, {int(b)}); font-size: 10px; font-weight: bold; background: transparent;")
        self.update()

    def enterEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Forward)
        self.anim.start()

    def leaveEvent(self, event):
        self.anim.setDirection(QVariantAnimation.Direction.Backward)
        self.anim.start()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.parent_page:
            QApplication.clipboard().setText(self.copy_text)
            self.parent_page.show_copy_notification()

    def paintEvent(self, event):
        if self._bar_height_factor > 0:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = self.rect()
            p.setBrush(QColor(COLORS['accent']))
            p.setPen(Qt.PenStyle.NoPen)
            
            radius = 1
            w = 3
            h = 16 * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            x = 4 
            
            path = QPainterPath()
            path.addRoundedRect(int(x), int(y), w, int(h), radius, radius)
            p.drawPath(path)

class SpecGroup(QFrame):
    def __init__(self, parent_page=None):
        super().__init__()
        self.parent_page = parent_page
        self.setObjectName("specGroup")
        self.setStyleSheet(f"#specGroup {{ background-color: {COLORS['item_bg']}; border-radius: 8px; }}")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(0)
        self.rows = []

    def add_row(self, title, value):
        if self.rows:
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background-color: {COLORS['border']}; margin-left: 15px; margin-right: 15px;")
            self.layout.addWidget(sep)
            
        row = SpecRow(title, value, self.parent_page)
        self.layout.addWidget(row)
        self.rows.append(row)

class DiskRow(QFrame):
    def __init__(self, disk_data, col_widths, parent_page):
        super().__init__()
        self.parent_page = parent_page
        self.data = disk_data
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(45)
        
        clean_name = clean_disk_name(self.data['name'])
        self.copy_text = f"{clean_name} {self.data['type']} {self.data['market_size']}"
        
        self._bg_color = QColor("transparent")
        self._bar_height_factor = 0.0 
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 25, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.add_column(clean_name, col_widths[0], f"color: {COLORS['fg']}; font-weight: 500;")
        self.add_column(self.data['type'], col_widths[1], f"color: {COLORS['sub_text']};")
        self.add_column(self.data['bus'], col_widths[2], f"color: {COLORS['sub_text']};")
        self.add_column(self.data['market_size'], col_widths[3], f"color: {COLORS['fg']}; font-weight: bold;")
        self.add_column(self.data['real_size'], col_widths[4], f"color: {COLORS['sub_text']};")

        self.layout.addStretch()
        
        self.copy_icon = QLabel()
        icon_path = resource_path("assets/images/copy-simple-thin.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            p = QPainter(pix)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(pix.rect(), QColor(COLORS['sub_text']))
            p.end()
            self.copy_icon.setPixmap(pix)
            
        self.op_effect = QGraphicsOpacityEffect(self.copy_icon)
        self.op_effect.setOpacity(0.0)
        self.copy_icon.setGraphicsEffect(self.op_effect)
        
        self.layout.addWidget(self.copy_icon)
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)

    def add_column(self, text, width, style):
        lbl = QLabel(text)
        lbl.setFixedWidth(width)
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        lbl.setStyleSheet(f"background: transparent; border: none; {style}")
        self.layout.addWidget(lbl)

    def _animate_step(self, val):
        self._bar_height_factor = val 
        self.op_effect.setOpacity(val) 
        
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
        if event.button() == Qt.MouseButton.LeftButton and self.parent_page:
            QApplication.clipboard().setText(self.copy_text)
            self.parent_page.show_copy_notification()
            
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        radius = 4
        
        if self._bg_color.alpha() > 0:
            p.setBrush(self._bg_color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, radius, radius)
            
        if getattr(self, '_bar_height_factor', 0) > 0:
            p.setBrush(QColor(COLORS['accent']))
            p.setPen(Qt.PenStyle.NoPen)
            
            h = rect.height() * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            
            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)
            p.setClipPath(path)
            
            p.drawRect(QRect(rect.x(), int(y), 4, int(h)))
            p.setClipping(False)

class AnimatedNavItem(QFrame):
    clicked = pyqtSignal(int)
    def __init__(self, text, icon_name, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(45)
        self._bg_color = QColor("transparent")
        self._bar_height_factor = 0.0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 10, 0)
        layout.setSpacing(12) # Mezera mezi ikonkou a textem
        
        # --- IKONKA ---
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(16, 16) # Velikost 16x16 perfektně ladí s fontem velikosti 13px
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        
        # Připravíme si dvě verze ikonky do paměti, ať je nemusíme obarvovat při každém framu animace
        self.pix_normal = QPixmap()
        self.pix_active = QPixmap()
        
        path = resource_path(f"assets/images/{icon_name}")
        if os.path.exists(path):
            raw_pix = QPixmap(path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # Neaktivní (šedá) verze
            self.pix_normal = raw_pix.copy()
            p = QPainter(self.pix_normal)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(self.pix_normal.rect(), QColor(COLORS['sub_text']))
            p.end()
            
            # Aktivní / Hover (bílá) verze
            self.pix_active = raw_pix.copy()
            p = QPainter(self.pix_active)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(self.pix_active.rect(), QColor(COLORS['fg']))
            p.end()
            
            self.icon_lbl.setPixmap(self.pix_normal)
            
        self.label = QLabel(text)
        self.label.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        
        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.label)
        layout.addStretch() # Zajistí, že se ikonka s textem nalepí doleva
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(250)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)
        
    def set_active(self, active): 
        self.active = active
        self._animate_step(1.0 if active else 0.0)
        
    def _animate_step(self, val):
        if not self.active:
            target_bg = QColor(COLORS['item_hover'])
            self._bg_color = QColor(target_bg.red(), target_bg.green(), target_bg.blue(), int(255 * val))
            self._bar_height_factor = val
            
            # V polovině animace přehoď barvu textu a ikonky
            is_highlighted = val > 0.5
            self.label.setStyleSheet(f"color: {COLORS['fg'] if is_highlighted else COLORS['sub_text']}; font-size: 13px; font-weight: 500; border: none; background: transparent;")
            if not self.pix_active.isNull():
                self.icon_lbl.setPixmap(self.pix_active if is_highlighted else self.pix_normal)
        else:
            self._bg_color = QColor(COLORS['item_bg'])
            self._bar_height_factor = 1.0
            self.label.setStyleSheet(f"color: {COLORS['fg']}; font-size: 13px; font-weight: 500; border: none; background: transparent;")
            if not self.pix_active.isNull():
                self.icon_lbl.setPixmap(self.pix_active)
        self.update()
        
    def enterEvent(self, event): 
        if not self.active: self.anim.setDirection(QVariantAnimation.Direction.Forward); self.anim.start()
        
    def leaveEvent(self, event): 
        if not self.active: self.anim.setDirection(QVariantAnimation.Direction.Backward); self.anim.start()
        
    def mousePressEvent(self, event): 
        self.clicked.emit(self.index)
        
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        radius = 8
        if self._bg_color.alpha() > 0:
            p.setBrush(self._bg_color); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(rect, radius, radius)
        if self._bar_height_factor > 0:
            p.setBrush(QColor(COLORS['accent'])); p.setPen(Qt.PenStyle.NoPen)
            h = rect.height() * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)
            p.setClipPath(path); p.drawRect(QRect(0, int(y), 4, int(h))); p.setClipping(False)

class AnimatedCard(QFrame):
    def __init__(self, title, value, parent_page=None):
        super().__init__()
        self.parent_page = parent_page 
        self.copy_text = str(value)
        self.setCursor(Qt.CursorShape.PointingHandCursor) 
        self.setFixedHeight(65) 
        self._bg_color = QColor(COLORS['item_bg'])
        self._bar_height_factor = 0.0 
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 15, 10)
        layout.setSpacing(2) 
        
        self.t_lbl = QLabel(title.upper())
        self.t_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 10px; font-weight: bold; background:transparent;")
        
        self.v_lbl = QLabel(str(value))
        self.v_lbl.setWordWrap(False) 
        self.v_lbl.setStyleSheet(f"color: {COLORS['fg']}; font-size: 13px; font-weight: 500; background:transparent;")
        
        self.copy_icon = QLabel()
        icon_path = resource_path("assets/images/copy-simple-thin.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            p = QPainter(pix)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(pix.rect(), QColor(COLORS['sub_text']))
            p.end()
            self.copy_icon.setPixmap(pix)
            
        self.op_effect = QGraphicsOpacityEffect(self.copy_icon)
        self.op_effect.setOpacity(0.0)
        self.copy_icon.setGraphicsEffect(self.op_effect)

        v_layout = QHBoxLayout()
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(8)
        v_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        v_layout.addWidget(self.v_lbl)
        v_layout.addWidget(self.copy_icon)
        v_layout.addStretch() 
        
        layout.addWidget(self.t_lbl)
        layout.addLayout(v_layout)
        layout.addStretch()
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._animate_step)
        
    def _animate_step(self, val):
        start_bg = QColor(COLORS['item_bg'])
        end_bg = QColor(COLORS['item_hover'])
        r = start_bg.red() + (end_bg.red() - start_bg.red()) * val
        g = start_bg.green() + (end_bg.green() - start_bg.green()) * val
        b = start_bg.blue() + (end_bg.blue() - start_bg.blue()) * val
        self._bg_color = QColor(int(r), int(g), int(b))
        self._bar_height_factor = val
        
        self.op_effect.setOpacity(val) 
        
        c_start = QColor(COLORS['sub_text'])
        c_end = QColor("#cccccc")
        tr = c_start.red() + (c_end.red() - c_start.red()) * val
        tg = c_start.green() + (c_end.green() - c_start.green()) * val
        tb = c_start.blue() + (c_end.blue() - c_start.blue()) * val
        self.t_lbl.setStyleSheet(f"color: rgb({int(tr)}, {int(tg)}, {int(tb)}); font-size: 10px; font-weight: bold; background:transparent;")
            
        self.update()
        
    def enterEvent(self, event): 
        self.anim.setDirection(QVariantAnimation.Direction.Forward)
        self.anim.start()
        
    def leaveEvent(self, event): 
        self.anim.setDirection(QVariantAnimation.Direction.Backward)
        self.anim.start()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.parent_page:
            QApplication.clipboard().setText(self.copy_text)
            self.parent_page.show_copy_notification()
        
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        radius = 8
        
        p.setBrush(self._bg_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, radius, radius)
        
        if self._bar_height_factor > 0:
            p.setBrush(QColor(COLORS['accent']))
            h = rect.height() * self._bar_height_factor
            y = rect.y() + (rect.height() - h) / 2
            path = QPainterPath()
            path.addRoundedRect(0, 0, rect.width(), rect.height(), radius, radius)
            p.setClipPath(path)
            p.drawRect(QRect(0, int(y), 4, int(h)))
            p.setClipping(False)

class MiniToast(QLabel):
    def __init__(self, parent):
        super().__init__("Zkopírováno!", parent)
        self.setStyleSheet(f"background: {COLORS['accent']}; color: white; padding: 5px 15px; border-radius: 4px; font-weight: bold;")
        self.adjustSize(); self.hide()

class InfoHeaderCard(QFrame):
    def __init__(self, icon_name, title, value):
        super().__init__()
        self.setStyleSheet("background-color: transparent; border: none;")
        
        l = QHBoxLayout(self)
        l.setContentsMargins(5, 8, 15, 8) 
        
        icon_lbl = QLabel()
        path = resource_path(f"assets/images/{icon_name}")
        if os.path.exists(path):
            pix = QPixmap(path).scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            p = QPainter(pix)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(pix.rect(), QColor(COLORS['fg'])) 
            p.end()
            icon_lbl.setPixmap(pix)
        l.addWidget(icon_lbl)
        
        v_l = QVBoxLayout()
        v_l.setSpacing(0)
        
        t = QLabel(title.upper())
        t.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 9px; font-weight: bold; border: none;")
        v = QLabel(value)
        v.setStyleSheet(f"color: {COLORS['fg']}; font-size: 13px; font-weight: bold; border: none;")
        
        v_l.addWidget(t)
        v_l.addWidget(v)
        l.addLayout(v_l)

# --- HLAVNÍ STRÁNKA ---

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

    def show_copy_notification(self, text="Zkopírováno!"):
        self.toast.setText(text)
        self.toast.adjustSize()
        self.toast.move((self.width() - self.toast.width()) // 2, 20)
        self.toast.show(); self.toast.raise_()
        QTimer.singleShot(1500, self.toast.hide)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(35, 30, 35, 30); main_layout.setSpacing(25)

        # Header
        header_row = QHBoxLayout()
        header_lbl = QLabel("Specifikace Počítače")
        header_lbl.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {COLORS['fg']};")
        
        header_row.addWidget(header_lbl); header_row.addStretch()
        main_layout.addLayout(header_row)

        top_bar = QHBoxLayout()
        top_bar.addWidget(InfoHeaderCard("desktop-thin.png", "Název zařízení", self.specs.get('pc_name', 'Neznámé')))
        top_bar.addWidget(InfoHeaderCard("windows-logo-thin.png", "Operační systém", self.specs.get('os', 'Neznámé')))
        top_bar.addWidget(InfoHeaderCard("circuitry-thin.png", "Architektura", platform.machine()))
        top_bar.addStretch(); main_layout.addLayout(top_bar)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine); separator.setStyleSheet(f"background-color: {COLORS['border']}; min-height: 1px; max-height: 1px; border: none;")
        main_layout.addWidget(separator)

        content_layout = QHBoxLayout(); content_layout.setSpacing(25)

        self.sidebar_frame = QFrame(); self.sidebar_frame.setFixedWidth(210)
        self.sidebar_frame.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_sidebar']}; border-radius: 12px; border: none; }}")
        sidebar_layout = QVBoxLayout(self.sidebar_frame); sidebar_layout.setContentsMargins(10, 15, 10, 15); sidebar_layout.setSpacing(5)

        # SEZNAM ZÁLOŽEK A IKONEK
        # Zkontroluj si, že tyto '.png' soubory existují v assets/images/
        sections = [
            ("Stručný přehled", "squares-four-thin.png"), # Nebo např. "info-thin.png"
            ("Procesor", "cpu-thin.png"),
            ("Základní deska", "circuitry-thin.png"),
            ("Grafická karta", "graphics-card-thin.png"),
            ("Paměť", "memory-thin.png"),
            ("Úložiště", "hard-drives-thin.png"),
            ("Monitory", "monitor-thin.png")
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
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content = QWidget()
        l = QVBoxLayout(content)
        l.setContentsMargins(0, 0, 10, 0)
        l.setSpacing(15)
        
        group = SpecGroup(self)
        group.add_row("Výrobce", m.get('vendor', 'Neznámé'))
        group.add_row("Model", m.get('product', 'Neznámé'))
        group.add_row("BIOS Verze", m.get('bios', 'Neznámé'))
        group.add_row("Sériové číslo", m.get('serial', 'Neznámé'))
        if m.get('uuid'):
            group.add_row("Systémové UUID", m.get('uuid'))
        l.addWidget(group)
        
        l.addStretch()
        scroll.setWidget(content)
        return scroll

    def create_cpu_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        l = QVBoxLayout(content)
        l.setContentsMargins(0, 0, 10, 0)
        l.setSpacing(15)
        
        group = SpecGroup(self)
        details = self.specs.get("cpu_details", {})
        group.add_row("Model", self.specs.get('cpu', 'Neznámé'))
        
        if details:
            group.add_row("Jádra / Vlákna", details.get('cores', 'N/A'))
            group.add_row("Frekvence", details.get('speed', 'N/A'))
            group.add_row("L2 Cache", details.get('l2', 'N/A'))
            group.add_row("L3 Cache", details.get('l3', 'N/A'))
            group.add_row("Socket", details.get('socket', 'N/A'))
            group.add_row("Virtualizace", details.get('virt', 'N/A'))
        else:
            group.add_row("Architektura", platform.machine())
            
        l.addWidget(group)
        l.addStretch()
        scroll.setWidget(content)
        return scroll

    def create_gpu_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        l = QVBoxLayout(content)
        l.setContentsMargins(0, 0, 10, 0)
        l.setSpacing(15)
        
        group = SpecGroup(self)
        details = self.specs.get("gpu_details", {})
        group.add_row("Model", self.specs.get('gpu', 'Neznámé'))

        if details:
            group.add_row("Video Paměť (VRAM)", details.get('vram', 'N/A'))
            group.add_row("Verze Ovladače", details.get('driver_ver', 'N/A'))
            group.add_row("Datum Ovladače", details.get('driver_date', 'N/A'))
        
        l.addWidget(group)
        l.addStretch()
        scroll.setWidget(content)
        return scroll

    def create_ram_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        l = QVBoxLayout(content)
        l.setContentsMargins(0, 0, 10, 0)
        l.setSpacing(15)

        group = SpecGroup(self)
        group.add_row("Celková kapacita", self.specs.get('ram', 'Neznámé'))
        
        for i, det in enumerate(self.specs.get('ram_details', [])):
            group.add_row(f"Slot {i+1}", det)

        l.addWidget(group)
        l.addStretch()
        scroll.setWidget(content)
        return scroll

    def create_monitors_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        l = QVBoxLayout(content)
        l.setContentsMargins(0, 0, 10, 0)
        l.setSpacing(15)

        mons = self.specs.get('monitors', [])

        if mons:
            group = SpecGroup(self)
            for i, mon in enumerate(mons): 
                group.add_row(f"Displej {i+1}", mon)
            l.addWidget(group)
        else:
            empty_lbl = QLabel("Nebyl nalezen žádný monitor.")
            empty_lbl.setStyleSheet(f"color: {COLORS['sub_text']}; font-size: 13px;")
            l.addWidget(empty_lbl)

        l.addStretch()
        scroll.setWidget(content)
        return scroll
    
    def create_summary_page(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(0,0,0,0); l.setSpacing(12)
        l.addWidget(AnimatedCard("Procesor", self.specs.get('cpu', 'Neznámé'), self))
        
        gpu_label = self.specs.get('gpu', 'Neznámé')
        vram = self.specs.get('gpu_details', {}).get('vram', '')
        if vram and vram != "Neznámá":
            gpu_label += f" {vram}"
            
        l.addWidget(AnimatedCard("Grafická karta", gpu_label, self))
        
        m_vendor = self.specs.get('mobo', {}).get('vendor', '')
        m_product = self.specs.get('mobo', {}).get('product', '')
        l.addWidget(AnimatedCard("Základní deska", f"{m_vendor} {m_product}", self))
        
        l.addWidget(AnimatedCard("Paměť RAM", self.specs.get('ram', 'Neznámé'), self))
        l.addStretch(); return page

    def create_disk_page(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(5)
        col_widths = [250, 80, 80, 90, 90] 
        
        head = QFrame(); head.setStyleSheet(f"background: {COLORS['item_bg']}; border-radius: 4px;")
        h_lay = QHBoxLayout(head)
        h_lay.setContentsMargins(15, 8, 25, 8) 
        h_lay.setSpacing(0)
        h_lay.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        titles = ["NÁZEV DISKU", "TYP", "SBĚRNICE", "VELIKOST", "REÁLNÁ"]
        for i, t in enumerate(titles):
            lbl = QLabel(t); lbl.setFixedWidth(col_widths[i])
            lbl.setStyleSheet(f"color: {COLORS['fg']}; font-size: 9px; font-weight: bold; border: none;")
            h_lay.addWidget(lbl)
            
        h_lay.addStretch()
        l.addWidget(head)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        cont = QWidget(); c_lay = QVBoxLayout(cont); c_lay.setSpacing(2); c_lay.setContentsMargins(0, 5, 0, 0); c_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        for d in self.specs.get('storage', []): 
            c_lay.addWidget(DiskRow(d, col_widths, self))
        
        c_lay.addStretch()
        scroll.setWidget(cont)
        l.addWidget(scroll)
        return page