from __future__ import annotations
import json,sys
from pathlib import Path

if len(sys.argv)!=3: raise SystemExit('uso: patch_release_identity_3150.py <pasta-web> <pasta-csm>')
web,csm=Path(sys.argv[1]),Path(sys.argv[2])
for p in web.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.js','.html','.css','.json'}: continue
    try:t=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    u=t.replace('3.14.1','3.15.0')
    if u!=t:p.write_text(u,encoding='utf-8',newline='\n')
info_path=csm/'build-info.json'
info=json.loads(info_path.read_text(encoding='utf-8'))
info.update({
 'version':'3.15.0',
 'build':'Consulta pública oficial NF-e para visualização dentro do CSM',
 'public_nfe_visualization':True,
 'public_nfe_official_portal':True,
 'public_nfe_portal_url':'https://www.nfe.fazenda.gov.br/portal/consultaRecaptcha.aspx',
 'public_nfe_hcaptcha_user_assisted':True,
 'public_nfe_requires_xml':False,
 'public_nfe_requires_certificate':False,
 'public_nfe_requires_csm_repository':False,
 'public_nfe_opens_pdf_in_viewer':True,
 'public_nfe_provider':'sefazpublica',
 'csm_repository_auto_sync':False,
 'native_key_lookup_key_only':True,
 'fresh_update_launch':True
})
info_path.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(web.parent.parent/'VERSION.txt').write_text(
 'CSM Visualizador XML 3.15.0\n'
 'Consulta pública oficial NF-e: somente chave para visualização\n'
 'Sem XML, sem certificado e sem Base CSM no fluxo principal\n'
 'hCaptcha da Receita é exibido somente quando exigido\n'
 'Consulta Completa é capturada e aberta como PDF fiscal no Visualizador\n',
 encoding='utf-8',newline='\n')
print('Identidade 3.15.0 aplicada.')
