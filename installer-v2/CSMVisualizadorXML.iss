#define AppName "CSM Visualizador XML"
#define AppVersion "3.7.8.8"
#define Publisher "CSM - Contabilidade São Mateus"
#define AppExe "CSM Visualizador XML.exe"

[Setup]
AppId={{B04F9B6B-49E4-4F4D-BC98-7F9D0C3A4A87}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#Publisher}
AppPublisherURL=https://github.com/8453csm-dev/csm-visualizador-xml
AppSupportURL=https://github.com/8453csm-dev/csm-visualizador-xml
DefaultDirName={localappdata}\CSM Visualizador XML
DefaultGroupName=CSM Visualizador XML
DisableProgramGroupPage=yes
DisableDirPage=yes
DisableReadyPage=no
DisableWelcomePage=no
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
WizardResizable=no
WizardImageFile=wizard.bmp
WizardSmallImageFile=wizard-small.bmp
WizardImageStretch=yes
SetupIconFile=payload\_internal\assets\CSMVisualizadorXML.ico
UninstallDisplayName=CSM Visualizador XML
UninstallDisplayIcon={app}\_internal\assets\CSMVisualizadorXML.ico
OutputDir=..\dist
OutputBaseFilename=CSMVisualizadorXML-Instalador-Completo
Compression=lzma2/max
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
AllowNoIcons=no
MinVersion=10.0
VersionInfoCompany={#Publisher}
VersionInfoDescription=Instalador completo do CSM Visualizador XML
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
VersionInfoVersion=3.7.8.8

[Files]
Source: "payload\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userdesktop}\CSM Visualizador XML"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\_internal\assets\CSMVisualizadorXML.ico"; Comment: "CSM Visualizador XML"
Name: "{userprograms}\CSM Visualizador XML\CSM Visualizador XML"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\_internal\assets\CSMVisualizadorXML.ico"
Name: "{userprograms}\CSM Visualizador XML\Desinstalar CSM Visualizador XML"; Filename: "{uninstallexe}"; IconFilename: "{app}\_internal\assets\CSMVisualizadorXML.ico"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir CSM Visualizador XML"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM ""CSM Visualizador XML.exe"""; Flags: runhidden; RunOnceId: "KillCSM"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: dirifempty; Name: "{userprograms}\CSM Visualizador XML"

[Code]
const
  CSMBlue = $00663B0F;
  CSMGreen = $006BA928;
  MutedText = $00807066;

procedure KillOldProcesses;
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM "CSM Visualizador XML.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM "CSMVisualizadorXML.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure RemoveDirIfExists(const P: String);
begin
  if (P <> '') and DirExists(P) then
    DelTree(P, True, True, True);
end;

procedure RemoveFileIfExists(const P: String);
begin
  if FileExists(P) then DeleteFile(P);
end;

procedure RemoveOldRegistry;
begin
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\CSMVisualizadorXML');
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B04F9B6B-49E4-4F4D-BC98-7F9D0C3A4A87}_is1');
  RegDeleteKeyIncludingSubkeys(HKLM32, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\CSMVisualizadorXML');
  RegDeleteKeyIncludingSubkeys(HKLM64, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\CSMVisualizadorXML');
  RegDeleteKeyIncludingSubkeys(HKLM32, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B04F9B6B-49E4-4F4D-BC98-7F9D0C3A4A87}_is1');
  RegDeleteKeyIncludingSubkeys(HKLM64, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B04F9B6B-49E4-4F4D-BC98-7F9D0C3A4A87}_is1');
end;

procedure CleanPreviousVersions;
begin
  WizardForm.StatusLabel.Caption := 'Removendo versões anteriores do CSM Visualizador XML...';
  KillOldProcesses;
  Sleep(400);

  { instalações históricas conhecidas }
  RemoveDirIfExists(ExpandConstant('{localappdata}\CSM Visualizador XML'));
  RemoveDirIfExists(ExpandConstant('{localappdata}\CSMVisualizadorXML'));
  RemoveDirIfExists(ExpandConstant('{localappdata}\CSM Visualizador XML 4'));
  RemoveDirIfExists(ExpandConstant('{localappdata}\Programs\CSM Visualizador XML'));
  RemoveDirIfExists(ExpandConstant('{localappdata}\Programs\CSMVisualizadorXML'));
  RemoveDirIfExists(ExpandConstant('{autopf}\CSM Visualizador XML'));
  RemoveDirIfExists(ExpandConstant('{autopf}\CSMVisualizadorXML'));
  if IsWin64 then begin
    RemoveDirIfExists(ExpandConstant('{autopf32}\CSM Visualizador XML'));
    RemoveDirIfExists(ExpandConstant('{autopf32}\CSMVisualizadorXML'));
  end;
  RemoveDirIfExists(ExpandConstant('{userappdata}\CSM Visualizador XML'));

  { atalhos antigos }
  RemoveFileIfExists(ExpandConstant('{userdesktop}\CSM Visualizador XML.lnk'));
  RemoveFileIfExists(ExpandConstant('{userdesktop}\CSMVisualizadorXML.lnk'));
  RemoveDirIfExists(ExpandConstant('{userprograms}\CSM Visualizador XML'));

  RemoveOldRegistry;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  CleanPreviousVersions;
  WizardForm.StatusLabel.Caption := 'Preparando a nova instalação...';
end;

procedure InitializeWizard;
begin
  WizardForm.Caption := 'CSM Visualizador XML  •  Instalação';
  WizardForm.Font.Name := 'Segoe UI';
  WizardForm.Font.Size := 9;

  WizardForm.WelcomeLabel1.Caption := 'Bem-vindo ao CSM Visualizador XML';
  WizardForm.WelcomeLabel1.Font.Name := 'Segoe UI';
  WizardForm.WelcomeLabel1.Font.Size := 17;
  WizardForm.WelcomeLabel1.Font.Style := [fsBold];
  WizardForm.WelcomeLabel1.Font.Color := CSMBlue;

  WizardForm.WelcomeLabel2.Caption :=
    'Instalação limpa e segura do CSM Visualizador XML.' + #13#10 + #13#10 +
    '• Remove automaticamente versões anteriores' + #13#10 +
    '• Instala a Aba XML otimizada com sintaxe e cores' + #13#10 +
    '• Cria atalho na Área de Trabalho e Menu Iniciar' + #13#10 +
    '• Instala desinstalador integrado ao Windows' + #13#10 + #13#10 +
    'Clique em Avançar para continuar.';
  WizardForm.WelcomeLabel2.Font.Color := MutedText;

  WizardForm.NextButton.Caption := 'Avançar';
  WizardForm.CancelButton.Caption := 'Cancelar';
  WizardForm.BackButton.Caption := 'Voltar';

  WizardForm.FinishedLabel.Caption := 'CSM Visualizador XML instalado com sucesso.';
  WizardForm.FinishedLabel.Font.Color := CSMGreen;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpReady then begin
    WizardForm.PageNameLabel.Caption := 'Tudo pronto para instalar';
    WizardForm.PageDescriptionLabel.Caption := 'A versão anterior será removida e a nova será instalada do zero.';
    WizardForm.NextButton.Caption := 'Instalar';
  end else if CurPageID = wpInstalling then begin
    WizardForm.PageNameLabel.Caption := 'Instalando CSM Visualizador XML';
    WizardForm.PageDescriptionLabel.Caption := 'Aguarde enquanto o software é instalado.';
  end else if CurPageID = wpFinished then begin
    WizardForm.PageNameLabel.Caption := 'Instalação concluída';
    WizardForm.PageDescriptionLabel.Caption := 'O CSM Visualizador XML está pronto para uso.';
    WizardForm.NextButton.Caption := 'Concluir';
  end else begin
    WizardForm.NextButton.Caption := 'Avançar';
  end;
end;
