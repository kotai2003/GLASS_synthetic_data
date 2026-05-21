; ============================================================
;  GLASS Synthesizer -- Inno Setup installer script
;  TOMOMI standard (mirrors 00.FORESIGHT_VIEWER_TR100/iss/*.iss),
;  trimmed: no license-file / file-association machinery (this app
;  has no .lic mechanism).
;
;  Build:  ISCC.exe glass_synthesizer_setup.iss
;          (or run build_all.py, which compiles this after a green build)
;
;  Input is the ONEDIR PyInstaller bundle produced OUTSIDE OneDrive at
;  C:\TR_build\GLASS\dist\GLASS_Synthesizer (override DistDir below if
;  GLASS_BUILD_ROOT was changed). Output goes to C:\TR_build\GLASS\installer.
; ============================================================

#define MyAppName "GLASS Synthesizer"
#define MyAppShortName "GLASS_Synthesizer"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TOMOMI RESEARCH, INC."
#define MyAppURL "https://www.tomomi-research.com/"
#define MyAppExeName "GLASS_Synthesizer.exe"

; --- Base paths (build output lives OUTSIDE OneDrive) ---
#define BuildRoot "C:\TR_build\GLASS"
#define DistDir BuildRoot + "\dist\GLASS_Synthesizer"
#define RepoDir "C:\Users\seong\OneDrive - Tomomi Research Inc\AI_Development\489.Synthetic_Data\01.GLASS"
#define IconFile RepoDir + "\synthesize_gui\ui\app_icon.ico"
#define LicenseTxt RepoDir + "\synthesize_gui\LICENSE"

[Setup]
; Unique AppId for GLASS Synthesizer -- do NOT reuse for other apps.
AppId={{A3F1C2D4-9B6E-4A57-8F23-1E7D5C0B9A48}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppShortName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}
; x64-only (cu118 torch bundle).
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
LicenseFile={#LicenseTxt}
OutputDir={#BuildRoot}\installer
OutputBaseFilename=GLASS_Synthesizer_Setup_V.{#MyAppVersion}
SetupIconFile={#IconFile}
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
; ONEDIR bundle is ~5.7 GB (cu118 torch + CUDA) -> exceeds the single-file
; 2 GB limit, so span across .bin volumes (default ~2100 MB slices).
DiskSpanning=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#DistDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
