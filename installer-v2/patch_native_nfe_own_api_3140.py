from pathlib import Path
import sys

MARK='CSM_OWN_NFE_UI_3140'
if len(sys.argv)!=2: raise SystemExit('uso: patch_native_nfe_own_api_3140.py <pasta-web>')
app=Path(sys.argv[1])/'app.js'
if not app.is_file(): raise SystemExit('app.js não encontrado')
s=app.read_text(encoding='utf-8')
if MARK in s:
    print('UI CSM Consulta NF-e 3.14.0 já aplicada')
    raise SystemExit(0)
if 'CSM_ISSUER_LOCAL_UI_3131' not in s:
    raise SystemExit('Aplique frontend 3.13.1 antes')

old='''<div class="csm3130-title">Consultar NF-e</div><div class="csm3130-sub">Consulte pela chave. O CSM usa os Web Services oficiais e só salva arquivo quando você pedir.</div>'''
new='''<div class="csm3130-title">Consultar NF-e</div><div class="csm3130-sub">Cole a chave de acesso. A Base CSM localiza o XML e abre a nota diretamente no Visualizador.</div>'''
if old not in s: raise SystemExit('Subtítulo 3.13 não localizado')
s=s.replace(old,new,1)

old='''<label class="csm3130-label">Empresa / certificado A1</label><div class="csm3130-row"><select id="csm3130-cert" class="csm3130-select"><option value="">Automático</option></select><button id="csm3130-manage-toggle" class="csm3130-btn secondary" type="button">Certificados</button></div><div class="csm3130-hint">Se o CSM já reconhecer o certificado da empresa, basta colar a chave e consultar.</div>'''
new='''<select id="csm3130-cert" class="csm3130-select" style="display:none"><option value="">Automático</option></select><div class="csm3130-actions" style="margin-top:9px"><button id="csm3130-manage-toggle" class="csm3130-btn ghost" type="button">Base CSM / Configurações</button></div><div class="csm3130-hint">A consulta principal usa somente a chave. Certificados e fontes XML trabalham em segundo plano para alimentar a Base CSM.</div>'''
if old not in s: raise SystemExit('Bloco visível de certificado não localizado')
s=s.replace(old,new,1)

old='''<div id="csm3130-manage" class="csm3130-manage"><strong>Certificados digitais A1</strong><div class="csm3130-hint">Adicione a pasta onde ficam os PFX/P12. O padrão EMPRESA - SENHA.pfx é reconhecido localmente e a senha não é mostrada na interface.</div>'''
new='''<div id="csm3130-manage" class="csm3130-manage"><strong>Base CSM de NF-e</strong><div class="csm3130-hint">A Base CSM é alimentada pelos XMLs já utilizados, pastas XML/SIEG e pela Distribuição DF-e oficial dos certificados A1 cadastrados.</div><div class="csm3130-actions"><button id="csm3140-sync" class="csm3130-btn secondary" type="button">Sincronizar Base CSM</button><button id="csm3140-refresh" class="csm3130-btn ghost" type="button">Atualizar status</button></div><div id="csm3140-repo-status" class="csm3130-hint" style="margin:9px 0 13px">Carregando status da base…</div><strong>Certificados digitais A1</strong><div class="csm3130-hint">Os certificados ficam nas configurações e não precisam ser escolhidos a cada consulta. O padrão EMPRESA - SENHA.pfx é reconhecido localmente e a senha não é mostrada.</div>'''
if old not in s: raise SystemExit('Painel de certificados não localizado')
s=s.replace(old,new,1)

old='''const cnpj=String(data?.cnpj||cert.value||'').trim();'''
new='''const cnpj=String(data?.cnpj||data?.actor_cnpj||cert.value||'').trim();'''
if old not in s: raise SystemExit('Manifestação sem actor_cnpj não localizada')
s=s.replace(old,new,1)

