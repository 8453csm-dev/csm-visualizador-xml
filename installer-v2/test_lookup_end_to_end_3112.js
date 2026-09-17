const fs=require('fs');
const helper=fs.readFileSync('installer-v2/launcher/consulta_danfe_helper.cs','utf8');
const app=fs.readFileSync(process.env.CSM_APP_JS,'utf8');
for(const t of ['CSM_LOOKUP_DELIVERY_3112','TryInvokeDownloadXmlStrict','CancelUnexpectedSpreadsheetSaveDialog','ValidateXmlForKey','NotifyBrokerOpen','CSM_LOOKUP_STATUS_TAG_3112','TagXmlWithStatus']){
  if(!helper.includes(t)) throw new Error('Helper sem '+t);
}
for(const t of ['CSM_LOOKUP_STATUS_TOAST_3112','NF-e consultada: ${st}']){
  if(!app.includes(t)) throw new Error('Frontend sem '+t);
}
if(helper.includes('TryInvokeDownloadXml(win)')) throw new Error('Fluxo antigo de download ainda ativo');
console.log('Consulta 3.11.2 validada: XML-only, status e abertura automática via broker.');
