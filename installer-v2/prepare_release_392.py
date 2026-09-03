from pathlib import Path
import re
p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')
s=re.sub(r'#define AppVersion "3\.8\.[01]"','#define AppVersion "3.9.2"',s)
s=re.sub(r'OutputBaseFilename=CSMVisualizadorXML-3\.8\.[01]-Instalador-Completo','OutputBaseFilename=CSMVisualizadorXML-3.9.2-Instalador-Completo',s)
s=re.sub(r'VersionInfoDescription=Instalador completo do CSM Visualizador XML 3\.8\.[01][^\r\n]*','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.9.2 com Entender a Tributacao e Motor Fiscal de Devolucao',s)
s=re.sub(r'VersionInfoVersion=3\.8\.[01]\.0','VersionInfoVersion=3.9.2.0',s)
s=s.replace('PrivilegesRequired=admin','PrivilegesRequired=lowest')
s=re.sub(r'CSM Visualizador XML 3\.8\.[01]', 'CSM Visualizador XML 3.9.2', s)
s=re.sub(r'versão 3\.8\.[01]', 'versão 3.9.2', s, flags=re.I)
for old in ('3.9.0','3.9.1'):
    s=s.replace(f'CSM Visualizador XML {old}', 'CSM Visualizador XML 3.9.2')
    s=s.replace(f'versão {old}', 'versão 3.9.2')
    s=s.replace(f'Versão {old}', 'Versão 3.9.2')
    s=s.replace(f'instalar a {old}', 'instalar a 3.9.2')
    s=s.replace(f'instalar a versão {old}', 'instalar a versão 3.9.2')
s=s.replace('NOVIDADES DA VERSÃO 3.9.0','NOVIDADES DA VERSÃO 3.9.2')
s=s.replace('• NOVO: Entender a Tributação — explica e confere os impostos diretamente do XML','• Entender a Tributação corrigido para aparecer em toda NF-e 55, inclusive na primeira nota aberta')
if 'Entender a Tributação' in s:
    s=s.replace('• Explicação simples para cliente e detalhamento técnico para a contabilidade','• Correção de congelamento e sincronização da aba com Documento / Itens')
for token in ('#define AppVersion "3.9.2"','OutputBaseFilename=CSMVisualizadorXML-3.9.2-Instalador-Completo','VersionInfoVersion=3.9.2.0','PrivilegesRequired=lowest','Entender a Tributação','Motor Fiscal de Devolução','BrazilianPortuguese.isl'):
    if token not in s:raise SystemExit('Instalador 3.9.2 incompleto: '+token)
if 'PrivilegesRequired=admin' in s:raise SystemExit('Instalador ainda exige administrador')
p.write_text(s,encoding='utf-8',newline='\n')
print('ISS preparado para CSM Visualizador XML 3.9.2.')
