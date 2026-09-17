from pathlib import Path
import re

p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')
s=s.replace('3.11.5','3.12.0')
s=re.sub(r'OutputBaseFilename=.*','OutputBaseFilename=CSMVisualizadorXML-3.12.0-Instalador-Completo',s,count=1)
s=re.sub(r'VersionInfoDescription=.*','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.12.0 com CSM Fiscal Core nativo',s,count=1)
s=re.sub(r'VersionInfoVersion=[0-9.]+','VersionInfoVersion=3.12.0.0',s,count=1)
# Atualiza o texto principal de novidades, sem alterar a lógica homologada do instalador.
pat=r"'NOVIDADES DA VERSÃO 3\.12\.0'.*?'O instalador removerá versões antigas antes de instalar a 3\.12\.0\.';"
new="""'NOVIDADES DA VERSÃO 3.12.0' + #13#10 +
    '• Novo CSM Fiscal Core: consulta NF-e diretamente nos Web Services oficiais' + #13#10 +
    '• NfeConsultaProtocolo 4.00 para situação/protocolo da NF-e' + #13#10 +
    '• NFeDistribuicaoDFe 1.01 / consChNFe para obter XML quando autorizado' + #13#10 +
    '• Integração com certificados A1 do CSM Certificados Digitais' + #13#10 +
    '• Senhas protegidas via Credential Manager / DPAPI' + #13#10 +
    '• Nenhum navegador, scraping ou site externo no fluxo principal' + #13#10 +
    '• XML oficial é validado pela mesma chave antes de abrir no Visualizador' + #13#10 + #13#10 +
    'O instalador removerá versões antigas antes de instalar a 3.12.0.';"""
s,_=re.subn(pat,new,s,flags=re.S)
for token in ('#define AppVersion "3.12.0"','OutputBaseFilename=CSMVisualizadorXML-3.12.0-Instalador-Completo','VersionInfoVersion=3.12.0.0','Abrir CSM Visualizador XML 3.12.0'):
    if token not in s:raise SystemExit('Instalador 3.12.0 incompleto: '+token)
p.write_text(s,encoding='utf-8',newline='\n')

test=Path('installer-v2/test_installed.ps1')
if test.is_file():
    t=test.read_text(encoding='utf-8').replace('3.11.5','3.12.0').replace('CSM-3115','CSM-3120')
    test.write_text(t,encoding='utf-8',newline='\n')
print('ISS preparado para 3.12.0: CSM Fiscal Core nativo.')
