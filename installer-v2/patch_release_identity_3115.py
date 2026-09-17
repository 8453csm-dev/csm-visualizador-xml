from __future__ import annotations
import json,re,sys
from pathlib import Path

APP_VERSION='3.11.5'
MARKER='CSM_RELEASE_IDENTITY_3_11_5'
BUILD_NAME='Consulta NF-e 3.11.5 Integrada + Provedor Oculto + Progresso no App + Fechamento Automatico + XML Seguro'

if len(sys.argv)!=3:
    raise SystemExit('uso: patch_release_identity_3115.py <pasta-web> <pasta-csm>')
web,csm=Path(sys.argv[1]),Path(sys.argv[2])
app=web/'app.js'

# A identidade 3.11.4 já foi aplicada antes deste patch. Aqui elevamos somente
# o pacote final e registramos a nova arquitetura visual/oculta.
for p in web.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.js','.html','.css','.json'}: continue
    try: t=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    u=t.replace('3.11.4','3.11.5')
    if u!=t: p.write_text(u,encoding='utf-8',newline='\n')

text=app.read_text(encoding='utf-8')
if MARKER not in text:
    text=text.rstrip()+f'\n// {MARKER} — {BUILD_NAME}\n'
app.write_text(text,encoding='utf-8',newline='\n')

csm.mkdir(parents=True,exist_ok=True)
info_path=csm/'build-info.json'
if not info_path.is_file(): raise SystemExit('build-info 3.11.4 ausente')
info=json.loads(info_path.read_text(encoding='utf-8'))
info.update({
    'version':APP_VERSION,
    'build':BUILD_NAME,
    'native_key_lookup_toolbar_button':'3.11.5',
    'native_key_lookup_fixed_button':False,
    'native_key_lookup_button_body_level':False,
    'native_key_lookup_progress_in_app':True,
    'native_key_lookup_hidden_provider':True,
    'native_key_lookup_provider_window_auto_close':True,
    'native_key_lookup_provider_visible_only_for_manual_challenge':True,
})
info_path.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')

root=web.parent.parent
(root/'VERSION.txt').write_text(
    'CSM Visualizador XML 3.11.5\n'
    'Consulta NF-e integrada à barra superior\n'
    'Consulta externa executada em segundo plano, sem segunda tela visível\n'
    'Progresso exibido dentro do CSM e janela externa encerrada automaticamente\n'
    'Janela externa somente é exibida se houver desafio que exija intervenção manual\n'
    'Somente XML validado pela chave; Excel/CSV/Biblioteca de XMLs bloqueados\n',
    encoding='utf-8',newline='\n')

final=app.read_text(encoding='utf-8')
for tok in (MARKER,'CSM_LOOKUP_EMBEDDED_3115','csm-native-lookup-header','csm:external-document-opened','Consultando em segundo plano','CSM_NATIVE_LOOKUP_DIRECT_3114','/lookup-automation'):
    if tok not in final: raise SystemExit('Componente 3.11.5 ausente: '+tok)
if 'csm-native-lookup-fixed' in final:
    raise SystemExit('Botão flutuante antigo ainda presente')
if "position:'fixed',top:'96px'" in final:
    raise SystemExit('Estilo flutuante antigo ainda presente')
print('Identidade 3.11.5 validada: botão integrado + progresso no app + provedor oculto.')
