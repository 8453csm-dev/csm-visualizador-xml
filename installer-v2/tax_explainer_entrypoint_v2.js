// CSM_TAX_EXPLAINER_ENTRYPOINT_V2
// 3.9.2: sincroniza a aba tributaria com a troca REAL de documento ativo.
const CSM_TAX_ENTRY_VERSION='1.0.2';

function csmTaxSyncForActiveDocument(renderIfOpen=false){
  try{
    csmTaxEnsureUi();
    const activeView=(typeof state!=='undefined'&&state)?state.activeView:'';
    if(renderIfOpen&&activeView==='taxexplain')csmTaxRenderCurrent();
  }catch(err){
    console.warn('CSM Entender Tributacao: falha ao sincronizar documento ativo',err);
  }
}

// activateDocument e a fonte oficial de troca/abertura de documento no Visualizador.
// O wrapper nao altera o retorno nem o fluxo existente; apenas sincroniza o modulo depois.
if(typeof activateDocument==='function'&&!globalThis.__CSM_TAX_ACTIVATE_WRAPPED){
  const csmTaxOriginalActivateDocument=activateDocument;
  activateDocument=async function(id){
    const result=await csmTaxOriginalActivateDocument(id);
    csmTaxSyncForActiveDocument(true);
    return result;
  };
  globalThis.__CSM_TAX_ACTIVATE_WRAPPED=true;
}

// Ao limpar/voltar para a tela inicial, atualiza a visibilidade sem polling.
if(typeof showWelcome==='function'&&!globalThis.__CSM_TAX_WELCOME_WRAPPED){
  const csmTaxOriginalShowWelcome=showWelcome;
  showWelcome=function(){
    const result=csmTaxOriginalShowWelcome();
    csmTaxSyncForActiveDocument(false);
    return result;
  };
  globalThis.__CSM_TAX_WELCOME_WRAPPED=true;
}

// Primeira sincronizacao apos todos os patches do app.js estarem carregados.
Promise.resolve().then(()=>csmTaxSyncForActiveDocument(false));

if(globalThis.CSM_TAX_EXPLAINER){
  globalThis.CSM_TAX_EXPLAINER.entryVersion=CSM_TAX_ENTRY_VERSION;
  globalThis.CSM_TAX_EXPLAINER.syncActive=csmTaxSyncForActiveDocument;
}
