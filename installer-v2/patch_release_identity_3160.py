from __future__ import annotations
import json,sys
from pathlib import Path
if len(sys.argv)!=3: raise SystemExit('uso: patch_release_identity_3160.py <pasta-web> <pasta-csm>')
web,csm=Path(sys.argv[1]),Path(sys.argv[2])
for p in web.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.js','.html','.css','.json'}: continue
    try:t=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    u=t.replace('3.15.0','3.16.0')
    if u!=t:p.write_text(u,encoding='utf-8',newline='\n')
info_path=csm/'build-info.json'
info=json.loads(info_path.read_text(encoding='utf-8'))
info.update({
 'version':'3.16.0',
 'build':'Consulta NF-e por chave via Meu Danfe API v2 + abertura XML nativa',
 'meudanfe_api_v2':True,
 'meudanfe_base_url':'https://api.meudanfe.com.br/v2',
 'meudanfe_api_key_credential_manager':True,
 'meudanfe_api_key_plaintext_storage':False,
 'meudanfe_get_xml_first':True,
 'meudanfe_add_by_key':True,
 'meudanfe_poll_min_ms':1200,
 'meudanfe_xml_key_validation':True,
 'native_key_lookup_opens_xml':True,
 'native_key_lookup_browser_flow':False,
 'native_key_lookup_requires_certificate':False,
 'native_key_lookup_requires_csm_repository':False,
 'public_nfe_visualization':False,
 'csm_repository_auto_sync':False,
 'fresh_update_launch':True
})
info_path.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(web.parent.parent/'VERSION.txt').write_text(
 'CSM Visualizador XML 3.16.0\n'
 'Consultar NF-e: chave -> Meu Danfe API v2 -> XML validado -> Visualizador\n'
 'Api-Key salva no Credential Manager do Windows\n'
 'Sem Base CSM, SIEG, certificado ou navegador no fluxo principal\n',
 encoding='utf-8',newline='\n')
print('Identidade 3.16.0 aplicada.')
