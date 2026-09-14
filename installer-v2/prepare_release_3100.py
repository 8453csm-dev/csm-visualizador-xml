from pathlib import Path
import re

p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')
s=re.sub(r'#define AppVersion "[0-9]+\.[0-9]+\.[0-9]+"','#define AppVersion "3.10.0"',s,count=1)
s=re.sub(r'OutputBaseFilename=.*','OutputBaseFilename=CSMVisualizadorXML-3.10.0-Instalador-Completo',s,count=1)
s=re.sub(r'VersionInfoDescription=.*','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.10.0 com DIFAL e ICMS ST',s,count=1)
s=re.sub(r'VersionInfoVersion=[0-9.]+','VersionInfoVersion=3.10.0.0',s,count=1)
s=s.replace('PrivilegesRequired=admin','PrivilegesRequired=lowest')
s=re.sub(r'CSM Visualizador XML 3\.[0-9]+\.[0-9]+','CSM Visualizador XML 3.10.0',s)
s=re.sub(r'(?i)versão 3\.[0-9]+\.[0-9]+','versão 3.10.0',s)
s=re.sub(r'(?i)instalar a 3\.[0-9]+\.[0-9]+','instalar a 3.10.0',s)
welcome="""  WizardForm.WelcomeLabel2.Caption :=
    'Instalador completo — funciona também em computadores que nunca tiveram o CSM Visualizador XML.' + #13#10 + #13#10 +
    'NOVIDADES DA VERSÃO 3.10.0' + #13#10 +
    '• Nova aba DIFAL / ICMS ST integrada ao XML aberto' + #13#10 +
    '• DIFAL separado por alíquota interestadual de 12% e 4%' + #13#10 +
    '• Revenda e uso/consumo com tratamento distinto do IPI na base' + #13#10 +
    '• Itens podem ser marcados como ICMS ST e usar MVA informada pelo usuário' + #13#10 +
    '• Alíquota interna preenchida do XML quando disponível e editável por item' + #13#10 +
    '• Mantidas Devolução, Entender a Tributação, Consulta DANFE e importação modal' + #13#10 + #13#10 +
    'O instalador removerá versões antigas antes de instalar a 3.10.0.';"""
s,n=re.subn(r"\s*WizardForm\.WelcomeLabel2\.Caption\s*:=.*?;\n\s*WizardForm\.WelcomeLabel2\.Font\.Color",'\n'+welcome+'\n  WizardForm.WelcomeLabel2.Font.Color',s,flags=re.S)
if n!=1:raise SystemExit(f'Não consegui atualizar novidades: {n}')
s=re.sub(r"WizardForm\.Caption := '.*?';","WizardForm.Caption := 'CSM Visualizador XML 3.10.0  •  Instalação completa';",s,count=1)
s=re.sub(r"WizardForm\.WelcomeLabel1\.Caption := '.*?';","WizardForm.WelcomeLabel1.Caption := 'CSM Visualizador XML 3.10.0';",s,count=1)
s=re.sub(r"WizardForm\.FinishedLabel\.Caption := '.*?';","WizardForm.FinishedLabel.Caption := 'CSM Visualizador XML 3.10.0 instalado com sucesso.';",s,count=1)
for token in ('#define AppVersion "3.10.0"','OutputBaseFilename=CSMVisualizadorXML-3.10.0-Instalador-Completo','VersionInfoVersion=3.10.0.0','PrivilegesRequired=lowest','BrazilianPortuguese.isl'):
    if token not in s:raise SystemExit('Instalador 3.10.0 incompleto: '+token)
if 'PrivilegesRequired=admin' in s:raise SystemExit('Instalador ainda exige administrador')
p.write_text(s,encoding='utf-8',newline='\n')
print('ISS preparado e validado para 3.10.0.')
