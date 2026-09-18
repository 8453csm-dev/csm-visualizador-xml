from pathlib import Path
import re
p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8').replace('3.14.1','3.15.0')
s=re.sub(r'OutputBaseFilename=.*','OutputBaseFilename=CSMVisualizadorXML-3.15.0-Instalador-Completo',s,count=1)
s=re.sub(r'VersionInfoDescription=.*','VersionInfoDescription=CSM Visualizador XML 3.15.0 - Consulta pública oficial NF-e',s,count=1)
s=re.sub(r'VersionInfoVersion=[0-9.]+','VersionInfoVersion=3.15.0.0',s,count=1)
for t in ['#define AppVersion "3.15.0"','OutputBaseFilename=CSMVisualizadorXML-3.15.0-Instalador-Completo','VersionInfoVersion=3.15.0.0','Parameters: "--post-install-fresh"']:
    if t not in s: raise SystemExit('ISS 3.15.0 incompleto: '+t)
p.write_text(s,encoding='utf-8',newline='\n')
print('ISS 3.15.0 preparado.')
