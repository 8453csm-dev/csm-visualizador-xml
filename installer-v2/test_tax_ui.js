const fs=require('fs');const {JSDOM}=require('jsdom');
const core=fs.readFileSync(process.env.CSM_TAX_CORE||__dirname+'/tax_engine_core.js','utf8');
const ui=fs.readFileSync(process.env.CSM_TAX_UI||__dirname+'/tax_explainer_ui.js','utf8');
const fixture=fs.readFileSync(__dirname+'/tax_test_fixture.xml','utf8');

async function scenario(late){
 const html=late?'<!doctype html><body><div id="printRoot"></div></body>':'<!doctype html><body><section class="content-panel"><div class="view-tabs"><button class="view-tab" data-view="fiscal">Fiscal</button></div><div id="fiscalView" class="view"></div></section><div id="printRoot"></div></body>';
 const dom=new JSDOM(html,{runScripts:'outside-only',pretendToBeVisual:true});const w=dom.window;
 let xmlCalls=0;
 w.state={activeId:'doc1',activeView:'pdf'};
 w.activeDoc=()=>({document_id:'doc1',doc_type:'nfe',model:'55'});
 w.switchView=v=>{w.state.activeView=v};w.esc=x=>String(x);w.toast=()=>{};w.clearPrintPages=()=>{};
 w.els={printRoot:w.document.getElementById('printRoot')};
 w.pywebview={api:{get_xml_text:async()=>{xmlCalls++;return {ok:true,xml:fixture}}}};
 w.navigator.clipboard={writeText:async()=>{}};w.print=()=>{};
 w.eval(core);w.eval(ui);
 if(late){const panel=w.document.createElement('section');panel.className='content-panel';panel.innerHTML='<div class="view-tabs"><button class="view-tab" data-view="fiscal">Fiscal</button></div><div id="fiscalView" class="view"></div>';w.document.body.appendChild(panel)}
 await new Promise(r=>w.setTimeout(r,80));
 const btn=w.document.querySelector('[data-view="taxexplain"]'),view=w.document.getElementById('taxexplainView');
 if(!btn||!view)throw new Error(`UI tributária não apareceu no cenário ${late?'DOM tardio':'DOM pronto'}`);
 if(btn.classList.contains('hidden'))throw new Error('Aba tributária ficou oculta para NF-e 55');
 btn.click();
 await new Promise(r=>w.setTimeout(r,180));
 if(xmlCalls!==1)throw new Error(`Abertura da aba disparou ${xmlCalls} leituras/renderizações; esperado 1. Possível loop de MutationObserver.`);
 if(!view.textContent.includes('MARTELETE TESTE'))throw new Error('Análise tributária não foi renderizada após o clique');
 if(!view.textContent.includes('R$'))throw new Error('Valores tributários não foram exibidos');
 dom.window.close();
}

(async()=>{
 if(!ui.includes('CSM_TAX_EXPLAINER_NO_FREEZE_391'))throw new Error('Correção anti-congelamento 3.9.1 ausente');
 if(ui.includes("if(eligible&&activeView==='taxexplain')csmTaxRenderCurrent();return true}"))throw new Error('Padrão recursivo da 3.9.0 ainda presente');
 await scenario(false);await scenario(true);
 console.log('OK - Entender a Tributação abre uma única vez, sem loop, em DOM pronto e tardio.');
})().catch(e=>{console.error(e);process.exit(1)});
