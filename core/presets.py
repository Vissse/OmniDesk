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
DEFAULT_ICON = os.path.join(ICONS_DIR, "default-app.png")

def get_icon(filename):
    """Vrací cestu k lokální ikoně. Pokud neexistuje, vrací výchozí ikonu."""
    local_path = os.path.join(ICONS_DIR, filename)
    if os.path.exists(local_path):
        return local_path
    return DEFAULT_ICON if os.path.exists(DEFAULT_ICON) else None

# ==============================================================================
# 1. DEFINICE JEDNOTLIVÝCH APLIKACÍ
# ==============================================================================

# --- Herní Launchery & Hry ---
steam_app = {"name": "Steam", "id": "Valve.Steam", "website": "https://store.steampowered.com", "icon_url": get_icon("Valve.Steam.png")}
epic_app = {"name": "Epic Games Launcher", "id": "EpicGames.EpicGamesLauncher", "website": "https://store.epicgames.com", "icon_url": get_icon("EpicGames.EpicGamesLauncher.png")}
ubisoft_app = {"name": "Ubisoft Connect", "id": "Ubisoft.Connect", "website": "https://ubisoftconnect.com", "icon_url": get_icon("Ubisoft.Connect.png")}
ea_app = {"name": "EA App", "id": "ElectronicArts.EADesktop", "website": "https://www.ea.com/ea-app", "icon_url": get_icon("ElectronicArts.EADesktop.png")}
gog_app = {"name": "GOG GALAXY", "id": "GOG.Galaxy", "website": "https://www.gog.com/galaxy", "icon_url": get_icon("GOG.Galaxy.png")}
playnite_app = {"name": "Playnite", "id": "Playnite.Playnite", "website": "https://playnite.link", "icon_url": get_icon("Playnite.Playnite.png")}
battlenet_app = {"name": "Battle.net", "id": "Blizzard.BattleNet", "website": "https://www.blizzard.com", "icon_url": get_icon("Blizzard.BattleNet.png")}
curseforge_app = {"name": "CurseForge", "id": "Overwolf.CurseForge", "website": "https://www.curseforge.com", "icon_url": get_icon("Overwolf.CurseForge.png")}
riot_app = {"name": "Riot Client", "id": "RiotGames.LeagueOfLegends.EUNE", "website": "https://www.riotgames.com", "icon_url": get_icon("RiotGames.LeagueOfLegends.EUNE.png")}
wargaming_app = {"name": "Wargaming.net", "id": "Wargaming.GameCenter", "website": "https://wargaming.net", "icon_url": get_icon("Wargaming.GameCenter.png")}
modrinth_app = {"name": "Modrinth App", "id": "Modrinth.ModrinthApp", "website": "https://modrinth.com/app", "icon_url": get_icon("Modrinth.ModrinthApp.png")}
psremote_app = {"name": "PS Remote Play", "id": "PlayStation.PSRemotePlay", "website": "https://remoteplay.dl.playstation.net/remoteplay/", "icon_url": get_icon("PlayStation.PSRemotePlay.png")}
psaccessories_app = {"name": "PlayStation Accessories", "id": "PlayStation.PlayStationAccessories", "website": "https://controller.dl.playstation.net/controller/", "icon_url": get_icon("PlayStation.PlayStationAccessories.png")}
bluestacks_app = {"name": "BlueStacks 5", "id": "BlueStack.BlueStacks", "website": "https://www.bluestacks.com/", "icon_url": get_icon("BlueStack.BlueStacks.png")}
faceit_app = {"name": "FACEIT", "id": "FACEITLTD.FACEITClient", "website": "https://www.faceit.com/", "icon_url": get_icon("FACEITLTD.FACEITClient.png")}
faceit_ac_app = {"name": "FACEIT Anti-Cheat", "id": "FACEITLTD.FACEITAC", "website": "https://www.faceit.com/en/anti-cheat", "icon_url": get_icon("FACEITLTD.FACEITClient.png")}
ftb_app = {"name": "FTB Electron App", "id": "FTB.App", "website": "https://feed-the-beast.com/", "icon_url": get_icon("FeedTheBeast.FTBApp.png")}
warthunder_app = {"name": "War Thunder", "id": "GaijinNetwork.WarThunder", "website": "https://warthunder.com/", "icon_url": get_icon("GaijinNetwork.WarThunder.png")}
minecraft_app = {"name": "Minecraft Launcher", "id": "Mojang.MinecraftLauncher", "website": "https://www.minecraft.net/", "icon_url": get_icon("Mojang.MinecraftLauncher.png")}
maniaplanet_app = {"name": "ManiaPlanet", "id": "Nadeo.ManiaPlanet", "website": "https://www.maniaplanet.com/", "icon_url": get_icon("Nadeo.ManiaPlanet.png")}

