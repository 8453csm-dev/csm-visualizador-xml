const fs=require('fs');
const {JSDOM}=require('jsdom');
const app=process.env.CSM_APP_JS;
if(!app||!fs.existsSync(app))throw new Error('CSM_APP_JS ausente');
const src=fs.readFileSync(app,'utf8');
for(const tok of ['CSM_LOOKUP_EMBEDDED_3115','csm-native-lookup-header','csm:external-document-opened','Consultando em segundo plano','lookupToolbarTarget']){
  if(!src.includes(tok))throw new Error('Token ausente: '+tok);
}
if(src.includes("position:'fixed',top:'96px'"))throw new Error('Botão flutuante 3.11.4 ainda presente');
if(src.includes("id='csm-native-lookup-fixed'"))throw new Error('ID do botão flutuante ainda presente');

const start=src.lastIndexOf('// CSM_NATIVE_KEY_LOOKUP_V1');
const end=src.indexOf('\n})();',start);
if(start<0||end<0)throw new Error('Módulo nativo não localizado');
const moduleSrc=src.slice(start,end+6);
const dom=new JSDOM('<!doctype html><html><head></head><body><div class="topbar-actions"><button id="open" class="topbtn">Abrir XML/PDF</button><button id="folder" class="topbtn">Abrir pasta</button><button id="save" class="topbtn">Salvar PDF</button></div></body></html>',{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window;
w.fetch=async()=>({ok:true,json:async()=>({started:true})});
w.pywebview={api:{open_lookup_site:async()=>({ok:true,session_id:'test'}),open_recent:async()=>({ok:true})}};
w.eval(moduleSrc);
w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
function wait(ms){return new Promise(r=>setTimeout(r,ms))}
(async()=>{
  await wait(100);
  const b=w.document.getElementById('csm-native-lookup-header');
  if(!b)throw new Error('Botão Consultar NF-e não foi criado na barra');
  const folder=w.document.getElementById('folder');
  if(folder.nextElementSibling!==b)throw new Error('Botão não ficou após Abrir pasta');
  if(b.className!==folder.className)throw new Error('Botão não herdou o padrão visual da toolbar');
  if(b.style.position!=='static')throw new Error('Botão ainda está em posição flutuante');
  if(!/consultar nf-e/i.test(b.textContent||''))throw new Error('Rótulo incorreto');
  console.log('OK - botão Consulta NF-e integrado à barra, sem posição flutuante, e progresso interno presente.');
  w.close();
})().catch(e=>{console.error(e);process.exit(1)});
