from pathlib import Path
import re
p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')
s=re.sub(r'#define AppVersion "[0-9]+\.[0-9]+\.[0-9]+"','#define AppVersion "3.9.4"',s,count=1)
s=re.sub(r'OutputBaseFilename=.*','OutputBaseFilename=CSMVisualizadorXML-3.9.4-Instalador-Completo',s,count=1)
s=re.sub(r'VersionInfoDescription=.*','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.9.4 com progresso imediato de importação',s,count=1)
s=re.sub(r'VersionInfoVersion=[0-9.]+','VersionInfoVersion=3.9.4.0',s,count=1)
s=s.replace('PrivilegesRequired=admin','PrivilegesRequired=lowest')
s=re.sub(r'CSM Visualizador XML 3\.[0-9]+\.[0-9]+','CSM Visualizador XML 3.9.4',s)
s=re.sub(r'(?i)versão 3\.[0-9]+\.[0-9]+','versão 3.9.4',s)
s=re.sub(r'(?i)instalar a 3\.[0-9]+\.[0-9]+','instalar a 3.9.4',s)
welcome="""  WizardForm.WelcomeLabel2.Caption :=
    'Instalador completo — funciona também em computadores que nunca tiveram o CSM Visualizador XML.' + #13#10 + #13#10 +
    'NOVIDADES DA VERSÃO 3.9.4' + #13#10 +
    '• O painel de importação de pasta aparece antes do processamento começar' + #13#10 +
    '• Feedback visual imediato ao selecionar/importar grandes volumes de XMLs' + #13#10 +
    '• Mantido o limite atual de até 5.000 arquivos por importação' + #13#10 +
    '• Entender a Tributação e Motor Fiscal de Devolução preservados' + #13#10 + #13#10 +
    'TAMBÉM INCLUI' + #13#10 +
    '• Abertura de vários XMLs em abas na mesma janela' + #13#10 +
    '• Localizador Fiscal e Consulta DANFE' + #13#10 +
    '• Tema claro/escuro, Aba XML avançada e associação .xml' + #13#10 +
    '• Instalação limpa, atalho na Área de Trabalho e desinstalador' + #13#10 + #13#10 +
    'O instalador removerá versões antigas antes de instalar a 3.9.4.';"""
s,n=re.subn(r"\s*WizardForm\.WelcomeLabel2\.Caption\s*:=.*?;\n\s*WizardForm\.WelcomeLabel2\.Font\.Color",'\n'+welcome+'\n  WizardForm.WelcomeLabel2.Font.Color',s,flags=re.S)
if n!=1:raise SystemExit(f'Não consegui atualizar novidades: {n}')
s=re.sub(r"WizardForm\.Caption := '.*?';","WizardForm.Caption := 'CSM Visualizador XML 3.9.4  •  Instalação completa';",s,count=1)
s=re.sub(r"WizardForm\.WelcomeLabel1\.Caption := '.*?';","WizardForm.WelcomeLabel1.Caption := 'CSM Visualizador XML 3.9.4';",s,count=1)
s=re.sub(r"WizardForm\.FinishedLabel\.Caption := '.*?';","WizardForm.FinishedLabel.Caption := 'CSM Visualizador XML 3.9.4 instalado com sucesso.';",s,count=1)
for token in ('#define AppVersion "3.9.4"','OutputBaseFilename=CSMVisualizadorXML-3.9.4-Instalador-Completo','VersionInfoVersion=3.9.4.0','PrivilegesRequired=lowest','BrazilianPortuguese.isl'):
    if token not in s:raise SystemExit('Instalador 3.9.4 incompleto: '+token)
if 'PrivilegesRequired=admin' in s:raise SystemExit('Instalador ainda exige administrador')
p.write_text(s,encoding='utf-8',newline='\n')
print('ISS preparado e validado para 3.9.4.')
