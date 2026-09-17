// CSM_NATIVE_NFE_LOOKUP_UI_V1
const CSM_NFE_BROKER='http://127.0.0.1:47878';

function csmNormalizeNfeKey(value){
  return String(value||'').toUpperCase().replace(/[^0-9A-Z]/g,'').slice(0,44);
}

function csmLookupEl(id){return document.getElementById(id)}

function csmSetLookupStatus(text,kind=''){
  const el=csmLookupEl('csmNfeLookupStatus');if(!el)return;
  el.textContent=text||'';el.dataset.kind=kind||'';
}

function csmSetLookupBusy(busy){
  const btn=csmLookupEl('csmNfeLookupSubmit');
  const input=csmLookupEl('csmNfeLookupKey');
  if(btn){btn.disabled=!!busy;btn.textContent=busy?'Consultando…':'Consultar NF-e'}
  if(input)input.disabled=!!busy;
}

async function csmBrokerJSON(path,options={}){
  const response=await fetch(CSM_NFE_BROKER+path,options);
  let data={};
  try{data=await response.json()}catch(_){data={ok:false,error:`Falha HTTP ${response.status}`}}
  if(!response.ok){
    const error=new Error(data?.error||`Falha HTTP ${response.status}`);
    error.code=data?.code||'';error.status=response.status;error.payload=data;throw error;
  }
  return data;
}

async function csmRefreshLookupConfig(){
  const badge=csmLookupEl('csmNfeConfigBadge');
  try{
    const data=await csmBrokerJSON('/nfe-lookup/config');
    if(badge){
      badge.textContent=data.configured?'NFE.io configurada neste Windows':'Configuração necessária';
      badge.dataset.ready=data.configured?'1':'0';
    }
    return !!data.configured;
  }catch(_){
    if(badge){badge.textContent='Não foi possível verificar a configuração';badge.dataset.ready='0'}
    return false;
  }
}

function csmToggleLookupConfig(force){
  const panel=csmLookupEl('csmNfeConfigPanel');if(!panel)return;
  const show=typeof force==='boolean'?force:panel.classList.contains('hidden');
  panel.classList.toggle('hidden',!show);
  if(show)setTimeout(()=>csmLookupEl('csmNfeApiKey')?.focus(),40);
}

async function csmSaveLookupConfig(){
  const apiKey=String(csmLookupEl('csmNfeApiKey')?.value||'').trim();
  const status=csmLookupEl('csmNfeConfigStatus');
  if(!apiKey){if(status){status.textContent='Informe a chave da API.';status.dataset.kind='error'};return}
  const btn=csmLookupEl('csmNfeConfigSave');if(btn)btn.disabled=true;
  if(status){status.textContent='Protegendo a credencial no Windows…';status.dataset.kind=''}
  try{
    await csmBrokerJSON('/nfe-lookup/config',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({provider:'nfeio',api_key:apiKey})
    });
    if(csmLookupEl('csmNfeApiKey'))csmLookupEl('csmNfeApiKey').value='';
    if(status){status.textContent='Configuração salva com proteção do Windows.';status.dataset.kind='ok'}
    await csmRefreshLookupConfig();
    setTimeout(()=>csmToggleLookupConfig(false),600);
  }catch(error){
    if(status){status.textContent=error?.message||'Não foi possível salvar a configuração.';status.dataset.kind='error'}
  }finally{if(btn)btn.disabled=false}
}

async function csmRunNativeNfeLookup(){
  const input=csmLookupEl('csmNfeLookupKey');
  const key=csmNormalizeNfeKey(input?.value);
  if(input)input.value=key;
  if(key.length!==44){csmSetLookupStatus(`Informe a chave completa: ${key.length}/44 caracteres.`,'error');input?.focus();return}
  csmSetLookupBusy(true);csmSetLookupStatus('Consultando NF-e pela chave de acesso…');
  try{
    const data=await csmBrokerJSON('/nfe-lookup',{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key})
    });
    csmSetLookupStatus(data.source==='cache'?'XML já consultado. Abrindo no Visualizador…':'NF-e localizada. Abrindo no Visualizador…','ok');
    setTimeout(()=>csmCloseNativeNfeLookup(),650);
  }catch(error){
    if(error?.code==='config_required'){
      csmSetLookupStatus('Configure a consulta uma única vez para continuar.','warn');
      csmToggleLookupConfig(true);
    }else{
      csmSetLookupStatus(error?.message||'Não foi possível consultar esta NF-e.','error');
    }
  }finally{csmSetLookupBusy(false)}
}

function csmOpenNativeNfeLookup(){
  const modal=csmLookupEl('csmNfeLookupModal');if(!modal)return;
  modal.classList.remove('hidden');modal.setAttribute('aria-hidden','false');
  csmSetLookupStatus('Cole a chave de acesso de 44 caracteres.');
  const input=csmLookupEl('csmNfeLookupKey');if(input){input.disabled=false;setTimeout(()=>input.focus(),50)}
  void csmRefreshLookupConfig();
}

function csmCloseNativeNfeLookup(){
  const modal=csmLookupEl('csmNfeLookupModal');if(!modal)return;
  modal.classList.add('hidden');modal.setAttribute('aria-hidden','true');
  csmToggleLookupConfig(false);
}

