from PyQt6.QtCore import QObject, pyqtSignal
from core.settings_manager import SettingsManager

TRANSLATIONS = {
    "Čeština": {
        # --- MENU (Navigace) ---
        "nav_home": "Přehled",
        "nav_catalog": "Katalog aplikací",
        "nav_queue": "Instalační fronta",
        "nav_updates": "Aktualizace aplikací",
        "nav_uninstall": "Odinstalace aplikací",
        "nav_health": "Kontrola stavu PC",
        "nav_specs": "Specifikace PC",
        "nav_settings": "Nastavení",

        # --- HOME PAGE ---
        "home_welcome": "Vítejte, {user}",
        "home_intro": "Toto je váš centrální rozcestník pro správu systému a aplikací.",
        "home_modules": "PŘEHLED MODULŮ",
        "home_desc_catalog": "Procházejte a instalujte nový software čistě a bez zbytečného klikání.",
        "home_desc_queue": "Hromadná, tichá instalace a automatická konfigurace vybraných programů.",
        "home_desc_updates": "Udržujte svůj systém v bezpečí pomocí hromadných aktualizací zastaralých verzí.",
        "home_desc_uninstall": "Rychlé a čisté odstranění nepotřebného softwaru ze systému.",
        "home_desc_health": "Sada diagnostických nástrojů, opravy systémových chyb a čištění disku.",
        "home_desc_specs": "Detailní přehled o hardwaru, komponentách a úložištích vašeho počítače.",
        "home_footer": "OmniDesk v{ver} • Moderní správce systému",

        # --- NASTAVENÍ ---
        "set_title": "Nastavení",
        "set_appearance": "Vzhled a Jazyk",
        "set_theme": "Barevný motiv",
        "set_theme_desc": "Vyberte si světlý nebo tmavý režim.",
        "set_lang": "Jazyk aplikace",
        "set_lang_desc": "Změna se projeví okamžitě napříč celou aplikací.",
        "set_system": "Systém",
        "set_update": "Aktualizace",
        "set_update_desc": "Zkontrolujte dostupnost nové verze programu OmniDesk.",
        "set_btn_update": " Zkontrolovat aktualizace",

        # --- OBECNÉ / SDÍLENÉ ---
        "btn_cancel": "Zrušit",
        "btn_close": "Zavřít",
        "btn_help": " Nápověda",
        "status_ready": "Připraveno.",
        "status_loading": "Načítání...",
        "unknown": "Neznámé",
        "search_apps": "Hledat v katalogu...",
        "search_queue": "Hledat v seznamu fronty...",
        "search_uninst": "Hledat v nainstalovaných aplikacích...",
        "search_upd": "Hledat v aktualizacích...",

        # --- KATALOG (Installer) ---
        "inst_title": "Katalog aplikací",
        "inst_install_sel": " Nainstalovat vybrané",
        "inst_settings": " Nastavení instalace",
        "inst_name": "Název",
        "inst_id": "ID",
        "inst_desc_empty": "Tato aplikace zatím nemá k dispozici podrobný popis.",

        # --- FRONTA (Queue) ---
        "q_title": "Instalační fronta",
        "q_new": " Nová",
        "q_open": " Otevřít",
        "q_save": " Uložit",
        "q_script": " Skript",
        "q_remove_sel": " Odebrat vybrané",

        # --- ODINSTALACE ---
        "un_title": "Odinstalace",
        "un_load": " Načíst aplikace",
        "un_uninstall_sel": " Odinstalovat vybrané",
        "un_progress_title": "PRŮBĚH ODINSTALACE",

        # --- AKTUALIZACE ---
        "up_title": "Aktualizace",
        "up_scan": " Skenovat",
        "up_update_sel": " Aktualizovat vybrané",
        "up_update_all": " Aktualizovat vše",
        "up_all_updated": "Všechny aplikace jsou aktuální ✨",
        "up_progress_title": "PRŮBĚH AKTUALIZACE",

        # --- ZDRAVÍ PC (Health Check) ---
        "h_title": "Kontrola stavu PC",
        "h_desc": "Nástroje pro diagnostiku, čištění a optimalizaci systému.",
        "h_sec_repair": "Opravy Systému",
        "h_sec_maint": "Správa a Údržba",
        "h_sec_adv": "Pokročilé Nástroje",
        "h_tool_sfc": "Kontrola a automatická oprava poškozených systémových souborů.",
        "h_tool_chkdsk": "Rychlá kontrola chyb na disku C: v režimu pouze pro čtení.",
        "h_tool_dism1": "Diagnostika obrazu Windows pro zjištění možného poškození.",
        "h_tool_dism2": "Stáhne a opraví systémové soubory pomocí Windows Update.",
        "h_tool_temp": "Bezpečně vymaže dočasné soubory zpomalující systém.",
        "h_tool_disk": "Otevře nativní nástroj Windows pro uvolnění místa.",
        "h_tool_bat": "Uloží podrobný HTML report o stavu baterie na disk C:.",
        "h_tool_sxs": "Hloubkové čištění starých aktualizací pro výraznou úsporu místa.",
        "h_tool_ctt": "Komplexní utilita pro debloat, instalaci aplikací a optimalizaci Windows.",

        # --- SPECIFIKACE ---
        "sp_title": "Specifikace Počítače",
        "sp_dev_name": "Název zařízení",
        "sp_os": "Operační systém",
        "sp_arch": "Architektura",
        "sp_tab_sum": "Stručný přehled",
        "sp_tab_cpu": "Procesor",
        "sp_tab_mb": "Základní deska",
        "sp_tab_gpu": "Grafická karta",
        "sp_tab_ram": "Paměť",
        "sp_tab_disk": "Úložiště",
        "sp_tab_mon": "Monitory",
        "sp_copied": "Zkopírováno!",
        "sp_vendor": "Výrobce",
        "sp_model": "Model",
        "sp_bios": "BIOS Verze",
        "sp_serial": "Sériové číslo",
        "sp_uuid": "Systémové UUID",
        "sp_cores": "Jádra / Vlákna",
        "sp_freq": "Frekvence",
        "sp_virt": "Virtualizace",
        "sp_vram": "Video Paměť (VRAM)",
        "sp_driver_ver": "Verze Ovladače",
        "sp_driver_date": "Datum Ovladače",
        "sp_total_cap": "Celková kapacita",
        "sp_slot": "Slot",
        "sp_display": "Displej",
        "sp_no_monitors": "Nebyl nalezen žádný monitor.",
        "sp_disk_name": "NÁZEV DISKU",
        "sp_disk_type": "TYP",
        "sp_disk_bus": "SBĚRNICE",
        "sp_disk_size": "VELIKOST",
        "sp_disk_real": "REÁLNÁ",
        
        # --- SPLASH SCREEN ---
        "splash_init": "Inicializace...",
        "splash_ver": "Verze",
    },
    "English": {
        # --- MENU (Navigation) ---
        "nav_home": "Dashboard",
        "nav_catalog": "App Catalog",
        "nav_queue": "Install Queue",
        "nav_updates": "App Updates",
        "nav_uninstall": "Uninstaller",
        "nav_health": "PC Health Check",
        "nav_specs": "PC Specs",
        "nav_settings": "Settings",

        # --- HOME PAGE ---
        "home_welcome": "Welcome, {user}",
        "home_intro": "This is your central hub for system and application management.",
        "home_modules": "MODULES OVERVIEW",
        "home_desc_catalog": "Browse and install new software cleanly without unnecessary clicking.",
        "home_desc_queue": "Bulk, silent installation and automatic configuration of selected programs.",
        "home_desc_updates": "Keep your system safe with bulk updates for outdated versions.",
        "home_desc_uninstall": "Fast and clean removal of unnecessary software from the system.",
        "home_desc_health": "A suite of diagnostic tools, system error repairs, and disk cleanup.",
        "home_desc_specs": "Detailed overview of your computer's hardware, components, and storage.",
        "home_footer": "OmniDesk v{ver} • Modern System Manager",

        # --- SETTINGS ---
        "set_title": "Settings",
        "set_appearance": "Appearance & Language",
        "set_theme": "Color Theme",
        "set_theme_desc": "Choose between light or dark mode.",
        "set_lang": "Application Language",
        "set_lang_desc": "Changes will apply immediately across the app.",
        "set_system": "System",
        "set_update": "Updates",
        "set_update_desc": "Check for new versions of the OmniDesk application.",
        "set_btn_update": " Check for Updates",

        # --- GENERAL / SHARED ---
        "btn_cancel": "Cancel",
        "btn_close": "Close",
        "btn_help": " Help",
        "status_ready": "Ready.",
        "status_loading": "Loading...",
        "unknown": "Unknown",
        "search_apps": "Search catalog...",
        "search_queue": "Search queue list...",
        "search_uninst": "Search installed apps...",
        "search_upd": "Search updates...",

        # --- CATALOG (Installer) ---
        "inst_title": "App Catalog",
        "inst_install_sel": " Install Selected",
        "inst_settings": " Install Settings",
        "inst_name": "Name",
        "inst_id": "ID",
        "inst_desc_empty": "No detailed description is available for this application yet.",

        # --- QUEUE ---
        "q_title": "Install Queue",
        "q_new": " New",
        "q_open": " Open",
        "q_save": " Save",
        "q_script": " Script",
        "q_remove_sel": " Remove Selected",

        # --- UNINSTALLER ---
        "un_title": "Uninstaller",
        "un_load": " Load Apps",
        "un_uninstall_sel": " Uninstall Selected",
        "un_progress_title": "UNINSTALL PROGRESS",

        # --- UPDATER ---
        "up_title": "Updates",
        "up_scan": " Scan",
        "up_update_sel": " Update Selected",
        "up_update_all": " Update All",
        "up_all_updated": "All applications are up to date ✨",
        "up_progress_title": "UPDATE PROGRESS",

        # --- PC HEALTH ---
        "h_title": "PC Health Check",
        "h_desc": "Tools for diagnostics, cleaning, and system optimization.",
        "h_sec_repair": "System Repairs",
        "h_sec_maint": "Management & Maintenance",
        "h_sec_adv": "Advanced Tools",
        "h_tool_sfc": "Check and automatically repair corrupted system files.",
        "h_tool_chkdsk": "Quick check for errors on the C: drive in read-only mode.",
        "h_tool_dism1": "Diagnose Windows image to detect potential corruption.",
        "h_tool_dism2": "Download and repair system files using Windows Update.",
        "h_tool_temp": "Safely delete temporary files slowing down the system.",
        "h_tool_disk": "Open the native Windows tool to free up space.",
        "h_tool_bat": "Save a detailed HTML battery health report to the C: drive.",
        "h_tool_sxs": "Deep clean old updates for significant space savings.",
        "h_tool_ctt": "Comprehensive utility for debloat, app installation, and Windows optimization.",

        # --- SPECS ---
        "sp_title": "Computer Specifications",
        "sp_dev_name": "Device Name",
        "sp_os": "Operating System",
        "sp_arch": "Architecture",
        "sp_tab_sum": "Summary",
        "sp_tab_cpu": "Processor",
        "sp_tab_mb": "Motherboard",
        "sp_tab_gpu": "Graphics Card",
        "sp_tab_ram": "Memory",
        "sp_tab_disk": "Storage",
        "sp_tab_mon": "Monitors",
        "sp_copied": "Copied!",
        "sp_vendor": "Vendor",
        "sp_model": "Model",
        "sp_bios": "BIOS Version",
        "sp_serial": "Serial Number",
        "sp_uuid": "System UUID",
        "sp_cores": "Cores / Threads",
        "sp_freq": "Frequency",
        "sp_virt": "Virtualization",
        "sp_vram": "Video Memory (VRAM)",
        "sp_driver_ver": "Driver Version",
        "sp_driver_date": "Driver Date",
        "sp_total_cap": "Total Capacity",
        "sp_slot": "Slot",
        "sp_display": "Display",
        "sp_no_monitors": "No monitor found.",
        "sp_disk_name": "DISK NAME",
        "sp_disk_type": "TYPE",
        "sp_disk_bus": "BUS",
        "sp_disk_size": "SIZE",
        "sp_disk_real": "REAL",

        # --- SPLASH SCREEN ---
        "splash_init": "Initializing...",
        "splash_ver": "Version",
    }
}

class TranslationManager(QObject):
    # Signál, který se odpálí při každé změně jazyka (zajišťuje okamžitou reakci appky)
    language_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        # Načteme uložený jazyk při startu
        settings = SettingsManager.load_settings()
        self.current_lang = settings.get("language", "Čeština")

    def set_language(self, lang):
        if lang in TRANSLATIONS and lang != self.current_lang:
            self.current_lang = lang
            self.language_changed.emit()

    def _(self, key):
        """Hlavní překladová funkce. Vrací překlad podle klíče."""
        return TRANSLATIONS.get(self.current_lang, TRANSLATIONS["Čeština"]).get(key, key)

# Globální instance a zkratka
translator = TranslationManager()
_ = translator._