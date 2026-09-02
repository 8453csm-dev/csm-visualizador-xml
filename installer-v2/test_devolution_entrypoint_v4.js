const fs=require('fs');
const {JSDOM}=require('jsdom');
const src=fs.readFileSync('installer-v2/devolution_entrypoint_v4_patch.js','utf8');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function make(html,initialDoc){
 const dom=new JSDOM(`<!doctype html><html><body>${html}</body></html>`,{runScripts:'outside-only',pretendToBeVisual:true,url:'http://localhost'});
 const w=dom.window;
 const ref={current:initialDoc};
 const opened=[];
 w.activeDoc=()=>ref.current;
 w.csmDevOpen=d=>opened.push(d);
 w.CSM_DEVOLUTION_ENGINE={version:'1.2.0'};
 w.console.warn=()=>{};
 w.eval(src);
 await sleep(30);
 return {dom,w,ref,opened};
}

(async()=>{
 const nfe={doc_type:'nfe',model:'55',document_id:'NFE1'};
 const cte={doc_type:'cte',model:'57',document_id:'CTE1'};

 // Cenário A: máquina rápida. A seção já existe quando o Motor Fiscal carrega.
 let t=await make('<section id="relationsSection"><button id="dossierBtn">Dossiê</button></section>',nfe);
 let box=t.w.document.querySelector('#relationsSection');
 if(box.querySelectorAll('.csm-create-devolution').length!==1)throw new Error('Falha: botão não apareceu na primeira execução com DOM já pronto');
 box.querySelector('.csm-create-devolution').click();
 if(t.opened.length!==1||t.opened[0]!==nfe)throw new Error('Falha: botão não abriu o documento ativo');
 t.w.CSM_DEVOLUTION_ENGINE.ensureEntryPoint();
 t.w.CSM_DEVOLUTION_ENGINE.ensureEntryPoint();
 if(box.querySelectorAll('.csm-create-devolution').length!==1)throw new Error('Falha: botão duplicado');
 t.dom.window.close();

 // Cenário B: máquina lenta/primeira instalação. A seção nasce depois do módulo.
 t=await make('<div id="app"></div>',nfe);
 if(t.w.document.querySelector('.csm-create-devolution'))throw new Error('Falha: botão apareceu sem seção');
 const late=t.w.document.createElement('section');
 late.id='relationsSection';
 late.innerHTML='<button id="dossierBtn">Dossiê</button>';
 t.w.document.querySelector('#app').appendChild(late);
 await sleep(40);
 if(late.querySelectorAll('.csm-create-devolution').length!==1)throw new Error('Falha: botão não apareceu quando a seção foi renderizada depois');

 // Troca de documento sem depender de recriação do DOM.
 t.ref.current=cte;
 t.w.document.body.dispatchEvent(new t.w.MouseEvent('click',{bubbles:true}));
 await sleep(20);
 if(late.querySelector('.csm-create-devolution'))throw new Error('Falha: botão permaneceu em documento não suportado');
 t.ref.current=nfe;
 t.w.document.body.dispatchEvent(new t.w.MouseEvent('click',{bubbles:true}));
 await sleep(20);
 if(late.querySelectorAll('.csm-create-devolution').length!==1)throw new Error('Falha: botão não voltou ao selecionar NF-e 55');
 if(t.w.CSM_DEVOLUTION_ENGINE.entrypointVersion!=='1.3.0')throw new Error('Versão do entrypoint incorreta');
 t.dom.window.close();
 console.log('OK - Motor Fiscal aparece de forma determinística em DOM rápido, DOM tardio e troca de documento.');
})().catch(err=>{console.error(err);process.exit(1)});
