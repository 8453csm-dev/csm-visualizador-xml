from __future__ import annotations
import json,sys
from pathlib import Path

if len(sys.argv)!=3: raise SystemExit('uso: patch_release_identity_3121.py <pasta-web> <pasta-csm>')
web,csm=Path(sys.argv[1]),Path(sys.argv[2])
for p in web.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.js','.html','.css','.json'}: continue
    try: t=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    u=t.replace('3.12.0','3.12.1')
    if u!=t: p.write_text(u,encoding='utf-8',newline='\n')
info_path=csm/'build-info.json'
info=json.loads(info_path.read_text(encoding='utf-8'))
info.update({
  'version':'3.12.1',
  'build':'CSM Fiscal Core 3.12.1 - SOAP NF-e 4.00 corrigido + cUFAutor na Distribuicao DF-e',
  'nfe_consulta_protocolo_soap_contract_fixed':True,
  'nfe_distribuicao_dfe_cufautor':True,
  'native_fiscal_core':True,
  'native_fiscal_core_version':'3.12.1'
})
info_path.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
root=web.parent.parent
(root/'VERSION.txt').write_text('CSM Visualizador XML 3.12.1\nFiscal Core: SOAP Consulta Protocolo NF-e 4.00 corrigido\nDistribuicao DF-e: cUFAutor incluido\nConsulta nativa sem navegador preservada\n',encoding='utf-8',newline='\n')
print('Identidade 3.12.1 aplicada.')
