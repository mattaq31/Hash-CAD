; Hash-CAD Windows Installer Script for Inno Setup
; This script creates a professional Windows installer for Hash-CAD

#define MyAppName "Hash-CAD"
#define MyAppPublisher "Shih Lab, Harvard University"
#define MyAppURL "https://hash-cad.readthedocs.io/"
#define MyAppExeName "hash_cad.exe"

; Version is passed via command line: /DMyAppVersion=0.4.5
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

[Setup]
; Unique identifier for this application (generated via uuidgen)
AppId={{51880774-9633-4A42-9570-6A2E7DE0C03A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL=https://github.com/mattaq31/Hash-CAD/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; Allow user to disable Start Menu group creation
AllowNoIcons=yes
; License file (optional - uncomment if you have one)
; LicenseFile=..\..\LICENSE
; Output settings
OutputDir=..\..\build\windows\installer
OutputBaseFilename=Hash-CAD-windows-installer
; Use LZMA2 compression for smaller installer size
Compression=lzma2
SolidCompression=yes
; Modern Windows visual style
WizardStyle=modern
; Require admin rights to install to Program Files
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
; Minimum Windows version (Windows 10)
MinVersion=10.0
; Uninstaller settings
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; Allow upgrading without uninstalling first
UsePreviousAppDir=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Install all files from the Flutter build output directory
; The source path is relative to the .iss file location
Source: "..\..\build\windows\x64\runner\Release\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop shortcut (optional, based on user selection)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Option to launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Check if a previous version is installed and offer to close running instances
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;

  // Check if Hash-CAD is currently running
  if CheckForMutexes('Hash-CAD-Running-Mutex') then
  begin
    if MsgBox('Hash-CAD is currently running. Please close it before continuing installation.' + #13#10 + #13#10 +
              'Click OK to close Hash-CAD automatically, or Cancel to abort installation.',
              mbConfirmation, MB_OKCANCEL) = IDOK then
    begin
      // Try to close the application gracefully
      Exec('taskkill', '/IM hash_cad.exe /F', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      Sleep(1000); // Wait for process to fully terminate
    end
    else
    begin
      Result := False;
    end;
  end;
end;

// Clean up old files that may have been removed in new version
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Future: Add any post-install cleanup here if needed
  end;
end;
