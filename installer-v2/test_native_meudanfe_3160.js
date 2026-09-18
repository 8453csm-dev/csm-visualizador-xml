const fs=require('fs');
const p=process.env.CSM_APP_JS;
if(!p||!fs.existsSync(p))throw new Error('CSM_APP_JS ausente');
const s=fs.readFileSync(p,'utf8');
for(const t of [
 'CSM_MEUDANFE_UI_3160',
 '/provider/meudanfe/status',
 '/provider/meudanfe/config',
 '/provider/meudanfe/consult',
 'Credential Manager',
 'XML validado e aberto no Visualizador'
]) if(!s.includes(t))throw new Error('UI Meu Danfe 3.16.0 incompleta: '+t);
const a=s.indexOf(' async function consult(){');
const b=s.indexOf('\n go.onclick=consult;',a);
if(a<0||b<0)throw new Error('consult() 3.16.0 ausente');
const block=s.slice(a,b);
for(const bad of ['sefazpublica','hCaptcha','/api/nfe/by-key','waitRepository(']){
 if(block.includes(bad))throw new Error('Consulta 3.16.0 ainda usa fluxo antigo: '+bad);
}
console.log('OK - 3.16.0: chave -> API Meu Danfe -> XML -> Visualizador.');
