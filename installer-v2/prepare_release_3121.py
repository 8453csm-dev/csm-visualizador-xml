from pathlib import Path
import re
p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')
s=s.replace('3.12.0','3.12.1')
s=re.sub(r'OutputBaseFilename=.*','OutputBaseFilename=CSMVisualizadorXML-3.12.1-Instalador-Completo',s,count=1)
s=re.sub(r'VersionInfoDescription=.*','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.12.1 com Fiscal Core SOAP NF-e corrigido',s,count=1)
s=re.sub(r'VersionInfoVersion=[0-9.]+','VersionInfoVersion=3.12.1.0',s,count=1)
for token in ('#define AppVersion "3.12.1"','OutputBaseFilename=CSMVisualizadorXML-3.12.1-Instalador-Completo','VersionInfoVersion=3.12.1.0','Abrir CSM Visualizador XML 3.12.1'):
    if token not in s: raise SystemExit('Instalador 3.12.1 incompleto: '+token)
p.write_text(s,encoding='utf-8',newline='\n')
print('ISS preparado para 3.12.1.')
