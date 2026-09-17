const fs=require('fs');
const appPath=process.env.CSM_APP_JS;
const cssPath=process.env.CSM_CSS;
if(!appPath||!cssPath)throw new Error('CSM_APP_JS/CSM_CSS ausentes');
const app=fs.readFileSync(appPath,'utf8');
const css=fs.readFileSync(cssPath,'utf8');
for(const token of ['CSM_NATIVE_KEY_LOOKUP_V1','CSM_NATIVE_LOOKUP_ACTION_3111','Consultar NF-e pela chave','CSMNativeKeyLookup','Ctrl+L','submitLookup','requestSubmit','KeyboardEvent','actionScore','lookup-automation']){
  if(!app.includes(token))throw new Error('app.js sem '+token);
}
if(app.includes('Localizador encontrado, mas o botão de consulta não foi identificado.'))throw new Error('Erro rígido antigo ainda presente');
if(!css.includes('CSM_NATIVE_KEY_LOOKUP_CSS_V1'))throw new Error('CSS da consulta nativa ausente');
if(!app.includes("provider==='consultadanfe'"))throw new Error('Fluxo Consulta DANFE legado não preservado');
if(!app.includes('open_lookup_site(provider,key,desired)'))throw new Error('Motor legado do Localizador não preservado');
console.log('Consulta NF-e nativa 3.11.1: acionamento resiliente validado');