# --- Nvidia Nástroje ---
geforcenow_app = {"name": "GeForce NOW", "id": "Nvidia.GeForceNOW", "website": "https://www.nvidia.com/en-us/geforce-now/", "icon_url": get_icon("Nvidia.GeForceNOW.png")}
cuda_app = {"name": "CUDA Toolkit", "id": "Nvidia.CUDA", "website": "https://developer.nvidia.com/cuda-toolkit", "icon_url": get_icon("Nvidia.GeForceNOW.png")}
physx_app = {"name": "NVIDIA PhysX", "id": "Nvidia.PhysX", "website": "https://www.nvidia.com/", "icon_url": get_icon("Nvidia.GeForceNOW.png")}
rtxvoice_app = {"name": "NVIDIA RTX Voice", "id": "Nvidia.RTXVoice", "website": "https://www.nvidia.com/", "icon_url": get_icon("Nvidia.GeForceNOW.png")}

# --- Prohlížeče ---
chrome_app = {"name": "Google Chrome", "id": "Google.Chrome", "website": "https://www.google.com/chrome", "icon_url": get_icon("Google.Chrome.png")}
firefox_app = {"name": "Mozilla Firefox", "id": "Mozilla.Firefox", "website": "https://www.mozilla.org/firefox", "icon_url": get_icon("Mozilla.Firefox.png")}
edge_app = {"name": "Microsoft Edge", "id": "Microsoft.Edge", "website": "https://www.microsoft.com/edge", "icon_url": get_icon("Microsoft.Edge.png")}
brave_app = {"name": "Brave Browser", "id": "Brave.Brave", "website": "https://brave.com", "icon_url": get_icon("Brave.Brave.png")}
opera_app = {"name": "Opera", "id": "Opera.Opera", "website": "https://www.opera.com", "icon_url": get_icon("Opera.Opera.png")}
opera_gx_app = {"name": "Opera GX", "id": "Opera.OperaGX", "website": "https://www.opera.com/gx", "icon_url": get_icon("Opera.OperaGX.png")}
vivaldi_app = {"name": "Vivaldi", "id": "Vivaldi.Vivaldi", "website": "https://vivaldi.com", "icon_url": get_icon("Vivaldi.Vivaldi.png")}
zen_app = {"name": "Zen Browser", "id": "Zen-Team.Zen-Browser", "website": "https://www.zen-browser.app", "icon_url": get_icon("Zen-Team.Zen-Browser.png")}
librewolf_app = {"name": "LibreWolf", "id": "LibreWolf.LibreWolf", "website": "https://librewolf.net", "icon_url": get_icon("LibreWolf.LibreWolf.png")}
ungoogled_app = {"name": "Ungoogled Chromium", "id": "eloston.ungoogled-chromium", "website": "https://github.com/ungoogled-software/ungoogled-chromium", "icon_url": get_icon("eloston.ungoogled-chromium.png")}
waterfox_app = {"name": "Waterfox", "id": "Waterfox.Waterfox", "website": "https://www.waterfox.net", "icon_url": get_icon("Waterfox.Waterfox.png")}
arc_app = {"name": "Arc", "id": "TheBrowserCompany.Arc", "website": "https://arc.net/", "icon_url": get_icon("TheBrowserCompany.Arc.png")}
tor_app = {"name": "Tor Browser", "id": "TorProject.TorBrowser", "website": "https://www.torproject.org/", "icon_url": get_icon("TorProject.TorBrowser.png")}
duckduckgo_app = {"name": "DuckDuckGo", "id": "DuckDuckGo.DesktopBrowser", "website": "https://duckduckgo.com/windows", "icon_url": get_icon("DuckDuckGo.DesktopBrowser.png")}
falkon_app = {"name": "Falkon", "id": "KDE.Falkon", "website": "https://www.falkon.org/", "icon_url": get_icon("KDE.Falkon.png")}

