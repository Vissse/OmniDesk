import os
import sys
import json
from pathlib import Path

# ==============================================================================
# 0. CHYTRÁ DEFINICE CEST (Relativní k aplikaci)
# ==============================================================================

def get_resource_path(relative_path):
    """Zajistí správnou cestu k souborům při vývoji i v .exe balíčku"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(current_dir)
        
    return os.path.join(base_path, relative_path)

ICONS_DIR = get_resource_path(os.path.join("assets", "icons"))
DESCRIPTIONS_FILE = get_resource_path(os.path.join("assets", "descriptions.json"))
DEFAULT_ICON = os.path.join(ICONS_DIR, "default-app.png")

# --- Načtení popisů z JSONu ---
APP_DESCRIPTIONS = {}
if os.path.exists(DESCRIPTIONS_FILE):
    try:
        with open(DESCRIPTIONS_FILE, "r", encoding="utf-8") as f:
            APP_DESCRIPTIONS = json.load(f)
    except Exception as e:
        print(f"DEBUG: Nelze načíst descriptions.json: {e}")

def get_icon(filename):
    """Vrací cestu k lokální ikoně. Pokud neexistuje, vrací výchozí ikonu."""
    local_path = os.path.join(ICONS_DIR, filename)
    if os.path.exists(local_path):
        return local_path
    return DEFAULT_ICON if os.path.exists(DEFAULT_ICON) else None

def create_app(name, app_id, website, icon_name):
    """Pomocná funkce, která automaticky přiřadí description z JSONu dle ID"""
    return {
        "name": name,
        "id": app_id,
        "website": website,
        "icon_url": get_icon(icon_name),
        "description": APP_DESCRIPTIONS.get(app_id, "Popis nebyl nalezen v databázi.")
    }

# ==============================================================================
# 1. DEFINICE JEDNOTLIVÝCH APLIKACÍ
# ==============================================================================

# --- Herní Launchery & Hry ---
steam_app = create_app("Steam", "Valve.Steam", "https://store.steampowered.com", "Valve.Steam.png")
epic_app = create_app("Epic Games Launcher", "EpicGames.EpicGamesLauncher", "https://store.epicgames.com", "EpicGames.EpicGamesLauncher.png")
ubisoft_app = create_app("Ubisoft Connect", "Ubisoft.Connect", "https://ubisoftconnect.com", "Ubisoft.Connect.png")
ea_app = create_app("EA App", "ElectronicArts.EADesktop", "https://www.ea.com/ea-app", "ElectronicArts.EADesktop.png")
gog_app = create_app("GOG GALAXY", "GOG.Galaxy", "https://www.gog.com/galaxy", "GOG.Galaxy.png")
playnite_app = create_app("Playnite", "Playnite.Playnite", "https://playnite.link", "Playnite.Playnite.png")
battlenet_app = create_app("Battle.net", "Blizzard.BattleNet", "https://www.blizzard.com", "Blizzard.BattleNet.png")
curseforge_app = create_app("CurseForge", "Overwolf.CurseForge", "https://www.curseforge.com", "Overwolf.CurseForge.png")
riot_app = create_app("Riot Client", "RiotGames.LeagueOfLegends.EUNE", "https://www.riotgames.com", "RiotGames.LeagueOfLegends.EUNE.png")
wargaming_app = create_app("Wargaming.net", "Wargaming.GameCenter", "https://wargaming.net", "Wargaming.GameCenter.png")
modrinth_app = create_app("Modrinth App", "Modrinth.ModrinthApp", "https://modrinth.com/app", "Modrinth.ModrinthApp.png")
psremote_app = create_app("PS Remote Play", "PlayStation.PSRemotePlay", "https://remoteplay.dl.playstation.net/remoteplay/", "PlayStation.PSRemotePlay.png")
psaccessories_app = create_app("PlayStation Accessories", "PlayStation.PlayStationAccessories", "https://controller.dl.playstation.net/controller/", "PlayStation.PlayStationAccessories.png")
bluestacks_app = create_app("BlueStacks 5", "BlueStack.BlueStacks", "https://www.bluestacks.com/", "BlueStack.BlueStacks.png")
faceit_app = create_app("FACEIT", "FACEITLTD.FACEITClient", "https://www.faceit.com/", "FACEITLTD.FACEITClient.png")
faceit_ac_app = create_app("FACEIT Anti-Cheat", "FACEITLTD.FACEITAC", "https://www.faceit.com/en/anti-cheat", "FACEITLTD.FACEITClient.png")
ftb_app = create_app("FTB Electron App", "FTB.App", "https://feed-the-beast.com/", "FeedTheBeast.FTBApp.png")
warthunder_app = create_app("War Thunder", "GaijinNetwork.WarThunder", "https://warthunder.com/", "GaijinNetwork.WarThunder.png")
minecraft_app = create_app("Minecraft Launcher", "Mojang.MinecraftLauncher", "https://www.minecraft.net/", "Mojang.MinecraftLauncher.png")
maniaplanet_app = create_app("ManiaPlanet", "Nadeo.ManiaPlanet", "https://www.maniaplanet.com/", "Nadeo.ManiaPlanet.png")

# --- Nvidia Nástroje ---
geforcenow_app = create_app("GeForce NOW", "Nvidia.GeForceNOW", "https://www.nvidia.com/en-us/geforce-now/", "Nvidia.GeForceNOW.png")
cuda_app = create_app("CUDA Toolkit", "Nvidia.CUDA", "https://developer.nvidia.com/cuda-toolkit", "Nvidia.GeForceNOW.png")
physx_app = create_app("NVIDIA PhysX", "Nvidia.PhysX", "https://www.nvidia.com/", "Nvidia.GeForceNOW.png")
rtxvoice_app = create_app("NVIDIA RTX Voice", "Nvidia.RTXVoice", "https://www.nvidia.com/", "Nvidia.GeForceNOW.png")

# --- Prohlížeče ---
chrome_app = create_app("Google Chrome", "Google.Chrome", "https://www.google.com/chrome", "Google.Chrome.png")
firefox_app = create_app("Mozilla Firefox", "Mozilla.Firefox", "https://www.mozilla.org/firefox", "Mozilla.Firefox.png")
edge_app = create_app("Microsoft Edge", "Microsoft.Edge", "https://www.microsoft.com/edge", "Microsoft.Edge.png")
brave_app = create_app("Brave Browser", "Brave.Brave", "https://brave.com", "Brave.Brave.png")
opera_app = create_app("Opera", "Opera.Opera", "https://www.opera.com", "Opera.Opera.png")
opera_gx_app = create_app("Opera GX", "Opera.OperaGX", "https://www.opera.com/gx", "Opera.OperaGX.png")
vivaldi_app = create_app("Vivaldi", "Vivaldi.Vivaldi", "https://vivaldi.com", "Vivaldi.Vivaldi.png")
zen_app = create_app("Zen Browser", "Zen-Team.Zen-Browser", "https://www.zen-browser.app", "Zen-Team.Zen-Browser.png")
librewolf_app = create_app("LibreWolf", "LibreWolf.LibreWolf", "https://librewolf.net", "LibreWolf.LibreWolf.png")
ungoogled_app = create_app("Ungoogled Chromium", "eloston.ungoogled-chromium", "https://github.com/ungoogled-software/ungoogled-chromium", "eloston.ungoogled-chromium.png")
waterfox_app = create_app("Waterfox", "Waterfox.Waterfox", "https://www.waterfox.net", "Waterfox.Waterfox.png")
arc_app = create_app("Arc", "TheBrowserCompany.Arc", "https://arc.net/", "TheBrowserCompany.Arc.png")
tor_app = create_app("Tor Browser", "TorProject.TorBrowser", "https://www.torproject.org/", "TorProject.TorBrowser.png")
duckduckgo_app = create_app("DuckDuckGo", "DuckDuckGo.DesktopBrowser", "https://duckduckgo.com/windows", "DuckDuckGo.DesktopBrowser.png")
falkon_app = create_app("Falkon", "KDE.Falkon", "https://www.falkon.org/", "KDE.Falkon.png")

# --- Komunikace ---
discord_app = create_app("Discord", "Discord.Discord", "https://discord.com", "Discord.Discord.png")
telegram_app = create_app("Telegram", "Telegram.TelegramDesktop", "https://desktop.telegram.org", "Telegram.TelegramDesktop.png")
teams_app = create_app("Teams", "Microsoft.Teams", "https://www.microsoft.com/microsoft-teams", "Microsoft.Teams.png")
teamspeak_app = create_app("TeamSpeak 3", "TeamSpeakSystems.TeamSpeakClient", "https://teamspeak.com/", "TeamSpeakSystems.TeamSpeakClient.png")
teamspeak6_app = create_app("TeamSpeak 6", "TeamSpeakSystems.TeamSpeakClient.Beta.6", "https://teamspeak.com/", "TeamSpeakSystems.TeamSpeakClient.Beta.6.png")
slack_app = create_app("Slack", "SlackTechnologies.Slack", "https://slack.com/", "SlackTechnologies.Slack.png")
zoom_app = create_app("Zoom", "Zoom.Zoom", "https://zoom.us/", "Zoom.Zoom.png")
thunderbird_app = create_app("Thunderbird", "Mozilla.Thunderbird", "https://www.thunderbird.net/", "Mozilla.Thunderbird.png")
betterbird_app = create_app("Betterbird", "Betterbird.Betterbird", "https://www.betterbird.eu/", "Betterbird.Betterbird.png")
viber_app = create_app("Viber", "Rakuten.Viber", "https://www.viber.com/", "Rakuten.Viber.png")
beeper_app = create_app("Beeper", "Beeper.Beeper", "https://www.beeper.com/", "Beeper.Beeper.png")
bluemail_app = create_app("BlueMail", "Blix.BlueMail", "https://bluemail.me/", "Blix.BlueMail.png")

# --- Média (Audio, Video, Grafika) ---
gimp_app = create_app("GIMP", "GIMP.GIMP.3", "https://www.gimp.org", "GIMP.GIMP.3.png")
paint_net_app = create_app("Paint.NET", "dotPDN.PaintDotNet", "https://www.getpaint.net", "dotPDN.PaintDotNet.png")
blender_app = create_app("Blender", "BlenderFoundation.Blender", "https://www.blender.org", "BlenderFoundation.Blender.png")
vlc_app = create_app("VLC media player", "VideoLAN.VLC", "https://www.videolan.org/vlc", "VideoLAN.VLC.png")
mpv_app = create_app("mpv", "shinchiro.mpv", "https://mpv.io/", "shinchiro.mpv.png")
stremio_app = create_app("Stremio", "Stremio.Stremio", "https://www.stremio.com/", "Stremio.Stremio.png")
audacity_app = create_app("Audacity", "Audacity.Audacity", "https://www.audacityteam.org", "Audacity.Audacity.png")
aimp_app = create_app("AIMP", "AIMP.AIMP", "https://www.aimp.ru/", "AIMP.AIMP.png")
fxsound_app = create_app("FxSound", "FxSound.FxSound", "https://www.fxsound.com/", "FxSound.FxSound.png")
obs_app = create_app("OBS Studio", "OBSProject.OBSStudio", "https://obsproject.com/", "OBSProject.OBSStudio.png")
inkscape_app = create_app("Inkscape", "Inkscape.Inkscape", "https://inkscape.org/", "Inkscape.Inkscape.png")
irfanview_app = create_app("IrfanView", "IrfanSkiljan.IrfanView", "https://www.irfanview.com/", "IrfanSkiljan.IrfanView.png")
krita_app = create_app("Krita", "KDE.Krita", "https://krita.org/", "KDE.Krita.png")
affinity_app = create_app("Affinity", "Canva.Affinity", "https://affinity.serif.com/", "Canva.Affinity.png")
spotify_app = create_app("Spotify", "Spotify.Spotify", "https://www.spotify.com/", "Spotify.Spotify.png")
itunes_app = create_app("iTunes", "Apple.iTunes", "https://www.apple.com/itunes/", "Apple.iTunes.png")
ytdownloader_app = create_app("4K Video Downloader", "OpenMedia.4KVideoDownloader", "https://www.4kdownload.com/", "OpenMedia.4KVideoDownloader.png")
honeyview_app = create_app("Honeyview", "Bandisoft.Honeyview", "https://cz.bandisoft.com/honeyview/", "Bandisoft.Honeyview.png")
bandiview_app = create_app("BandiView", "Bandisoft.BandiView", "https://www.bandisoft.com/bandiview/", "Bandisoft.BandiView.png")
bandicut_app = create_app("Bandicut", "BandicamCompany.Bandicut", "https://www.bandicam.com/bandicut-video-cutter/", "BandicamCompany.Bandicut.png")
bandicam_app = create_app("Bandicam", "BandicamCompany.Bandicam", "https://www.bandicam.com/", "BandicamCompany.Bandicam.png")
capcut_app = create_app("CapCut", "ByteDance.CapCut", "https://www.capcut.com/", "ByteDance.CapCut.png")
pixso_app = create_app("Pixso", "Bosyun.Pixso", "https://pixso.net/", "Bosyun.Pixso.png")
deezer_app = create_app("Deezer", "Deezer.Deezer", "https://www.deezer.com/", "Deezer.Deezer.png")
handbrake_app = create_app("HandBrake", "Handbrake.Handbrake", "https://handbrake.fr/", "Handbrake.Handbrake.png")
qview_app = create_app("qView", "jurplel.qView", "https://interversehq.com/qview/", "jurplel.qView.png")
imgburn_app = create_app("ImgBurn", "LIGHTNINGUK.ImgBurn", "https://www.imgburn.com/", "LIGHTNINGUK.ImgBurn.png")
fontbase_app = create_app("FontBase", "Levitsky.FontBase", "https://fontba.se/", "Levitsky.FontBase.png")
asio4all_app = create_app("ASIO4ALL", "MichaelTippach.ASIO4ALL", "https://www.asio4all.org/", "MichaelTippach.ASIO4ALL.png")
musescore_app = create_app("MuseScore", "Musescore.Musescore", "https://musescore.org/", "Musescore.Musescore.png")
pixelorama_app = create_app("Pixelorama", "OramaInteractive.Pixelorama", "https://orama-interactive.itch.io/pixelorama", "OramaInteractive.Pixelorama.png")
spotiflyer_app = create_app("SpotiFlyer", "Shabinder.SpotiFlyer", "https://github.com/Shabinder/SpotiFlyer", "Shabinder.SpotiFlyer.png")
streamlabs_app = create_app("Streamlabs", "Streamlabs.Streamlabs", "https://streamlabs.com/", "Streamlabs.Streamlabs.png")

# --- Kancelář, PDF & Text ---
ms_office_app = create_app("Microsoft 365", "Microsoft.OfficeDeploymentTool", "https://office.com", "Microsoft.OfficeDeploymentTool.png")
libreoffice_app = create_app("LibreOffice", "TheDocumentFoundation.LibreOffice", "https://www.libreoffice.org/", "TheDocumentFoundation.LibreOffice.png")
wps_app = create_app("WPS Office", "Kingsoft.WPSOffice", "https://www.wps.com/", "Kingsoft.WPSOffice.png")
pdfxchange_app = create_app("PDF-XChange Editor", "TrackerSoftware.PDF-XChangeEditor", "https://www.tracker-software.com/", "TrackerSoftware.PDF-XChangeEditor.png")
adobe_reader_app = create_app("Adobe Acrobat Reader", "Adobe.Acrobat.Reader.64-bit", "https://get.adobe.com/reader/", "Adobe.Acrobat.Reader.64-bit.png")
notepadplus_app = create_app("Notepad++", "Notepad++.Notepad++", "https://notepad-plus-plus.org/", "Notepad++.Notepad++.png")
notepads_app = create_app("Notepads", "JackieLiu.NotepadsApp", "https://www.notepadsapp.com/", "JackieLiu.NotepadsApp.png")
obsidian_app = create_app("Obsidian", "Obsidian.Obsidian", "https://obsidian.md/", "Obsidian.Obsidian.png")
notion_app = create_app("Notion", "Notion.Notion", "https://www.notion.so/", "Notion.Notion.png")
sumatra_app = create_app("Sumatra PDF", "SumatraPDF.SumatraPDF", "https://www.sumatrapdfreader.org/", "SumatraPDF.SumatraPDF.png")
onlyoffice_app = create_app("ONLYOFFICE", "ONLYOFFICE.DesktopEditors", "https://www.onlyoffice.com/", "ONLYOFFICE.DesktopEditors.png")
anydo_app = create_app("Any.do", "AnyDo.AnyDo", "https://www.any.do/", "AnyDo.AnyDo.png")
naps2_app = create_app("NAPS2", "Cyanfish.NAPS2", "https://www.naps2.com/", "Cyanfish.NAPS2.png")
zotero_app = create_app("Zotero", "DigitalScholar.Zotero", "https://www.zotero.org/", "DigitalScholar.Zotero.png")
affine_app = create_app("AFFiNE", "ToEverything.AFFiNE", "https://affine.pro/", "ToEverything.AFFiNE.png")

# --- Vývojářské nástroje ---
python_app = create_app("Python 3", "Python.Python.3.12", "https://www.python.org", "Python.Python.3.12.png")
vscode_app = create_app("VS Code", "Microsoft.VisualStudioCode", "https://code.visualstudio.com", "Microsoft.VisualStudioCode.png")
vscode_insiders_app = create_app("VS Code Insiders", "Microsoft.VisualStudioCode.Insiders", "https://code.visualstudio.com/insiders/", "Microsoft.VisualStudioCode.Insiders.png")
github_desktop_app = create_app("GitHub Desktop", "GitHub.GitHubDesktop", "https://desktop.github.com/", "GitHub.GitHubDesktop.png")
sublime_app = create_app("Sublime Text", "SublimeHQ.SublimeText.4", "https://www.sublimetext.com/", "SublimeHQ.SublimeText.4.png")
vs2022_app = create_app("Visual Studio 2022", "Microsoft.VisualStudio.2022.Community", "https://visualstudio.microsoft.com/", "Microsoft.VisualStudio.2022.Community.png")
nodejs_app = create_app("Node.js", "OpenJS.NodeJS", "https://nodejs.org/", "OpenJS.NodeJS.png")
githubcli_app = create_app("GitHub CLI", "GitHub.cli", "https://cli.github.com/", "GitHub.cli.png")
unity_app = create_app("Unity Hub", "Unity.UnityHub", "https://unity.com/", "Unity.UnityHub.png")
git_app = create_app("Git", "Git.Git", "https://git-scm.com/", "Git.Git.png")
mingit_app = create_app("MinGit", "Git.MinGit", "https://gitforwindows.org/", "Git.MinGit.png")
cursor_app = create_app("Cursor", "Anysphere.Cursor", "https://www.cursor.com/", "Anysphere.Cursor.png")
anaconda_app = create_app("Anaconda3", "Anaconda.Anaconda3", "https://www.anaconda.com/", "Anaconda.Anaconda3.png")
wordpress_app = create_app("WordPress.com", "Automattic.Wordpress", "https://localwp.com/", "Automattic.Wordpress.png")
sqlite_app = create_app("DB Browser for SQLite", "DBBrowserForSQLite.DBBrowserForSQLite", "https://sqlitebrowser.org/", "DBBrowserForSQLite.DBBrowserForSQLite.png")
inno_app = create_app("Inno Setup 6", "jrsoftware.InnoSetup", "https://jrsoftware.org/isinfo.php", "jrsoftware.InnoSetup.png")
vulkan_app = create_app("Vulkan SDK", "KhronosGroup.VulkanSDK", "https://vulkan.lunarg.com/", "KhronosGroup.VulkanSDK.png")
mongodb_app = create_app("MongoDB Compass", "MongoDB.Compass.Full", "https://www.mongodb.com/products/tools/compass", "MongoDB.Compass.Full.png")
ngrok_app = create_app("ngrok", "ngrok.ngrok", "https://ngrok.com/", "ngrok.ngrok.png")
r_app = create_app("R for Windows", "RProject.R", "https://www.r-project.org/", "RProject.R.png")
tailwindcss_app = create_app("Tailwind CSS", "TailwindLabs.TailwindCSS", "https://tailwindcss.com/", "TailwindLabs.TailwindCSS.png")

# --- Správa disků ---
aomei_app = create_app("AOMEI Partition Assistant", "AOMEI.PartitionAssistant", "https://www.diskpart.com/", "AOMEI.PartitionAssistant.png")
easeus_app = create_app("EaseUS Partition Master", "EaseUS.PartitionMaster", "https://www.easeus.com/partition-manager/", "EaseUS.PartitionMaster.png")
windirstat_app = create_app("WinDirStat", "WinDirStat.WinDirStat", "https://windirstat.net/", "WinDirStat.WinDirStat.png")
cdi_app = create_app("CrystalDiskInfo", "CrystalDewWorld.CrystalDiskInfo", "https://crystalmark.info/en/software/crystaldiskinfo/", "CrystalDewWorld.CrystalDiskInfo.png")
cdm_app = create_app("CrystalDiskMark", "CrystalDewWorld.CrystalDiskMark", "https://crystalmark.info/en/software/crystaldiskmark/", "CrystalDewWorld.CrystalDiskMark.png")
hdtune_app = create_app("HD Tune Pro", "EFDSoftware.HDTunePro", "https://www.hdtune.com/", "EFDSoftware.HDTunePro.png")
kingston_app = create_app("Kingston SSD Manager", "Kingston.SSDManager", "https://www.kingston.com/en/support/technical/ssdmanager", "Kingston.SSDManager.png")
rufus_app = create_app("Rufus", "Rufus.Rufus", "https://rufus.ie/", "Rufus.Rufus.png")
balena_app = create_app("balenaEtcher", "Balena.Etcher", "https://etcher.balena.io/", "Balena.Etcher.png")
rpi_imager_app = create_app("Raspberry Pi Imager", "RaspberryPiFoundation.RaspberryPiImager", "https://www.raspberrypi.com/software/", "RaspberryPiFoundation.RaspberryPiImager.png")
ventoy_app = create_app("Ventoy", "Ventoy.Ventoy", "https://www.ventoy.net/", "Ventoy.Ventoy.png")

# --- Utilities (Systémové nástroje) ---
winrar_app = create_app("WinRAR", "RARLab.WinRAR", "https://www.win-rar.com", "RARLab.WinRAR.png")
zip7_app = create_app("7-Zip", "7zip.7zip", "https://www.7-zip.org", "7zip.7zip.png")
nanazip_app = create_app("NanaZip", "M2Team.NanaZip", "https://github.com/M2Team/NanaZip", "M2Team.NanaZip.png")
zip360_app = create_app("360 Zip", "360.360Zip", "https://360zip.com/", "360.360Zip.png")
bandizip_app = create_app("Bandizip", "Bandisoft.Bandizip", "https://cz.bandisoft.com/bandizip/", "Bandisoft.Bandizip.png")
anydesk_app = create_app("AnyDesk", "AnyDesk.AnyDesk", "https://anydesk.com/", "AnyDesk.AnyDesk.png")
teamviewer_app = create_app("TeamViewer", "TeamViewer.TeamViewer", "https://www.teamviewer.com/", "TeamViewer.TeamViewer.png")
cpu_z_app = create_app("CPU-Z", "CPUID.CPU-Z", "https://www.cpuid.com/softwares/cpu-z.html", "CPUID.CPU-Z.png")
gpuz_app = create_app("GPU-Z", "TechPowerUp.GPU-Z", "https://www.techpowerup.com/gpuz/", "TechPowerUp.GPU-Z.png")
hwinfo_app = create_app("HWiNFO", "REALiX.HWiNFO", "https://www.hwinfo.com/", "REALiX.HWiNFO.png")
hwmonitor_app = create_app("HWMonitor", "CPUID.HWMonitor", "https://www.cpuid.com/softwares/hwmonitor.html", "CPUID.HWMonitor.png")
aida64_app = create_app("AIDA64 Extreme", "FinalWire.AIDA64.Extreme", "https://www.aida64.com/", "FinalWire.AIDA64.Extreme.png")
coretemp_app = create_app("Core Temp", "ALCPU.CoreTemp", "https://www.alcpu.com/CoreTemp/", "ALCPU.CoreTemp.png")
msiafterburner_app = create_app("MSI Afterburner", "Guru3D.Afterburner", "https://www.msi.com/Landing/afterburner", "Guru3D.Afterburner.png")
jdownloader_app = create_app("JDownloader 2", "AppWork.JDownloader", "https://jdownloader.org/", "AppWork.JDownloader.png")
qbittorrent_app = create_app("qBittorrent", "qBittorrent.qBittorrent", "https://www.qbittorrent.org/", "qBittorrent.qBittorrent.png")
revo_app = create_app("Revo Uninstaller", "RevoUninstaller.RevoUninstaller", "https://www.revouninstaller.com/", "RevoUninstaller.RevoUninstaller.png")
gdrive_app = create_app("Google Drive", "Google.GoogleDrive", "https://www.google.com/drive/", "Google.GoogleDrive.png")
dropbox_app = create_app("Dropbox", "Dropbox.Dropbox", "https://www.dropbox.com/", "Dropbox.Dropbox.png")
healthcheck_app = create_app("PC Health Check", "Microsoft.WindowsPCHealthCheck", "https://support.microsoft.com/", "Microsoft.WindowsPCHealthCheck.png")
fileconverter_app = create_app("File Converter", "AdrienAllard.FileConverter", "https://file-converter.org/", "AdrienAllard.FileConverter.png")
rainmeter_app = create_app("Rainmeter", "Rainmeter.Rainmeter", "https://www.rainmeter.net/", "Rainmeter.Rainmeter.png")
todoist_app = create_app("Todoist", "Doist.Todoist", "https://todoist.com/", "Doist.Todoist.png")
ahk_app = create_app("AutoHotkey", "AutoHotkey.AutoHotkey", "https://www.autohotkey.com/", "AutoHotkey.AutoHotkey.png")
totalcmd_app = create_app("Total Commander", "Ghisler.TotalCommander", "https://www.ghisler.com/", "Ghisler.TotalCommander.png")
opautoclicker_app = create_app("OP AutoClicker", "OPAutoClicker.OPAutoClicker", "https://www.opautoclicker.com/", "OPAutoClicker.OPAutoClicker.png")
unigetui_app = create_app("UniGetUI", "Devolutions.UniGetUI", "https://github.com/marticliment/UniGetUI", "Devolutions.UniGetUI.png")
everything_app = create_app("Everything", "voidtools.Everything", "https://www.voidtools.com/", "voidtools.Everything.png")
malwarebytes_app = create_app("Malwarebytes", "Malwarebytes.Malwarebytes", "https://www.malwarebytes.com/", "Malwarebytes.Malwarebytes.png")
powertoys_app = create_app("PowerToys", "Microsoft.PowerToys", "https://learn.microsoft.com/windows/powertoys/", "Microsoft.PowerToys.png")
adguard_app = create_app("AdGuard Home", "Adguard.AdguardHome", "https://adguard.com/en/adguard-home/overview.html", "Adguard.AdguardHome.png")
bleachbit_app = create_app("BleachBit", "BleachBit.BleachBit", "https://www.bleachbit.org/", "BleachBit.BleachBit.png")
bitwarden_app = create_app("Bitwarden", "Bitwarden.Bitwarden", "https://bitwarden.com/", "Bitwarden.Bitwarden.png")
iconviewer_app = create_app("IconViewer", "BotProductions.IconViewer", "https://www.botproductions.com/iconview/", "BotProductions.IconViewer.png")
deepl_app = create_app("DeepL", "DeepL.DeepL", "https://www.deepl.com/", "DeepL.DeepL.png")
eset_app = create_app("ESET Security", "ESET.Security", "https://www.eset.com/", "ESET.Security.png")
virtualclonedrive_app = create_app("VirtualCloneDrive", "ElaborateBytes.VirtualCloneDrive", "https://www.elby.ch/products/vcd.html", "ElaborateBytes.VirtualCloneDrive.png")
localsend_app = create_app("LocalSend", "LocalSend.LocalSend", "https://localsend.org/", "LocalSend.LocalSend.png")
authme_app = create_app("AuthMe", "Levminer.AuthMe", "https://github.com/Levminer/authme", "Levminer.AuthMe.png")
protonvpn_app = create_app("Proton VPN", "Proton.ProtonVPN", "https://protonvpn.com/", "Proton.ProtonVPN.png")
openvpn_app = create_app("OpenVPN", "OpenVPNTechnologies.OpenVPN", "https://openvpn.net/", "OpenVPNTechnologies.OpenVPN.png")
owncloud_app = create_app("ownCloud", "ownCloud.ownCloudDesktop", "https://owncloud.com/", "ownCloud.ownCloudDesktop.png")
registryfinder_app = create_app("Registry Finder", "SergeyFilippov.RegistryFinder", "https://registry-finder.com/", "SergeyFilippov.RegistryFinder.png")
fdm_app = create_app("Free Download Manager", "SoftDeluxe.FreeDownloadManager", "https://www.freedownloadmanager.org/", "SoftDeluxe.FreeDownloadManager.png")
spicetify_app = create_app("Spicetify", "Spicetify.Spicetify", "https://spicetify.app/", "Spicetify.Spicetify.png")
sdi_app = create_app("Snappy Driver Installer", "GlennDelahoy.SnappyDriverInstallerOrigin", "https://www.snappy-driver-installer.org/", "GlennDelahoy.SnappyDriverInstallerOrigin.png")
transmission_app = create_app("Transmission", "Transmission.Transmission", "https://transmissionbt.com/", "Transmission.Transmission.png")
eartrumpet_app = create_app("EarTrumpet", "File-New-Project.EarTrumpet", "https://eartrumpet.app/", "File-New-Project.EarTrumpet.png")


# ==============================================================================
# 2. DEFINICE SKUPIN (SOUHRNNÉ LISTY)
# ==============================================================================

_BROWSERS = [chrome_app, firefox_app, edge_app, brave_app, opera_app, opera_gx_app, vivaldi_app, zen_app, librewolf_app, ungoogled_app, waterfox_app, arc_app, tor_app, duckduckgo_app, falkon_app]
_CHAT = [discord_app, telegram_app, teams_app, teamspeak_app, teamspeak6_app, slack_app, zoom_app, thunderbird_app, betterbird_app, viber_app, beeper_app, bluemail_app]
_GAMES = [steam_app, epic_app, ubisoft_app, ea_app, gog_app, battlenet_app, curseforge_app, riot_app, wargaming_app, playnite_app, modrinth_app, psremote_app, psaccessories_app, bluestacks_app, faceit_app, faceit_ac_app, ftb_app, warthunder_app, minecraft_app, maniaplanet_app]
_NVIDIA = [geforcenow_app, cuda_app, physx_app, rtxvoice_app]
_MEDIA = [gimp_app, paint_net_app, blender_app, vlc_app, mpv_app, stremio_app, audacity_app, aimp_app, fxsound_app, obs_app, inkscape_app, irfanview_app, qview_app, krita_app, affinity_app, spotify_app, itunes_app, ytdownloader_app, honeyview_app, bandiview_app, bandicut_app, bandicam_app, capcut_app, pixso_app, deezer_app, handbrake_app, imgburn_app, fontbase_app, asio4all_app, musescore_app, pixelorama_app, spotiflyer_app, streamlabs_app]
_OFFICE = [ms_office_app, libreoffice_app, wps_app, pdfxchange_app, adobe_reader_app, notepadplus_app, notepads_app, obsidian_app, notion_app, sumatra_app, onlyoffice_app, anydo_app, naps2_app, zotero_app, affine_app]
_DISKS = [aomei_app, easeus_app, windirstat_app, hdtune_app, cdi_app, cdm_app, rufus_app, balena_app, rpi_imager_app, kingston_app, ventoy_app]
_DEV = [vscode_app, vscode_insiders_app, python_app, github_desktop_app, sublime_app, vs2022_app, nodejs_app, githubcli_app, unity_app, git_app, mingit_app, cursor_app, anaconda_app, wordpress_app, sqlite_app, inno_app, vulkan_app, mongodb_app, ngrok_app, r_app, tailwindcss_app]
_UTILITIES = [zip7_app, winrar_app, nanazip_app, zip360_app, bandizip_app, anydesk_app, teamviewer_app, cpu_z_app, gpuz_app, hwinfo_app, hwmonitor_app, aida64_app, coretemp_app, msiafterburner_app, jdownloader_app, qbittorrent_app, revo_app, gdrive_app, dropbox_app, healthcheck_app, fileconverter_app, rainmeter_app, todoist_app, ahk_app, totalcmd_app, opautoclicker_app, unigetui_app, everything_app, malwarebytes_app, powertoys_app, adguard_app, bleachbit_app, bitwarden_app, iconviewer_app, deepl_app, eset_app, virtualclonedrive_app, localsend_app, authme_app, protonvpn_app, openvpn_app, owncloud_app, registryfinder_app, fdm_app, spicetify_app, sdi_app, transmission_app, eartrumpet_app]

# ==============================================================================
# 3. HLAVNÍ KATALOG PRO UI (APP_CATEGORIES)
# ==============================================================================

APP_CATEGORIES = {
    "🌐 Prohlížeče": _BROWSERS,
    "💬 Komunikace": _CHAT,
    "🎮 Hry": _GAMES,
    "🟩 Nvidia Nástroje": _NVIDIA,
    "🎨 Média (Obraz, Zvuk, Video)": _MEDIA,
    "📄 Kancelářské aplikace": _OFFICE,
    "💽 Správa disků": _DISKS,
    "🛠️ Systémové nástroje (Utilities)": _UTILITIES,
    "💻 Vývojářské nástroje": _DEV
}

# ==============================================================================
# 4. MAPOVÁNÍ KLÍČOVÝCH SLOV PRO HLEDÁNÍ (PRESETS)
# ==============================================================================

PRESETS = {
    "hry": _GAMES,
    "browser": _BROWSERS,
    "chat": _CHAT,
    "steam": [steam_app],
    "chrome": [chrome_app],
    "python": [python_app]
}

# ==============================================================================
# 5. NAČTENÍ A APLIKACE VLASTNÍCH OPRAV ID (OVERRIDES)
# ==============================================================================

try:
    _docs_dir = Path.home() / "Documents" / "OmniDesk"
    _docs_dir.mkdir(parents=True, exist_ok=True)
    OVERRIDES_FILE = str(_docs_dir / "preset_overrides.json")

    if os.path.exists(OVERRIDES_FILE):
        with open(OVERRIDES_FILE, "r", encoding="utf-8") as f:
            overrides = json.load(f)
        
        for category_apps in APP_CATEGORIES.values():
            for app in category_apps:
                if app["id"] in overrides:
                    app["id"] = overrides[app["id"]]
except Exception as e:
    print(f"DEBUG: Nelze načíst preset_overrides.json: {e}")