function csmInstallNativeNfeLookupUI(){
  if(csmLookupEl('csmNfeLookupBtn'))return;
  const folderBtn=csmLookupEl('folderBtn');
  const topActions=document.querySelector('.top-actions');
  if(!folderBtn&&!topActions){setTimeout(csmInstallNativeNfeLookupUI,250);return}

  const button=document.createElement('button');
  button.id='csmNfeLookupBtn';button.className='button csm-nfe-lookup-trigger';button.type='button';
  button.title='Consultar uma NF-e usando a chave de acesso';
  button.innerHTML='<span class="csm-lookup-search-icon">⌕</span><span>Consultar NF-e</span>';
  button.addEventListener('click',csmOpenNativeNfeLookup);
  if(folderBtn?.parentNode)folderBtn.parentNode.insertBefore(button,folderBtn.nextSibling);else topActions.prepend(button);

  const modal=document.createElement('div');
  modal.id='csmNfeLookupModal';modal.className='modal-backdrop hidden csm-native-nfe-modal';modal.setAttribute('aria-hidden','true');
  modal.innerHTML=`
    <div class="modal csm-native-nfe-card" role="dialog" aria-modal="true" aria-labelledby="csmNfeLookupTitle">
      <div class="modal-header">
        <div>
          <strong id="csmNfeLookupTitle">Consultar NF-e pela chave</strong>
          <span class="csm-native-nfe-subtitle">Localize o XML e abra a nota diretamente no CSM Visualizador XML.</span>
        </div>
        <button class="modal-close" id="csmNfeLookupClose" aria-label="Fechar">×</button>
      </div>
      <div class="csm-native-nfe-body">
        <label class="csm-native-nfe-label" for="csmNfeLookupKey">Chave de acesso</label>
        <div class="csm-native-nfe-keyrow">
          <input id="csmNfeLookupKey" class="csm-native-nfe-input" inputmode="numeric" autocomplete="off" spellcheck="false" maxlength="60" placeholder="Cole aqui a chave de acesso da NF-e">
          <span id="csmNfeLookupCounter" class="csm-native-nfe-counter">0/44</span>
        </div>
        <div class="csm-native-nfe-hint">Pode colar a chave com espaços ou pontuação; o Visualizador limpa automaticamente.</div>
        <div id="csmNfeLookupStatus" class="csm-native-nfe-status">Cole a chave de acesso de 44 caracteres.</div>

        <div class="csm-native-nfe-configline">
          <span id="csmNfeConfigBadge" class="csm-native-nfe-badge" data-ready="0">Verificando configuração…</span>
          <button id="csmNfeConfigToggle" class="button small-button" type="button">Configurar consulta</button>
        </div>

        <div id="csmNfeConfigPanel" class="csm-native-nfe-config hidden">
          <div class="csm-native-nfe-config-title">Configuração da consulta</div>
          <div class="csm-native-nfe-config-copy">A credencial é salva criptografada pelo Windows e não fica gravada em texto puro.</div>
          <label class="csm-native-nfe-label" for="csmNfeApiKey">Chave de dados da NFE.io</label>
          <input id="csmNfeApiKey" class="csm-native-nfe-input" type="password" autocomplete="new-password" placeholder="Cole a chave da API">
          <div class="csm-native-nfe-config-actions">
            <span id="csmNfeConfigStatus" class="csm-native-nfe-config-status"></span>
            <button id="csmNfeConfigSave" class="button primary" type="button">Salvar configuração</button>
          </div>
        </div>
      </div>
      <div class="csm-native-nfe-actions">
        <button id="csmNfeLookupCancel" class="button" type="button">Cancelar</button>
        <button id="csmNfeLookupSubmit" class="button primary" type="button">Consultar NF-e</button>
      </div>
    </div>`;
  document.body.appendChild(modal);

  const input=csmLookupEl('csmNfeLookupKey');
  input?.addEventListener('input',()=>{
    const clean=csmNormalizeNfeKey(input.value);input.value=clean;
    const counter=csmLookupEl('csmNfeLookupCounter');if(counter)counter.textContent=`${clean.length}/44`;
    if(clean.length===44)csmSetLookupStatus('Chave completa. Clique em Consultar NF-e.');
  });
  input?.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();void csmRunNativeNfeLookup()}else if(event.key==='Escape')csmCloseNativeNfeLookup()});
  csmLookupEl('csmNfeLookupSubmit')?.addEventListener('click',()=>void csmRunNativeNfeLookup());
  csmLookupEl('csmNfeLookupCancel')?.addEventListener('click',csmCloseNativeNfeLookup);
  csmLookupEl('csmNfeLookupClose')?.addEventListener('click',csmCloseNativeNfeLookup);
  csmLookupEl('csmNfeConfigToggle')?.addEventListener('click',()=>csmToggleLookupConfig());
  csmLookupEl('csmNfeConfigSave')?.addEventListener('click',()=>void csmSaveLookupConfig());
  csmLookupEl('csmNfeApiKey')?.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();void csmSaveLookupConfig()}});
  modal.addEventListener('mousedown',event=>{if(event.target===modal)csmCloseNativeNfeLookup()});
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',csmInstallNativeNfeLookupUI,{once:true});
else csmInstallNativeNfeLookupUI();