# --- Komunikace ---
discord_app = {"name": "Discord", "id": "Discord.Discord", "website": "https://discord.com", "icon_url": get_icon("Discord.Discord.png")}
telegram_app = {"name": "Telegram", "id": "Telegram.TelegramDesktop", "website": "https://desktop.telegram.org", "icon_url": get_icon("Telegram.TelegramDesktop.png")}
teams_app = {"name": "Teams", "id": "Microsoft.Teams", "website": "https://www.microsoft.com/microsoft-teams", "icon_url": get_icon("Microsoft.Teams.png")}
teamspeak_app = {"name": "TeamSpeak 3", "id": "TeamSpeakSystems.TeamSpeakClient", "website": "https://teamspeak.com/", "icon_url": get_icon("TeamSpeakSystems.TeamSpeakClient.png")}
teamspeak6_app = {"name": "TeamSpeak 6", "id": "TeamSpeakSystems.TeamSpeakClient.Beta.6", "website": "https://teamspeak.com/", "icon_url": get_icon("TeamSpeakSystems.TeamSpeakClient.Beta.6.png")}
slack_app = {"name": "Slack", "id": "SlackTechnologies.Slack", "website": "https://slack.com/", "icon_url": get_icon("SlackTechnologies.Slack.png")}
zoom_app = {"name": "Zoom", "id": "Zoom.Zoom", "website": "https://zoom.us/", "icon_url": get_icon("Zoom.Zoom.png")}
thunderbird_app = {"name": "Thunderbird", "id": "Mozilla.Thunderbird", "website": "https://www.thunderbird.net/", "icon_url": get_icon("Mozilla.Thunderbird.png")}
betterbird_app = {"name": "Betterbird", "id": "Betterbird.Betterbird", "website": "https://www.betterbird.eu/", "icon_url": get_icon("Betterbird.Betterbird.png")}
viber_app = {"name": "Viber", "id": "Rakuten.Viber", "website": "https://www.viber.com/", "icon_url": get_icon("Rakuten.Viber.png")}
beeper_app = {"name": "Beeper", "id": "Beeper.Beeper", "website": "https://www.beeper.com/", "icon_url": get_icon("Beeper.Beeper.png")}
bluemail_app = {"name": "BlueMail", "id": "Blix.BlueMail", "website": "https://bluemail.me/", "icon_url": get_icon("Blix.BlueMail.png")}

