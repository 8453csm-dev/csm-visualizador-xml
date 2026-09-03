from __future__ import annotations

import sys
from pathlib import Path

JS_MARKER = 'CSM_FOLDER_IMPORT_PROGRESS_V1'
CSS_MARKER = 'CSM_FOLDER_IMPORT_PROGRESS_V1'

OLD_OPEN = "async function openFolder(){await waitApi();handleLoadResult(await window.pywebview.api.open_folder(),true)}"

NEW_OPEN = r'''// CSM_FOLDER_IMPORT_PROGRESS_V1
const csmFolderImportState={visible:false,hideTimer:null};
function csmFolderImportEnsure(){
 let box=document.getElementById('csmFolderImportProgress');
 if(box)return box;
 box=document.createElement('div');
 box.id='csmFolderImportProgress';
 box.className='csm-folder-import-progress';
 box.setAttribute('role','status');
 box.setAttribute('aria-live','polite');
 box.innerHTML=`<div class="csm-folder-import-head"><div class="csm-folder-import-spinner" aria-hidden="true"></div><div><strong>Importando pasta de XMLs</strong><div class="csm-folder-import-status">Lendo e validando os documentos...</div></div></div><div class="csm-folder-import-bar" aria-hidden="true"><span></span></div><div class="csm-folder-import-foot">O CSM continua trabalhando. Pastas grandes podem levar alguns instantes.</div>`;
 document.body.appendChild(box);return box
}
function csmFolderImportShow(status='Lendo e validando os documentos...'){
 const box=csmFolderImportEnsure(),txt=box.querySelector('.csm-folder-import-status');
 if(txt)txt.textContent=status;
 box.classList.remove('done','error');box.classList.add('show');
 csmFolderImportState.visible=true;
 if(csmFolderImportState.hideTimer){clearTimeout(csmFolderImportState.hideTimer);csmFolderImportState.hideTimer=null}
}
function csmFolderImportStage(status){
 csmFolderImportShow(status)
}
function csmFolderImportFinish(count){
 const box=csmFolderImportEnsure(),txt=box.querySelector('.csm-folder-import-status'),spin=box.querySelector('.csm-folder-import-spinner');
 const n=Number(count||0);if(txt)txt.textContent=n===1?'1 documento importado com sucesso.':`${n.toLocaleString('pt-BR')} documentos importados com sucesso.`;
 if(spin)spin.textContent='✓';box.classList.add('show','done');csmFolderImportState.visible=true;
 csmFolderImportState.hideTimer=setTimeout(()=>csmFolderImportHide(),1400)
}
function csmFolderImportError(message='Não foi possível concluir a importação.'){
 const box=csmFolderImportEnsure(),txt=box.querySelector('.csm-folder-import-status'),spin=box.querySelector('.csm-folder-import-spinner');
 if(txt)txt.textContent=message;if(spin)spin.textContent='!';box.classList.add('show','error');csmFolderImportState.visible=true;
 csmFolderImportState.hideTimer=setTimeout(()=>csmFolderImportHide(),2200)
}
function csmFolderImportHide(){
 const box=document.getElementById('csmFolderImportProgress');if(!box)return;
 box.classList.remove('show','done','error');const spin=box.querySelector('.csm-folder-import-spinner');if(spin)spin.textContent='';csmFolderImportState.visible=false
}
async function csmNextPaint(){await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}
async function openFolder(){
 await waitApi();
 let settled=false,sawBlur=false,focusTimer=null,fallbackTimer=null;
 const onBlur=()=>{sawBlur=true};window.addEventListener('blur',onBlur,{once:true});
 focusTimer=setInterval(()=>{if(!settled&&sawBlur&&document.hasFocus()){clearInterval(focusTimer);focusTimer=null;csmFolderImportShow()}},120);
 fallbackTimer=setTimeout(()=>{if(!settled&&!sawBlur)csmFolderImportShow()},900);
 if(els.folderBtn)els.folderBtn.disabled=true;if(els.welcomeFolderBtn)els.welcomeFolderBtn.disabled=true;
 try{
  const result=await window.pywebview.api.open_folder();settled=true;
  if(focusTimer)clearInterval(focusTimer);if(fallbackTimer)clearTimeout(fallbackTimer);
  if(!result?.ok){csmFolderImportHide();handleLoadResult(result,true);return}
  const count=(result.documents||[]).length;
  csmFolderImportStage(count?`Organizando ${count.toLocaleString('pt-BR')} documento${count===1?'':'s'} na tela...`:'Finalizando a importação...');
  await csmNextPaint();
  handleLoadResult(result,true);
  csmFolderImportFinish(count)
 }catch(e){
  settled=true;if(focusTimer)clearInterval(focusTimer);if(fallbackTimer)clearTimeout(fallbackTimer);
  csmFolderImportError('Ocorreu um erro ao importar a pasta.');toast(`Não foi possível importar a pasta: ${e?.message||e}`,true)
 }finally{
  if(els.folderBtn)els.folderBtn.disabled=false;if(els.welcomeFolderBtn)els.welcomeFolderBtn.disabled=false
 }
}'''

