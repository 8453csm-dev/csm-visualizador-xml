from __future__ import annotations
import json,re,sys
from pathlib import Path
APP_VERSION='3.9.6';MARKER='CSM_RELEASE_IDENTITY_3_9_6';DEV_VERSION='1.3.0';TAX_VERSION='1.0.2';BUILD_NAME='Entender a Tributacao 1.0.2 + Motor Fiscal de Devolucao 1.3 + Importacao Modal V3.1 Fullscreen + Startup Maximizado'
OLD=r'(?:3\.7\.8|3\.8\.0|3\.8\.1|3\.9\.0|3\.9\.1|3\.9\.2|3\.9\.3|3\.9\.4|3\.9\.5)(?:\.\d+)?'

def patch_text(text:str):
    pats=[
      (rf"(?i)(APP_VERSION\s*=\s*['\"]){OLD}(['\"])",rf"\g<1>{APP_VERSION}\g<2>"),
      (rf"(?i)(CURRENT_VERSION\s*=\s*['\"]){OLD}(['\"])",rf"\g<1>{APP_VERSION}\g<2>"),
      (rf"(?i)(\bappVersion\b\s*[:=]\s*['\"]){OLD}(['\"])",rf"\g<1>{APP_VERSION}\g<2>"),
      (rf"(?i)(\bcurrentVersion\b\s*[:=]\s*['\"]){OLD}(['\"])",rf"\g<1>{APP_VERSION}\g<2>"),
      (rf"(?i)(\bversion\b\s*:\s*['\"]){OLD}(['\"])",rf"\g<1>{APP_VERSION}\g<2>"),
      (rf"(?i)(data-version\s*=\s*['\"]){OLD}(['\"])",rf"\g<1>{APP_VERSION}\g<2>"),
      (rf"(?i)(Versão\s+){OLD}",rf"\g<1>{APP_VERSION}"),(rf"(?i)(Versao\s+){OLD}",rf"\g<1>{APP_VERSION}")]
    changed=0
    for pat,repl in pats:text,n=re.subn(pat,repl,text);changed+=n
    return text,changed

def patch_about(text:str):
    changed=0
    patterns=[
      (r"els\.aboutVersion\.textContent\s*=\s*`Versão\s+\$\{r\?\.version\|\|['\"][^'\"]+['\"]\}`",f"els.aboutVersion.textContent='Versão {APP_VERSION}'"),
      (r"els\.aboutVersion\.textContent\s*=\s*`Versão\s+\$\{r\.current\|\|['\"][^'\"]+['\"]\}`",f"els.aboutVersion.textContent='Versão {APP_VERSION}'")]
    for pat,repl in patterns:text,n=re.subn(pat,repl,text);changed+=n
    return text,changed

def main():
    if len(sys.argv)!=3:return 2
    web,csm=Path(sys.argv[1]),Path(sys.argv[2]);app=web/'app.js';total=0
    for p in web.rglob('*'):
      if not p.is_file() or p.suffix.lower() not in {'.js','.html','.css','.json'}:continue
      try:t=p.read_text(encoding='utf-8')
      except UnicodeDecodeError:continue
      u,n=patch_text(t)
      if p.name=='app.js':u,m=patch_about(u);n+=m
      if n:p.write_text(u,encoding='utf-8',newline='\n');total+=n
    t=app.read_text(encoding='utf-8')
    expected=f"els.aboutVersion.textContent='Versão {APP_VERSION}'"
    if t.count(expected)<2:raise SystemExit('Modal Sobre nao esta fixado em 3.9.6')
    if MARKER not in t:app.write_text(t.rstrip()+f'\n// {MARKER} — {BUILD_NAME}\n',encoding='utf-8',newline='\n')
    csm.mkdir(parents=True,exist_ok=True);root=web.parent.parent
    (root/'VERSION.txt').write_text(f'CSM Visualizador XML {APP_VERSION}\nMotor Fiscal de Devolucao {DEV_VERSION}\nEntender a Tributacao {TAX_VERSION}\nImportacao de Pasta Modal V3.1 Fullscreen\nStartup maximizado\nInstalador completo\n',encoding='utf-8',newline='\n')
    info={'product':'CSM Visualizador XML','version':APP_VERSION,'build':BUILD_NAME,'motor_devolucao':DEV_VERSION,'entender_tributacao':TAX_VERSION,'folder_import_progress':'3.1.0','complete_installer':True,'base_runtime':'3.7.8','entrypoint_deterministic':True,'tax_xml_direct':True,'tax_entry_activate_document':True,'tax_no_mutation_render_loop':True,'folder_progress_after_picker':True,'folder_progress_blocking_modal':True,'folder_progress_fullscreen':True,'folder_progress_background_locked':True,'folder_picker_native_broker':True,'startup_maximized':True}
    (csm/'build-info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    final=app.read_text(encoding='utf-8')
    for tok in (MARKER,'CSM_TAX_ENGINE_V1','CSM_TAX_EXPLAINER_UI_V1','CSM_TAX_EXPLAINER_ENTRYPOINT_V2','CSM_DEVOLUTION_ENTRYPOINT_V4','CSM_FOLDER_IMPORT_PROGRESS_V3'):
      if tok not in final:raise SystemExit('Componente ausente apos identidade: '+tok)
    print(f'Identidade {APP_VERSION} validada; alteracoes frontend: {total}')
    return 0
if __name__=='__main__':raise SystemExit(main())
