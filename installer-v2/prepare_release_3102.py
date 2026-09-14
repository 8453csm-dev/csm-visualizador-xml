from pathlib import Path
import re

p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')
s=re.sub(r'#define AppVersion "[0-9]+\.[0-9]+\.[0-9]+"','#define AppVersion "3.10.2"',s,count=1)
s=re.sub(r'OutputBaseFilename=.*','OutputBaseFilename=CSMVisualizadorXML-3.10.2-Instalador-Completo',s,count=1)
s=re.sub(r'VersionInfoDescription=.*','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.10.2 com DIFAL e ICMS ST',s,count=1)
s=re.sub(r'VersionInfoVersion=[0-9.]+','VersionInfoVersion=3.10.2.0',s,count=1)
s=s.replace('PrivilegesRequired=admin','PrivilegesRequired=lowest')
s=re.sub(r'CSM Visualizador XML 3\.[0-9]+\.[0-9]+','CSM Visualizador XML 3.10.2',s)
s=re.sub(r'(?i)versão 3\.[0-9]+\.[0-9]+','versão 3.10.2',s)
s=re.sub(r'(?i)instalar a 3\.[0-9]+\.[0-9]+','instalar a 3.10.2',s)

welcome="""  WizardForm.WelcomeLabel2.Caption :=
    'Instalador completo — funciona também em computadores que nunca tiveram o CSM Visualizador XML.' + #13#10 + #13#10 +
    'NOVIDADES DA VERSÃO 3.10.2' + #13#10 +
    '• DIFAL continua apurado isoladamente quando existem CFOPs diferentes' + #13#10 +
    '• Resumo visual volta a mostrar somente a alíquota interestadual' + #13#10 +
    '• O mesmo padrão simplificado foi aplicado ao resumo da aba Fiscal' + #13#10 +
    '• Corrigida abertura automática ao terminar a instalação para nunca reutilizar um Core antigo' + #13#10 +
    '• Mantidas Devolução, Entender a Tributação, Consulta DANFE e importação modal' + #13#10 + #13#10 +
    'O instalador removerá versões antigas antes de instalar a 3.10.2.';"""
s,n=re.subn(r"\s*WizardForm\.WelcomeLabel2\.Caption\s*:=.*?;\n\s*WizardForm\.WelcomeLabel2\.Font\.Color",'\n'+welcome+'\n  WizardForm.WelcomeLabel2.Font.Color',s,flags=re.S)
if n!=1:raise SystemExit(f'Nao consegui atualizar novidades: {n}')

s=re.sub(r"WizardForm\.Caption := '.*?';","WizardForm.Caption := 'CSM Visualizador XML 3.10.2  •  Instalação completa';",s,count=1)
s=re.sub(r"WizardForm\.WelcomeLabel1\.Caption := '.*?';","WizardForm.WelcomeLabel1.Caption := 'CSM Visualizador XML 3.10.2';",s,count=1)
s=re.sub(r"WizardForm\.FinishedLabel\.Caption := '.*?';","WizardForm.FinishedLabel.Caption := 'CSM Visualizador XML 3.10.2 instalado com sucesso.';",s,count=1)

# A abertura pelo checkbox final deve usar exatamente o launcher recém-instalado e o diretório correto.
run_pat=r'Filename: "\{app\}\\\{#AppExe\}"; Description: "Abrir CSM Visualizador XML [^"]+"; Flags: nowait postinstall skipifsilent'
run_new='Filename: "{app}\\{#AppExe}"; WorkingDir: "{app}"; Description: "Abrir CSM Visualizador XML 3.10.2"; Flags: nowait postinstall skipifsilent'
s,nrun=re.subn(run_pat,run_new,s,count=1)
if nrun!=1:raise SystemExit(f'Nao consegui corrigir abertura pos-instalacao: {nrun}')

# Antes da tela final, mata qualquer broker/Core que tenha sobrevivido de versão anterior.
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
if old_step not in s:raise SystemExit('CurStepChanged esperado nao encontrado')
s=s.replace(old_step,new_step,1)

for token in ('#define AppVersion "3.10.2"','OutputBaseFilename=CSMVisualizadorXML-3.10.2-Instalador-Completo','VersionInfoVersion=3.10.2.0','PrivilegesRequired=lowest','WorkingDir: "{app}"; Description: "Abrir CSM Visualizador XML 3.10.2"','KillOldProcesses;'):
    if token not in s:raise SystemExit('Instalador 3.10.2 incompleto: '+token)
if 'PrivilegesRequired=admin' in s:raise SystemExit('Instalador ainda exige administrador')
p.write_text(s,encoding='utf-8',newline='\n')

# O teste legado usa um nome alternativo do instalador. Na 3.10.2, apontamos a homologação
# para o EXE versionado realmente produzido pela compilação, sem criar cópias artificiais.
test=Path('installer-v2/test_installed.ps1')
t=test.read_text(encoding='utf-8')
old='$installer = (Resolve-Path "dist/CSMVisualizadorXML-Instalador-Completo-Abas-Fix.exe").Path'
new='$installer = (Resolve-Path "dist/CSM Visualizador XML 3.10.2 - Instalador Completo.exe").Path'
if old in t:
    t=t.replace(old,new,1)
elif new not in t:
    raise SystemExit('Caminho do instalador no teste legado nao reconhecido')
test.write_text(t,encoding='utf-8',newline='\n')

print('ISS preparado para 3.10.2 com abertura pos-instalacao limpa e homologacao apontando para o EXE real.')
