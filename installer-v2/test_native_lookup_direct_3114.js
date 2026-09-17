const fs=require('fs');
const {JSDOM}=require('jsdom');
const app=process.env.CSM_APP_JS;
if(!app||!fs.existsSync(app))throw new Error('CSM_APP_JS ausente');
const src=fs.readFileSync(app,'utf8');

for(const tok of ['CSM_NATIVE_LOOKUP_DIRECT_3114','CSM_NATIVE_LOOKUP_FIXED_BUTTON_3114','/lookup-automation','open_lookup_site(provider,key,desired)',"csm-native-lookup-fixed"]){
  if(!src.includes(tok))throw new Error('Token 3.11.4 ausente: '+tok);
}
const ds=src.indexOf('async function dispatchLookup(key,setStatus){',src.indexOf('CSM_NATIVE_LOOKUP_DIRECT_3114'));
const de=src.indexOf('\nfunction style(){',ds);
if(ds<0||de<0)throw new Error('dispatchLookup 3.11.4 não localizado');
const dispatch=src.slice(ds,de);
for(const forbidden of ['findActionButton(','submitLookup(','getLegacyControls(','button.click()']){
  if(dispatch.includes(forbidden))throw new Error('Consulta 3.11.4 ainda usa ação legada: '+forbidden);
}
if(!dispatch.includes("provider='consultadanfe',desired='xml'"))throw new Error('Consulta não força provider/XML');

const start=src.lastIndexOf('// CSM_NATIVE_KEY_LOOKUP_V1');
const end=src.indexOf('\n})();',start);
if(start<0||end<0)throw new Error('Módulo nativo não localizado');
const moduleSrc=src.slice(start,end+6);
const dom=new JSDOM('<!doctype html><html><head></head><body><div class="topbar-actions"><button>Abrir XML/PDF</button><button>Abrir pasta</button><button>Salvar PDF</button></div></body></html>',{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window;
w.eval(moduleSrc);
w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
const wait=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  await wait(80);
  let b=w.document.getElementById('csm-native-lookup-fixed');
  if(!b)throw new Error('Botão próprio Consultar NF-e não foi criado');
  if(b.parentElement!==w.document.body)throw new Error('Botão ainda está preso à toolbar/containers legados');
  if(b.style.position!=='fixed')throw new Error('Botão não é fixo/determinístico');
  if(!/consultar nf-e/i.test(b.textContent||''))throw new Error('Rótulo incorreto');
  b.click();
  await wait(20);
  if(!w.document.getElementById('csm-native-lookup-overlay'))throw new Error('Botão não abre o modal da consulta');
  w.document.getElementById('csm-native-lookup-overlay').remove();
  b.remove();
  await wait(120);
  b=w.document.getElementById('csm-native-lookup-fixed');
  if(!b||b.parentElement!==w.document.body)throw new Error('Botão próprio não foi restaurado');
  console.log('OK - 3.11.4: botão próprio fixo + modal + restauração; dispatch direto broker/helper sem Localizador legado.');
  w.close();
})().catch(e=>{console.error(e);process.exit(1)});
