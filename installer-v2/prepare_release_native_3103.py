from pathlib import Path

VERSION='3.10.3'
p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')

# Parte sempre da preparacao 3.10.2, ja homologada, e altera apenas identidade/novidade desta beta.
s=s.replace('3.10.2',VERSION)
s=s.replace('OutputBaseFilename=CSMVisualizadorXML-3.10.3-Instalador-Completo','OutputBaseFilename=CSMVisualizadorXML-3.10.3-Consulta-NFe-Beta')
s=s.replace('VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.10.3 com DIFAL e ICMS ST','VersionInfoDescription=CSM Visualizador XML 3.10.3 Beta com Consulta NF-e Nativa')

needle="    'NOVIDADES DA VERSÃO 3.10.3' + #13#10 +\n"
extra=(
    "    'NOVIDADES DA VERSÃO 3.10.3' + #13#10 +\n"
    "    '• Nova consulta de NF-e pela chave de acesso sem abrir navegador' + #13#10 +\n"
    "    '• XML localizado abre diretamente nas abas normais do Visualizador' + #13#10 +\n"
    "    '• Cache local evita nova consulta da mesma chave já recuperada' + #13#10 +\n"
    "    '• Credencial da API protegida pelo Windows (DPAPI)' + #13#10 +\n"
)
if needle not in s:
    raise SystemExit('Bloco de novidades 3.10.3 nao encontrado no ISS')
s=s.replace(needle,extra,1)

for token in (
    '#define AppVersion "3.10.3"',
    'OutputBaseFilename=CSMVisualizadorXML-3.10.3-Consulta-NFe-Beta',
    'VersionInfoVersion=3.10.3.0',
    'Consulta NF-e Nativa',
    'WorkingDir: "{app}"; Description: "Abrir CSM Visualizador XML 3.10.3"',
):
    if token not in s:
        raise SystemExit('Instalador beta 3.10.3 incompleto: '+token)

p.write_text(s,encoding='utf-8',newline='\n')
print('ISS preparado para CSM Visualizador XML 3.10.3 Beta - Consulta NF-e Nativa.')
