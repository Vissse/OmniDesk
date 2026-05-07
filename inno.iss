#define MyAppName "OmniDesk"
#define MyAppVersion "7.6.4"
#define MyAppPublisher "Vissse"
#define MyAppExeName "OmniDesk.exe"

[Setup]
; --- Základní informace ---
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

; --- Výchozí složka instalace ---
; {autopf} = Program Files (x86) nebo Program Files podle architektury
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; --- Nastavení instalátoru ---
AllowNoIcons=yes
; Název výsledného instalačního souboru
OutputBaseFilename=OmniDesk_Setup
; Cesta k ikoně instalátoru (použije tvoji existující ikonu)
SetupIconFile=assets\icons\program_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
; Vyžádá si práva správce už při spuštění instalátoru
PrivilegesRequired=admin

[Languages]
; Nastavení češtiny jako jazyka instalátoru
Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"

[Tasks]
; Checkbox pro vytvoření zástupce na ploše
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Kopírování samotného zkompilovaného EXE souboru
; Ujisti se, že jsi předtím spustil build.py a soubor ve složce dist existuje!
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Zástupce v nabídce Start
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; Odinstalační zástupce v nabídce Start
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Zástupce na ploše (pokud to uživatel zaškrtl)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Možnost spustit aplikaci hned po dokončení instalace
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec