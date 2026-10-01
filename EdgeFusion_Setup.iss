; ============================================================
;  EdgeFusion V4 — Script Inno Setup
;  Crée : EdgeFusion_Setup.exe
;  Prérequis : Inno Setup 6+ (https://jrsoftware.org/isdl.php)
;  Démarrage auto via Planificateur de tâches (pas de service Windows)
; ============================================================

[Setup]
AppName=Edge Fusion
AppVersion=2.0
AppPublisher=ManaTechnology
AppPublisherURL=
AppSupportURL=
AppUpdatesURL=
DefaultDirName={autopf}\EdgeFusion
DefaultGroupName=EdgeFusion
AllowNoIcons=no
OutputDir=..\installer
OutputBaseFilename=EdgeFusion_Setup
SetupIconFile=appicon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
UninstallDisplayIcon={app}\_internal\appicon.ico
UninstallDisplayName=Edge Fusion

; ============================================================
[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

; ============================================================
[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: unchecked

; ============================================================
[Files]
; Tous les fichiers buildés par PyInstaller
Source: "dist\EdgeFusion\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; ============================================================
[Dirs]
; Dossier données persistantes (config, buffer, certificats)
Name: "{commonappdata}\EdgeFusion"; Permissions: everyone-full

; ============================================================
[Icons]
; Menu Démarrer
Name: "{group}\EdgeFusion";         Filename: "{app}\EdgeFusion.exe"; IconFilename: "{app}\_internal\appicon.ico"
Name: "{group}\Désinstaller";       Filename: "{uninstallexe}"

; Bureau (optionnel)
Name: "{commondesktop}\EdgeFusion"; Filename: "{app}\EdgeFusion.exe"; IconFilename: "{app}\_internal\appicon.ico"; Tasks: desktopicon

; ============================================================
[Run]
; 1. Créer la tâche planifiée (démarrage automatique au boot)
Filename: "{app}\EdgeFusion.exe"; Parameters: "install"; \
    Flags: shellexec runhidden waituntilterminated; \
    StatusMsg: "Création de la tâche de démarrage automatique..."

; 2. Lancer EdgeFusion maintenant en arrière-plan
Filename: "{app}\EdgeFusion.exe"; Parameters: "start"; \
    Flags: shellexec runhidden waituntilterminated; \
    StatusMsg: "Démarrage d'EdgeFusion en arrière-plan..."

; 3. Lancer la GUI après installation (optionnel, coché par défaut)
Filename: "{app}\EdgeFusion.exe"; \
    Flags: shellexec nowait postinstall skipifsilent; \
    Description: "Lancer EdgeFusion maintenant"

; ============================================================
[UninstallRun]
; Arrêter EdgeFusion et supprimer la tâche planifiée
Filename: "{app}\EdgeFusion.exe"; Parameters: "stop";   Flags: shellexec runhidden waituntilterminated; RunOnceId: "StopEdgeFusion"
Filename: "{app}\EdgeFusion.exe"; Parameters: "remove"; Flags: shellexec runhidden waituntilterminated; RunOnceId: "RemoveEdgeFusion"

; ============================================================
[UninstallDelete]
; Supprimer les données générées (buffer, logs)
; NE PAS supprimer config.json → préserver la configuration
Type: files; Name: "{commonappdata}\EdgeFusion\buffer_*.json"
Type: files; Name: "{commonappdata}\EdgeFusion\stop.signal"

; ============================================================
[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
