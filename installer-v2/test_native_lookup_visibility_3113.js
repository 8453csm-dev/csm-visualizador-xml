const fs=require('fs');
const {JSDOM}=require('jsdom');
const app=process.env.CSM_APP_JS;
if(!app||!fs.existsSync(app))throw new Error('CSM_APP_JS ausente');
const src=fs.readFileSync(app,'utf8');
for(const tok of ['CSM_NATIVE_LOOKUP_VISIBLE_3113','maintainLookupButton','lookupHeaderScore',"insertAdjacentElement('afterend',b)",'ensureButton:installButton']){
  if(!src.includes(tok))throw new Error('Token ausente: '+tok);
}
const start=src.lastIndexOf('// CSM_NATIVE_KEY_LOOKUP_V1');
const end=src.indexOf('\n})();',start);
if(start<0||end<0)throw new Error('Módulo nativo não localizado no app final');
const moduleSrc=src.slice(start,end+6);
const dom=new JSDOM('<!doctype html><html><head></head><body><div class="topbar-actions"><button id="open">Abrir XML/PDF</button><button id="folder">Abrir pasta</button><button id="save">Salvar PDF</button></div></body></html>',{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window;
w.eval(moduleSrc);
w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
function wait(ms){return new Promise(r=>setTimeout(r,ms))}
(async()=>{
  await wait(80);
  let b=w.document.querySelector('[data-csm-native-lookup="1"]');
  if(!b)throw new Error('Botão Consultar NF-e não foi criado');
  const folder=w.document.getElementById('folder');
  if(folder.nextElementSibling!==b)throw new Error('Botão não ficou logo após Abrir pasta');
  if(!/consultar nf-e/i.test(b.textContent||''))throw new Error('Rótulo do botão incorreto');
  b.remove();
  await wait(120);
  b=w.document.querySelector('[data-csm-native-lookup="1"]');
  if(!b)throw new Error('MutationObserver não restaurou o botão');
  if(folder.nextElementSibling!==b)throw new Error('Botão restaurado em posição errada');
  console.log('OK - Consulta NF-e visível, posicionada após Abrir pasta e restaurada após reconstrução do cabeçalho.');
  w.close();
})().catch(e=>{console.error(e);process.exit(1)});
