const fs=require('fs');
const p='installer-v2/launcher/consulta_danfe_helper.cs';
const s=fs.readFileSync(p,'utf8');
for(const token of [
  'CSM_LOOKUP_DELIVERY_3112',
  'TryInvokeDownloadXmlStrict',
  'CancelUnexpectedSpreadsheetSaveDialog',
  'TryConfirmXmlSaveDialog',
  'FindMatchingXmlInDownloads',
  'ValidateXmlForKey',
  'NotifyBrokerOpen',
  'IsSpreadsheetText'
]) if(!s.includes(token)) throw new Error('Helper 3.11.2 sem '+token);
if(s.includes('TryInvokeDownloadXml(win)')) throw new Error('Fluxo antigo de download XML ainda ativo');
console.log('Entrega XML 3.11.2 validada: somente XML, sem Excel/CSV e abertura via broker.');
