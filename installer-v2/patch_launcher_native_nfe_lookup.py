from pathlib import Path

MARKER='mux.HandleFunc("/nfe-lookup", b.handleNativeNfeLookup)'
p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')

if MARKER in s:
    print('Launcher ja possui as rotas da consulta nativa NF-e')
    raise SystemExit(0)

source=Path('installer-v2/launcher/native_nfe_lookup_windows.go')
if not source.is_file():
    raise SystemExit('Motor native_nfe_lookup_windows.go nao encontrado')

anchor='    mux.HandleFunc("/lookup-automation", b.handleLookupAutomation)\n'
if anchor not in s:
    anchor='\tmux.HandleFunc("/lookup-automation", b.handleLookupAutomation)\n'
if anchor not in s:
    raise SystemExit('Ancora /lookup-automation nao encontrada no launcher final')

indent='\t' if anchor.startswith('\t') else '    '
insert=(
    anchor+
    indent+'mux.HandleFunc("/nfe-lookup", b.handleNativeNfeLookup)\n'+
    indent+'mux.HandleFunc("/nfe-lookup/config", b.handleNativeNfeConfig)\n'
)
s=s.replace(anchor,insert,1)
p.write_text(s,encoding='utf-8',newline='\n')

final=p.read_text(encoding='utf-8')
for token in (
    'mux.HandleFunc("/nfe-lookup", b.handleNativeNfeLookup)',
    'mux.HandleFunc("/nfe-lookup/config", b.handleNativeNfeConfig)',
    'mux.HandleFunc("/lookup-automation", b.handleLookupAutomation)',
    'mux.HandleFunc("/events", b.handleEvents)',
):
    if token not in final:
        raise SystemExit('Launcher sem componente obrigatorio apos patch: '+token)

print('Launcher atualizado: consulta NF-e nativa integrada ao broker local.')
