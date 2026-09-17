from pathlib import Path
import sys

MARKER='CSM_LOOKUP_STATUS_TOAST_3112'

def main():
    if len(sys.argv)!=2: return 2
    app=Path(sys.argv[1])/'app.js'
    s=app.read_text(encoding='utf-8')
    if MARKER in s:
        print('Toast de situação 3.11.2 já aplicado')
        return 0
    old="""async function openExternalDocument(path){
 path=String(path||'').trim();if(!path)return;
 try{await waitApi();const result=await window.pywebview.api.open_recent(path);handleLoadResult(result);await acknowledgeExternalDocument(path)}catch(e){toast(`Não foi possível abrir ${path.split(/[\\\\/]/).pop()||'o XML'}: ${e?.message||e}`,true)}
}"""
    new="""async function openExternalDocument(path){
 path=String(path||'').trim();if(!path)return;
 try{
  await waitApi();const result=await window.pywebview.api.open_recent(path);handleLoadResult(result);await acknowledgeExternalDocument(path);
  const file=(path.split(/[\\\\/]/).pop()||''),m=file.match(/ - (AUTORIZADA|CANCELADA|DENEGADA|ENCONTRADA) - /i);
  if(m){const st=m[1].toUpperCase(),bad=st==='CANCELADA'||st==='DENEGADA';toast(`NF-e consultada: ${st}`,bad)}
 }catch(e){toast(`Não foi possível abrir ${path.split(/[\\\\/]/).pop()||'o XML'}: ${e?.message||e}`,true)}
} // CSM_LOOKUP_STATUS_TOAST_3112"""
    if old not in s:
        raise SystemExit('openExternalDocument esperado não encontrado')
    s=s.replace(old,new,1)
    app.write_text(s,encoding='utf-8',newline='\n')
    print('Frontend 3.11.2: situação da NF-e consultada exibida ao abrir o XML.')
    return 0

if __name__=='__main__': raise SystemExit(main())
