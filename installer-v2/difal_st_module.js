// CSM_DIFAL_ST_MODULE_V1
// CSM Visualizador XML 3.10.1 - DIFAL / ICMS ST por CFOP + aliquota e resumo integrado ao Fiscal.
(() => {
  'use strict';
  const VERSION='1.1.0';
  const STORE=new Map();
  const NOTE_CACHE=new Map();
  const money=v=>(Number(v)||0).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
  const pct=v=>`${(Number(v)||0).toLocaleString('pt-BR',{minimumFractionDigits:0,maximumFractionDigits:4})}%`;
  const h=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const round2=v=>Math.round((Number(v)||0)*100)/100;
  const n=v=>{const x=Number(String(v??'').replace(',','.'));return Number.isFinite(x)?x:0};
  const local=(root,name)=>root?.getElementsByTagNameNS?.('*',name)?.[0]||root?.getElementsByTagName?.(name)?.[0]||null;
  const txt=(root,name)=>local(root,name)?.textContent?.trim()||'';
  const num=(root,name)=>n(txt(root,name));
  const all=(root,name)=>Array.from(root?.getElementsByTagNameNS?.('*',name)||root?.getElementsByTagName?.(name)||[]);
  const close=(a,b,t=.03)=>Math.abs((Number(a)||0)-(Number(b)||0))<=t;

  function parseXml(xml){
    const doc=new DOMParser().parseFromString(xml,'application/xml');
    if(local(doc,'parsererror'))throw new Error('XML inválido ou não reconhecido.');
    const emit=local(doc,'emit'),dest=local(doc,'dest'),ide=local(doc,'ide');
    const emitUF=txt(local(emit,'enderEmit'),'UF');
    const destUF=txt(local(dest,'enderDest'),'UF');
    const note={nNF:txt(ide,'nNF'),serie:txt(ide,'serie'),emitUF,destUF,emitNome:txt(emit,'xNome'),destNome:txt(dest,'xNome'),items:[]};
    all(doc,'det').forEach((det,idx)=>{
      const prod=local(det,'prod'),imp=local(det,'imposto'),icms=local(imp,'ICMS');
      const icmsNode=icms?.children?.[0]||icms?.firstElementChild||icms;
      const ipi=local(imp,'IPI'),ipiNode=local(ipi,'IPITrib')||local(ipi,'IPINT')||ipi;
      const difalNode=local(imp,'ICMSUFDest');
      const item={
        index:idx+1,nItem:n(txt(det,'nItem'))||idx+1,cProd:txt(prod,'cProd'),xProd:txt(prod,'xProd'),ncm:txt(prod,'NCM'),cest:txt(prod,'CEST'),cfop:txt(prod,'CFOP'),
        vProd:num(prod,'vProd'),vFrete:num(prod,'vFrete'),vSeg:num(prod,'vSeg'),vOutro:num(prod,'vOutro'),vDesc:num(prod,'vDesc'),vIPI:num(ipiNode,'vIPI'),
        orig:txt(icmsNode,'orig'),cst:txt(icmsNode,'CST')||txt(icmsNode,'CSOSN'),vBC:num(icmsNode,'vBC'),pICMS:num(icmsNode,'pICMS'),vICMS:num(icmsNode,'vICMS'),
        pRedBC:num(icmsNode,'pRedBC'),vBCST:num(icmsNode,'vBCST'),pMVAST:num(icmsNode,'pMVAST'),pRedBCST:num(icmsNode,'pRedBCST'),pICMSST:num(icmsNode,'pICMSST'),vICMSST:num(icmsNode,'vICMSST'),
        pICMSUFDest:num(difalNode,'pICMSUFDest'),vICMSUFDest:num(difalNode,'vICMSUFDest')
      };
      item.baseMercadoria=round2(item.vProd+item.vFrete+item.vSeg+item.vOutro-item.vDesc);
      if(!item.pICMS&&item.vBC>0&&item.vICMS>0)item.pICMS=round2(item.vICMS/item.vBC*100);
      item.interstate=!!emitUF&&!!destUF&&emitUF!==destUF&&String(item.cfop).startsWith('6');
      item.hasXmlST=item.vBCST>0||item.vICMSST>0||item.pMVAST>0||item.pICMSST>0;
      note.items.push(item);
    });
    return note;
  }

  function inferInternalRate(item){if(item.pICMSUFDest>0)return item.pICMSUFDest;if(item.pICMSST>0)return item.pICMSST;return 18}
  function defaultConfig(note){const items={};note.items.forEach(item=>{items[item.nItem]={mode:item.hasXmlST?'st':'difal',purpose:'revenda',internalRate:inferInternalRate(item),mvaOverride:item.pMVAST>0?item.pMVAST:''}});return {purposeAll:'revenda',mva4:'',mva12:'',mvaOther:'',items}}
  function effectiveMva(item,cfg,root){const ov=n(cfg?.mvaOverride);if(ov>0)return ov;const r=n(item.pICMS);if(Math.abs(r-4)<.051)return n(root.mva4);if(Math.abs(r-12)<.051)return n(root.mva12);return n(root.mvaOther)}
  function difalBase(item,purpose){const baseNoIpi=item.vBC>0?item.vBC:item.baseMercadoria;if(purpose!=='uso')return round2(baseNoIpi);if(item.vIPI<=0)return round2(baseNoIpi);const likelyIpiAlreadyIncluded=close(item.vBC,item.baseMercadoria+item.vIPI)||item.vBC>item.baseMercadoria+0.03;return round2(baseNoIpi+(likelyIpiAlreadyIncluded?0:item.vIPI))}
  function calculateDifal(item,cfg){const purpose=cfg?.purpose==='uso'?'uso':'revenda';const base=difalBase(item,purpose),orig=n(item.pICMS),internal=n(cfg?.internalRate)||inferInternalRate(item);const icmsOrig=round2(base*orig/100),icmsDest=round2(base*internal/100),due=round2(Math.max(0,icmsDest-icmsOrig));return {type:'difal',base,orig,internal,icmsOrig,icmsDest,due,purpose}}
  function calculateSt(item,cfg,root){const mva=effectiveMva(item,cfg,root),internal=n(cfg?.internalRate)||inferInternalRate(item);const initial=round2(item.baseMercadoria+item.vIPI);let baseST=round2(initial*(1+mva/100));const reduction=item.pRedBCST>0?item.pRedBCST:0;if(reduction>0)baseST=round2(baseST*(1-reduction/100));const icmsDest=round2(baseST*internal/100);const icmsOwn=round2(item.vICMS>0?item.vICMS:((item.vBC>0?item.vBC:item.baseMercadoria)*n(item.pICMS)/100));const due=round2(Math.max(0,icmsDest-icmsOwn));return {type:'st',initial,baseST,mva,internal,reduction,icmsDest,icmsOwn,due}}
  function groupKey(rate){if(Math.abs(rate-4)<.051)return '4';if(Math.abs(rate-12)<.051)return '12';return String(round2(rate||0))}
  function emptyRate(rate){return {rate,count:0,base:0,icmsOrig:0,icmsDest:0,due:0}}
  function emptySt(){return {count:0,initial:0,baseST:0,icmsDest:0,icmsOwn:0,due:0}}
  function addRounded(target,calc,fields){target.count++;for(const k of fields)target[k]+=Number(calc[k])||0}

  function summarize(note,cfg){
    const groups={4:emptyRate(4),12:emptyRate(12),other:emptyRate(null)};
    const st=emptySt(),map=new Map();let eligible=0;
    note.items.forEach(item=>{
      if(!item.interstate)return;eligible++;
      const icfg=cfg.items[item.nItem]||{};
      if(icfg.mode==='st'){
        const c=calculateSt(item,icfg,cfg),rate=groupKey(item.pICMS),key=`${item.cfop||'-'}|${rate}|st`;
        addRounded(st,c,['initial','baseST','icmsDest','icmsOwn','due']);
        if(!map.has(key))map.set(key,{cfop:item.cfop||'-',rate:n(item.pICMS),rateKey:rate,mode:'st',count:0,initial:0,baseST:0,icmsDest:0,icmsOwn:0,due:0});
        addRounded(map.get(key),c,['initial','baseST','icmsDest','icmsOwn','due']);
      }else{
        const c=calculateDifal(item,icfg),rk=groupKey(c.orig),g=(rk==='4'?groups['4']:rk==='12'?groups['12']:groups.other),key=`${item.cfop||'-'}|${rk}|difal`;
        addRounded(g,c,['base','icmsOrig','icmsDest','due']);
        if(!map.has(key))map.set(key,{cfop:item.cfop||'-',rate:c.orig,rateKey:rk,mode:'difal',count:0,base:0,icmsOrig:0,icmsDest:0,due:0});
        addRounded(map.get(key),c,['base','icmsOrig','icmsDest','due']);
      }
    });
    Object.values(groups).forEach(g=>['base','icmsOrig','icmsDest','due'].forEach(k=>g[k]=round2(g[k])));
    ['initial','baseST','icmsDest','icmsOwn','due'].forEach(k=>st[k]=round2(st[k]));
    const breakdown=Array.from(map.values()).map(g=>{const fields=g.mode==='st'?['initial','baseST','icmsDest','icmsOwn','due']:['base','icmsOrig','icmsDest','due'];fields.forEach(k=>g[k]=round2(g[k]));return g}).sort((a,b)=>String(a.cfop).localeCompare(String(b.cfop),'pt-BR',{numeric:true})||(a.mode===b.mode?0:a.mode==='difal'?-1:1)||(a.rate-b.rate));
    const totalDifal=round2(groups['4'].due+groups['12'].due+groups.other.due),totalSt=st.due;
    return {groups,st,breakdown,eligible,totalDifal,totalSt,total:round2(totalDifal+totalSt)};
  }

  function getCfg(id,note){if(!STORE.has(id))STORE.set(id,defaultConfig(note));return STORE.get(id)}
  function currentDoc(){return typeof activeDoc==='function'?activeDoc():null}
  function currentId(){const d=currentDoc();return d?.document_id||((typeof state!=='undefined'&&state)?state.activeId:null)||'active'}

  function breakdownCard(g){
    const label=`CFOP ${g.cfop} • ${pct(g.rate)} • ${g.mode==='st'?'ICMS ST':'DIFAL'}`;
    if(g.mode==='st')return `<article class="csm-difal-card st"><div class="csm-difal-card-title">${h(label)}</div><div class="csm-difal-big">${money(g.due)}</div><div class="csm-difal-grid mini"><span>Itens<strong>${g.count}</strong></span><span>Base ST<strong>${money(g.baseST)}</strong></span><span>ICMS interno<strong>${money(g.icmsDest)}</strong></span><span>ICMS próprio<strong>${money(g.icmsOwn)}</strong></span></div></article>`;
    return `<article class="csm-difal-card"><div class="csm-difal-card-title">${h(label)}</div><div class="csm-difal-big">${money(g.due)}</div><div class="csm-difal-grid mini"><span>Itens<strong>${g.count}</strong></span><span>Base<strong>${money(g.base)}</strong></span><span>ICMS origem<strong>${money(g.icmsOrig)}</strong></span><span>ICMS interno<strong>${money(g.icmsDest)}</strong></span></div></article>`;
  }

  function itemHtml(item,cfg,root){
    const isSt=cfg.mode==='st',calc=isSt?calculateSt(item,cfg,root):calculateDifal(item,cfg),mva=effectiveMva(item,cfg,root);
    return `<article class="csm-difal-item ${isSt?'is-st':'is-difal'}" data-item="${item.nItem}"><div class="csm-difal-item-head"><div><strong>${item.nItem}. ${h(item.xProd||item.cProd||'Item')}</strong><small>CFOP ${h(item.cfop||'-')} • NCM ${h(item.ncm||'-')} • CST/CSOSN ${h(item.cst||'-')}</small></div><div class="csm-difal-result"><small>${isSt?'ICMS ST':'DIFAL'}</small><b>${money(calc.due)}</b></div></div><div class="csm-difal-controls"><label class="csm-difal-switch"><input type="checkbox" data-field="mode" ${isSt?'checked':''}><span>Calcular como ICMS ST</span></label><label>Finalidade<select data-field="purpose" ${isSt?'disabled':''}><option value="revenda" ${cfg.purpose!=='uso'?'selected':''}>Revenda</option><option value="uso" ${cfg.purpose==='uso'?'selected':''}>Uso / consumo</option></select></label><label>Alíquota interna<input data-field="internalRate" inputmode="decimal" value="${h(cfg.internalRate)}"><em>%</em></label>${isSt?`<label>MVA do item<input data-field="mvaOverride" inputmode="decimal" placeholder="${mva?String(mva):'usar MVA por alíquota'}" value="${h(cfg.mvaOverride)}"><em>%</em></label>`:''}</div><div class="csm-difal-calc">${isSt?`<span>Base inicial<strong>${money(calc.initial)}</strong><small>produto + acréscimos − desconto + IPI</small></span><span>MVA<strong>${pct(calc.mva)}</strong></span><span>Base ST<strong>${money(calc.baseST)}</strong></span><span>ICMS interno<strong>${money(calc.icmsDest)}</strong></span><span>ICMS próprio<strong>${money(calc.icmsOwn)}</strong></span><span class="total">ST devido<strong>${money(calc.due)}</strong></span>`:`<span>Base DIFAL<strong>${money(calc.base)}</strong><small>${cfg.purpose==='uso'?'uso/consumo: IPI compõe quando ainda não está na vBC':'revenda: IPI não é somado manualmente'}</small></span><span>Origem<strong>${pct(calc.orig)}</strong></span><span>Interna<strong>${pct(calc.internal)}</strong></span><span>ICMS origem<strong>${money(calc.icmsOrig)}</strong></span><span>ICMS interno<strong>${money(calc.icmsDest)}</strong></span><span class="total">DIFAL<strong>${money(calc.due)}</strong></span>`}</div></article>`;
  }

  function render(note,cfg,view){
    const s=summarize(note,cfg),interstate=note.emitUF&&note.destUF&&note.emitUF!==note.destUF,items=note.items.filter(x=>x.interstate);
    view.innerHTML=`<div class="csm-difal-wrap"><header class="csm-difal-hero"><div><span class="csm-difal-kicker">APURAÇÃO ASSISTIDA</span><h2>DIFAL / ICMS ST</h2><p>NF ${h(note.nNF||'-')} • ${h(note.emitUF||'?')} → ${h(note.destUF||'?')}</p></div><div class="csm-difal-total"><small>Total calculado</small><strong>${money(s.total)}</strong><span>DIFAL ${money(s.totalDifal)} • ST ${money(s.totalSt)}</span></div></header>${!interstate?'<div class="csm-difal-alert">Esta NF-e não é interestadual. O módulo não calcula DIFAL para operação interna.</div>':''}<div class="csm-difal-section-title"><div><strong>Resumo por CFOP e alíquota</strong><small>Cada combinação é apurada separadamente; o total geral é apenas a soma dos grupos.</small></div><span>${s.breakdown.length} grupo(s)</span></div><section class="csm-difal-summary by-cfop">${s.breakdown.length?s.breakdown.map(breakdownCard).join(''):'<div class="csm-difal-empty">Nenhum grupo interestadual encontrado.</div>'}</section><section class="csm-difal-setup"><div><strong>Configuração rápida</strong><small>O MVA é aplicado conforme a alíquota interestadual do item. Um item pode ter MVA próprio.</small></div><label>Finalidade padrão<select id="csmDifalPurposeAll"><option value="revenda" ${cfg.purposeAll!=='uso'?'selected':''}>Revenda</option><option value="uso" ${cfg.purposeAll==='uso'?'selected':''}>Uso / consumo</option></select></label><label>MVA itens 12%<input id="csmDifalMva12" inputmode="decimal" value="${h(cfg.mva12)}" placeholder="ex.: 50"><em>%</em></label><label>MVA itens 4%<input id="csmDifalMva4" inputmode="decimal" value="${h(cfg.mva4)}" placeholder="ex.: 70"><em>%</em></label></section><div class="csm-difal-note"><b>Regra aplicada:</b> a apuração é agrupada por <b>CFOP + alíquota interestadual</b>. Marque <b>Calcular como ICMS ST</b> quando a mercadoria estiver sujeita à substituição tributária; o item sai do DIFAL e entra no grupo de ST do mesmo CFOP/alíquota.</div><section class="csm-difal-items">${items.length?items.map(i=>itemHtml(i,cfg.items[i.nItem],cfg)).join(''):'<div class="csm-difal-empty">Nenhum item interestadual com CFOP iniciado em 6 foi encontrado nesta NF-e.</div>'}</section></div>`;
    bind(view,note,cfg);
    renderFiscalPanel(note,cfg);
  }

  function bind(view,note,cfg){
    const rer=()=>render(note,cfg,view);
    const purpose=view.querySelector('#csmDifalPurposeAll');if(purpose)purpose.onchange=e=>{cfg.purposeAll=e.target.value;Object.values(cfg.items).forEach(x=>x.purpose=e.target.value);rer()};
    const m12=view.querySelector('#csmDifalMva12');if(m12)m12.onchange=e=>{cfg.mva12=e.target.value;rer()};
    const m4=view.querySelector('#csmDifalMva4');if(m4)m4.onchange=e=>{cfg.mva4=e.target.value;rer()};
    view.querySelectorAll('.csm-difal-item').forEach(row=>{const icfg=cfg.items[n(row.dataset.item)];if(!icfg)return;row.querySelectorAll('[data-field]').forEach(el=>{el.onchange=e=>{const f=e.target.dataset.field;if(f==='mode')icfg.mode=e.target.checked?'st':'difal';else icfg[f]=e.target.value;rer()}})});
  }

  function fiscalBreakdownRow(g){
    return `<div class="csm-difal-fiscal-row"><span><b>CFOP ${h(g.cfop)}</b><small>${pct(g.rate)} • ${g.mode==='st'?'ICMS ST':'DIFAL'} • ${g.count} item(ns)</small></span><span><small>${g.mode==='st'?'Base ST':'Base'}</small><b>${money(g.mode==='st'?g.baseST:g.base)}</b></span><span><small>${g.mode==='st'?'ICMS próprio':'ICMS origem'}</small><b>${money(g.mode==='st'?g.icmsOwn:g.icmsOrig)}</b></span><span><small>ICMS interno</small><b>${money(g.icmsDest)}</b></span><span class="value"><small>${g.mode==='st'?'ST devido':'DIFAL'}</small><b>${money(g.due)}</b></span></div>`;
  }

  function renderFiscalPanel(note,cfg){
    const fiscal=document.getElementById('fiscalView');if(!fiscal)return false;
    let panel=fiscal.querySelector('#csmDifalFiscalPanel');if(panel)panel.remove();
    if(!note||!note.items?.some(x=>x.interstate))return false;
    const s=summarize(note,cfg);
    panel=document.createElement('section');panel.id='csmDifalFiscalPanel';panel.className='csm-difal-fiscal-panel';
    panel.innerHTML=`<div class="csm-difal-fiscal-head"><div><span>DIFAL / ICMS ST</span><strong>Apuração calculada</strong><small>Separada por CFOP + alíquota interestadual</small></div><div class="csm-difal-fiscal-totals"><span>DIFAL<b>${money(s.totalDifal)}</b></span><span>ICMS ST<b>${money(s.totalSt)}</b></span><span class="grand">TOTAL<b>${money(s.total)}</b></span></div></div><div class="csm-difal-fiscal-list">${s.breakdown.map(fiscalBreakdownRow).join('')}</div>`;
    const children=Array.from(fiscal.children),anchor=children.find(el=>/CFOPS\s+ENCONTRADOS/i.test(el.textContent||''));
    if(anchor)fiscal.insertBefore(panel,anchor);else fiscal.appendChild(panel);
    return true;
  }

  async function getCurrentContext(){
    const d=currentDoc();if(!d||String(d.model||'')!=='55')return null;
    const id=d.document_id||currentId();let note=NOTE_CACHE.get(id);
    if(!note){const r=await window.pywebview.api.get_xml_text(d.document_id);if(!r?.ok||!r?.xml)throw new Error(r?.error||'XML não disponível para este documento.');note=parseXml(r.xml);NOTE_CACHE.set(id,note)}
    return {id,note,cfg:getCfg(id,note)};
  }

  async function renderCurrent(){
    ensureUi();const view=document.getElementById('difalstView');if(!view)return;
    const d=currentDoc();if(!d||String(d.model||'')!=='55'){view.innerHTML='<div class="csm-difal-empty">Abra uma NF-e modelo 55 para calcular DIFAL / ICMS ST.</div>';return}
    view.innerHTML='<div class="csm-difal-loading">Lendo XML e preparando a apuração...</div>';
    try{const ctx=await getCurrentContext();render(ctx.note,ctx.cfg,view)}catch(err){view.innerHTML=`<div class="csm-difal-alert error">${h(err?.message||err)}</div>`}
  }

  async function refreshFiscalPanel(){
    try{const ctx=await getCurrentContext();if(!ctx){const old=document.getElementById('csmDifalFiscalPanel');if(old)old.remove();return false}return renderFiscalPanel(ctx.note,ctx.cfg)}catch(err){console.warn('CSM DIFAL/ST: falha ao atualizar resumo Fiscal',err);return false}
  }

  function ensureUi(){
    const panel=document.querySelector('.content-panel'),tabs=panel?.querySelector('.view-tabs');if(!panel||!tabs)return false;
    let btn=tabs.querySelector('[data-view="difalst"]');if(!btn){btn=document.createElement('button');btn.className='view-tab advanced-view-tab hidden';btn.dataset.view='difalst';btn.textContent='DIFAL / ICMS ST';tabs.appendChild(btn);btn.addEventListener('click',async()=>{if(typeof switchView==='function')await switchView('difalst');await renderCurrent()})}
    let view=document.getElementById('difalstView');if(!view){view=document.createElement('div');view.id='difalstView';view.className='view';panel.appendChild(view)}
    const d=currentDoc();btn.classList.toggle('hidden',!(d&&String(d.model||'')==='55'));return true;
  }

  function sync(renderIfOpen=false){try{ensureUi();const active=(typeof state!=='undefined'&&state)?state.activeView:'';if(renderIfOpen&&active==='difalst')renderCurrent();if(active==='fiscal')refreshFiscalPanel()}catch(e){console.warn('CSM DIFAL/ST: falha de sincronização',e)}}
  if(typeof switchView==='function'&&!globalThis.__CSM_DIFAL_SWITCH_WRAPPED){const old=switchView;switchView=async function(v){const r=await old(v);if(v==='fiscal')await refreshFiscalPanel();return r};globalThis.__CSM_DIFAL_SWITCH_WRAPPED=true}
  if(typeof activateDocument==='function'&&!globalThis.__CSM_DIFAL_ACTIVATE_WRAPPED){const old=activateDocument;activateDocument=async function(id){const r=await old(id);sync(true);return r};globalThis.__CSM_DIFAL_ACTIVATE_WRAPPED=true}
  if(typeof showWelcome==='function'&&!globalThis.__CSM_DIFAL_WELCOME_WRAPPED){const old=showWelcome;showWelcome=function(){const r=old();const p=document.getElementById('csmDifalFiscalPanel');if(p)p.remove();sync(false);return r};globalThis.__CSM_DIFAL_WELCOME_WRAPPED=true}
  const root=document.body||document.documentElement;if(root&&!document.querySelector('[data-view="difalst"]')){const obs=new MutationObserver(()=>{if(ensureUi())obs.disconnect()});obs.observe(root,{childList:true,subtree:true})}
  Promise.resolve().then(()=>sync(false));
  globalThis.CSM_DIFAL_ST={version:VERSION,parseXml,inferInternalRate,difalBase,calculateDifal,calculateSt,summarize,ensureUi,renderCurrent,renderFiscalPanel,refreshFiscalPanel,store:STORE,noteCache:NOTE_CACHE};
})();
