from __future__ import annotations
import json,sys
from pathlib import Path

if len(sys.argv)!=3: raise SystemExit('uso: patch_release_identity_3130.py <pasta-web> <pasta-csm>')
web,csm=Path(sys.argv[1]),Path(sys.argv[2])
for p in web.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.js','.html','.css','.json'}: continue
    try: t=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    u=t.replace('3.12.1','3.13.0')
    if u!=t: p.write_text(u,encoding='utf-8',newline='\n')
info_path=csm/'build-info.json'
info=json.loads(info_path.read_text(encoding='utf-8'))
info.update({
  'version':'3.13.0',
  'build':'CSM Fiscal Core 3.13.0 - Certificados A1 integrados + Ciencia 210210 + XML oficial para visualizacao/G5',
  'native_fiscal_core':True,
  'native_fiscal_core_version':'3.13.0',
  'certificate_folder_manager':True,
  'certificate_recursive_scan':True,
  'certificate_filename_password_pattern':True,
  'certificate_credential_manager':True,
  'certificate_dpapi_fallback':True,
  'certificate_public_paths_hidden':True,
  'certificate_public_ids':True,
  'nfe_manifestacao_ciencia_210210':True,
  'nfe_manifestacao_requires_user_confirmation':True,
  'nfe_distribution_retry_after_manifestation':True,
  'nfe_xml_cache':True,
  'nfe_xml_export_preserves_official_bytes':True,
  'nfe_native_workflow_3130':True,
  'native_key_lookup_browser_flow':False
})
info_path.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
root=web.parent.parent
(root/'VERSION.txt').write_text('CSM Visualizador XML 3.13.0\nFiscal Core nativo SEFAZ/Receita\nCertificados A1 integrados e protegidos\nCiência da Operação 210210 somente com confirmação\nXML oficial: visualizar no CSM ou salvar para G5\n',encoding='utf-8',newline='\n')
print('Identidade 3.13.0 aplicada.')
