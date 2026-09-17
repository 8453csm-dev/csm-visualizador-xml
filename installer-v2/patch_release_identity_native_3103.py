from __future__ import annotations

import json
import sys
from pathlib import Path

APP_VERSION='3.10.3'
MODULE_VERSION='1.0.0'
MARKER='CSM_NATIVE_NFE_LOOKUP_RELEASE_3103'


def main():
    if len(sys.argv)!=3:
        raise SystemExit('uso: patch_release_identity_native_3103.py <pasta-web> <pasta-csm>')
    web=Path(sys.argv[1]);csm=Path(sys.argv[2])
    app=web/'app.js';info_path=csm/'build-info.json'
    if not app.is_file() or not info_path.is_file():
        raise SystemExit('Execute a identidade 3.10.2 antes da identidade 3.10.3')

    changed=0
    for p in web.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in {'.js','.html','.css','.json'}:
            continue
        try:text=p.read_text(encoding='utf-8')
        except UnicodeDecodeError:continue
        updated=text.replace('3.10.2',APP_VERSION)
        if updated!=text:
            p.write_text(updated,encoding='utf-8',newline='\n');changed+=1

    info=json.loads(info_path.read_text(encoding='utf-8'))
    info['version']=APP_VERSION
    info['build']=str(info.get('build','')).strip()+' + Consulta NF-e Nativa '+MODULE_VERSION
    info['native_nfe_lookup']=MODULE_VERSION
    info['native_nfe_provider']='nfeio'
    info['native_nfe_cache']=True
    info['native_nfe_dpapi']=True
    info['native_nfe_loopback_guard']=True
    info_path.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')

    root=web.parent.parent
    version_file=root/'VERSION.txt'
    version_text=version_file.read_text(encoding='utf-8') if version_file.is_file() else ''
    lines=version_text.splitlines()
    if lines:
        lines[0]=f'CSM Visualizador XML {APP_VERSION}'
    else:
        lines=[f'CSM Visualizador XML {APP_VERSION}']
    if not any('Consulta NF-e Nativa' in line for line in lines):
        lines.append(f'Consulta NF-e Nativa {MODULE_VERSION}')
    version_file.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')

    app_text=app.read_text(encoding='utf-8')
    if MARKER not in app_text:
        app.write_text(app_text.rstrip()+f'\n// {MARKER} — Consulta NF-e pela chave dentro do Visualizador\n',encoding='utf-8',newline='\n')

    final_info=json.loads(info_path.read_text(encoding='utf-8'))
    for key in ('native_nfe_lookup','native_nfe_provider','native_nfe_cache','native_nfe_dpapi','native_nfe_loopback_guard'):
        if not final_info.get(key):
            raise SystemExit('Build-info sem '+key)
    index=(web/'index.html').read_text(encoding='utf-8')
    for token in ('native_nfe_lookup.js','native_nfe_lookup.css'):
        if token not in index:
            raise SystemExit('Payload 3.10.3 sem '+token)
    print(f'Identidade {APP_VERSION} aplicada; arquivos web atualizados: {changed}')


if __name__=='__main__':
    main()
