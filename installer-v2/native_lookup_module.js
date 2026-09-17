// CSM_NATIVE_KEY_LOOKUP_V1
(function(){
'use strict';
const MARK='CSM_NATIVE_KEY_LOOKUP_V1';
const HISTORY_KEY='csm_native_nfe_lookup_history_v1';
const MAX_HISTORY=10;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function digitsOnly(v){return String(v||'').replace(/\D/g,'')}
function calcDv(base43){
  if(!/^\d{43}$/.test(base43))return -1;
  let sum=0,weight=2;
  for(let i=42;i>=0;i--){sum+=Number(base43[i])*weight;weight++;if(weight>9)weight=2}
  const mod=sum%11,dv=11-mod;
  return dv===10||dv===11?0:dv;
}
function normalizeKey(raw){
  const all=digitsOnly(raw);
  if(all.length===44&&calcDv(all.slice(0,43))===Number(all[43]))return all;
  if(all.length>44){
    for(let i=0;i<=all.length-44;i++){
      const k=all.slice(i,i+44);
      if(calcDv(k.slice(0,43))===Number(k[43]))return k;
    }
  }
  return '';
}
function keyMeta(key){
  return {uf:key.slice(0,2),aamm:key.slice(2,6),cnpj:key.slice(6,20),model:key.slice(20,22),series:String(Number(key.slice(22,25))),number:String(Number(key.slice(25,34)))};
}
function fmtKey(key){return key.replace(/(\d{4})(?=\d)/g,'$1 ').trim()}
function textOf(el){return String(el?.innerText||el?.textContent||el?.value||'').trim()}
function normText(v){return String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()}
function visible(el){if(!el)return false;const s=getComputedStyle(el);return s.display!=='none'&&s.visibility!=='hidden'&&s.opacity!=='0'}

function getHistory(){
  try{const v=JSON.parse(localStorage.getItem(HISTORY_KEY)||'[]');return Array.isArray(v)?v:[]}catch(_){return []}
}
function saveHistory(key){
  const meta=keyMeta(key),now=new Date().toISOString();
  const list=getHistory().filter(x=>x&&x.key!==key);
  list.unshift({key,number:meta.number,series:meta.series,model:meta.model,at:now});
  try{localStorage.setItem(HISTORY_KEY,JSON.stringify(list.slice(0,MAX_HISTORY)))}catch(_){}
}

function isOwnNativeControl(el){return !!(el?.matches?.('[data-csm-native-lookup="1"]')||el?.closest?.('#csm-native-lookup-overlay'))}
function findLocatorTrigger(){
  const els=[...document.querySelectorAll('button,[role="button"],a')].filter(el=>visible(el)&&!isOwnNativeControl(el));
  return els.find(el=>{const t=normText(textOf(el));return t.includes('localizador fiscal')||t==='localizador'||t.includes('consulta danfe')||t.includes('meu danfe')});
}
function inputScore(el){
  if(el.closest?.('#csm-native-lookup-overlay'))return -999;
  const hay=normText([el.id,el.name,el.placeholder,el.getAttribute('aria-label'),el.title].filter(Boolean).join(' '));
  let s=0;
  if(hay.includes('chave'))s+=12;
  if(hay.includes('acesso'))s+=5;
  if(hay.includes('nfe')||hay.includes('nf-e'))s+=4;
  if(Number(el.maxLength)===44)s+=8;
  if((el.inputMode||'').toLowerCase()==='numeric')s+=2;
  if(!visible(el))s-=3;
  return s;
}
function findKeyInput(){
  const list=[...document.querySelectorAll('input,textarea')].map(el=>({el,s:inputScore(el)})).sort((a,b)=>b.s-a.s);
  return list.length&&list[0].s>=7?list[0].el:null;
}
function setNativeValue(el,value){
  const proto=el instanceof HTMLTextAreaElement?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
  const setter=Object.getOwnPropertyDescriptor(proto,'value')?.set;
  if(setter)setter.call(el,value);else el.value=value;
  el.dispatchEvent(new Event('input',{bubbles:true}));
  el.dispatchEvent(new Event('change',{bubbles:true}));
}
function setProviderAndFormat(root){
  for(const sel of root.querySelectorAll?.('select')||[]){
    const options=[...sel.options];
    const p=options.find(o=>normText(o.textContent+' '+o.value).includes('consulta danfe'));
    if(p){sel.value=p.value;sel.dispatchEvent(new Event('change',{bubbles:true}));continue}
    const x=options.find(o=>/\bxml\b/i.test(o.textContent+' '+o.value));
    if(x){sel.value=x.value;sel.dispatchEvent(new Event('change',{bubbles:true}))}
  }
  for(const el of root.querySelectorAll?.('input[type="radio"],input[type="checkbox"]')||[]){
    const label=el.labels?.length?[...el.labels].map(textOf).join(' '):'';
    if(/\bxml\b/i.test(label+' '+el.value)){el.checked=true;el.dispatchEvent(new Event('change',{bubbles:true}))}
  }
}
function findActionButton(input){
  let root=input.parentElement;
  for(let depth=0;root&&depth<7;depth++,root=root.parentElement){
    const buttons=[...root.querySelectorAll('button,[role="button"],a')].filter(el=>!isOwnNativeControl(el));
    const hit=buttons.find(el=>{const t=normText(textOf(el));return /consultar|localizar|buscar|baixar/.test(t)&&!/historico|limpar/.test(t)});
    if(hit)return {button:hit,root};
  }
  return {button:null,root:input.parentElement||document};
}
async function getLegacyControls(){
  let input=findKeyInput();
  if(input)return input;
  const trigger=findLocatorTrigger();
  if(trigger){trigger.click();for(let i=0;i<20;i++){await sleep(100);input=findKeyInput();if(input)return input}}
  return null;
}
async function dispatchLookup(key,setStatus){
  setStatus('Abrindo o Localizador Fiscal interno…','work');
  const input=await getLegacyControls();
  if(!input)throw new Error('Não encontrei o Localizador Fiscal desta instalação.');
  const {button,root}=findActionButton(input);
  if(!button)throw new Error('Localizador encontrado, mas o botão de consulta não foi identificado.');
  setProviderAndFormat(root||document);
  setNativeValue(input,key);
  input.focus();
  setStatus('Chave validada. Consultando a NF-e…','work');
  button.click();
  saveHistory(key);
  return true;
}

function style(){
  if(document.getElementById('csm-native-lookup-style'))return;
  const s=document.createElement('style');s.id='csm-native-lookup-style';s.textContent=`
#csm-native-lookup-overlay{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;background:rgba(3,10,22,.72);backdrop-filter:blur(5px);padding:24px}
#csm-native-lookup-card{width:min(680px,calc(100vw - 40px));max-height:calc(100vh - 48px);overflow:auto;border:1px solid rgba(100,170,255,.24);border-radius:18px;background:linear-gradient(180deg,#101b2f,#0b1424);box-shadow:0 28px 80px rgba(0,0,0,.5);color:#eaf3ff;font-family:Inter,Segoe UI,Arial,sans-serif}
.csm-nlk-head{display:flex;justify-content:space-between;gap:20px;padding:22px 24px 12px}.csm-nlk-title{font-size:19px;font-weight:800}.csm-nlk-sub{margin-top:5px;color:#91a8c6;font-size:12px}.csm-nlk-x{border:0;background:transparent;color:#9db3cf;font-size:26px;cursor:pointer;line-height:1}
.csm-nlk-body{padding:12px 24px 24px}.csm-nlk-label{display:block;margin-bottom:8px;color:#a9bed8;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}.csm-nlk-row{display:flex;gap:10px}.csm-nlk-input{flex:1;min-width:0;border:1px solid #315174;border-radius:11px;background:#08111f;color:#f5f9ff;padding:13px 14px;font:600 13px ui-monospace,SFMono-Regular,Consolas,monospace;outline:none}.csm-nlk-input:focus{border-color:#55a5ff;box-shadow:0 0 0 3px rgba(85,165,255,.14)}
.csm-nlk-go{border:1px solid #2f84df;border-radius:11px;background:#1976d2;color:white;padding:0 18px;font-weight:800;cursor:pointer}.csm-nlk-go:disabled{opacity:.55;cursor:default}.csm-nlk-hint{margin-top:9px;color:#7189a8;font-size:11px}.csm-nlk-preview{display:none;margin-top:15px;padding:12px 14px;border:1px solid #263b56;border-radius:11px;background:#0b1728;color:#bcd0e8;font-size:12px}.csm-nlk-preview strong{color:#f1f7ff}.csm-nlk-status{min-height:18px;margin-top:13px;font-size:12px;color:#91a8c6}.csm-nlk-status.err{color:#ff9c9c}.csm-nlk-status.ok{color:#91e6b0}.csm-nlk-history{margin-top:20px;padding-top:16px;border-top:1px solid #24364e}.csm-nlk-history-title{font-size:11px;font-weight:800;color:#829ab8;text-transform:uppercase;letter-spacing:.08em}.csm-nlk-item{display:flex;justify-content:space-between;gap:12px;width:100%;margin-top:7px;padding:9px 10px;border:1px solid transparent;border-radius:9px;background:transparent;color:#b8cce4;cursor:pointer;text-align:left}.csm-nlk-item:hover{background:#10213a;border-color:#284666}.csm-nlk-item small{color:#6883a3}
.csm-native-lookup-fallback{position:fixed;right:18px;top:74px;z-index:9000;border:1px solid #2f79bd!important;border-radius:9px!important;background:#12365b!important;color:#eaf5ff!important;padding:8px 12px!important;font-weight:750!important;box-shadow:0 6px 18px rgba(0,0,0,.2)}
body.light #csm-native-lookup-card{background:linear-gradient(180deg,#fff,#f4f8fc);color:#17324d;border-color:#c9d9e8}body.light .csm-nlk-sub,body.light .csm-nlk-status{color:#617d9a}body.light .csm-nlk-input{background:#fff;color:#17324d;border-color:#b8cde0}body.light .csm-nlk-preview{background:#edf5fc;color:#35536f;border-color:#c5d7e7}body.light .csm-nlk-preview strong{color:#17324d}`;
  document.head.appendChild(s);
}
function renderHistory(box,input,preview){
  const list=getHistory();box.innerHTML='<div class="csm-nlk-history-title">Consultas recentes</div>';
  if(!list.length){box.insertAdjacentHTML('beforeend','<div class="csm-nlk-hint">As chaves consultadas aparecerão aqui.</div>');return}
  for(const h of list){
    const b=document.createElement('button');b.type='button';b.className='csm-nlk-item';b.innerHTML=`<span>NF-e ${h.number||'—'} <small>• Série ${h.series||'—'}</small></span><small>${fmtKey(h.key).slice(0,24)}…</small>`;
    b.onclick=()=>{input.value=h.key;input.dispatchEvent(new Event('input',{bubbles:true}));input.focus()};box.appendChild(b);
  }
}
function showModal(prefill=''){
  style();document.getElementById('csm-native-lookup-overlay')?.remove();
  const o=document.createElement('div');o.id='csm-native-lookup-overlay';o.innerHTML=`<div id="csm-native-lookup-card"><div class="csm-nlk-head"><div><div class="csm-nlk-title">Consultar NF-e pela chave</div><div class="csm-nlk-sub">Cole a chave de acesso. O CSM localiza o documento e abre a nota no próprio Visualizador.</div></div><button class="csm-nlk-x" type="button" aria-label="Fechar">×</button></div><div class="csm-nlk-body"><label class="csm-nlk-label">Chave de acesso</label><div class="csm-nlk-row"><input class="csm-nlk-input" inputmode="numeric" autocomplete="off" spellcheck="false" placeholder="44 dígitos da chave de acesso"><button class="csm-nlk-go" type="button">Consultar</button></div><div class="csm-nlk-hint">Aceita chave com espaços, pontos, traços ou copiada junto com outro texto.</div><div class="csm-nlk-preview"></div><div class="csm-nlk-status"></div><div class="csm-nlk-history"></div></div></div>`;
  document.body.appendChild(o);
  const input=o.querySelector('.csm-nlk-input'),go=o.querySelector('.csm-nlk-go'),preview=o.querySelector('.csm-nlk-preview'),status=o.querySelector('.csm-nlk-status'),hist=o.querySelector('.csm-nlk-history');
  const close=()=>o.remove();o.querySelector('.csm-nlk-x').onclick=close;o.addEventListener('mousedown',e=>{if(e.target===o)close()});
  const setStatus=(msg,kind='')=>{status.textContent=msg;status.className='csm-nlk-status '+(kind==='err'?'err':kind==='ok'?'ok':'')};
  const refresh=()=>{const key=normalizeKey(input.value);if(!key){preview.style.display='none';return ''}const m=keyMeta(key);preview.style.display='block';preview.innerHTML=`<strong>NF-e ${m.number}</strong> • Série ${m.series} • Modelo ${m.model}<br><span>${fmtKey(key)}</span>`;return key};
  input.addEventListener('input',refresh);
  input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();go.click()}else if(e.key==='Escape')close()});
  go.onclick=async()=>{const key=refresh();if(!key){setStatus('A chave precisa ter 44 dígitos e um dígito verificador válido.','err');return}go.disabled=true;try{await dispatchLookup(key,setStatus);setStatus('Consulta iniciada. O XML será aberto automaticamente no CSM quando for localizado.','ok');renderHistory(hist,input,preview);setTimeout(()=>{if(o.isConnected)o.remove()},1100)}catch(e){setStatus(e?.message||String(e),'err');go.disabled=false}};
  renderHistory(hist,input,preview);input.value=prefill||'';refresh();setTimeout(()=>{input.focus();input.select()},30);
}
function findActionHost(){
  const refs=[...document.querySelectorAll('button,[role="button"]')].filter(el=>{const t=normText(textOf(el));return t.includes('abrir xml')||t.includes('abrir pasta')});
  if(refs.length){let p=refs[0].parentElement;for(let i=0;p&&i<4;i++,p=p.parentElement){if(p.querySelectorAll('button,[role="button"]').length>=2)return {host:p,ref:refs[0]}}return {host:refs[0].parentElement,ref:refs[0]}}
  for(const sel of ['.topbar-actions','.header-actions','.toolbar-actions','.actions']){const h=document.querySelector(sel);if(h)return {host:h,ref:h.querySelector('button')}}
  return null;
}
function installButton(){
  if(document.querySelector('[data-csm-native-lookup="1"]'))return true;
  const found=findActionHost(),b=document.createElement('button');b.type='button';b.dataset.csmNativeLookup='1';b.textContent='🔎 Consultar NF-e';b.title='Consultar NF-e pela chave de acesso (Ctrl+L)';b.onclick=()=>showModal();
  if(found?.host){if(found.ref?.className)b.className=found.ref.className;found.host.appendChild(b)}else{b.className='csm-native-lookup-fallback';document.body.appendChild(b)}
  return true;
}
function setup(){
  if(window.__csmNativeLookupReady)return;window.__csmNativeLookupReady=true;style();installButton();setTimeout(installButton,600);setTimeout(installButton,1800);
  document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&!e.altKey&&String(e.key).toLowerCase()==='l'){e.preventDefault();e.stopPropagation();showModal()}},true);
  window.CSMNativeKeyLookup={show:showModal,normalizeKey,keyMeta,version:MARK};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',setup,{once:true});else setTimeout(setup,0);
})();
