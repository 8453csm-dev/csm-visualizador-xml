const fs=require('fs');const {JSDOM}=require('jsdom');
const core=fs.readFileSync(process.env.CSM_TAX_CORE||__dirname+'/tax_engine_core.js','utf8'),ui=fs.readFileSync(process.env.CSM_TAX_UI||__dirname+'/tax_explainer_ui.js','utf8');
async function scenario(late){
 const html=late?'<!doctype html><body><div id="printRoot"></div></body>':'<!doctype html><body><section class="content-panel"><div class="view-tabs"><button class="view-tab" data-view="fiscal">Fiscal</button></div><div id="fiscalView" class="view"></div></section><div id="printRoot"></div></body>';
 const dom=new JSDOM(html,{runScripts:'outside-only',pretendToBeVisual:true});const w=dom.window;
 w.state={activeId:'doc1',activeView:'pdf'};w.activeDoc=()=>({document_id:'doc1',doc_type:'nfe',model:'55'});w.switchView=v=>{w.state.activeView=v};w.esc=x=>String(x);w.toast=()=>{};w.clearPrintPages=()=>{};w.els={printRoot:w.document.getElementById('printRoot')};w.pywebview={api:{get_xml_text:async()=>({ok:true,xml:'<nfeProc/>'})}};w.navigator.clipboard={writeText:async()=>{}};w.print=()=>{};
 w.eval(core);w.eval(ui);
 if(late){const panel=w.document.createElement('section');panel.className='content-panel';panel.innerHTML='<div class="view-tabs"><button class="view-tab" data-view="fiscal">Fiscal</button></div><div id="fiscalView" class="view"></div>';w.document.body.appendChild(panel)}
 await new Promise(r=>w.setTimeout(r,80));
 const btn=w.document.querySelector('[data-view="taxexplain"]'),view=w.document.getElementById('taxexplainView');if(!btn||!view)throw new Error(`UI tributária não apareceu no cenário ${late?'DOM tardio':'DOM pronto'}`);if(btn.classList.contains('hidden'))throw new Error('Aba tributária ficou oculta para NF-e 55');dom.window.close();
}
(async()=>{await scenario(false);await scenario(true);console.log('OK - aba Entender a Tributação é determinística em DOM pronto e tardio.');})().catch(e=>{console.error(e);process.exit(1)});
