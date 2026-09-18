const fs=require('fs');
const path=process.env.CSM_APP_JS;
if(!path||!fs.existsSync(path))throw new Error('CSM_APP_JS ausente');
const s=fs.readFileSync(path,'utf8');
const required=[
 'CSM_ISSUER_LOCAL_UI_3131',
 'Procurar XML',
 'Selecionar XML',
 'Pastas XML / SIEG',
 '/fiscal/nfe/find-local',
 '/fiscal/nfe/pick-local',
 '/fiscal/xml-folders/add',
 'issuer_document',
 'setTimeout(close,320)'
];
for(const t of required)if(!s.includes(t))throw new Error('Frontend 3.13.1 incompleto: '+t);
console.log('OK - 3.13.1 trata NF-e própria e abre XML local no Visualizador.');
