from pathlib import Path
import re
p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8').replace('3.14.0','3.14.1')
s=re.sub(r'OutputBaseFilename=.*','OutputBaseFilename=CSMVisualizadorXML-3.14.1-Instalador-Completo',s,count=1)
s=re.sub(r'VersionInfoDescription=.*','VersionInfoDescription=CSM Visualizador XML 3.14.1 - consulta por chave com SIEG/XML autodetectado',s,count=1)
s=re.sub(r'VersionInfoVersion=[0-9.]+','VersionInfoVersion=3.14.1.0',s,count=1)
for t in ['#define AppVersion "3.14.1"','OutputBaseFilename=CSMVisualizadorXML-3.14.1-Instalador-Completo','VersionInfoVersion=3.14.1.0']:
    if t not in s: raise SystemExit('ISS 3.14.1 incompleto: '+t)
p.write_text(s,encoding='utf-8',newline='\n')
print('ISS 3.14.1 preparado.')
