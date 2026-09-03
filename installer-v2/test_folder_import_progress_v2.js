const fs=require('fs');
const path=process.env.CSM_APP_JS;
if(!path||!fs.existsSync(path))throw new Error('CSM_APP_JS ausente');
const s=fs.readFileSync(path,'utf8');
const must=[
 'CSM_FOLDER_IMPORT_PROGRESS_V2',
 "csmFolderImportShow('Selecione a pasta de XMLs...')",
 'await csmNextPaint();',
 'const result=await window.pywebview.api.open_folder();',
 "csmFolderImportStage('Lendo e validando os documentos...')",
 'handleLoadResult(result,true)',
 'csmFolderImportFinish(count)'
];
for(const t of must)if(!s.includes(t))throw new Error('Ausente: '+t);
const show=s.indexOf("csmFolderImportShow('Selecione a pasta de XMLs...')");
const paint=s.indexOf('await csmNextPaint();',show);
const call=s.indexOf('const result=await window.pywebview.api.open_folder();',show);
if(!(show>=0&&paint>show&&call>paint))throw new Error('Ordem incorreta: painel deve aparecer e pintar antes de open_folder');
for(const bad of ['focusTimer=setInterval','fallbackTimer=setTimeout',"window.addEventListener('blur',onBlur"])if(s.includes(bad))throw new Error('Lógica de foco antiga ainda presente: '+bad);
console.log('OK: painel de importação pinta antes do seletor/processamento e não depende de foco do Windows.');
