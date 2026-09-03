from pathlib import Path
import re

p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')

s=re.sub(r'#define AppVersion "[0-9]+\.[0-9]+\.[0-9]+"','#define AppVersion "3.9.3"',s,count=1)
s=re.sub(r'OutputBaseFilename=.*','OutputBaseFilename=CSMVisualizadorXML-3.9.3-Instalador-Completo',s,count=1)
s=re.sub(r'VersionInfoDescription=.*','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.9.3 com progresso de importacao por pasta, Entender a Tributacao e Motor Fiscal de Devolucao',s,count=1)
s=re.sub(r'VersionInfoVersion=[0-9.]+','VersionInfoVersion=3.9.3.0',s,count=1)
s=s.replace('PrivilegesRequired=admin','PrivilegesRequired=lowest')

s=re.sub(r'CSM Visualizador XML 3\.[0-9]+\.[0-9]+','CSM Visualizador XML 3.9.3',s)
s=re.sub(r'(?i)versão 3\.[0-9]+\.[0-9]+','versão 3.9.3',s)
s=re.sub(r'(?i)instalar a 3\.[0-9]+\.[0-9]+','instalar a 3.9.3',s)

welcome="""  WizardForm.WelcomeLabel2.Caption :=
    'Instalador completo — funciona também em computadores que nunca tiveram o CSM Visualizador XML.' + #13#10 + #13#10 +
    'NOVIDADES DA VERSÃO 3.9.3' + #13#10 +
    '• Novo painel de progresso ao importar uma pasta de XMLs' + #13#10 +
    '• Feedback visual durante leitura, validação e organização dos documentos' + #13#10 +
    '• Conclusão informa quantos documentos foram importados' + #13#10 +
    '• Motor de importação e limite atual de até 5.000 arquivos preservados' + #13#10 +
    '• Entender a Tributação e Motor Fiscal de Devolução preservados' + #13#10 + #13#10 +
    'TAMBÉM INCLUI' + #13#10 +
    '• Abertura de vários XMLs em abas na mesma janela' + #13#10 +
    '• Localizador Fiscal e Consulta DANFE' + #13#10 +
    '• Tema claro/escuro, Aba XML avançada e associação .xml' + #13#10 +
    '• Instalação limpa, atalho na Área de Trabalho e desinstalador' + #13#10 + #13#10 +
    'O instalador removerá versões antigas antes de instalar a 3.9.3.';"""

s,n=re.subn(r"\s*WizardForm\.WelcomeLabel2\.Caption\s*:=.*?;\n\s*WizardForm\.WelcomeLabel2\.Font\.Color",'\n'+welcome+'\n  WizardForm.WelcomeLabel2.Font.Color',s,flags=re.S)
if n!=1:raise SystemExit(f'Não consegui atualizar a tela de novidades do instalador: {n}')

s=re.sub(r"WizardForm\.Caption := '.*?';","WizardForm.Caption := 'CSM Visualizador XML 3.9.3  •  Instalação completa';",s,count=1)
s=re.sub(r"WizardForm\.WelcomeLabel1\.Caption := '.*?';","WizardForm.WelcomeLabel1.Caption := 'CSM Visualizador XML 3.9.3';",s,count=1)
s=re.sub(r"WizardForm\.FinishedLabel\.Caption := '.*?';","WizardForm.FinishedLabel.Caption := 'CSM Visualizador XML 3.9.3 instalado com sucesso.';",s,count=1)

for token in ('#define AppVersion "3.9.3"','OutputBaseFilename=CSMVisualizadorXML-3.9.3-Instalador-Completo','VersionInfoVersion=3.9.3.0','PrivilegesRequired=lowest','progresso','Entender a Tributação','Motor Fiscal de Devolução','BrazilianPortuguese.isl'):
    if token not in s:raise SystemExit('Instalador 3.9.3 incompleto: '+token)
if 'PrivilegesRequired=admin' in s:raise SystemExit('Instalador ainda exige administrador')

p.write_text(s,encoding='utf-8',newline='\n')
print('ISS preparado e validado para CSM Visualizador XML 3.9.3.')
