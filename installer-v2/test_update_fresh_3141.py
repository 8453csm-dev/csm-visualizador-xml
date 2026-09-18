from pathlib import Path
s=Path('installer-v2/CSMVisualizadorXML.iss').read_text(encoding='utf-8')
for t in [
 'AppVersion "3.14.1"',
 'Parameters: "--post-install-fresh"',
 'PreserveCSMPersistentData',
 '/T /F /IM "CSM Visualizador XML Core.exe"',
 r'{localappdata}\CSM\VisualizadorXML'
]:
    if t not in s: raise SystemExit('Update fresh 3.14.1 incompleto: '+t)
print('OK - instalador 3.14.1 encerra runtime antigo, abre fresh e preserva dados persistentes.')
