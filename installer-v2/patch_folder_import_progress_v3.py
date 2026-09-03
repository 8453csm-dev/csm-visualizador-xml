from __future__ import annotations

import re, sys
from pathlib import Path

MARKER='CSM_FOLDER_IMPORT_PROGRESS_V3'

NEW_OPEN=r'''// CSM_FOLDER_IMPORT_PROGRESS_V3 — selecionar primeiro; bloquear somente durante a importação.
async function csmPickFolderNative(){
 const resp=await fetch('http://127.0.0.1:47878/pick-folder',{method:'POST'});
 let data=null;try{data=await resp.json()}catch(_){}
 if(!resp.ok||!data?.ok)throw new Error(data?.error||'Não foi possível abrir o seletor de pasta.');
 return data
}
async function csmListFolderNative(path){
 const resp=await fetch('http://127.0.0.1:47878/list-folder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path})});
 let data=null;try{data=await resp.json()}catch(_){}
 if(!resp.ok||!data?.ok)return {ok:false,error:data?.error||'Não foi possível analisar a pasta selecionada.'};
 return data
}
function csmFolderImportBusy(on){document.body.classList.toggle('csm-folder-import-busy',!!on)}
async function openFolder(){
 await waitApi();
 if(els.folderBtn)els.folderBtn.disabled=true;if(els.welcomeFolderBtn)els.welcomeFolderBtn.disabled=true;
 try{
  const picked=await csmPickFolderNative();
  if(picked?.cancelled||!picked?.path)return;
  csmFolderImportBusy(true);
  csmFolderImportShow('Preparando a pasta selecionada...');
  await csmNextPaint();
  const listing=await csmListFolderNative(picked.path);
  if(!listing?.ok){csmFolderImportError(listing?.error||'Não foi possível analisar a pasta.');toast(listing?.error||'Não foi possível analisar a pasta.',true);return}
  const paths=Array.isArray(listing.paths)?listing.paths:[];
  if(!paths.length){csmFolderImportError('Nenhum XML ou PDF fiscal foi encontrado nessa pasta.');return}
  const total=Number(listing.count||paths.length);
  csmFolderImportStage(`${total.toLocaleString('pt-BR')} documento${total===1?'':'s'} encontrado${total===1?'':'s'}. Lendo e validando...`);
  await csmNextPaint();
  const result=await window.pywebview.api.open_dropped_paths(paths);
  if(!result?.ok){csmFolderImportError(result?.error||'Não foi possível concluir a importação.');handleLoadResult(result,true);return}
  const count=(result.documents||[]).length;
  csmFolderImportStage(count?`Organizando ${count.toLocaleString('pt-BR')} documento${count===1?'':'s'} na tela...`:'Finalizando a importação...');
  await csmNextPaint();
  handleLoadResult(result,true);
  csmFolderImportFinish(count)
 }catch(e){
  csmFolderImportError('Ocorreu um erro ao importar a pasta.');toast(`Não foi possível importar a pasta: ${e?.message||e}`,true)
 }finally{
  csmFolderImportBusy(false);
  if(els.folderBtn)els.folderBtn.disabled=false;if(els.welcomeFolderBtn)els.welcomeFolderBtn.disabled=false
 }
}'''

CSS=r'''

/* CSM_FOLDER_IMPORT_PROGRESS_V3 — modal central e bloqueio durante a importação */
.csm-folder-import-progress{inset:0!important;right:auto!important;bottom:auto!important;width:auto!important;height:auto!important;padding:20px!important;border:0!important;border-radius:0!important;background:rgba(4,12,22,.62)!important;backdrop-filter:blur(3px);display:flex!important;align-items:center;justify-content:center;box-shadow:none!important;transform:none!important;pointer-events:none;}
.csm-folder-import-progress.show{opacity:1!important;transform:none!important;pointer-events:auto;}
.csm-folder-import-progress.done,.csm-folder-import-progress.error{pointer-events:none;}
.csm-folder-import-card{width:min(455px,calc(100vw - 36px));padding:22px 23px 19px;border:1px solid #31577f;border-radius:18px;background:#0d2035;box-shadow:0 24px 68px rgba(0,0,0,.48);color:#eef6ff;}
.csm-folder-import-card .csm-folder-import-head strong{font-size:15px}.csm-folder-import-card .csm-folder-import-status{font-size:12px;margin-top:5px}.csm-folder-import-card .csm-folder-import-foot{font-size:10px;margin-top:10px}.csm-folder-import-card .csm-folder-import-bar{height:5px;margin-top:15px}
body.csm-folder-import-busy{overflow:hidden!important;}
body.light .csm-folder-import-progress{background:rgba(28,47,67,.28)!important;}
body.light .csm-folder-import-card{background:#f9fcff;border-color:#b9d2e9;color:#173554;box-shadow:0 24px 60px rgba(31,66,102,.24)}
@media(max-width:640px){.csm-folder-import-progress{inset:0!important;width:auto!important;right:auto!important;bottom:auto!important;padding:12px!important}.csm-folder-import-card{width:100%;}}
'''


