from __future__ import annotations
import json,sys
from pathlib import Path

APP_VERSION='3.12.0'
MARKER='CSM_RELEASE_IDENTITY_3_12_0'
BUILD_NAME='CSM Fiscal Core 1.0 + NfeConsultaProtocolo + NFeDistribuicaoDFe + A1 Integrado + Zero Navegador'

if len(sys.argv)!=3:
    raise SystemExit('uso: patch_release_identity_3120.py <pasta-web> <pasta-csm>')
web,csm=Path(sys.argv[1]),Path(sys.argv[2]);app=web/'app.js'

# O pacote 3.11.5 já está montado. Elevamos a identidade após aplicar o Fiscal Core.
for p in web.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.js','.html','.css','.json'}: continue
    try:t=p.read_text(encoding='utf-8')
    except UnicodeDecodeError:continue
    u=t.replace('3.11.5','3.12.0')
    if u!=t:p.write_text(u,encoding='utf-8',newline='\n')

text=app.read_text(encoding='utf-8')
if MARKER not in text:text=text.rstrip()+f'\n// {MARKER} — {BUILD_NAME}\n'
app.write_text(text,encoding='utf-8',newline='\n')

csm.mkdir(parents=True,exist_ok=True)
info_path=csm/'build-info.json'
if not info_path.is_file():raise SystemExit('build-info anterior ausente')
info=json.loads(info_path.read_text(encoding='utf-8'))
info.update({
    'version':APP_VERSION,
    'build':BUILD_NAME,
    'native_fiscal_core':True,
    'native_fiscal_core_version':'1.0.0',
    'native_fiscal_core_executable':'CSM Fiscal Core.exe',
    'native_fiscal_core_official_webservices_only':True,
    'native_fiscal_core_certificate_source':'CSM_Certificados_Digitais',
    'native_fiscal_core_credential_manager':True,
    'native_fiscal_core_dpapi_fallback':True,
    'nfe_consulta_protocolo_v400':True,
    'nfe_distribuicao_dfe_v101':True,
    'nfe_distribution_cons_chave':True,
    'native_key_lookup_toolbar_button':'3.12.0',
    'native_key_lookup_browser_flow':False,
    'native_key_lookup_direct_broker':True,
    'native_key_lookup_progress_in_app':True,
    'native_key_lookup_hidden_provider':False,
    'native_key_lookup_provider_window_auto_close':False,
    'native_key_lookup_provider_fallback_enabled':False,
    'native_key_lookup_xml_only':True,
    'native_key_lookup_requires_actor_certificate_for_xml':True,
    'native_key_lookup_manifestation_auto':False,
})
info_path.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')

root=web.parent.parent
(root/'VERSION.txt').write_text(
    'CSM Visualizador XML 3.12.0\n'
    'CSM Fiscal Core 1.0 nativo\n'
    'Consulta de situação: NfeConsultaProtocolo 4.00\n'
    'Obtenção de documentos: NFeDistribuicaoDFe 1.01 / consChNFe\n'
    'Certificado A1 via integração CSM Certificados Digitais\n'
    'Senha protegida via Credential Manager com fallback DPAPI\n'
    'Sem navegador, scraping ou site externo no fluxo principal\n'
    'XML completo somente quando liberado oficialmente para o ator selecionado\n',
    encoding='utf-8',newline='\n')

final=app.read_text(encoding='utf-8')
for tok in (MARKER,'CSM_NATIVE_FISCAL_CORE_3120','/fiscal/certificates','/fiscal/nfe/consultar','csm-native-lookup-header','Empresa / certificado A1'):
    if tok not in final:raise SystemExit('Componente 3.12.0 ausente: '+tok)
dispatch=final[final.find('async function dispatchLookup'):final.find('\nfunction style(){',final.find('async function dispatchLookup'))]
for bad in ('/lookup-automation','open_lookup_site(','consultadanfe'):
    if bad in dispatch:raise SystemExit('Fluxo principal 3.12.0 ainda usa provedor web: '+bad)
print('Identidade 3.12.0 validada: CSM Fiscal Core nativo e Web Services oficiais.')