# --- Média (Audio, Video, Grafika) ---
gimp_app = {"name": "GIMP", "id": "GIMP.GIMP.3", "website": "https://www.gimp.org", "icon_url": get_icon("GIMP.GIMP.3.png")}
paint_net_app = {"name": "Paint.NET", "id": "dotPDN.PaintDotNet", "website": "https://www.getpaint.net", "icon_url": get_icon("dotPDN.PaintDotNet.png")}
blender_app = {"name": "Blender", "id": "BlenderFoundation.Blender", "website": "https://www.blender.org", "icon_url": get_icon("BlenderFoundation.Blender.png")}
vlc_app = {"name": "VLC media player", "id": "VideoLAN.VLC", "website": "https://www.videolan.org/vlc", "icon_url": get_icon("VideoLAN.VLC.png")}
mpv_app = {"name": "mpv", "id": "shinchiro.mpv", "website": "https://mpv.io/", "icon_url": get_icon("shinchiro.mpv.png")}
stremio_app = {"name": "Stremio", "id": "Stremio.Stremio", "website": "https://www.stremio.com/", "icon_url": get_icon("Stremio.Stremio.png")}
audacity_app = {"name": "Audacity", "id": "Audacity.Audacity", "website": "https://www.audacityteam.org", "icon_url": get_icon("Audacity.Audacity.png")}
aimp_app = {"name": "AIMP", "id": "AIMP.AIMP", "website": "https://www.aimp.ru/", "icon_url": get_icon("AIMP.AIMP.png")}
fxsound_app = {"name": "FxSound", "id": "FxSound.FxSound", "website": "https://www.fxsound.com/", "icon_url": get_icon("FxSound.FxSound.png")}
obs_app = {"name": "OBS Studio", "id": "OBSProject.OBSStudio", "website": "https://obsproject.com/", "icon_url": get_icon("OBSProject.OBSStudio.png")}
inkscape_app = {"name": "Inkscape", "id": "Inkscape.Inkscape", "website": "https://inkscape.org/", "icon_url": get_icon("Inkscape.Inkscape.png")}
irfanview_app = {"name": "IrfanView", "id": "IrfanSkiljan.IrfanView", "website": "https://www.irfanview.com/", "icon_url": get_icon("IrfanSkiljan.IrfanView.png")}
krita_app = {"name": "Krita", "id": "KDE.Krita", "website": "https://krita.org/", "icon_url": get_icon("KDE.Krita.png")}
affinity_app = {"name": "Affinity", "id": "Canva.Affinity", "website": "https://affinity.serif.com/", "icon_url": get_icon("Canva.Affinity.png")}
spotify_app = {"name": "Spotify", "id": "Spotify.Spotify", "website": "https://www.spotify.com/", "icon_url": get_icon("Spotify.Spotify.png")}
itunes_app = {"name": "iTunes", "id": "Apple.iTunes", "website": "https://www.apple.com/itunes/", "icon_url": get_icon("Apple.iTunes.png")}
ytdownloader_app = {"name": "4K Video Downloader", "id": "OpenMedia.4KVideoDownloader", "website": "https://www.4kdownload.com/", "icon_url": get_icon("OpenMedia.4KVideoDownloader.png")}
honeyview_app = {"name": "Honeyview", "id": "Bandisoft.Honeyview", "website": "https://cz.bandisoft.com/honeyview/", "icon_url": get_icon("Bandisoft.Honeyview.png")}
bandiview_app = {"name": "BandiView", "id": "Bandisoft.BandiView", "website": "https://www.bandisoft.com/bandiview/", "icon_url": get_icon("Bandisoft.BandiView.png")}
bandicut_app = {"name": "Bandicut", "id": "BandicamCompany.Bandicut", "website": "https://www.bandicam.com/bandicut-video-cutter/", "icon_url": get_icon("BandicamCompany.Bandicut.png")}
bandicam_app = {"name": "Bandicam", "id": "BandicamCompany.Bandicam", "website": "https://www.bandicam.com/", "icon_url": get_icon("BandicamCompany.Bandicam.png")}
capcut_app = {"name": "CapCut", "id": "ByteDance.CapCut", "website": "https://www.capcut.com/", "icon_url": get_icon("ByteDance.CapCut.png")}
pixso_app = {"name": "Pixso", "id": "Bosyun.Pixso", "website": "https://pixso.net/", "icon_url": get_icon("Bosyun.Pixso.png")}
deezer_app = {"name": "Deezer", "id": "Deezer.Deezer", "website": "https://www.deezer.com/", "icon_url": get_icon("Deezer.Deezer.png")}
handbrake_app = {"name": "HandBrake", "id": "Handbrake.Handbrake", "website": "https://handbrake.fr/", "icon_url": get_icon("Handbrake.Handbrake.png")}
qview_app = {"name": "qView", "id": "jurplel.qView", "website": "https://interversehq.com/qview/", "icon_url": get_icon("jurplel.qView.png")}
imgburn_app = {"name": "ImgBurn", "id": "LIGHTNINGUK.ImgBurn", "website": "https://www.imgburn.com/", "icon_url": get_icon("LIGHTNINGUK.ImgBurn.png")}
fontbase_app = {"name": "FontBase", "id": "Levitsky.FontBase", "website": "https://fontba.se/", "icon_url": get_icon("Levitsky.FontBase.png")}
asio4all_app = {"name": "ASIO4ALL", "id": "MichaelTippach.ASIO4ALL", "website": "https://www.asio4all.org/", "icon_url": get_icon("MichaelTippach.ASIO4ALL.png")}
musescore_app = {"name": "MuseScore", "id": "Musescore.Musescore", "website": "https://musescore.org/", "icon_url": get_icon("Musescore.Musescore.png")}
pixelorama_app = {"name": "Pixelorama", "id": "OramaInteractive.Pixelorama", "website": "https://orama-interactive.itch.io/pixelorama", "icon_url": get_icon("OramaInteractive.Pixelorama.png")}
spotiflyer_app = {"name": "SpotiFlyer", "id": "Shabinder.SpotiFlyer", "website": "https://github.com/Shabinder/SpotiFlyer", "icon_url": get_icon("Shabinder.SpotiFlyer.png")}
streamlabs_app = {"name": "Streamlabs", "id": "Streamlabs.Streamlabs", "website": "https://streamlabs.com/", "icon_url": get_icon("Streamlabs.Streamlabs.png")}

