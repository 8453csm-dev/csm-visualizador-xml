from pathlib import Path
import sys

MARKER='CSM_LOOKUP_EMBEDDED_3115'

if len(sys.argv)!=2:
    raise SystemExit('uso: patch_lookup_embedded_3115.py <pasta-web>')

app=Path(sys.argv[1])/'app.js'
s=app.read_text(encoding='utf-8')
if MARKER in s:
    print('Interface de consulta 3.11.5 já aplicada')
    raise SystemExit(0)

# O broker já entrega o XML ao app. Emita um evento para o modal saber quando
# a consulta terminou de verdade, em vez de fechar 1s após iniciar.
old="async function openExternalDocument(path){\n path=String(path||'').trim();if(!path)return;\n try{await waitApi();const result=await window.pywebview.api.open_recent(path);handleLoadResult(result);await acknowledgeExternalDocument(path)}catch(e){toast(`Não foi possível abrir ${path.split(/[\\\\/]/).pop()||'o XML'}: ${e?.message||e}`,true)}\n}"
new="async function openExternalDocument(path){\n path=String(path||'').trim();if(!path)return;\n try{await waitApi();const result=await window.pywebview.api.open_recent(path);handleLoadResult(result);window.dispatchEvent(new CustomEvent('csm:external-document-opened',{detail:{path,result}}));await acknowledgeExternalDocument(path)}catch(e){toast(`Não foi possível abrir ${path.split(/[\\\\/]/).pop()||'o XML'}: ${e?.message||e}`,true)}\n}"
if old not in s:
    raise SystemExit('openExternalDocument esperado não encontrado')
s=s.replace(old,new,1)

# Troca o botão flutuante da 3.11.4 por um botão real da barra superior.
start=s.find('// CSM_NATIVE_LOOKUP_FIXED_BUTTON_3114')
end=s.find('function setup(){',start)
if start<0 or end<0:
    raise SystemExit('Botão fixo 3.11.4 não encontrado')
button=r'''// CSM_LOOKUP_EMBEDDED_3115 — botão integrado à barra superior
function lookupToolbarTarget(){
  const all=[...document.querySelectorAll('button,[role="button"]')].filter(el=>!isOwnNativeControl(el));
  const folder=all.find(el=>normText(textOf(el)).includes('abrir pasta'));
  if(folder)return {host:folder.parentElement||document.querySelector('.topbar-actions'),ref:folder};
  const open=all.find(el=>normText(textOf(el)).includes('abrir xml'));
  if(open)return {host:open.parentElement||document.querySelector('.topbar-actions'),ref:open};
  const host=document.querySelector('.topbar-actions,.header-actions,.toolbar-actions');
  return host?{host,ref:host.querySelector('button,[role="button"]')}:null;
}
function installButton(){
  let b=document.getElementById('csm-native-lookup-header');
  document.querySelectorAll('[data-csm-native-lookup="1"]').forEach(el=>{if(el!==b)el.remove()});
  const target=lookupToolbarTarget();
  if(!target?.host)return null;
  if(!b){
    b=document.createElement('button');b.id='csm-native-lookup-header';b.type='button';b.dataset.csmNativeLookup='1';
    b.innerHTML='<span aria-hidden="true" style="font-size:14px;line-height:1">⌕</span><span>Consultar NF-e</span>';
    b.title='Consultar NF-e pela chave de acesso (Ctrl+L)';b.setAttribute('aria-label','Consultar NF-e pela chave de acesso');b.onclick=()=>showModal();
  }
  if(target.ref?.className)b.className=target.ref.className;
  Object.assign(b.style,{position:'static',inset:'auto',zIndex:'auto',display:'inline-flex',alignItems:'center',justifyContent:'center',gap:'6px',height:'32px',minHeight:'32px',padding:'0 11px',margin:'0',borderRadius:'7px',boxShadow:'none',whiteSpace:'nowrap',visibility:'visible',opacity:'1',pointerEvents:'auto',flex:'0 0 auto'});
  if(target.ref&&target.ref.nextElementSibling!==b)target.ref.insertAdjacentElement('afterend',b);
  else if(!b.isConnected)target.host.appendChild(b);
  return b;
}
let lookupButtonObserver=null,lookupButtonTimer=null;
function maintainLookupButton(){
  if(!document.body)return;
  installButton();
  if(!lookupButtonObserver){
    let queued=false;lookupButtonObserver=new MutationObserver(()=>{if(queued)return;queued=true;setTimeout(()=>{queued=false;installButton()},40)});
    lookupButtonObserver.observe(document.body,{childList:true,subtree:true});
  }
  if(!lookupButtonTimer){let n=0;lookupButtonTimer=setInterval(()=>{installButton();if(++n>30){clearInterval(lookupButtonTimer);lookupButtonTimer=null}},400)}
}
'''
s=s[:start]+button+s[end:]

# Mantém o modal aberto enquanto o motor oculto trabalha e fecha somente quando
# o XML efetivamente chega ao CSM.
old_go="go.onclick=async()=>{const key=refresh();if(!key){setStatus('A chave precisa ter 44 dígitos e um dígito verificador válido.','err');return}go.disabled=true;try{await dispatchLookup(key,setStatus);setStatus('Consulta iniciada. O XML será aberto automaticamente no CSM quando for localizado.','ok');renderHistory(hist,input,preview);setTimeout(()=>{if(o.isConnected)o.remove()},1100)}catch(e){setStatus(e?.message||String(e),'err');go.disabled=false}};"
new_go="let resultTimer=null;const onResult=e=>{const path=String(e?.detail?.path||'');if(!/\\.xml$/i.test(path))return;clearTimeout(resultTimer);window.removeEventListener('csm:external-document-opened',onResult);setStatus('XML localizado, validado e aberto no CSM.','ok');renderHistory(hist,input,preview);setTimeout(()=>{if(o.isConnected)o.remove()},700)};const cleanup=()=>{clearTimeout(resultTimer);window.removeEventListener('csm:external-document-opened',onResult)};const oldClose=close;const closeWithCleanup=()=>{cleanup();oldClose()};o.querySelector('.csm-nlk-x').onclick=closeWithCleanup;o.addEventListener('mousedown',e=>{if(e.target===o)closeWithCleanup()});go.onclick=async()=>{const key=refresh();if(!key){setStatus('A chave precisa ter 44 dígitos e um dígito verificador válido.','err');return}go.disabled=true;window.addEventListener('csm:external-document-opened',onResult);try{await dispatchLookup(key,setStatus);setStatus('Consultando em segundo plano… você pode continuar no CSM.','work');resultTimer=setTimeout(()=>{if(o.isConnected)setStatus('A consulta ainda está em andamento em segundo plano…','work')},15000)}catch(e){cleanup();setStatus(e?.message||String(e),'err');go.disabled=false}};"
if old_go not in s:
    raise SystemExit('Fluxo do botão Consultar no modal não encontrado')
s=s.replace(old_go,new_go,1)

# Atualiza a versão exposta pelo módulo.
s=s.replace("version:'3.11.4'","version:'3.11.5'",1)

for tok in (MARKER,'csm-native-lookup-header','lookupToolbarTarget','csm:external-document-opened','Consultando em segundo plano'):
    if tok not in s:raise SystemExit('Patch 3.11.5 incompleto: '+tok)
if "position:'fixed',top:'96px'" in s:
    raise SystemExit('Botão flutuante da 3.11.4 ainda presente')
app.write_text(s,encoding='utf-8',newline='\n')
print('3.11.5: botão integrado à toolbar e consulta exibida somente como progresso dentro do CSM.')
