from pathlib import Path
import re

p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')
s=s.replace('3.13.1','3.14.0')
s=re.sub(r'OutputBaseFilename=.*','OutputBaseFilename=CSMVisualizadorXML-3.14.0-Instalador-Completo',s,count=1)
s=re.sub(r'VersionInfoDescription=.*','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.14.0 com CSM Consulta NF-e API',s,count=1)
s=re.sub(r'VersionInfoVersion=[0-9.]+','VersionInfoVersion=3.14.0.0',s,count=1)

# Corrige definitivamente o pós-update: a primeira abertura DEVE usar o modo fresh.
run_pattern=r'Filename: "\{app\}\\\{#AppExe\}";(?: Parameters: "[^"]*";)? WorkingDir: "\{app\}"; Description: "Abrir CSM Visualizador XML 3\.14\.0"; Flags: nowait postinstall skipifsilent'
run_new='Filename: "{app}\\{#AppExe}"; Parameters: "--post-install-fresh"; WorkingDir: "{app}"; Description: "Abrir CSM Visualizador XML 3.14.0"; Flags: nowait postinstall skipifsilent'
s,n=re.subn(run_pattern,run_new,s,count=1)
if n!=1:
    # fallback para o formato sem WorkingDir produzido por alguma base.
    alt=r'Filename: "\{app\}\\\{#AppExe\}"; Description: "Abrir CSM Visualizador XML 3\.14\.0"; Flags: nowait postinstall skipifsilent'
    s,n=re.subn(alt,'Filename: "{app}\\{#AppExe}"; Parameters: "--post-install-fresh"; Description: "Abrir CSM Visualizador XML 3.14.0"; Flags: nowait postinstall skipifsilent',s,count=1)
if n!=1: raise SystemExit('Linha [Run] do app não localizada para modo fresh')

# Mata a árvore de processos antiga (Core + WebView2 filho), sem matar WebView2 de outros apps.
s=s.replace('Exec(ExpandConstant(\'{sys}\\taskkill.exe\'), \'/F /IM "CSM Visualizador XML.exe"\'',
            'Exec(ExpandConstant(\'{sys}\\taskkill.exe\'), \'/T /F /IM "CSM Visualizador XML.exe"\'')
s=s.replace('Exec(ExpandConstant(\'{sys}\\taskkill.exe\'), \'/F /IM "CSM Visualizador XML Core.exe"\'',
            'Exec(ExpandConstant(\'{sys}\\taskkill.exe\'), \'/T /F /IM "CSM Visualizador XML Core.exe"\'')
s=s.replace('Exec(ExpandConstant(\'{sys}\\taskkill.exe\'), \'/F /IM "CSMVisualizadorXML.exe"\'',
            'Exec(ExpandConstant(\'{sys}\\taskkill.exe\'), \'/T /F /IM "CSMVisualizadorXML.exe"\'')

# Migra configurações persistentes para fora da pasta de instalação antes da limpeza.
anchor='''procedure CleanPreviousVersions;
begin
  WizardForm.StatusLabel.Caption := 'Removendo completamente versões anteriores...';'''
if anchor not in s: raise SystemExit('CleanPreviousVersions não localizado')
preserve=r'''procedure PreserveCSMPersistentData;
var
  SrcBase, DstBase: String;
begin
  SrcBase := ExpandConstant('{localappdata}\CSM Visualizador XML');
  DstBase := ExpandConstant('{localappdata}\CSM\VisualizadorXML');
  ForceDirectories(DstBase);
  ForceDirectories(DstBase + '\certificados');
  if FileExists(SrcBase + '\certificados\folders.json') then
    FileCopy(SrcBase + '\certificados\folders.json', DstBase + '\certificados\folders.json', False);
  if FileExists(SrcBase + '\certificados\certificados.json') then
    FileCopy(SrcBase + '\certificados\certificados.json', DstBase + '\certificados\certificados.json', False);
  if FileExists(SrcBase + '\xml-folders.json') then
    FileCopy(SrcBase + '\xml-folders.json', DstBase + '\xml-folders.json', False);
end;

procedure CleanPreviousVersions;
begin
  WizardForm.StatusLabel.Caption := 'Removendo completamente versões anteriores...';
  PreserveCSMPersistentData;'''
s=s.replace(anchor,preserve,1)

for token in (
    '#define AppVersion "3.14.0"',
    'OutputBaseFilename=CSMVisualizadorXML-3.14.0-Instalador-Completo',
    'VersionInfoVersion=3.14.0.0',
    'Parameters: "--post-install-fresh"',
    'PreserveCSMPersistentData',
    '/T /F /IM "CSM Visualizador XML Core.exe"'
):
    if token not in s: raise SystemExit('Instalador 3.14.0 incompleto: '+token)
p.write_text(s,encoding='utf-8',newline='\n')
print('ISS preparado para 3.14.0 com atualização fresh e dados persistentes.')
