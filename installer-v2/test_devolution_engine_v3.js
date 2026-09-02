const fs=require('fs');
const path=require('path');
const snippet=fs.readFileSync(path.join(__dirname,'devolution_engine_snippet.js'),'utf8');
const v3=fs.readFileSync(path.join(__dirname,'devolution_engine_v3_patch.js'),'utf8');
const harness=`
const esc=v=>String(v??''); const $=id=>null; const state={documents:new Map()}; const activeDoc=()=>null; const els={printRoot:{innerHTML:''}}; const toast=()=>{}; const clearPrintPages=()=>{};
global.localStorage={getItem(){return null},setItem(){}}; global.document={querySelector(){return null},querySelectorAll(){return []}}; global.window={CSM_DEVOLUTION_ENGINE:{}}; global.Node={TEXT_NODE:3};
${snippet}
function csmDevUpgradeDraftV2(d){return d}
${v3}
function assert(cond,msg){if(!cond)throw new Error(msg)}
const doc={document_id:'st',doc_type:'nfe',model:'55',access_key:'35260949318538000308550000006406451139122276',number:'640645',series:'0',issuer_name:'FORNECEDOR',issuer_doc:'49318538000308',recipient_name:'CLIENTE',recipient_doc:'59133728000134',recipient_uf:'SP',items:[{n:'1',code:'A',description:'ITEM ST',qty:'1',unit:'UN',unit_value:100,total:100,cfop:'5405',cst:'500',bc_icms:50,rate_icms:18,icms:9,bc_icms_st:120,icms_st:21.60,ipi:0,pis:1.65,cofins:7.6}],totals:{products:100,freight:0,insurance:0,discount:0,other:0}};
let d=csmDevMakeDraft(doc);
assert(d.lines[0].cfop==='5411','CFOP ST comercial');
assert(d.lines[0].vSt===21.6,'valor ST preservado');
assert(d.lines[0].vOutro===0,'modo padrão não duplica ST em vOutro');
let fields=csmDevCalcFields(d);let map=Object.fromEntries(fields);
assert(map['VALOR DO ICMS-ST']===21.6,'modo padrão mostra ST no campo próprio');
assert(map['OUTRAS DESPESAS']===0,'modo padrão não repete ST em outras despesas');
assert(csmDevInfoAdFisco(d).includes('campo próprio VALOR DO ICMS-ST'),'informação complementar do modo padrão');
d.stHandling='other';csmDevApplyStHandling(d);fields=csmDevCalcFields(d);map=Object.fromEntries(fields);
assert(d.lines[0].vOutro===21.6,'fallback leva ST para vOutro');
assert(map['VALOR DO ICMS-ST']===0,'fallback zera campo próprio no modelo');
assert(map['OUTRAS DESPESAS']===21.6,'fallback usa outras despesas uma única vez');
assert(csmDevInfoAdFisco(d).includes('OUTRAS DESPESAS'),'fallback é explicado nas informações complementares');
assert(csmDevProductRows(d).includes('prod-detail'),'detalhe legível dos produtos presente');
assert(v3.includes('background:#fff!important')&&v3.includes('overflow:visible!important'),'CSS de impressão impede texto apagado/cortado');
console.log('Motor Fiscal 1.2: ICMS-ST sem duplicidade e PDF legível OK');
`;
eval(harness);