def patch(web:Path)->None:
    app=web/'app.js';css=web/'refinement.css'
    if not app.is_file() or not css.is_file():raise SystemExit('Arquivos web não encontrados')
    text=app.read_text(encoding='utf-8')
    if MARKER in text:
        print('Progresso V3 já aplicado.');return
    if 'CSM_FOLDER_IMPORT_PROGRESS_V2' not in text:raise SystemExit('V2 não encontrado')

    # O V1 criou o cartão diretamente na raiz. V3 adiciona um cartão central dentro do backdrop.
    old_html="box.innerHTML=`<div class=\"csm-folder-import-head\"><div class=\"csm-folder-import-spinner\" aria-hidden=\"true\"></div><div><strong>Importando pasta de XMLs</strong><div class=\"csm-folder-import-status\">Lendo e validando os documentos...</div></div></div><div class=\"csm-folder-import-bar\" aria-hidden=\"true\"><span></span></div><div class=\"csm-folder-import-foot\">O CSM continua trabalhando. Pastas grandes podem levar alguns instantes.</div>`;"
    new_html="box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.innerHTML=`<div class=\"csm-folder-import-card\"><div class=\"csm-folder-import-head\"><div class=\"csm-folder-import-spinner\" aria-hidden=\"true\"></div><div><strong>Importando documentos fiscais</strong><div class=\"csm-folder-import-status\">Preparando a pasta selecionada...</div></div></div><div class=\"csm-folder-import-bar\" aria-hidden=\"true\"><span></span></div><div class=\"csm-folder-import-foot\">Aguarde a conclusão. A interface fica temporariamente bloqueada para evitar comandos duplicados.</div></div>`;"
    if old_html not in text:raise SystemExit('Markup V1 esperado não encontrado')
    text=text.replace(old_html,new_html,1)

    start=text.find('async function openFolder(){')
    end=text.find('\nfunction handleLoadResult',start)
    if start<0 or end<0:raise SystemExit('Função openFolder não encontrada')
    text=text[:start]+NEW_OPEN+text[end:]

    # Bloqueia atalhos enquanto a importação está realmente em curso.
    anchor='function csmFolderImportBusy(on){document.body.classList.toggle(\'csm-folder-import-busy\',!!on)}'
    guard="""function csmFolderImportBusy(on){document.body.classList.toggle('csm-folder-import-busy',!!on)}
document.addEventListener('keydown',e=>{if(document.body.classList.contains('csm-folder-import-busy')){e.preventDefault();e.stopImmediatePropagation()}},true);"""
    if anchor not in text:raise SystemExit('Âncora de busy não encontrada')
    text=text.replace(anchor,guard,1)
    app.write_text(text,encoding='utf-8',newline='\n')

    c=css.read_text(encoding='utf-8')
    if MARKER not in c:css.write_text(c.rstrip()+CSS+'\n',encoding='utf-8',newline='\n')

    final=app.read_text(encoding='utf-8')
    required=(MARKER,"await csmPickFolderNative();","if(picked?.cancelled||!picked?.path)return;","csmFolderImportShow('Preparando a pasta selecionada...')","/list-folder","window.pywebview.api.open_dropped_paths(paths)",'csm-folder-import-busy')
    for tok in required:
        if tok not in final:raise SystemExit('V3 incompleto: '+tok)
    # Na nova função openFolder, o overlay deve vir depois da confirmação e open_folder antigo não pode ser chamado.
    fn=final[final.find('async function openFolder(){'):final.find('\nfunction handleLoadResult',final.find('async function openFolder(){'))]
    if 'window.pywebview.api.open_folder()' in fn:raise SystemExit('open_folder antigo ainda ativo')
    if fn.find("if(picked?.cancelled||!picked?.path)return;")>fn.find("csmFolderImportShow('Preparando a pasta selecionada...')"):raise SystemExit('Overlay aparece antes da confirmação')
    print('Progresso V3: seletor primeiro; modal central somente após confirmar a pasta.')


def main()->int:
    if len(sys.argv)!=2:return 2
    patch(Path(sys.argv[1]));return 0
if __name__=='__main__':raise SystemExit(main())