# --- Kancelář, PDF & Text ---
ms_office_app = {"name": "Microsoft 365", "id": "Microsoft.OfficeDeploymentTool", "website": "https://office.com", "icon_url": get_icon("Microsoft.OfficeDeploymentTool.png")}
libreoffice_app = {"name": "LibreOffice", "id": "TheDocumentFoundation.LibreOffice", "website": "https://www.libreoffice.org/", "icon_url": get_icon("TheDocumentFoundation.LibreOffice.png")}
wps_app = {"name": "WPS Office", "id": "Kingsoft.WPSOffice", "website": "https://www.wps.com/", "icon_url": get_icon("Kingsoft.WPSOffice.png")}
pdfxchange_app = {"name": "PDF-XChange Editor", "id": "TrackerSoftware.PDF-XChangeEditor", "website": "https://www.tracker-software.com/", "icon_url": get_icon("TrackerSoftware.PDF-XChangeEditor.png")}
adobe_reader_app = {"name": "Adobe Acrobat Reader", "id": "Adobe.Acrobat.Reader.64-bit", "website": "https://get.adobe.com/reader/", "icon_url": get_icon("Adobe.Acrobat.Reader.64-bit.png")}
notepadplus_app = {"name": "Notepad++", "id": "Notepad++.Notepad++", "website": "https://notepad-plus-plus.org/", "icon_url": get_icon("Notepad++.Notepad++.png")}
notepads_app = {"name": "Notepads", "id": "JackieLiu.NotepadsApp", "website": "https://www.notepadsapp.com/", "icon_url": get_icon("JackieLiu.NotepadsApp.png")}
obsidian_app = {"name": "Obsidian", "id": "Obsidian.Obsidian", "website": "https://obsidian.md/", "icon_url": get_icon("Obsidian.Obsidian.png")}
notion_app = {"name": "Notion", "id": "Notion.Notion", "website": "https://www.notion.so/", "icon_url": get_icon("Notion.Notion.png")}
sumatra_app = {"name": "Sumatra PDF", "id": "SumatraPDF.SumatraPDF", "website": "https://www.sumatrapdfreader.org/", "icon_url": get_icon("SumatraPDF.SumatraPDF.png")}
onlyoffice_app = {"name": "ONLYOFFICE", "id": "ONLYOFFICE.DesktopEditors", "website": "https://www.onlyoffice.com/", "icon_url": get_icon("ONLYOFFICE.DesktopEditors.png")}
anydo_app = {"name": "Any.do", "id": "AnyDo.AnyDo", "website": "https://www.any.do/", "icon_url": get_icon("AnyDo.AnyDo.png")}
naps2_app = {"name": "NAPS2", "id": "Cyanfish.NAPS2", "website": "https://www.naps2.com/", "icon_url": get_icon("Cyanfish.NAPS2.png")}
zotero_app = {"name": "Zotero", "id": "DigitalScholar.Zotero", "website": "https://www.zotero.org/", "icon_url": get_icon("DigitalScholar.Zotero.png")}
affine_app = {"name": "AFFiNE", "id": "ToEverything.AFFiNE", "website": "https://affine.pro/", "icon_url": get_icon("ToEverything.AFFiNE.png")}

# --- Vývojářské nástroje ---
python_app = {"name": "Python 3", "id": "Python.Python.3.12", "website": "https://www.python.org", "icon_url": get_icon("Python.Python.3.12.png")}
vscode_app = {"name": "VS Code", "id": "Microsoft.VisualStudioCode", "website": "https://code.visualstudio.com", "icon_url": get_icon("Microsoft.VisualStudioCode.png")}
vscode_insiders_app = {"name": "VS Code Insiders", "id": "Microsoft.VisualStudioCode.Insiders", "website": "https://code.visualstudio.com/insiders/", "icon_url": get_icon("Microsoft.VisualStudioCode.Insiders.png")}
github_desktop_app = {"name": "GitHub Desktop", "id": "GitHub.GitHubDesktop", "website": "https://desktop.github.com/", "icon_url": get_icon("GitHub.GitHubDesktop.png")}
sublime_app = {"name": "Sublime Text", "id": "SublimeHQ.SublimeText.4", "website": "https://www.sublimetext.com/", "icon_url": get_icon("SublimeHQ.SublimeText.4.png")}
vs2022_app = {"name": "Visual Studio 2022", "id": "Microsoft.VisualStudio.2022.Community", "website": "https://visualstudio.microsoft.com/", "icon_url": get_icon("Microsoft.VisualStudio.2022.Community.png")}
nodejs_app = {"name": "Node.js", "id": "OpenJS.NodeJS", "website": "https://nodejs.org/", "icon_url": get_icon("OpenJS.NodeJS.png")}
githubcli_app = {"name": "GitHub CLI", "id": "GitHub.cli", "website": "https://cli.github.com/", "icon_url": get_icon("GitHub.cli.png")}
unity_app = {"name": "Unity Hub", "id": "Unity.UnityHub", "website": "https://unity.com/", "icon_url": get_icon("Unity.UnityHub.png")}
git_app = {"name": "Git", "id": "Git.Git", "website": "https://git-scm.com/", "icon_url": get_icon("Git.Git.png")}
mingit_app = {"name": "MinGit", "id": "Git.MinGit", "website": "https://gitforwindows.org/", "icon_url": get_icon("Git.MinGit.png")}
cursor_app = {"name": "Cursor", "id": "Anysphere.Cursor", "website": "https://www.cursor.com/", "icon_url": get_icon("Anysphere.Cursor.png")}
anaconda_app = {"name": "Anaconda3", "id": "Anaconda.Anaconda3", "website": "https://www.anaconda.com/", "icon_url": get_icon("Anaconda.Anaconda3.png")}
wordpress_app = {"name": "WordPress.com", "id": "Automattic.Wordpress", "website": "https://localwp.com/", "icon_url": get_icon("Automattic.Wordpress.png")}
sqlite_app = {"name": "DB Browser for SQLite", "id": "DBBrowserForSQLite.DBBrowserForSQLite", "website": "https://sqlitebrowser.org/", "icon_url": get_icon("DBBrowserForSQLite.DBBrowserForSQLite.png")}
inno_app = {"name": "Inno Setup 6", "id": "jrsoftware.InnoSetup", "website": "https://jrsoftware.org/isinfo.php", "icon_url": get_icon("jrsoftware.InnoSetup.png")}
vulkan_app = {"name": "Vulkan SDK", "id": "KhronosGroup.VulkanSDK", "website": "https://vulkan.lunarg.com/", "icon_url": get_icon("KhronosGroup.VulkanSDK.png")}
mongodb_app = {"name": "MongoDB Compass", "id": "MongoDB.Compass.Full", "website": "https://www.mongodb.com/products/tools/compass", "icon_url": get_icon("MongoDB.Compass.Full.png")}
ngrok_app = {"name": "ngrok", "id": "ngrok.ngrok", "website": "https://ngrok.com/", "icon_url": get_icon("ngrok.ngrok.png")}
r_app = {"name": "R for Windows", "id": "RProject.R", "website": "https://www.r-project.org/", "icon_url": get_icon("RProject.R.png")}
tailwindcss_app = {"name": "Tailwind CSS", "id": "TailwindLabs.TailwindCSS", "website": "https://tailwindcss.com/", "icon_url": get_icon("TailwindLabs.TailwindCSS.png")}

