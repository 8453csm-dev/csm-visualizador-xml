const fs=require('fs');
const path=require('path');
const snippet=fs.readFileSync(path.join(__dirname,'devolution_engine_snippet.js'),'utf8');
const harness=`
const esc=v=>String(v??''); const $=id=>({}); const state={documents:new Map()}; const activeDoc=()=>null; const els={}; const toast=()=>{}; const clearPrintPages=()=>{};
global.localStorage={getItem(){return null},setItem(){}}; global.document={}; global.window={};
${snippet}
function assert(cond,msg){if(!cond)throw new Error(msg)}
const doc={document_id:'x',doc_type:'nfe',model:'55',access_key:'35260812345678000123550010000000011000000010',number:'1',series:'1',issuer_name:'FORNECEDOR',issuer_doc:'123',recipient_name:'CLIENTE',recipient_doc:'456',recipient_uf:'SP',items:[{n:'1',code:'A',description:'ITEM',qty:'10',unit:'UN',total:1000,cfop:'5102',cst:'00',bc_icms:1000,rate_icms:18,icms:180,bc_icms_st:0,icms_st:0,ipi:100,pis:16.5,cofins:76}]};
let d=csmDevMakeDraft(doc);assert(d.prefix==='5','prefix interno');assert(d.lines[0].cfop==='5202','CFOP comercial interno');assert(d.lines[0].icmsCode==='00','CST regime normal');
d.returnType='partial';d.lines[0].qtyReturn=4;csmDevRecalcLine(d.lines[0],d);assert(d.lines[0].vProd===400,'produto proporcional');assert(d.lines[0].vIcms===72,'ICMS proporcional');assert(d.lines[0].vIpi===40,'IPI proporcional');assert(d.lines[0].pDevol===40,'pDevol proporcional');
d.regime='simple';csmDevRecalcLine(d.lines[0],d,true);assert(d.lines[0].icmsCode==='900','CSOSN 900 no Simples');
const stDoc={...doc,items:[{...doc.items[0],cfop:'5405',bc_icms_st:1200,icms_st:216}]};let s=csmDevMakeDraft(stDoc);assert(s.lines[0].cfop==='5411','CFOP ST comercial');assert(s.lines[0].vOutro===216,'ICMS-ST em vOutro SP');
console.log('Motor Fiscal de Devolução: testes OK');
`;
eval(harness);
