from pathlib import Path
import re

p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')
s=re.sub(r'#define AppVersion "[0-9]+\.[0-9]+\.[0-9]+"','#define AppVersion "3.11.1"',s,count=1)
s=re.sub(r'OutputBaseFilename=.*','OutputBaseFilename=CSMVisualizadorXML-3.11.1-Instalador-Completo',s,count=1)
s=re.sub(r'VersionInfoDescription=.*','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.11.1 com correção da consulta NF-e por chave',s,count=1)
s=re.sub(r'VersionInfoVersion=[0-9.]+','VersionInfoVersion=3.11.1.0',s,count=1)
s=s.replace('PrivilegesRequired=admin','PrivilegesRequired=lowest')
s=re.sub(r'CSM Visualizador XML 3\.[0-9]+\.[0-9]+','CSM Visualizador XML 3.11.1',s)
s=re.sub(r'(?i)versão 3\.[0-9]+\.[0-9]+','versão 3.11.1',s)
s=re.sub(r'(?i)instalar a 3\.[0-9]+\.[0-9]+','instalar a 3.11.1',s)
welcome="""  WizardForm.WelcomeLabel2.Caption :=
    'Instalador completo — funciona também em computadores que nunca tiveram o CSM Visualizador XML.' + #13#10 + #13#10 +
    'NOVIDADES DA VERSÃO 3.11.1' + #13#10 +
    '• Corrigido o acionamento da consulta NF-e quando o botão interno muda de texto ou layout' + #13#10 +
    '• Adicionados fallbacks por botão submit, formulário e tecla Enter' + #13#10 +
    '• Mantidos Ctrl+L, validação da chave, histórico e abertura da nota dentro do CSM' + #13#10 +
    '• Mantidas todas as rotinas fiscais da 3.11.0' + #13#10 + #13#10 +
    'O instalador removerá versões antigas antes de instalar a 3.11.1.';"""
s,n=re.subn(r"\s*WizardForm\.WelcomeLabel2\.Caption\s*:=.*?;\n\s*WizardForm\.WelcomeLabel2\.Font\.Color",'\n'+welcome+'\n  WizardForm.WelcomeLabel2.Font.Color',s,flags=re.S)
if n!=1:raise SystemExit(f'Nao consegui atualizar novidades: {n}')
s=re.sub(r"WizardForm\.Caption := '.*?';","WizardForm.Caption := 'CSM Visualizador XML 3.11.1  •  Instalação completa';",s,count=1)
s=re.sub(r"WizardForm\.WelcomeLabel1\.Caption := '.*?';","WizardForm.WelcomeLabel1.Caption := 'CSM Visualizador XML 3.11.1';",s,count=1)
s=re.sub(r"WizardForm\.FinishedLabel\.Caption := '.*?';","WizardForm.FinishedLabel.Caption := 'CSM Visualizador XML 3.11.1 instalado com sucesso.';",s,count=1)
run_pat=r'Filename: "\{app\}\\\{#AppExe\}"; (?:WorkingDir: "\{app\}"; )?Description: "Abrir CSM Visualizador XML [^"]+"; Flags: nowait postinstall skipifsilent'
run_new='Filename: "{app}\\{#AppExe}"; WorkingDir: "{app}"; Description: "Abrir CSM Visualizador XML 3.11.1"; Flags: nowait postinstall skipifsilent'
s,nrun=re.subn(run_pat,run_new,s,count=1)
if nrun!=1:raise SystemExit(f'Nao consegui corrigir abertura pos-instalacao: {nrun}')
old_step="""procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, 0, 0);
end;"""
new_step="""procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    KillOldProcesses;
    Sleep(250);
    SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, 0, 0);
  end;
end;"""
if old_step in s:s=s.replace(old_step,new_step,1)
elif 'if CurStep = ssPostInstall then begin' not in s or 'KillOldProcesses;' not in s:raise SystemExit('CurStepChanged esperado nao encontrado')
for token in ('#define AppVersion "3.11.1"','OutputBaseFilename=CSMVisualizadorXML-3.11.1-Instalador-Completo','VersionInfoVersion=3.11.1.0','PrivilegesRequired=lowest','WorkingDir: "{app}"; Description: "Abrir CSM Visualizador XML 3.11.1"','KillOldProcesses;'):
    if token not in s:raise SystemExit('Instalador 3.11.1 incompleto: '+token)
p.write_text(s,encoding='utf-8',newline='\n')
test=Path('installer-v2/test_installed.ps1')
t=test.read_text(encoding='utf-8')
t=re.sub(r'\$installer = \(Resolve-Path "dist/CSM Visualizador XML [0-9.]+ - Instalador Completo\.exe"\)\.Path','$installer = (Resolve-Path "dist/CSM Visualizador XML 3.11.1 - Instalador Completo.exe").Path',t,count=1)
if '3.11.1 - Instalador Completo.exe' not in t:
    old='$installer = (Resolve-Path "dist/CSMVisualizadorXML-Instalador-Completo-Abas-Fix.exe").Path'
    if old in t:t=t.replace(old,'$installer = (Resolve-Path "dist/CSM Visualizador XML 3.11.1 - Instalador Completo.exe").Path',1)
test.write_text(t,encoding='utf-8',newline='\n')
print('ISS preparado para 3.11.1 com hotfix da Consulta NF-e.')