# --- Správa disků ---
aomei_app = {"name": "AOMEI Partition Assistant", "id": "AOMEI.PartitionAssistant", "website": "https://www.diskpart.com/", "icon_url": get_icon("AOMEI.PartitionAssistant.png")}
easeus_app = {"name": "EaseUS Partition Master", "id": "EaseUS.PartitionMaster", "website": "https://www.easeus.com/partition-manager/", "icon_url": get_icon("EaseUS.PartitionMaster.png")}
windirstat_app = {"name": "WinDirStat", "id": "WinDirStat.WinDirStat", "website": "https://windirstat.net/", "icon_url": get_icon("WinDirStat.WinDirStat.png")}
cdi_app = {"name": "CrystalDiskInfo", "id": "CrystalDewWorld.CrystalDiskInfo", "website": "https://crystalmark.info/en/software/crystaldiskinfo/", "icon_url": get_icon("CrystalDewWorld.CrystalDiskInfo.png")}
cdm_app = {"name": "CrystalDiskMark", "id": "CrystalDewWorld.CrystalDiskMark", "website": "https://crystalmark.info/en/software/crystaldiskmark/", "icon_url": get_icon("CrystalDewWorld.CrystalDiskMark.png")}
hdtune_app = {"name": "HD Tune Pro", "id": "EFDSoftware.HDTunePro", "website": "https://www.hdtune.com/", "icon_url": get_icon("EFDSoftware.HDTunePro.png")}
kingston_app = {"name": "Kingston SSD Manager", "id": "Kingston.SSDManager", "website": "https://www.kingston.com/en/support/technical/ssdmanager", "icon_url": get_icon("Kingston.SSDManager.png")}
rufus_app = {"name": "Rufus", "id": "Rufus.Rufus", "website": "https://rufus.ie/", "icon_url": get_icon("Rufus.Rufus.png")}
balena_app = {"name": "balenaEtcher", "id": "Balena.Etcher", "website": "https://etcher.balena.io/", "icon_url": get_icon("Balena.Etcher.png")}
rpi_imager_app = {"name": "Raspberry Pi Imager", "id": "RaspberryPiFoundation.RaspberryPiImager", "website": "https://www.raspberrypi.com/software/", "icon_url": get_icon("RaspberryPiFoundation.RaspberryPiImager.png")}
ventoy_app = {"name": "Ventoy", "id": "Ventoy.Ventoy", "website": "https://www.ventoy.net/", "icon_url": get_icon("Ventoy.Ventoy.png")}

