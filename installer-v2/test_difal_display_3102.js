const fs=require('fs');
const {JSDOM}=require('jsdom');
const moduleCode=fs.readFileSync(__dirname+'/difal_st_module.js','utf8');
const displayCode=fs.readFileSync(__dirname+'/difal_st_display_3102.js','utf8');
const xml=fs.readFileSync(__dirname+'/difal_st_fixture.xml','utf8');

(async()=>{
  const dom=new JSDOM('<!doctype html><body><section class="content-panel"><div class="view-tabs"><button class="view-tab" data-view="fiscal">Fiscal</button></div><div id="fiscalView" class="view"><section>CFOPS ENCONTRADOS</section></div></section></body>',{runScripts:'outside-only',pretendToBeVisual:true});
  const w=dom.window;
  const active={document_id:'d1',model:'55',doc_type:'nfe'};
  w.state={activeId:'d1',activeView:'pdf'};
  w.activeDoc=()=>active;
  w.switchView=async v=>{w.state.activeView=v;w.document.querySelectorAll('.view').forEach(x=>x.classList.toggle('active',x.id===v+'View'))};
  w.activateDocument=async()=>{};w.showWelcome=()=>{};
  w.pywebview={api:{get_xml_text:async()=>({ok:true,xml})}};
  w.eval(moduleCode);w.eval(displayCode);
  await new Promise(r=>w.setTimeout(r,30));
  const api=w.CSM_DIFAL_ST;if(!api)throw new Error('Modulo DIFAL/ST ausente');
  const note=api.parseXml(xml);
  const clone={...note.items[0],nItem:3,index:3,cfop:'6102'};
  note.items.push(clone);
  const cfg={purposeAll:'revenda',mva4:'',mva12:'',mvaOther:'',items:{
    1:{mode:'difal',purpose:'revenda',internalRate:18,mvaOverride:''},
    2:{mode:'difal',purpose:'revenda',internalRate:18,mvaOverride:''},
    3:{mode:'difal',purpose:'revenda',internalRate:18,mvaOverride:''}
  }};
  const s=api.summarize(note,cfg);
  if(s.breakdown.filter(x=>x.rate===12&&x.mode==='difal').length!==2)throw new Error('CFOPs de 12% foram misturados internamente');
  api.noteCache.set('d1',note);api.store.set('d1',cfg);
  const btn=w.document.querySelector('[data-view="difalst"]');btn.click();
  await new Promise(r=>w.setTimeout(r,80));
  const view=w.document.getElementById('difalstView');
  const titles=[...view.querySelectorAll('.csm-difal-card-title')].map(x=>x.textContent.trim());
  if(titles.some(x=>/CFOP/i.test(x)))throw new Error('Resumo principal ainda exibe CFOP: '+titles.join(' | '));
  if(titles.filter(x=>x==='Alíquota interestadual 12%').length!==2)throw new Error('Dois calculos isolados de 12% deveriam permanecer separados visualmente');
  if(!view.textContent.includes('Resumo por alíquota'))throw new Error('Titulo simplificado ausente');
  await w.switchView('fiscal');await new Promise(r=>w.setTimeout(r,80));
  const fp=w.document.getElementById('csmDifalFiscalPanel');
  if(!fp)throw new Error('Painel Fiscal ausente');
  if(/CFOP\s+610/i.test(fp.textContent))throw new Error('Painel Fiscal ainda exibe codigo CFOP');
  const rateLabels=[...fp.querySelectorAll('.csm-difal-fiscal-row > span:first-child > b')].map(x=>x.textContent.trim());
  if(rateLabels.filter(x=>x==='Alíquota interestadual 12%').length!==2)throw new Error('Fiscal deve manter calculos isolados e exibir somente aliquota');
  dom.window.close();
  console.log('OK - calculos continuam isolados por CFOP internamente e a UI mostra somente aliquotas.');
})().catch(e=>{console.error(e);process.exit(1)});
