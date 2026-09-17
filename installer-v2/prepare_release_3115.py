from pathlib import Path
import re

p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')
s=s.replace('3.11.4','3.11.5')
s=re.sub(r'OutputBaseFilename=.*','OutputBaseFilename=CSMVisualizadorXML-3.11.5-Instalador-Completo',s,count=1)
s=re.sub(r'VersionInfoDescription=.*','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.11.5 com Consulta NF-e integrada e oculta',s,count=1)
s=re.sub(r'VersionInfoVersion=[0-9.]+','VersionInfoVersion=3.11.5.0',s,count=1)
# Atualiza o texto de novidades sem mexer na lógica do instalador já homologada.
pat=r"'NOVIDADES DA VERSÃO 3\.11\.5'.*?'O instalador removerá versões antigas antes de instalar a 3\.11\.5\.';"
new="""'NOVIDADES DA VERSÃO 3.11.5' + #13#10 +
    '• Consultar NF-e integrado à barra superior do aplicativo' + #13#10 +
    '• O site de apoio roda oculto em segundo plano, sem abrir uma segunda tela' + #13#10 +
    '• O andamento da consulta aparece dentro do CSM' + #13#10 +
    '• A janela externa é encerrada automaticamente ao concluir' + #13#10 +
    '• Se houver desafio manual, a janela é exibida somente enquanto for necessária' + #13#10 +
    '• XML validado pela chave; Excel/CSV/Biblioteca de XMLs continuam bloqueados' + #13#10 + #13#10 +
    'O instalador removerá versões antigas antes de instalar a 3.11.5.';"""
s,n=re.subn(pat,new,s,flags=re.S)
if n==0:
    # O prepare 3.11.4 pode deixar uma redação diferente; versão e binário ainda
    # ficam corretos, então só garantimos os tokens essenciais abaixo.
    pass
for token in ('#define AppVersion "3.11.5"','OutputBaseFilename=CSMVisualizadorXML-3.11.5-Instalador-Completo','VersionInfoVersion=3.11.5.0','Abrir CSM Visualizador XML 3.11.5'):
    if token not in s: raise SystemExit('Instalador 3.11.5 incompleto: '+token)
p.write_text(s,encoding='utf-8',newline='\n')

test=Path('installer-v2/test_installed.ps1')
if test.is_file():
    t=test.read_text(encoding='utf-8').replace('3.11.4','3.11.5').replace('CSM-3114','CSM-3115')
    test.write_text(t,encoding='utf-8',newline='\n')
print('ISS preparado para 3.11.5: consulta integrada e provedor oculto.')
