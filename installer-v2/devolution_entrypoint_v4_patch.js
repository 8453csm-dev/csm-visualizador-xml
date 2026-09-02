// CSM_DEVOLUTION_ENTRYPOINT_V4
// Motor Fiscal 1.3: entrada determinística, independente da velocidade/renderização do PC.
const CSM_DEV_ENTRYPOINT_VERSION='1.3.0';
let csmDevEntrySyncQueued=false;

function csmDevEntryEligible(doc){
 return !!doc&&doc.doc_type==='nfe'&&String(doc.model||'')==='55';
}

function csmDevEnsureEntryPoint(){
 const doc=(typeof activeDoc==='function')?activeDoc():null;
 let count=0;
 document.querySelectorAll('#relationsSection').forEach(box=>{
  let button=box.querySelector('.csm-create-devolution');
  if(!csmDevEntryEligible(doc)){
   if(button)button.remove();
   return;
  }
  if(!button){
   button=document.createElement('button');
   button.className='button csm-create-devolution';
   button.textContent='Criar modelo de devolução';
   const dossier=box.querySelector('#dossierBtn');
   dossier?dossier.before(button):box.appendChild(button);
  }
  button.onclick=()=>csmDevOpen((typeof activeDoc==='function')?activeDoc():doc);
  count++;
 });
 if(window.CSM_DEVOLUTION_ENGINE){
  window.CSM_DEVOLUTION_ENGINE.version=CSM_DEV_ENTRYPOINT_VERSION;
  window.CSM_DEVOLUTION_ENGINE.entrypointVersion=CSM_DEV_ENTRYPOINT_VERSION;
  window.CSM_DEVOLUTION_ENGINE.ensureEntryPoint=csmDevEnsureEntryPoint;
 }
 return count;
}

function csmDevQueueEntrySync(){
 if(csmDevEntrySyncQueued)return;
 csmDevEntrySyncQueued=true;
 const run=()=>{
  csmDevEntrySyncQueued=false;
  try{csmDevEnsureEntryPoint()}catch(err){console.warn('CSM Motor Fiscal: sincronização da entrada falhou',err)}
 };
 if(typeof queueMicrotask==='function')queueMicrotask(run);
 else Promise.resolve().then(run);
}

function csmDevStartupEntrySync(){
 csmDevEnsureEntryPoint();
 if(typeof requestAnimationFrame==='function')requestAnimationFrame(()=>csmDevEnsureEntryPoint());
 [50,250,750,1500,3000,6000].forEach(ms=>setTimeout(()=>csmDevEnsureEntryPoint(),ms));
}

csmDevStartupEntrySync();

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',csmDevStartupEntrySync,{once:true});
else csmDevQueueEntrySync();
window.addEventListener('load',csmDevStartupEntrySync,{once:true});

const csmDevEntryObserver=new MutationObserver(()=>csmDevQueueEntrySync());
const csmDevObserveRoot=document.body||document.documentElement;
if(csmDevObserveRoot)csmDevEntryObserver.observe(csmDevObserveRoot,{childList:true,subtree:true});

document.addEventListener('click',()=>setTimeout(csmDevQueueEntrySync,0),true);
document.addEventListener('change',()=>setTimeout(csmDevQueueEntrySync,0),true);

if(window.CSM_DEVOLUTION_ENGINE){
 window.CSM_DEVOLUTION_ENGINE.version=CSM_DEV_ENTRYPOINT_VERSION;
 window.CSM_DEVOLUTION_ENGINE.entrypointVersion=CSM_DEV_ENTRYPOINT_VERSION;
 window.CSM_DEVOLUTION_ENGINE.ensureEntryPoint=csmDevEnsureEntryPoint;
}
