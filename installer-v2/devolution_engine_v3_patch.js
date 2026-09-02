// CSM_DEVOLUTION_ENGINE_V3
// Motor Fiscal 1.2: ICMS-ST sem duplicidade, fallback de emissor e PDF mais legivel.
const CSM_DEV_UI_VERSION_V3='1.2.0';
const csmDevUpgradeDraftV2Base=csmDevUpgradeDraftV2;
const csmDevRenderV2Base=csmDevRender;
const csmDevGuideHtmlV2Base=csmDevGuideHtml;
const csmDevWarningsBase=csmDevWarnings;

function csmDevHasSt(draft){return !!draft?.lines?.some(x=>x.selected&&x.qtyReturn>0&&csmDevIsSt(x.raw))}
function csmDevStMode(draft){return draft?.stHandling==='other'?'other':'dedicated'}
function csmDevApplyStHandling(draft){
 if(!draft)return;
 draft.stHandling=csmDevStMode(draft);
 for(const line of draft.lines||[]){
  line.manual=line.manual||{};
  if(csmDevIsSt(line.raw))line.vOutro=draft.stHandling==='other'?csmDevRound(line.vSt):0;
  else if(!line.manual.vOutro)line.vOutro=0;
  delete line.manual.vOutro;
 }
}

csmDevRecalcLine=function(line,draft,force=false){
 const ratio=csmDevPct(line.qtyReturn,line.qtyOriginal);line.pDevol=csmDevRound(ratio*100);
 const proportional={vProd:'total',bcIcms:'bc_icms',vIcms:'icms',bcSt:'bc_icms_st',vSt:'icms_st',vIpi:'ipi',vPis:'pis',vCofins:'cofins'};
 for(const [field,src] of Object.entries(proportional))if(force||!line.manual[field])line[field]=csmDevRound(csmDevNum(line.raw?.[src])*ratio);
 if(force||!line.manual.rateIcms)line.rateIcms=csmDevNum(line.raw?.rate_icms);
 if(force||!line.manual.cfop)line.cfop=csmDevSuggestCfop(line,draft);
 if(force||!line.manual.icmsCode)line.icmsCode=csmDevSuggestIcmsCode(line,draft);
 if(csmDevIsSt(line.raw))line.vOutro=csmDevStMode(draft)==='other'?csmDevRound(line.vSt):0;
 else if(force||!line.manual.vOutro)line.vOutro=0;
 delete line.manual.vOutro;
 return line
};

csmDevUpgradeDraftV2=function(draft,doc){
 const d=csmDevUpgradeDraftV2Base(draft,doc);if(!d)return d;
 d.uiVersion=CSM_DEV_UI_VERSION_V3;
 if(!['dedicated','other'].includes(d.stHandling))d.stHandling='dedicated';
 csmDevApplyStHandling(d);
 return d
};

csmDevModelTotal=function(draft){
 const t=csmDevTotals(draft),e=draft.extras||{};
 const stPart=csmDevStMode(draft)==='other'?t.vOutro:t.vSt;
 return csmDevRound(t.vProd-csmDevNum(e.discount)+csmDevNum(e.freight)+csmDevNum(e.insurance)+csmDevNum(e.other)+stPart+t.vIpi)
};

csmDevInfoAdFisco=function(draft){
 const st=draft.lines.filter(x=>x.selected&&x.qtyReturn>0&&csmDevIsSt(x.raw));
 let text=`Devolução referente à NF-e ${draft.number||''}, série ${draft.series||''}, chave ${draft.key}.`;
 if(st.length){
  const bc=csmDevRound(st.reduce((a,x)=>a+csmDevNum(x.bcSt),0)),v=csmDevRound(st.reduce((a,x)=>a+csmDevNum(x.vSt),0));
  text+=` ICMS-ST devolvido proporcionalmente: BC-ST ${csmDevMoney(bc)}; ICMS-ST ${csmDevMoney(v)}.`;
  if(csmDevStMode(draft)==='other')text+=` Por limitação do emissor, lançar ${csmDevMoney(v)} em OUTRAS DESPESAS e não repetir o mesmo valor no campo VALOR DO ICMS-ST.`;
  else text+=` Informar o valor no campo próprio VALOR DO ICMS-ST e não repetir em OUTRAS DESPESAS.`;
 }
 return text
};

csmDevWarnings=function(draft,doc){
 const base=csmDevWarningsBase(draft,doc).filter(x=>!String(x).startsWith('SP / ICMS-ST:'));
 if(csmDevHasSt(draft)){
  if(csmDevStMode(draft)==='other')base.push('ICMS-ST: modo alternativo selecionado. O valor do ST será levado para Outras Despesas apenas porque o emissor não permite o campo próprio.');
  else base.push('ICMS-ST: padrão recomendado ativo. O valor será informado somente no campo próprio de ICMS-ST; Outras Despesas não repetirá o ST.');
 }
 return base
};

csmDevCalcFields=function(draft){
 const t=csmDevTotals(draft),e=draft.extras||{},fallback=csmDevStMode(draft)==='other';
 return [
  ['BASE DE CÁLCULO DO ICMS',t.bcIcms],['VALOR DO ICMS',t.vIcms],['BASE DE CÁLCULO ICMS-ST',t.bcSt],
  ['VALOR DO ICMS-ST',fallback?0:t.vSt],['VALOR TOTAL DOS PRODUTOS',t.vProd],['VALOR DO FRETE',e.freight],
  ['VALOR DO SEGURO',e.insurance],['DESCONTO',e.discount],['OUTRAS DESPESAS',csmDevNum(e.other)+(fallback?t.vOutro:0)],
  ['VALOR DO IPI',t.vIpi],['VALOR DO PIS',t.vPis],['VALOR DA COFINS',t.vCofins],['VALOR TOTAL DA NF-e',csmDevModelTotal(draft)]
 ]
};

