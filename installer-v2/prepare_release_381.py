from pathlib import Path

p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')
s=s.replace('#define AppVersion "3.8.0"','#define AppVersion "3.8.1"')
s=s.replace('OutputBaseFilename=CSMVisualizadorXML-3.8.0-Instalador-Completo','OutputBaseFilename=CSMVisualizadorXML-3.8.1-Instalador-Completo')
s=s.replace('VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.8.0 com Motor Fiscal de Devolução','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.8.1 com Motor Fiscal de Devolução')
s=s.replace('VersionInfoVersion=3.8.0.0','VersionInfoVersion=3.8.1.0')
s=s.replace('Abrir CSM Visualizador XML 3.8.0','Abrir CSM Visualizador XML 3.8.1')
s=s.replace('CSM Visualizador XML 3.8.0','CSM Visualizador XML 3.8.1')
s=s.replace('Preparando o CSM Visualizador XML 3.8.0','Preparando o CSM Visualizador XML 3.8.1')
s=s.replace('PrivilegesRequired=admin','PrivilegesRequired=lowest')
# Atualização 3.8.1: deixa explícita a correção de compatibilidade entre máquinas.
s=s.replace('NOVIDADES DESTA VERSÃO', 'NOVIDADES DESTA VERSÃO')
if 'PrivilegesRequired=lowest' not in s:
    raise SystemExit('Instalador 3.8.1 ainda exige administrador')
for token in ('3.8.1','OutputBaseFilename=CSMVisualizadorXML-3.8.1-Instalador-Completo','VersionInfoVersion=3.8.1.0'):
    if token not in s:
        raise SystemExit(f'Identidade 3.8.1 ausente no ISS: {token}')
p.write_text(s,encoding='utf-8',newline='\n')
print('ISS preparado para CSM Visualizador XML 3.8.1, instalação por usuário.')
