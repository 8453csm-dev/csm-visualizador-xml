from pathlib import Path
s=Path('installer-v2/CSMVisualizadorXML.iss').read_text(encoding='utf-8')
for t in ['AppVersion "3.15.0"','Parameters: "--post-install-fresh"','PreserveCSMPersistentData','/T /F /IM "CSM Visualizador XML Core.exe"']:
    if t not in s: raise SystemExit('Update fresh 3.15.0 incompleto: '+t)
print('OK - instalador 3.15.0 mantém atualização fresh.')
