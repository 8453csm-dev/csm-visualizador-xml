from __future__ import annotations
import json,sys
from pathlib import Path

if len(sys.argv)!=3: raise SystemExit('uso: patch_release_identity_3131.py <pasta-web> <pasta-csm>')
web,csm=Path(sys.argv[1]),Path(sys.argv[2])
for p in web.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.js','.html','.css','.json'}: continue
    try: t=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    u=t.replace('3.13.0','3.13.1')
    if u!=t: p.write_text(u,encoding='utf-8',newline='\n')
info_path=csm/'build-info.json'
info=json.loads(info_path.read_text(encoding='utf-8'))
info.update({
  'version':'3.13.1',
  'build':'CSM Fiscal Core 3.13.1 - NF-e própria com fontes XML/SIEG + abertura automática',
  'native_fiscal_core_version':'3.13.1',
  'nfe_issuer_cons_chave_restriction_641':True,
  'nfe_issuer_local_xml_sources':True,
  'nfe_local_xml_key_validation':True,
  'nfe_local_xml_auto_open':True,
  'nfe_xml_source_folder_manager':True,
  'nfe_native_workflow_3131':True,
  'native_key_lookup_browser_flow':False
})
info_path.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
root=web.parent.parent
(root/'VERSION.txt').write_text('CSM Visualizador XML 3.13.1\nConsulta NF-e oficial + certificados A1\nNF-e de entrada: Distribuição DF-e e Ciência 210210\nNF-e própria: procura XML original em pastas locais/SIEG\nXML localizado abre automaticamente no Visualizador\n',encoding='utf-8',newline='\n')
print('Identidade 3.13.1 aplicada.')
