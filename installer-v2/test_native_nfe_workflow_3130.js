const fs=require('fs');
const path=process.env.CSM_APP_JS;
if(!path||!fs.existsSync(path))throw new Error('CSM_APP_JS ausente');
const s=fs.readFileSync(path,'utf8');
const required=[
 'CSM_NATIVE_NFE_WORKFLOW_3130',
 'Obter XML completo',
 '/fiscal/nfe/manifestar',
 '/fiscal/nfe/export-xml',
 '/fiscal/nfe/open-cached',
 '/fiscal/certificate-folders/add',
 '/fiscal/certificates/scan',
 '/fiscal/certificate/pick',
 '/fiscal/certificate/validate',
 'Registrar Ciência',
 'Salvar XML',
 'DANFE / PDF',
 'EMPRESA - SENHA.pfx'
];
for(const t of required)if(!s.includes(t))throw new Error('Frontend 3.13.0 incompleto: '+t);
const m=s.indexOf('CSM_NATIVE_NFE_WORKFLOW_3130');
const tail=s.slice(m);
for(const forbidden of ['open_lookup_site(','/lookup-automation','consultadanfe']){
 if(tail.includes(forbidden))throw new Error('Fluxo 3.13.0 voltou a depender de navegador/site: '+forbidden);
}
console.log('OK - consulta NF-e 3.13.0, certificados, Ciência, XML e DANFE integrados no frontend.');
