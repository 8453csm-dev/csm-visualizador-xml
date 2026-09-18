const fs=require('fs');
const p=process.env.CSM_APP_JS;if(!p||!fs.existsSync(p))throw new Error('CSM_APP_JS ausente');
const s=fs.readFileSync(p,'utf8');
for(const t of ['CSM_OWN_NFE_UI_3140','/api/nfe/by-key','Base CSM / Configurações','/api/nfe/repository/sync','/api/nfe/repository/status','waitRepository']){
 if(!s.includes(t))throw new Error('UI 3.14.0 incompleta: '+t)
}
if(!s.includes('style="display:none"><option value="">Automático</option>'))throw new Error('Seleção de certificado ainda está visível na consulta principal');
console.log('OK - 3.14.0 consulta somente pela chave e usa a Base CSM/API própria.');
