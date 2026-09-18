const fs=require('fs');
const p=process.env.CSM_APP_JS;
if(!p||!fs.existsSync(p))throw new Error('CSM_APP_JS ausente');
const s=fs.readFileSync(p,'utf8');
for(const t of [
 'CSM_PUBLIC_NFE_UI_3150',
 "provider:'sefazpublica'",
 'Consulta pública apenas para visualização',
 'hCaptcha',
 '/lookup-automation',
 'csm:external-document-opened'
]) if(!s.includes(t)) throw new Error('UI pública 3.15.0 incompleta: '+t);
const a=s.indexOf(' async function consult(){');
const b=s.indexOf('\n go.onclick=consult;',a);
if(a<0||b<0)throw new Error('consult() pública ausente');
const block=s.slice(a,b);
for(const bad of ['/api/nfe/by-key','waitRepository(','findLocalXML(','Base CSM / Configurações']){
 if(block.includes(bad))throw new Error('Consulta pública ainda depende de fluxo antigo: '+bad);
}
console.log('OK - 3.15.0 consulta somente para visualização via portal público oficial.');
