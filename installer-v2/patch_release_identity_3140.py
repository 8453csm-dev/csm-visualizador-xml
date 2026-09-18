from __future__ import annotations
import json,sys
from pathlib import Path

if len(sys.argv)!=3: raise SystemExit('uso: patch_release_identity_3140.py <pasta-web> <pasta-csm>')
web,csm=Path(sys.argv[1]),Path(sys.argv[2])
for p in web.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.js','.html','.css','.json'}: continue
    try: t=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    u=t.replace('3.13.1','3.14.0')
    if u!=t: p.write_text(u,encoding='utf-8',newline='\n')
info_path=csm/'build-info.json'
info=json.loads(info_path.read_text(encoding='utf-8'))
info.update({
  'version':'3.14.0',
  'build':'CSM Consulta NF-e API + Base CSM + distNSU oficial + consulta somente pela chave',
  'native_fiscal_core_version':'3.14.0',
  'csm_own_nfe_api':True,
  'csm_own_nfe_api_local_endpoint':'/api/nfe/by-key',
  'csm_repository_enabled':True,
  'csm_repository_dist_nsu':True,
  'csm_repository_summary_index':True,
  'csm_repository_auto_sync':True,
  'csm_repository_official_cooldown':True,
  'csm_repository_persistent_data':True,
  'csm_repository_indexes_opened_xml':True,
  'native_key_lookup_key_only':True,
  'native_key_lookup_certificate_visible':False,
  'nfe_manifestacao_ciencia_210210':True,
  'native_key_lookup_browser_flow':False,
  'fresh_update_launch':True,
  'persistent_data_root':'%LOCALAPPDATA%\\CSM\\VisualizadorXML'
})
info_path.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
root=web.parent.parent
(root/'VERSION.txt').write_text(
    'CSM Visualizador XML 3.14.0\n'
    'CSM Consulta NF-e API própria\n'
    'Consulta principal: somente chave de acesso\n'
    'Base CSM: XMLs locais + Distribuição DF-e oficial por distNSU\n'
    'Certificados A1 trabalham em segundo plano\n'
    'Atualização fresh: encerra runtime antigo antes de abrir a nova interface\n',
    encoding='utf-8',newline='\n')
print('Identidade 3.14.0 aplicada.')
