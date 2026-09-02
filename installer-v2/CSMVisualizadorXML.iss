#define AppName "CSM Visualizador XML"
#define AppVersion "3.8.0"
#define Publisher "CSM - Contabilidade São Mateus"
#define AppExe "CSM Visualizador XML.exe"
#define CoreExe "CSM Visualizador XML Core.exe"
#define XmlProgId "CSM.VisualizadorXML.xml"

[Setup]
AppId={{B04F9B6B-49E4-4F4D-BC98-7F9D0C3A4A87}
AppName={#AppName}
AppVerName={#AppName} {#AppVersion}
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
UninstallDisplayVersion={#AppVersion}
OutputDir=..\dist
OutputBaseFilename=CSMVisualizadorXML-3.8.0-Instalador-Completo
Compression=lzma2/max
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
AllowNoIcons=no
MinVersion=10.0
VersionInfoCompany={#Publisher}
VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.8.0 com Motor Fiscal de Devolução
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
VersionInfoVersion=3.8.0.0
SetupLogging=yes
UsePreviousAppDir=no
UsePreviousGroup=no
UsePreviousTasks=no
ShowLanguageDialog=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "defaultxml"; Description: "Escolher o CSM Visualizador XML como aplicativo padrão para arquivos XML"; GroupDescription: "Arquivos XML:"; Flags: checkedonce

[Files]
Source: "payload\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userdesktop}\CSM Visualizador XML"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\_internal\assets\CSMVisualizadorXML.ico"; Comment: "CSM Visualizador XML"
Name: "{userprograms}\CSM Visualizador XML\CSM Visualizador XML"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\_internal\assets\CSMVisualizadorXML.ico"
Name: "{userprograms}\CSM Visualizador XML\Desinstalar CSM Visualizador XML"; Filename: "{uninstallexe}"; IconFilename: "{app}\_internal\assets\CSMVisualizadorXML.ico"

[Registry]
Root: HKCU; Subkey: "Software\Classes\Applications\CSM Visualizador XML.exe"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "CSM Visualizador XML"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Applications\CSM Visualizador XML.exe\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\_internal\assets\CSMVisualizadorXML.ico,0"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Applications\CSM Visualizador XML.exe\shell\open"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\_internal\assets\CSMVisualizadorXML.ico,0"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Applications\CSM Visualizador XML.exe\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Applications\CSM Visualizador XML.exe\SupportedTypes"; ValueType: string; ValueName: ".xml"; ValueData: ""; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\{#XmlProgId}"; ValueType: string; ValueName: ""; ValueData: "Documento XML - CSM Visualizador XML"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\{#XmlProgId}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\_internal\assets\CSMVisualizadorXML.ico,0"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\{#XmlProgId}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\CSM\CSM Visualizador XML\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "CSM Visualizador XML"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\CSM\CSM Visualizador XML\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Visualizador e analisador de documentos fiscais XML da CSM"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\CSM\CSM Visualizador XML\Capabilities"; ValueType: string; ValueName: "ApplicationIcon"; ValueData: "{app}\_internal\assets\CSMVisualizadorXML.ico,0"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\CSM\CSM Visualizador XML\Capabilities\FileAssociations"; ValueType: string; ValueName: ".xml"; ValueData: "{#XmlProgId}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "CSM Visualizador XML"; ValueData: "Software\CSM\CSM Visualizador XML\Capabilities"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\CSM Visualizador XML.exe"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExe}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\CSM Visualizador XML.exe"; ValueType: string; ValueName: "Path"; ValueData: "{app}"; Flags: uninsdeletekey

[Run]
Filename: "ms-settings:defaultapps?registeredAppUser=CSM%20Visualizador%20XML"; Description: "Escolher CSM Visualizador XML como padrão para arquivos XML"; Flags: shellexec postinstall skipifsilent; Tasks: defaultxml
Filename: "{app}\{#AppExe}"; Description: "Abrir CSM Visualizador XML 3.8.0"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM ""CSM Visualizador XML.exe"""; Flags: runhidden; RunOnceId: "KillCSMLauncher"
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM ""CSM Visualizador XML Core.exe"""; Flags: runhidden; RunOnceId: "KillCSMCore"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: dirifempty; Name: "{userprograms}\CSM Visualizador XML"

[Code]
const
  CSMBlue = $00663B0F;
  CSMGreen = $006BA928;
  MutedText = $00807066;
  SHCNE_ASSOCCHANGED = $08000000;
  SHCNF_IDLIST = $0000;

procedure SHChangeNotify(wEventId, uFlags: LongWord; dwItem1, dwItem2: Longint);
  external 'SHChangeNotify@shell32.dll stdcall';

procedure KillOldProcesses;
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM "CSM Visualizador XML.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM "CSM Visualizador XML Core.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM "CSMVisualizadorXML.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM "CSMVisualizadorXML-4.0.0-alpha.1.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure RunOldUninstaller(const P: String);
var
  ResultCode: Integer;
begin
  if FileExists(P) then
    Exec(P, '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
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

procedure RemoveOldAssociations;
begin
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\Applications\CSM Visualizador XML.exe');
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\Applications\CSMVisualizadorXML.exe');
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\Applications\CSM Visualizador XML Core.exe');
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\CSM.VisualizadorXML.xml');
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\CSMVisualizadorXML.xml');
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\CSM\CSM Visualizador XML\Capabilities');
  RegDeleteValue(HKCU, 'Software\RegisteredApplications', 'CSM Visualizador XML');
  RegDeleteValue(HKCU, 'Software\RegisteredApplications', 'CSMVisualizadorXML');
  RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.xml\OpenWithProgids', 'CSM.VisualizadorXML.xml');
  RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.xml\OpenWithProgids', 'CSMVisualizadorXML.xml');
end;

procedure RemoveOldRegistry;
begin
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\CSMVisualizadorXML');
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B04F9B6B-49E4-4F4D-BC98-7F9D0C3A4A87}_is1');
  RegDeleteKeyIncludingSubkeys(HKLM32, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\CSMVisualizadorXML');
  RegDeleteKeyIncludingSubkeys(HKLM64, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\CSMVisualizadorXML');
  RegDeleteKeyIncludingSubkeys(HKLM32, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B04F9B6B-49E4-4F4D-BC98-7F9D0C3A4A87}_is1');
  RegDeleteKeyIncludingSubkeys(HKLM64, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B04F9B6B-49E4-4F4D-BC98-7F9D0C3A4A87}_is1');
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Microsoft\Windows\CurrentVersion\App Paths\CSM Visualizador XML.exe');
  RegDeleteKeyIncludingSubkeys(HKLM32, 'Software\Microsoft\Windows\CurrentVersion\App Paths\CSM Visualizador XML.exe');
  RegDeleteKeyIncludingSubkeys(HKLM64, 'Software\Microsoft\Windows\CurrentVersion\App Paths\CSM Visualizador XML.exe');
  RemoveOldAssociations;
end;

procedure RunKnownOldUninstallers;
begin
  RunOldUninstaller(ExpandConstant('{localappdata}\CSM Visualizador XML\unins000.exe'));
  RunOldUninstaller(ExpandConstant('{localappdata}\Programs\CSM Visualizador XML\unins000.exe'));
  RunOldUninstaller(ExpandConstant('{localappdata}\Programs\CSMVisualizadorXML\unins000.exe'));
  RunOldUninstaller(ExpandConstant('{autopf}\CSM Visualizador XML\unins000.exe'));
  RunOldUninstaller(ExpandConstant('{autopf}\CSMVisualizadorXML\unins000.exe'));
  if IsWin64 then begin
    RunOldUninstaller(ExpandConstant('{autopf32}\CSM Visualizador XML\unins000.exe'));
    RunOldUninstaller(ExpandConstant('{autopf32}\CSMVisualizadorXML\unins000.exe'));
  end;
end;

procedure CleanPreviousVersions;
begin
  WizardForm.StatusLabel.Caption := 'Removendo completamente versões anteriores...';
  KillOldProcesses;
  Sleep(350);
  RunKnownOldUninstallers;
  KillOldProcesses;
  Sleep(350);

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
  RemoveDirIfExists(ExpandConstant('{userappdata}\CSMVisualizadorXML'));

  RemoveFileIfExists(ExpandConstant('{userdesktop}\CSM Visualizador XML.lnk'));
  RemoveFileIfExists(ExpandConstant('{userdesktop}\CSMVisualizadorXML.lnk'));
  RemoveDirIfExists(ExpandConstant('{userprograms}\CSM Visualizador XML'));
  RemoveDirIfExists(ExpandConstant('{userprograms}\CSMVisualizadorXML'));

  RemoveOldRegistry;
  SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, 0, 0);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  CleanPreviousVersions;
  WizardForm.StatusLabel.Caption := 'Preparando o CSM Visualizador XML 3.8.0...';
end;

procedure InitializeWizard;
begin
  WizardForm.Caption := 'CSM Visualizador XML 3.8.0  •  Instalação completa';
  WizardForm.Font.Name := 'Segoe UI';
  WizardForm.Font.Size := 9;

  WizardForm.WelcomeLabel1.Caption := 'CSM Visualizador XML 3.8.0';
  WizardForm.WelcomeLabel1.Font.Name := 'Segoe UI';
  WizardForm.WelcomeLabel1.Font.Size := 17;
  WizardForm.WelcomeLabel1.Font.Style := [fsBold];
  WizardForm.WelcomeLabel1.Font.Color := CSMBlue;

  WizardForm.WelcomeLabel2.Caption :=
    'Instalador completo — funciona também em computadores que nunca tiveram o CSM Visualizador XML.' + #13#10 + #13#10 +
    'NOVIDADES DESTA VERSÃO' + #13#10 +
    '• Motor Fiscal de Devolução com devolução total e parcial' + #13#10 +
    '• Modelo orientativo para o cliente com CFOP, CST/CSOSN, impostos e referência por item' + #13#10 +
    '• Tratamento correto do ICMS-ST: campo próprio ou fallback em Outras Despesas, sem duplicidade' + #13#10 +
    '• PDF de devolução com Cálculo do Imposto, Transportador/Volumes e Produtos/Serviços' + #13#10 +
    '• Produtos do PDF com contraste e leitura aprimorados' + #13#10 + #13#10 +
    'TAMBÉM INCLUI' + #13#10 +
    '• Abertura de vários XMLs em abas na mesma janela' + #13#10 +
    '• Localizador Fiscal e Consulta DANFE' + #13#10 +
    '• Tema claro/escuro, Aba XML avançada e associação .xml' + #13#10 +
    '• Instalação limpa, atalho na Área de Trabalho e desinstalador' + #13#10 + #13#10 +
    'O instalador removerá versões antigas antes de instalar a 3.8.0.';
  WizardForm.WelcomeLabel2.Font.Color := MutedText;

  WizardForm.NextButton.Caption := 'Avançar';
  WizardForm.CancelButton.Caption := 'Cancelar';
  WizardForm.BackButton.Caption := 'Voltar';

  WizardForm.FinishedLabel.Caption := 'CSM Visualizador XML 3.8.0 instalado com sucesso.';
  WizardForm.FinishedLabel.Font.Color := CSMGreen;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpReady then begin
    WizardForm.PageNameLabel.Caption := 'Tudo pronto para instalar a versão 3.8.0';
    WizardForm.PageDescriptionLabel.Caption := 'A instalação antiga será removida e substituída pelo pacote completo atual.';
    WizardForm.NextButton.Caption := 'Instalar';
  end else if CurPageID = wpInstalling then begin
    WizardForm.PageNameLabel.Caption := 'Instalando CSM Visualizador XML 3.8.0';
    WizardForm.PageDescriptionLabel.Caption := 'Limpando versões antigas e instalando todos os componentes atuais.';
  end else if CurPageID = wpFinished then begin
    WizardForm.PageNameLabel.Caption := 'Instalação concluída';
    WizardForm.PageDescriptionLabel.Caption := 'A versão 3.8.0 foi instalada. Você pode escolher o CSM como padrão para arquivos XML.';
    WizardForm.NextButton.Caption := 'Concluir';
  end else begin
    WizardForm.NextButton.Caption := 'Avançar';
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, 0, 0);
end;