csmDevProductRows=function(draft){
 const fallback=csmDevStMode(draft)==='other';
 return draft.lines.filter(x=>x.selected&&x.qtyReturn>0).map(x=>{
  const st=csmDevIsSt(x.raw)?` · ICMS-ST ref.: BC ${csmDevMoney(x.bcSt)} / valor ${csmDevMoney(x.vSt)}${fallback?' · lançar em Outras Despesas':' · usar campo próprio ICMS-ST'}`:'';
  const ipi=csmDevNum(x.vIpi)>0?` · IPI devolvido ${csmDevMoney(x.vIpi)} (${csmDevDecimal(x.pDevol)}%)`:'';
  return `<tr><td>${esc(x.code||'—')}</td><td class="desc"><b>${esc(x.description||'')}</b><span class="prod-detail">Item original ${esc(x.n)} · PIS CST ${esc(x.pisCst)} ${csmDevMoney(x.vPis)} · COFINS CST ${esc(x.cofinsCst)} ${csmDevMoney(x.vCofins)}${st}${ipi}</span></td><td>${esc(x.ncm||'—')}</td><td>${esc(x.icmsCode||'—')}</td><td>${esc(x.cfop||'—')}</td><td>${esc(x.unit||'—')}</td><td>${csmDevQty(x.qtyReturn)}</td><td>${csmDevMoney(x.raw?.unit_value)}</td><td>${csmDevMoney(x.vProd)}</td><td>${csmDevMoney(x.bcIcms)}</td><td>${csmDevMoney(x.vIcms)}</td><td>${csmDevDecimal(x.rateIcms)}</td><td>${csmDevMoney(x.vIpi)}</td></tr>`
 }).join('')
};

csmDevRender=function(){
 csmDevRenderV2Base();
 const d=csmDevDraft;if(!d)return;
 if(csmDevHasSt(d)){
  const grid=document.querySelector('#csmDevType')?.closest('.csm-dev-config-grid');
  if(grid&&!document.getElementById('csmDevStHandling')){
   const label=document.createElement('label');label.className='csm-dev-st-mode';
   label.innerHTML=`Tratamento do ICMS-ST<select id="csmDevStHandling"><option value="dedicated" ${csmDevStMode(d)==='dedicated'?'selected':''}>Usar campo próprio VALOR DO ICMS-ST (recomendado)</option><option value="other" ${csmDevStMode(d)==='other'?'selected':''}>Emissor não aceita ST: usar OUTRAS DESPESAS</option></select><small>O CSM nunca duplica o mesmo ST nos dois campos. O modo alternativo deve ser usado somente quando o emissor não permitir informar o ICMS-ST no campo próprio.</small>`;
   grid.appendChild(label);
   label.querySelector('select').onchange=e=>{d.stHandling=e.target.value;for(const line of d.lines||[])if(csmDevIsSt(line.raw)){line.vOutro=d.stHandling==='other'?csmDevRound(line.vSt):0;delete line.manual?.vOutro}csmDevRender()};
  }
 }
 document.querySelectorAll('input[data-dev-field="vOutro"]').forEach(inp=>{
  inp.disabled=true;const label=inp.closest('label');
  if(label){const text=label.childNodes[0];if(text&&text.nodeType===Node.TEXT_NODE)text.textContent=csmDevStMode(d)==='other'?'ST em Outras despesas (automático) ':'Outras despesas do ST (não usada) '}
 });
 if(window.CSM_DEVOLUTION_ENGINE)window.CSM_DEVOLUTION_ENGINE.version=CSM_DEV_UI_VERSION_V3
};

csmDevGuideHtml=function(draft,doc,standalone=false){
 const html=csmDevGuideHtmlV2Base(draft,doc,standalone);
 const css=`
 .prod,.prod thead,.prod tbody,.prod tr,.prod th,.prod td{background:#fff!important;color:#111!important;opacity:1!important}
 .prod th{background:#e7edf4!important;color:#183247!important;font-size:6.7px!important;font-weight:800!important;line-height:1.2!important}
 .prod td{font-size:7px!important;line-height:1.28!important;height:auto!important;min-height:0!important;overflow:visible!important;white-space:normal!important;vertical-align:top!important}
 .prod td.desc{width:25%!important;min-width:0!important}
 .prod td.desc>b{display:block!important;color:#111!important;font-size:7.3px!important;line-height:1.28!important;margin:0 0 3px!important;white-space:normal!important}
 .prod .prod-detail{display:block!important;color:#263746!important;background:#f4f7fa!important;border-top:1px solid #d3dde7!important;padding:3px 2px 1px!important;margin-top:2px!important;font-size:6.3px!important;line-height:1.35!important;white-space:normal!important;overflow:visible!important}
 .csm-dev-print-guide .prod td,.csm-dev-print-guide .prod th,.csm-dev-print-guide .prod b,.csm-dev-print-guide .prod span{opacity:1!important}
 `;
 return standalone?html.replace('</head>',`<style id="csm-dev-print-v3">${css}</style></head>`):`<style id="csm-dev-print-v3">${css}</style>${html}`
};

if(window.CSM_DEVOLUTION_ENGINE)window.CSM_DEVOLUTION_ENGINE.version=CSM_DEV_UI_VERSION_V3;