start=s.find(' async function consult(){')
if start<0: raise SystemExit('consult() não localizada')
end=s.find('\\n go.onclick=consult;',start)
if end<0: raise SystemExit('Fim de consult() não localizado')
new_consult=r''' async function waitRepository(k,seconds=30){
  const until=Date.now()+seconds*1000;
  while(Date.now()<until){
    await new Promise(r=>setTimeout(r,3000));
    try{
      const data=await request('/api/nfe/by-key',{key:k});
      if(data?.xml_available||data?.summary_only)return data;
      if(!data?.syncing)break
    }catch(_){break}
  }
  return null
 }
 async function consult(){
  const k=keyOf(key.value);if(!k){setStatus('A chave precisa ter 44 dígitos e DV válido.','err');return}
  go.disabled=true;result.className='csm3130-result';setStatus('Consultando a Base CSM…','');
  try{
    let data=await request('/api/nfe/by-key',{key:k});
    if(data?.xml_available){
      setStatus('NF-e localizada. Abrindo no Visualizador…','ok');
      actionsFor({...data,status:'NF-e LOCALIZADA'},k);setTimeout(close,320);return
    }
    if(data?.summary_only||data?.requires_manifestation){
      data={...data,cnpj:data.actor_cnpj||data.cnpj,status:'NF-e LOCALIZADA'};
      setStatus('NF-e localizada na Base CSM. O XML completo ainda depende da liberação oficial para esta empresa.','');
      actionsFor(data,k);return
    }
    if(data?.syncing){
      setStatus('A chave ainda não estava indexada. Sincronizando a Base CSM e procurando novamente…','');
      const retry=await waitRepository(k,30);
      if(retry?.xml_available){
        setStatus('NF-e localizada. Abrindo no Visualizador…','ok');
        actionsFor({...retry,status:'NF-e LOCALIZADA'},k);setTimeout(close,320);return
      }
      if(retry?.summary_only||retry?.requires_manifestation){
        retry.cnpj=retry.actor_cnpj||retry.cnpj;setStatus('NF-e localizada. O XML completo ainda não foi distribuído para esta empresa.','');actionsFor({...retry,status:'NF-e LOCALIZADA'},k);return
      }
    }
    setStatus(data?.message||'A NF-e ainda não está na Base CSM. A sincronização continuará em segundo plano.','');
    result.className='csm3130-result show';
    result.innerHTML='<strong>Ainda não indexada</strong><div class="csm3130-hint">A Base CSM continuará consultando as fontes oficiais e as pastas XML configuradas. Você pode abrir as configurações para sincronizar agora.</div><div class="csm3130-actions"><button id="csm3140-open-settings" class="csm3130-btn secondary" type="button">Base CSM / Configurações</button></div>';
    result.querySelector('#csm3140-open-settings').onclick=()=>manage.classList.add('show')
  }catch(e){setStatus(e.message,'err')}finally{go.disabled=false}
 }'''
s=s[:start]+new_consult+s[end:]

needle=''' q('csm3130-manage-toggle').onclick=()=>manage.classList.toggle('show');'''
if needle not in s: raise SystemExit('Toggle de configurações não localizado')
inject=r''' async function loadRepoStatus(){
  const el=q('csm3140-repo-status');if(!el)return;
  try{
    const r=await request('/api/nfe/repository/status',undefined,'GET');
    const xml=Number(r?.xml_count||0),idx=Number(r?.index_count||0),run=!!r?.sync_running,processed=Number(r?.sync_processed||0);
    el.textContent=\`\${xml} XML\${xml===1?'':'s'} completos • \${idx} chave\${idx===1?'':'s'} indexada\${idx===1?'':'s'}\${run?' • sincronizando agora ('+processed+' empresas processadas)':''}\`;
  }catch(e){el.textContent='Status da Base CSM indisponível: '+e.message}
 }
 const syncBtn=q('csm3140-sync'),refreshBtn=q('csm3140-refresh');
 if(syncBtn)syncBtn.onclick=async()=>{try{await request('/api/nfe/repository/sync',{});setStatus('Sincronização da Base CSM iniciada em segundo plano.','ok');loadRepoStatus()}catch(e){setStatus(e.message,'err')}};
 if(refreshBtn)refreshBtn.onclick=loadRepoStatus;
 q('csm3130-manage-toggle').onclick=()=>{manage.classList.toggle('show');if(manage.classList.contains('show'))loadRepoStatus()};'''
s=s.replace(needle,inject,1)

s=s.rstrip()+"\\n// "+MARK+" — consulta principal somente por chave; certificados viraram infraestrutura da Base CSM.\\n"
for tok in (MARK,'/api/nfe/by-key','Sincronizando a Base CSM','Base CSM / Configurações','/api/nfe/repository/status','/api/nfe/repository/sync'):
    if tok not in s: raise SystemExit('Frontend 3.14.0 incompleto: '+tok)
app.write_text(s,encoding='utf-8',newline='\\n')
print('3.14.0: consulta NF-e somente por chave usando a API/Base CSM.')
