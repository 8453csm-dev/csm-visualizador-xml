from pathlib import Path
import sys

MARKER='CSM_NATIVE_LOOKUP_DIRECT_3114'
BUTTON_MARKER='CSM_NATIVE_LOOKUP_FIXED_BUTTON_3114'

if len(sys.argv)!=2:
    raise SystemExit('uso: patch_native_lookup_core_3114.py <pasta-web>')

app=Path(sys.argv[1])/'app.js'
text=app.read_text(encoding='utf-8')
if MARKER in text:
    print('Consulta direta 3.11.4 já aplicada')
    raise SystemExit(0)

# 1) A consulta nativa NÃO toca mais no DOM do Localizador Fiscal legado.
#    Ela fala diretamente com o broker/helper compilado e abre a janela do
#    provedor já no formato XML. Isso elimina o clique acidental em Biblioteca
#    de XMLs / exportação Excel.
start=text.find('async function dispatchLookup(key,setStatus){')
end=text.find('\nfunction style(){', start)
if start<0 or end<0:
    raise SystemExit('dispatchLookup da Consulta NF-e não encontrado')

direct=r'''// CSM_NATIVE_LOOKUP_DIRECT_3114 — fluxo próprio, sem clicar em controles do Localizador legado
async function dispatchLookup(key,setStatus){
  const provider='consultadanfe',desired='xml';
  setStatus('Chave validada. Preparando consulta da NF-e…','work');
  await waitApi();

  let helperStarted=false;
  try{
    const resp=await fetch('http://127.0.0.1:47878/lookup-automation',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({provider,key,format:desired})
    });
    if(!resp.ok){
      let detail='';try{detail=await resp.text()}catch(_){}
      throw new Error(detail||`HTTP ${resp.status}`);
    }
    const data=await resp.json().catch(()=>({ok:true,started:true}));
    helperStarted=data?.started!==false;
  }catch(e){
    console.error('CSM Consulta NF-e: helper não iniciou',e);
    throw new Error('Não foi possível iniciar o motor de consulta da NF-e.');
  }
  if(!helperStarted)throw new Error('O motor de consulta da NF-e não foi iniciado.');

  setStatus('Consultando a NF-e e aguardando o XML…','work');
  const r=await window.pywebview.api.open_lookup_site(provider,key,desired);
  if(!r?.ok)throw new Error(r?.error||'Não foi possível abrir a consulta da NF-e.');

  saveHistory(key);
  console.info('CSM Consulta NF-e 3.11.4: fluxo direto broker/helper iniciado',r?.session_id||'');
  return true;
}
'''
text=text[:start]+direct+text[end:]

# 2) Botão próprio do CSM. Não é mais filho da toolbar (que pode ter overflow,
#    ser reconstruída ou esconder itens). Fica numa faixa fixa logo abaixo do
#    cabeçalho e é recriado se algum render o remover.
vis=text.find('// CSM_NATIVE_LOOKUP_VISIBLE_3113')
setup=text.find('function setup(){', vis if vis>=0 else 0)
if vis<0 or setup<0:
    raise SystemExit('Bloco visual 3.11.3 não encontrado para substituição')

button=r'''// CSM_NATIVE_LOOKUP_FIXED_BUTTON_3114 — botão próprio, fora de containers com overflow
function installButton(){
  let b=document.getElementById('csm-native-lookup-fixed');
  document.querySelectorAll('[data-csm-native-lookup="1"]').forEach(el=>{if(el!==b)el.remove()});
  if(!b){
    b=document.createElement('button');
    b.id='csm-native-lookup-fixed';b.type='button';b.dataset.csmNativeLookup='1';
    b.innerHTML='<span aria-hidden="true">⌕</span><span>Consultar NF-e</span>';
    b.title='Consultar NF-e pela chave de acesso (Ctrl+L)';
    b.setAttribute('aria-label','Consultar NF-e pela chave de acesso');
    b.onclick=()=>showModal();
    Object.assign(b.style,{
      position:'fixed',top:'96px',right:'18px',zIndex:'2147482000',display:'inline-flex',
      alignItems:'center',gap:'7px',height:'34px',padding:'0 13px',border:'1px solid #2f79bd',
      borderRadius:'9px',background:'#12365b',color:'#eef7ff',fontFamily:'Inter, Segoe UI, Arial, sans-serif',
      fontSize:'12px',fontWeight:'800',cursor:'pointer',boxShadow:'0 6px 18px rgba(0,0,0,.22)',
      whiteSpace:'nowrap',visibility:'visible',opacity:'1',pointerEvents:'auto'
    });
  }
  if(!b.isConnected)document.body.appendChild(b);
  return b;
}
let lookupButtonObserver=null;
function maintainLookupButton(){
  if(!document.body)return;
  installButton();
  if(!lookupButtonObserver){
    let queued=false;
    lookupButtonObserver=new MutationObserver(()=>{
      if(queued)return;queued=true;
      setTimeout(()=>{queued=false;if(!document.getElementById('csm-native-lookup-fixed'))installButton()},40);
    });
    lookupButtonObserver.observe(document.body,{childList:true,subtree:true});
  }
}
'''
text=text[:vis]+button+text[setup:]

# 3) Setup enxuto: botão fixo + Ctrl+L. Não mantém qualquer lógica antiga de
#    posicionamento na toolbar.
setup=text.find('function setup(){', text.find(BUTTON_MARKER))
ready=text.find("if(document.readyState==='loading')", setup)
if setup<0 or ready<0:
    raise SystemExit('Setup da Consulta NF-e não encontrado')
new_setup=r'''function setup(){
  if(window.__csmNativeLookupReady){maintainLookupButton();return}
  window.__csmNativeLookupReady=true;style();maintainLookupButton();
  document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&!e.altKey&&String(e.key).toLowerCase()==='l'){e.preventDefault();e.stopPropagation();showModal()}},true);
  window.CSMNativeKeyLookup={show:showModal,normalizeKey,keyMeta,version:'3.11.4',ensureButton:installButton};
}
'''
text=text[:setup]+new_setup+text[ready:]

# Garantias arquiteturais: dispatch não pode voltar a clicar no Localizador.
block=text[text.find(MARKER):text.find('\nfunction style(){',text.find(MARKER))]
for forbidden in ('findActionButton(','submitLookup(','getLegacyControls('):
    if forbidden in block:raise SystemExit('Fluxo direto ainda depende do Localizador legado: '+forbidden)
for required in (MARKER,BUTTON_MARKER,"/lookup-automation","open_lookup_site(provider,key,desired)","id='csm-native-lookup-fixed'"):
    if required not in text:raise SystemExit('Patch 3.11.4 incompleto: '+required)

app.write_text(text,encoding='utf-8',newline='\n')
print('3.11.4: Consulta NF-e usa broker/helper diretamente; botão próprio e persistente; zero cliques no Localizador legado.')