CSS = r'''

/* CSM_FOLDER_IMPORT_PROGRESS_V1 — feedback visual sem alterar o motor de importação */
.csm-folder-import-progress{position:fixed;right:22px;bottom:22px;width:min(390px,calc(100vw - 44px));z-index:100000;padding:14px 15px 12px;border:1px solid #29486d;border-radius:14px;background:rgba(12,29,50,.97);box-shadow:0 16px 42px rgba(0,0,0,.38);color:#eef6ff;opacity:0;transform:translateY(14px) scale(.985);pointer-events:none;transition:opacity .18s ease,transform .18s ease;font-family:inherit}
.csm-folder-import-progress.show{opacity:1;transform:translateY(0) scale(1)}
.csm-folder-import-head{display:flex;align-items:center;gap:11px}.csm-folder-import-head strong{display:block;font-size:13px;font-weight:800;letter-spacing:.05px}.csm-folder-import-status{margin-top:3px;color:#a8bfd8;font-size:11px;line-height:1.35}
.csm-folder-import-spinner{width:28px;height:28px;min-width:28px;border:3px solid rgba(114,177,244,.2);border-top-color:#4da3ff;border-radius:50%;animation:csm-folder-spin .8s linear infinite;display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:900;color:#5fd08b;box-sizing:border-box}
.csm-folder-import-bar{height:4px;margin-top:12px;overflow:hidden;border-radius:999px;background:rgba(115,164,214,.16)}.csm-folder-import-bar span{display:block;width:34%;height:100%;border-radius:inherit;background:#4da3ff;animation:csm-folder-indeterminate 1.15s ease-in-out infinite}
.csm-folder-import-foot{margin-top:8px;color:#7593b2;font-size:9.5px;line-height:1.3}.csm-folder-import-progress.done{border-color:#2d7653}.csm-folder-import-progress.done .csm-folder-import-spinner{border:1px solid rgba(95,208,139,.35);animation:none;background:rgba(95,208,139,.11)}.csm-folder-import-progress.done .csm-folder-import-bar span{width:100%;animation:none;background:#5fd08b}.csm-folder-import-progress.error{border-color:#824b55}.csm-folder-import-progress.error .csm-folder-import-spinner{border:1px solid rgba(240,111,129,.4);animation:none;color:#ff8192;background:rgba(240,111,129,.1)}.csm-folder-import-progress.error .csm-folder-import-bar span{width:100%;animation:none;background:#ef6b7d}
body.light .csm-folder-import-progress{background:rgba(249,252,255,.98);border-color:#c5d9ee;color:#173554;box-shadow:0 15px 38px rgba(31,66,102,.18)}body.light .csm-folder-import-status{color:#567695}body.light .csm-folder-import-foot{color:#7890a8}
@keyframes csm-folder-spin{to{transform:rotate(360deg)}}@keyframes csm-folder-indeterminate{0%{transform:translateX(-110%)}55%{transform:translateX(175%)}100%{transform:translateX(310%)}}
@media(max-width:640px){.csm-folder-import-progress{right:12px;bottom:12px;width:calc(100vw - 24px)}}
'''


def patch(web: Path) -> None:
    app = web / 'app.js'
    css = web / 'refinement.css'
    if not app.is_file() or not css.is_file():
        raise SystemExit(f'Arquivos web não encontrados em {web}')

    text = app.read_text(encoding='utf-8')
    if JS_MARKER not in text:
        if OLD_OPEN not in text:
            raise SystemExit('Função openFolder original não encontrada; abortando para não alterar fluxo desconhecido.')
        text = text.replace(OLD_OPEN, NEW_OPEN, 1)
        app.write_text(text, encoding='utf-8', newline='\n')
        print('Importação por pasta recebeu painel visual sem alterar a API open_folder.')
    else:
        print('Painel de importação por pasta já aplicado.')

    ctext = css.read_text(encoding='utf-8')
    if CSS_MARKER not in ctext:
        css.write_text(ctext.rstrip() + CSS + '\n', encoding='utf-8', newline='\n')
        print('Estilos do painel de importação aplicados.')

    final = app.read_text(encoding='utf-8')
    required = (
        JS_MARKER,
        'window.pywebview.api.open_folder()',
        'Organizando ${count.toLocaleString',
        'csmFolderImportFinish(count)',
        'handleLoadResult(result,true)',
        'if(els.folderBtn)els.folderBtn.disabled=true',
    )
    for token in required:
        if token not in final:
            raise SystemExit('Validação do progresso de pasta falhou: '+token)


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_folder_import_progress.py <pasta-web>', file=sys.stderr)
        return 2
    patch(Path(sys.argv[1]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
