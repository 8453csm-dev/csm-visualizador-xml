const fs=require('fs');
const {JSDOM}=require('jsdom');
const app=process.env.CSM_APP_JS;
if(!app||!fs.existsSync(app))throw new Error('CSM_APP_JS ausente');
const src=fs.readFileSync(app,'utf8');
for(const tok of ['CSM_NATIVE_FISCAL_CORE_3120','/fiscal/certificates','/fiscal/nfe/consultar','Empresa / certificado A1','csm-native-lookup-header']){
  if(!src.includes(tok))throw new Error('Token ausente: '+tok);
}
const ds=src.indexOf('async function dispatchLookup');
const de=src.indexOf('\nfunction style(){',ds);
if(ds<0||de<0)throw new Error('dispatchLookup não encontrado');
const dispatch=src.slice(ds,de);
for(const bad of ['/lookup-automation','open_lookup_site(','consultadanfe']){
  if(dispatch.includes(bad))throw new Error('Fluxo principal ainda depende do site: '+bad);
}
if(!dispatch.includes('/fiscal/nfe/consultar'))throw new Error('dispatch não chama Fiscal Core');

const start=src.lastIndexOf('// CSM_NATIVE_KEY_LOOKUP_V1');
const end=src.indexOf('\n})();',start);
if(start<0||end<0)throw new Error('Módulo nativo não localizado');
const moduleSrc=src.slice(start,end+6);
const dom=new JSDOM('<!doctype html><html><head></head><body><div class="topbar-actions"><button id="open" class="topbtn">Abrir XML/PDF</button><button id="folder" class="topbtn">Abrir pasta</button><button id="save" class="topbtn">Salvar PDF</button></div></body></html>',{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window;
const calls=[];
w.fetch=async(url,opt={})=>{
  calls.push({url:String(url),opt});
  if(String(url).includes('/fiscal/certificates'))return {ok:true,json:async()=>({ok:true,certificates:[{cnpj:'22636383000121',empresa:'EMPRESA TESTE',expiry:'31/12/2027',available:true}]})};
  if(String(url).includes('/fiscal/nfe/consultar'))return {ok:true,json:async()=>({ok:true,native:true,browser:false,status:'AUTORIZADA',message:'Autorizado o uso da NF-e',xml_available:false,requires_manifestation:false})};
  throw new Error('Endpoint inesperado: '+url);
};
w.pywebview={api:{open_recent:async()=>({ok:true})}};
w.eval(moduleSrc);
w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
const wait=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  await wait(120);
  const b=w.document.getElementById('csm-native-lookup-header');
  if(!b)throw new Error('Botão Consultar NF-e não foi criado');
  if(w.document.getElementById('folder').nextElementSibling!==b)throw new Error('Botão não ficou integrado após Abrir pasta');
  b.click();await wait(80);
  const input=w.document.querySelector('.csm-nlk-input');
  const cert=w.document.getElementById('csm-nlk-cert');
  const go=w.document.querySelector('.csm-nlk-go');
  if(!input||!cert||!go)throw new Error('Modal nativo incompleto');
  input.value='35260822636383000121550010000034651119682428';
  input.dispatchEvent(new w.Event('input',{bubbles:true}));
  await wait(120);
  if(cert.value!=='22636383000121')throw new Error('Certificado integrado não foi selecionado');
  go.click();await wait(120);
  if(!calls.some(x=>x.url.includes('/fiscal/certificates')))throw new Error('Lista de certificados não consultada');
  const q=calls.find(x=>x.url.includes('/fiscal/nfe/consultar'));
  if(!q)throw new Error('Consulta não foi enviada ao Fiscal Core');
  const body=JSON.parse(q.opt.body||'{}');
  if(body.key!=='35260822636383000121550010000034651119682428'||body.cnpj!=='22636383000121')throw new Error('Payload fiscal incorreto');
  const status=w.document.querySelector('.csm-nlk-status')?.textContent||'';
  if(!/AUTORIZADA/i.test(status))throw new Error('Retorno oficial não apareceu no modal');
  console.log('OK - 3.12.0 usa CSM Fiscal Core, certificado A1 e endpoints locais nativos; zero navegador no fluxo principal.');
  w.close();
})().catch(e=>{console.error(e);process.exit(1)});
