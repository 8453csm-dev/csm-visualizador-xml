from __future__ import annotations

import sys
from pathlib import Path

OLD_MARKER = 'CSM_FOLDER_IMPORT_PROGRESS_V1'
NEW_MARKER = 'CSM_FOLDER_IMPORT_PROGRESS_V2'

OLD_START = r'''async function openFolder(){
 await waitApi();
 let settled=false,sawBlur=false,focusTimer=null,fallbackTimer=null;
 const onBlur=()=>{sawBlur=true};window.addEventListener('blur',onBlur,{once:true});
 focusTimer=setInterval(()=>{if(!settled&&sawBlur&&document.hasFocus()){clearInterval(focusTimer);focusTimer=null;csmFolderImportShow()}},120);
 fallbackTimer=setTimeout(()=>{if(!settled&&!sawBlur)csmFolderImportShow()},900);
 if(els.folderBtn)els.folderBtn.disabled=true;if(els.welcomeFolderBtn)els.welcomeFolderBtn.disabled=true;
 try{
  const result=await window.pywebview.api.open_folder();settled=true;
  if(focusTimer)clearInterval(focusTimer);if(fallbackTimer)clearTimeout(fallbackTimer);'''

NEW_START = r'''async function openFolder(){
 await waitApi();
 // CSM_FOLDER_IMPORT_PROGRESS_V2 — pintar o feedback ANTES de abrir o diálogo nativo.
 // Não dependemos mais de blur/focus do Windows, que varia entre máquinas/WebView2.
 csmFolderImportShow('Selecione a pasta de XMLs...');
 if(els.folderBtn)els.folderBtn.disabled=true;if(els.welcomeFolderBtn)els.welcomeFolderBtn.disabled=true;
 await csmNextPaint();
 try{
  const result=await window.pywebview.api.open_folder();
  csmFolderImportStage('Lendo e validando os documentos...');'''

OLD_CATCH = r''' }catch(e){
  settled=true;if(focusTimer)clearInterval(focusTimer);if(fallbackTimer)clearTimeout(fallbackTimer);
  csmFolderImportError('Ocorreu um erro ao importar a pasta.');toast(`Não foi possível importar a pasta: ${e?.message||e}`,true)'''
NEW_CATCH = r''' }catch(e){
  csmFolderImportError('Ocorreu um erro ao importar a pasta.');toast(`Não foi possível importar a pasta: ${e?.message||e}`,true)'''


def patch(web: Path) -> None:
    app = web / 'app.js'
    if not app.is_file():
        raise SystemExit(f'app.js não encontrado em {web}')
    text = app.read_text(encoding='utf-8')
    if NEW_MARKER in text:
        print('Progresso imediato de pasta já aplicado.')
        return
    if OLD_MARKER not in text:
        raise SystemExit('Patch V1 de progresso não encontrado; abortando para preservar fluxo conhecido.')
    if OLD_START not in text:
        raise SystemExit('Trecho V1 de inicialização não encontrado.')
    text = text.replace(OLD_START, NEW_START, 1)
    if OLD_CATCH not in text:
        raise SystemExit('Trecho V1 de tratamento de erro não encontrado.')
    text = text.replace(OLD_CATCH, NEW_CATCH, 1)
    app.write_text(text, encoding='utf-8', newline='\n')

    final = app.read_text(encoding='utf-8')
    required = (
        NEW_MARKER,
        "csmFolderImportShow('Selecione a pasta de XMLs...')",
        'await csmNextPaint();',
        'const result=await window.pywebview.api.open_folder();',
        "csmFolderImportStage('Lendo e validando os documentos...')",
        'handleLoadResult(result,true)',
        'csmFolderImportFinish(count)',
    )
    for token in required:
        if token not in final:
            raise SystemExit('Validação V2 falhou: '+token)
    for forbidden in ('focusTimer=setInterval', 'fallbackTimer=setTimeout', "window.addEventListener('blur',onBlur"):
        if forbidden in final:
            raise SystemExit('Detecção frágil de foco ainda presente: '+forbidden)
    print('Progresso de pasta V2 aplicado: painel pintado antes do seletor nativo.')


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_folder_import_progress_v2.py <pasta-web>', file=sys.stderr)
        return 2
    patch(Path(sys.argv[1]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
