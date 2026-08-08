; ============================================================================
; Assumption Zero — Windows Installer Script
; Requires Inno Setup 6+ to compile: https://jrsoftware.org/isinfo.php
;
; To build:
;   iscc setup_assumption_zero.iss
; Or run build_installer.bat in this directory.
;
; What it does:
;   1. Clones the repo from GitHub (requires Git)
;   2. Creates Python virtual environment and installs backend
;   3. Installs Node.js frontend dependencies
;   4. Creates Start Menu + Desktop shortcuts to start_web.bat
; ============================================================================

#define MyAppName "Assumption Zero"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Assumption Zero Contributors"
#define MyAppURL "https://github.com/your-org/assumption-zero"
#define MyAppGitRepo "https://github.com/your-org/assumption-zero.git"
#define MyAppExeName "start_web.bat"
#define MyInstallDir "{autopf}\AssumptionZero"

[Setup]
AppId={{A7B3C2D1-E4F5-6789-ABCD-EF0123456789}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={#MyInstallDir}
DefaultGroupName={#MyAppName}
AllowNoIcons=no
OutputDir=dist
OutputBaseFilename=AssumptionZero_Setup_{#MyAppVersion}
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableProgramGroupPage=no
DisableWelcomePage=no
ShowLanguageDialog=no
LanguageDetectionMethod=uilanguage
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\start_web.bat
CloseApplications=yes
RestartApplications=no
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checked
Name: "startmenuicon"; Description: "Create &Start Menu shortcuts"; GroupDescription: "Additional icons:"; Flags: checked

[Files]
; The installer ships an embedded copy of the repo zip downloaded from GitHub,
; OR you can place the project folder here. For simplicity we use a post-install
; script to clone from GitHub. No files are shipped in this installer.

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{cmd}"; Parameters: "/k ""{app}\start_web.bat"""; WorkingDir: "{app}"; IconFilename: "{app}\frontend\public\logo.png"; Comment: "Launch Assumption Zero Web App"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{cmd}"; Parameters: "/k ""{app}\start_web.bat"""; WorkingDir: "{app}"; Tasks: desktopicon; Comment: "Launch Assumption Zero Web App"

[Run]
; Step 1: Clone repository from GitHub
Filename: "{cmd}"; Parameters: "/c ""git clone {#MyAppGitRepo} ""{app}""""; WorkingDir: "{tmp}"; StatusMsg: "Downloading Assumption Zero from GitHub..."; Flags: runhidden waituntilterminated

; Step 2: Create Python virtual environment
Filename: "{cmd}"; Parameters: "/c ""python -m venv ""{app}\backend\.venv""""; StatusMsg: "Creating Python virtual environment..."; Flags: runhidden waituntilterminated

; Step 3: Install Python backend dependencies
Filename: "{app}\backend\.venv\Scripts\pip.exe"; Parameters: "install -e ""{app}\backend"" --quiet"; StatusMsg: "Installing backend AI engine dependencies..."; Flags: runhidden waituntilterminated

; Step 4: Install Node.js frontend dependencies
Filename: "{cmd}"; Parameters: "/c ""cd /d ""{app}\frontend"" && npm install --silent"""; StatusMsg: "Installing frontend dependencies..."; Flags: runhidden waituntilterminated

; Step 5: Copy .env template
Filename: "{cmd}"; Parameters: "/c ""copy ""{app}\.env.example"" ""{app}\.env""""; StatusMsg: "Setting up configuration file..."; Flags: runhidden waituntilterminated; Check: not FileExists(ExpandConstant('{app}\.env'))

; Step 6: Open browser to app after install (optional)
Filename: "{app}\start_web.bat"; Description: "Launch Assumption Zero now"; Flags: postinstall nowait skipifsilent shellexec

[UninstallRun]
; Kill any running server processes on uninstall
Filename: "{cmd}"; Parameters: "/c ""taskkill /f /im uvicorn.exe >nul 2>&1"""; Flags: runhidden

[Code]
// ── Pre-install checks ─────────────────────────────────────────────────────

function CheckPrerequisites(): Boolean;
var
  ResultCode: Integer;
  PythonOk, NodeOk, GitOk: Boolean;
  Msg: String;
begin
  Result := True;

  // Check Python
  PythonOk := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
  // Check Node.js
  NodeOk := Exec('node', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
  // Check Git
  GitOk := Exec('git', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);

  if not PythonOk or not NodeOk or not GitOk then
  begin
    Msg := 'The following prerequisites are missing:' + #13#10;
    if not PythonOk then Msg := Msg + '  • Python 3.12+  —  https://www.python.org/downloads/' + #13#10;
    if not NodeOk   then Msg := Msg + '  • Node.js 20+   —  https://nodejs.org/' + #13#10;
    if not GitOk    then Msg := Msg + '  • Git           —  https://git-scm.com/' + #13#10;
    Msg := Msg + #13#10 + 'Please install the missing tools and re-run the installer.';
    MsgBox(Msg, mbError, MB_OK);
    Result := False;
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := CheckPrerequisites();
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpWelcome then
    Result := CheckPrerequisites();
end;
