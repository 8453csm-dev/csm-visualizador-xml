from __future__ import annotations
import json,sys
from pathlib import Path
if len(sys.argv)!=3: raise SystemExit('uso: patch_release_identity_3141.py <pasta-web> <pasta-csm>')
web,csm=Path(sys.argv[1]),Path(sys.argv[2])
for p in web.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.js','.html','.css','.json'}: continue
    try:t=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    u=t.replace('3.14.0','3.14.1')
    if u!=t:p.write_text(u,encoding='utf-8',newline='\n')
info_path=csm/'build-info.json'
info=json.loads(info_path.read_text(encoding='utf-8'))
info.update({
 'version':'3.14.1',
 'build':'CSM Consulta NF-e - Base CSM + autodiscovery SIEG/XML + DF-e',
 'native_fiscal_core_version':'3.14.1',
 'csm_xml_source_autodiscovery':True,
 'csm_sieg_drive_autodiscovery':True,
 'csm_key_lookup_no_fake_wait':True,
 'csm_source_selftest':True
})
info_path.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(web.parent.parent/'VERSION.txt').write_text('CSM Visualizador XML 3.14.1\nConsulta por chave com Base CSM + SIEG/XML autodetectado + DF-e\n',encoding='utf-8',newline='\n')
print('Identidade 3.14.1 aplicada.')
