from pathlib import Path
import sys

MARKER='CSM_NATIVE_LOOKUP_VISIBLE_3113'

if len(sys.argv)!=2:
    raise SystemExit('uso: patch_native_lookup_visibility_3113.py <pasta-web>')

app=Path(sys.argv[1])/'app.js'
text=app.read_text(encoding='utf-8')
if MARKER in text:
    print('Visibilidade 3.11.3 já aplicada')
    raise SystemExit(0)

start=text.find('function findActionHost(){')
setup_start=text.find('function setup(){', start)
ready_start=text.find("if(document.readyState==='loading')", setup_start)
if start<0 or setup_start<0 or ready_start<0:
    raise SystemExit('Blocos da Consulta NF-e não encontrados')

replacement=r'''// CSM_NATIVE_LOOKUP_VISIBLE_3113
function lookupHeaderScore(el){
  const t=normText(textOf(el));let score=t.includes('abrir pasta')?80:t.includes('abrir xml')?55:0;
  let p=el;
  for(let i=0;p&&i<7;i++,p=p.parentElement){
    const h=normText(`${p.id||''} ${p.className||''} ${p.getAttribute?.('role')||''}`);
    if(/topbar|toolbar|header|nav|actions|command/.test(h))score+=25;
  }
  try{const r=el.getBoundingClientRect();if(r.height>0&&r.top>=0&&r.top<125)score+=60;if(r.left>window.innerWidth*.35)score+=8}catch(_){}
  return score;
}
function findActionHost(){
  const refs=[...document.querySelectorAll('button,[role="button"]')]
    .filter(el=>visible(el)&&!isOwnNativeControl(el)&&(/abrir pasta|abrir xml/.test(normText(textOf(el)))))
    .sort((a,b)=>lookupHeaderScore(b)-lookupHeaderScore(a));
  if(refs.length){const ref=refs[0];return {host:ref.parentElement||document.body,ref}}
  for(const sel of ['.topbar-actions','.header-actions','.toolbar-actions','.actions']){
    const h=document.querySelector(sel);if(h)return {host:h,ref:h.querySelector('button,[role="button"]')}
  }
  return null;
}
function nativeButtonOnScreen(b){
  try{const r=b.getBoundingClientRect();if(r.width<=0||r.height<=0)return true;return r.right>0&&r.left<window.innerWidth&&r.bottom>0&&r.top<window.innerHeight}catch(_){return true}
}
function installButton(){
  let b=document.querySelector('[data-csm-native-lookup="1"]');
  const found=findActionHost();
  if(!b){
    b=document.createElement('button');b.type='button';b.dataset.csmNativeLookup='1';b.textContent='Consultar NF-e';b.title='Consultar NF-e pela chave de acesso (Ctrl+L)';b.onclick=()=>showModal();
  }
  if(found?.host&&found.ref){
    if(found.ref.className)b.className=found.ref.className;
    b.classList.remove('csm-native-lookup-fallback');
    if(found.ref.nextElementSibling!==b)found.ref.insertAdjacentElement('afterend',b);
    requestAnimationFrame(()=>{if(!nativeButtonOnScreen(b)){b.className='csm-native-lookup-fallback';document.body.appendChild(b)}});
  }else if(!b.isConnected){
    b.className='csm-native-lookup-fallback';document.body.appendChild(b);
  }
  return !!b.isConnected;
}
let lookupButtonObserver=null,lookupButtonTimer=null;
function maintainLookupButton(){
  installButton();
  if(!lookupButtonObserver&&document.body){
    let queued=false;
    lookupButtonObserver=new MutationObserver(()=>{if(queued)return;queued=true;setTimeout(()=>{queued=false;installButton()},30)});
    lookupButtonObserver.observe(document.body,{childList:true,subtree:true});
  }
  if(!lookupButtonTimer){let n=0;lookupButtonTimer=setInterval(()=>{installButton();if(++n>=40){clearInterval(lookupButtonTimer);lookupButtonTimer=null}},500)}
}
'''
text=text[:start]+replacement+text[setup_start:]

setup_start=text.find('function setup(){', start)
ready_start=text.find("if(document.readyState==='loading')", setup_start)
if setup_start<0 or ready_start<0:
    raise SystemExit('Setup da Consulta NF-e não encontrado após patch')
new_setup=r'''function setup(){
  if(window.__csmNativeLookupReady){maintainLookupButton();return}
  window.__csmNativeLookupReady=true;style();maintainLookupButton();
  document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&!e.altKey&&String(e.key).toLowerCase()==='l'){e.preventDefault();e.stopPropagation();showModal()}},true);
  window.CSMNativeKeyLookup={show:showModal,normalizeKey,keyMeta,version:MARK,ensureButton:installButton};
}
'''
text=text[:setup_start]+new_setup+text[ready_start:]

for tok in (MARKER,'maintainLookupButton','lookupHeaderScore','insertAdjacentElement(\'afterend\',b)','ensureButton:installButton'):
    if tok not in text:raise SystemExit('Patch 3.11.3 incompleto: '+tok)
app.write_text(text,encoding='utf-8',newline='\n')
print('3.11.3: botão Consultar NF-e fixado logo após Abrir pasta/XML e monitorado contra reconstrução do cabeçalho.')
