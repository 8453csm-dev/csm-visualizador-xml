from pathlib import Path

MARKER='CSM_POSTINSTALL_FRESH_3112'
p=Path('installer-v2/prepare_release_3111.py')
if not p.exists():
    p=Path('installer-v2/prepare_release_3110.py')
s=p.read_text(encoding='utf-8')
if MARKER in s:
    print('Pós-instalação fresh 3.11.2 já aplicado')
    raise SystemExit(0)

# Em vez de abrir o app diretamente enquanto o instalador ainda está vivo,
# agenda uma abertura limpa alguns segundos depois. Isso evita reaproveitar
# broker/Core/WebView ainda pertencentes à instalação anterior.
old="""run_new='Filename: \"{app}\\\\{#AppExe}\"; WorkingDir: \"{app}\"; Description: \"Abrir CSM Visualizador XML 3.11.1\"; Flags: nowait postinstall skipifsilent'"""
if old not in s:
    old="""run_new='Filename: \"{app}\\\\{#AppExe}\"; WorkingDir: \"{app}\"; Description: \"Abrir CSM Visualizador XML 3.11.0\"; Flags: nowait postinstall skipifsilent'"""
new="""run_new='Filename: \"{cmd}\"; Parameters: \"/C timeout /T 3 /NOBREAK >NUL & start \\\"\\\" \\\"{app}\\\\{#AppExe}\\\" --post-install-fresh\"; WorkingDir: \"{app}\"; Description: \"Abrir CSM Visualizador XML 3.11.2\"; Flags: nowait postinstall skipifsilent'  # CSM_POSTINSTALL_FRESH_3112"""
if old not in s:
    raise RuntimeError('Linha run_new esperada não encontrada')
s=s.replace(old,new,1)

# Atualiza a versão alvo deste preparador para 3.11.2.
s=s.replace('3.11.1','3.11.2').replace('3.11.0','3.11.2')
p.write_text(s,encoding='utf-8',newline='\n')
print('Preparador ajustado: abertura pós-instalação atrasada e instância realmente nova.')