# --- Utilities (Systémové nástroje) ---
winrar_app = {"name": "WinRAR", "id": "RARLab.WinRAR", "website": "https://www.win-rar.com", "icon_url": get_icon("RARLab.WinRAR.png")}
zip7_app = {"name": "7-Zip", "id": "7zip.7zip", "website": "https://www.7-zip.org", "icon_url": get_icon("7zip.7zip.png")}
nanazip_app = {"name": "NanaZip", "id": "M2Team.NanaZip", "website": "https://github.com/M2Team/NanaZip", "icon_url": get_icon("M2Team.NanaZip.png")}
zip360_app = {"name": "360 Zip", "id": "360.360Zip", "website": "https://360zip.com/", "icon_url": get_icon("360.360Zip.png")}
bandizip_app = {"name": "Bandizip", "id": "Bandisoft.Bandizip", "website": "https://cz.bandisoft.com/bandizip/", "icon_url": get_icon("Bandisoft.Bandizip.png")}
anydesk_app = {"name": "AnyDesk", "id": "AnyDesk.AnyDesk", "website": "https://anydesk.com/", "icon_url": get_icon("AnyDesk.AnyDesk.png")}
teamviewer_app = {"name": "TeamViewer", "id": "TeamViewer.TeamViewer", "website": "https://www.teamviewer.com/", "icon_url": get_icon("TeamViewer.TeamViewer.png")}
cpu_z_app = {"name": "CPU-Z", "id": "CPUID.CPU-Z", "website": "https://www.cpuid.com/softwares/cpu-z.html", "icon_url": get_icon("CPUID.CPU-Z.png")}
gpuz_app = {"name": "GPU-Z", "id": "TechPowerUp.GPU-Z", "website": "https://www.techpowerup.com/gpuz/", "icon_url": get_icon("TechPowerUp.GPU-Z.png")}
hwinfo_app = {"name": "HWiNFO", "id": "REALiX.HWiNFO", "website": "https://www.hwinfo.com/", "icon_url": get_icon("REALiX.HWiNFO.png")}
hwmonitor_app = {"name": "HWMonitor", "id": "CPUID.HWMonitor", "website": "https://www.cpuid.com/softwares/hwmonitor.html", "icon_url": get_icon("CPUID.HWMonitor.png")}
aida64_app = {"name": "AIDA64 Extreme", "id": "FinalWire.AIDA64.Extreme", "website": "https://www.aida64.com/", "icon_url": get_icon("FinalWire.AIDA64.Extreme.png")}
coretemp_app = {"name": "Core Temp", "id": "ALCPU.CoreTemp", "website": "https://www.alcpu.com/CoreTemp/", "icon_url": get_icon("ALCPU.CoreTemp.png")}
msiafterburner_app = {"name": "MSI Afterburner", "id": "Guru3D.Afterburner", "website": "https://www.msi.com/Landing/afterburner", "icon_url": get_icon("Guru3D.Afterburner.png")}
jdownloader_app = {"name": "JDownloader 2", "id": "AppWork.JDownloader", "website": "https://jdownloader.org/", "icon_url": get_icon("AppWork.JDownloader.png")}
qbittorrent_app = {"name": "qBittorrent", "id": "qBittorrent.qBittorrent", "website": "https://www.qbittorrent.org/", "icon_url": get_icon("qBittorrent.qBittorrent.png")}
revo_app = {"name": "Revo Uninstaller", "id": "RevoUninstaller.RevoUninstaller", "website": "https://www.revouninstaller.com/", "icon_url": get_icon("RevoUninstaller.RevoUninstaller.png")}
gdrive_app = {"name": "Google Drive", "id": "Google.GoogleDrive", "website": "https://www.google.com/drive/", "icon_url": get_icon("Google.GoogleDrive.png")}
dropbox_app = {"name": "Dropbox", "id": "Dropbox.Dropbox", "website": "https://www.dropbox.com/", "icon_url": get_icon("Dropbox.Dropbox.png")}
healthcheck_app = {"name": "PC Health Check", "id": "Microsoft.WindowsPCHealthCheck", "website": "https://support.microsoft.com/", "icon_url": get_icon("Microsoft.WindowsPCHealthCheck.png")}
fileconverter_app = {"name": "File Converter", "id": "AdrienAllard.FileConverter", "website": "https://file-converter.org/", "icon_url": get_icon("AdrienAllard.FileConverter.png")}
rainmeter_app = {"name": "Rainmeter", "id": "Rainmeter.Rainmeter", "website": "https://www.rainmeter.net/", "icon_url": get_icon("Rainmeter.Rainmeter.png")}
todoist_app = {"name": "Todoist", "id": "Doist.Todoist", "website": "https://todoist.com/", "icon_url": get_icon("Doist.Todoist.png")}
ahk_app = {"name": "AutoHotkey", "id": "AutoHotkey.AutoHotkey", "website": "https://www.autohotkey.com/", "icon_url": get_icon("AutoHotkey.AutoHotkey.png")}
totalcmd_app = {"name": "Total Commander", "id": "Ghisler.TotalCommander", "website": "https://www.ghisler.com/", "icon_url": get_icon("Ghisler.TotalCommander.png")}
opautoclicker_app = {"name": "OP AutoClicker", "id": "OPAutoClicker.OPAutoClicker", "website": "https://www.opautoclicker.com/", "icon_url": get_icon("OPAutoClicker.OPAutoClicker.png")}
unigetui_app = {"name": "UniGetUI", "id": "Devolutions.UniGetUI", "website": "https://github.com/marticliment/UniGetUI", "icon_url": get_icon("Devolutions.UniGetUI.png")}
everything_app = {"name": "Everything", "id": "voidtools.Everything", "website": "https://www.voidtools.com/", "icon_url": get_icon("voidtools.Everything.png")}
malwarebytes_app = {"name": "Malwarebytes", "id": "Malwarebytes.Malwarebytes", "website": "https://www.malwarebytes.com/", "icon_url": get_icon("Malwarebytes.Malwarebytes.png")}
powertoys_app = {"name": "PowerToys", "id": "Microsoft.PowerToys", "website": "https://learn.microsoft.com/windows/powertoys/", "icon_url": get_icon("Microsoft.PowerToys.png")}
adguard_app = {"name": "AdGuard Home", "id": "Adguard.AdguardHome", "website": "https://adguard.com/en/adguard-home/overview.html", "icon_url": get_icon("Adguard.AdguardHome.png")}
bleachbit_app = {"name": "BleachBit", "id": "BleachBit.BleachBit", "website": "https://www.bleachbit.org/", "icon_url": get_icon("BleachBit.BleachBit.png")}
bitwarden_app = {"name": "Bitwarden", "id": "Bitwarden.Bitwarden", "website": "https://bitwarden.com/", "icon_url": get_icon("Bitwarden.Bitwarden.png")}
iconviewer_app = {"name": "IconViewer", "id": "BotProductions.IconViewer", "website": "https://www.botproductions.com/iconview/", "icon_url": get_icon("BotProductions.IconViewer.png")}
deepl_app = {"name": "DeepL", "id": "DeepL.DeepL", "website": "https://www.deepl.com/", "icon_url": get_icon("DeepL.DeepL.png")}
eset_app = {"name": "ESET Security", "id": "ESET.Security", "website": "https://www.eset.com/", "icon_url": get_icon("ESET.Security.png")}
virtualclonedrive_app = {"name": "VirtualCloneDrive", "id": "ElaborateBytes.VirtualCloneDrive", "website": "https://www.elby.ch/products/vcd.html", "icon_url": get_icon("ElaborateBytes.VirtualCloneDrive.png")}
localsend_app = {"name": "LocalSend", "id": "LocalSend.LocalSend", "website": "https://localsend.org/", "icon_url": get_icon("LocalSend.LocalSend.png")}
authme_app = {"name": "AuthMe", "id": "Levminer.AuthMe", "website": "https://github.com/Levminer/authme", "icon_url": get_icon("Levminer.AuthMe.png")}
protonvpn_app = {"name": "Proton VPN", "id": "Proton.ProtonVPN", "website": "https://protonvpn.com/", "icon_url": get_icon("Proton.ProtonVPN.png")}
openvpn_app = {"name": "OpenVPN", "id": "OpenVPNTechnologies.OpenVPN", "website": "https://openvpn.net/", "icon_url": get_icon("OpenVPNTechnologies.OpenVPN.png")}
owncloud_app = {"name": "ownCloud", "id": "ownCloud.ownCloudDesktop", "website": "https://owncloud.com/", "icon_url": get_icon("ownCloud.ownCloudDesktop.png")}
registryfinder_app = {"name": "Registry Finder", "id": "SergeyFilippov.RegistryFinder", "website": "https://registry-finder.com/", "icon_url": get_icon("SergeyFilippov.RegistryFinder.png")}
fdm_app = {"name": "Free Download Manager", "id": "SoftDeluxe.FreeDownloadManager", "website": "https://www.freedownloadmanager.org/", "icon_url": get_icon("SoftDeluxe.FreeDownloadManager.png")}
spicetify_app = {"name": "Spicetify", "id": "Spicetify.Spicetify", "website": "https://spicetify.app/", "icon_url": get_icon("Spicetify.Spicetify.png")}
sdi_app = {"name": "Snappy Driver Installer", "id": "GlennDelahoy.SnappyDriverInstallerOrigin", "website": "https://www.snappy-driver-installer.org/", "icon_url": get_icon("GlennDelahoy.SnappyDriverInstallerOrigin.png")}
transmission_app = {"name": "Transmission", "id": "Transmission.Transmission", "website": "https://transmissionbt.com/", "icon_url": get_icon("Transmission.Transmission.png")}
eartrumpet_app = {"name": "EarTrumpet", "id": "File-New-Project.EarTrumpet", "website": "https://eartrumpet.app/", "icon_url": get_icon("File-New-Project.EarTrumpet.png")}


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