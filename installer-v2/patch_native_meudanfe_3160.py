from pathlib import Path
import sys

MARK='CSM_MEUDANFE_UI_3160'
if len(sys.argv)!=2: raise SystemExit('uso: patch_native_meudanfe_3160.py <pasta-web>')
app=Path(sys.argv[1])/'app.js'
if not app.is_file(): raise SystemExit('app.js não encontrado')
s=app.read_text(encoding='utf-8')
if MARK in s:
    print('UI Meu Danfe 3.16.0 já aplicada')
    raise SystemExit(0)
if 'CSM_PUBLIC_NFE_UI_3150' not in s:
    raise SystemExit('Aplique a UI 3.15.0 antes')

s=s.replace(
'''<div class="csm3130-title">Consultar NF-e</div><div class="csm3130-sub">Cole a chave de acesso. O CSM consulta a página pública oficial da NF-e e abre a visualização dentro do software.</div>''',
'''<div class="csm3130-title">Consultar NF-e</div><div class="csm3130-sub">Cole a chave de acesso. O CSM localiza o XML pela integração fiscal e abre a nota completa diretamente no Visualizador.</div>''',
1)

old_hint='''<div class="csm3130-hint">Consulta pública apenas para visualização. Não precisa de XML, certificado digital ou Base CSM. Se a Receita solicitar hCaptcha, faça a validação na janela oficial que abrir.</div>'''
new_hint='''<div id="csm3160-provider-hint" class="csm3130-hint">Verificando a integração de consulta…</div>
<div id="csm3160-provider-setup" class="csm3130-result" style="margin-top:12px">
  <strong>Configuração inicial da consulta</strong>
  <div class="csm3130-hint" style="margin-top:5px">Informe uma única vez a Api-Key criada na Área do Cliente do Meu Danfe em <b>API / Integração</b>. Ela será guardada no Credential Manager do Windows e não fica salva no navegador.</div>
  <div class="csm3130-hint" style="margin-top:5px">A busca de uma NF-e nova por chave pode consumir R$ 0,03 conforme a política atual do provedor; notas já existentes na conta podem ser consultadas novamente sem nova cobrança.</div>
  <div class="csm3130-row" style="margin-top:10px">
    <input id="csm3160-api-key" class="csm3130-input" type="password" autocomplete="off" placeholder="Api-Key Meu Danfe">
    <button id="csm3160-save-key" class="csm3130-btn" type="button">Salvar integração</button>
  </div>
  <div id="csm3160-config-status" class="csm3130-hint" style="margin-top:7px"></div>
</div>'''
if old_hint not in s: raise SystemExit('Hint público 3.15.0 não localizado')
s=s.replace(old_hint,new_hint,1)

start=s.find(' async function consult(){')
end=s.find('\n go.onclick=consult;',start)
if start<0 or end<0: raise SystemExit('consult() 3.15.0 não localizada')

new_consult=r''' let meuDanfeConfigured=false;
 async function loadMeuDanfeStatus(){
  const hint=q('csm3160-provider-hint'),setup=q('csm3160-provider-setup');
  try{
    await waitApi();
    const r=await fetch('http://127.0.0.1:47878/provider/meudanfe/status');
    if(!r.ok)throw new Error(await r.text());
    const d=await r.json();
    meuDanfeConfigured=!!d?.configured;
    if(hint)hint.textContent=meuDanfeConfigured?'Integração de consulta pronta. Basta colar a chave e consultar.':'Configure a integração uma única vez para habilitar a busca por chave.';
    if(setup){setup.classList.toggle('show',!meuDanfeConfigured);setup.style.display=meuDanfeConfigured?'none':'block'}
  }catch(e){
    meuDanfeConfigured=false;
    if(hint)hint.textContent='Não foi possível verificar a integração de consulta.';
    if(setup){setup.classList.add('show');setup.style.display='block'}
  }
 }
 async function saveMeuDanfeKey(){
  const input=q('csm3160-api-key'),msg=q('csm3160-config-status'),btn=q('csm3160-save-key');
  const apiKey=String(input?.value||'').trim();
  if(apiKey.length<8){if(msg)msg.textContent='Informe uma Api-Key válida.';return}
  if(btn)btn.disabled=true;if(msg)msg.textContent='Salvando no Credential Manager do Windows…';
  try{
    const r=await fetch('http://127.0.0.1:47878/provider/meudanfe/config',{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key:apiKey})
    });
    if(!r.ok)throw new Error((await r.text())||'Falha ao salvar a Api-Key.');
    if(input)input.value='';
    if(msg)msg.textContent='Integração configurada.';
    await loadMeuDanfeStatus()
  }catch(e){if(msg)msg.textContent=e?.message||String(e)}
  finally{if(btn)btn.disabled=false}
 }
 async function consult(){
  const k=keyOf(key.value);if(!k){setStatus('A chave precisa ter 44 dígitos e DV válido.','err');return}
  if(!meuDanfeConfigured){
    setStatus('Configure a integração uma única vez antes da primeira consulta.','err');
    const setup=q('csm3160-provider-setup');if(setup){setup.style.display='block';setup.classList.add('show')}
    q('csm3160-api-key')?.focus();return
  }
  go.disabled=true;result.className='csm3130-result';
  setStatus('Buscando a NF-e pela chave de acesso…','');
  let timeout=null,opened=false;
  const onOpened=e=>{
    const path=String(e?.detail?.path||'');
    if(!/\.xml$/i.test(path))return;
    opened=true;clearTimeout(timeout);window.removeEventListener('csm:external-document-opened',onOpened);
    setStatus('NF-e localizada. XML validado e aberto no Visualizador.','ok');
    saveHistory(k);setTimeout(close,380)
  };
  window.addEventListener('csm:external-document-opened',onOpened);
  try{
    await waitApi();
    const resp=await fetch('http://127.0.0.1:47878/provider/meudanfe/consult',{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:k})
    });
    if(!resp.ok){let d='';try{d=await resp.text()}catch(_){}
      throw new Error(d||'Não foi possível consultar a NF-e.')}
    const data=await resp.json();
    if(!data?.ok){
      if(data?.code==='api_key_required'){meuDanfeConfigured=false;await loadMeuDanfeStatus()}
      throw new Error(data?.error||'NF-e não localizada.')
    }
    if(data?.xml_available){
      setStatus(data?.cached?'XML já estava no cache seguro do CSM. Abrindo a nota…':'XML localizado. Abrindo a nota completa no Visualizador…','ok');
      if(data?.opened&&!opened){
        timeout=setTimeout(()=>{if(!opened){setStatus('XML localizado e encaminhado ao Visualizador.','ok');go.disabled=false}},3500)
      }
      return
    }
    throw new Error('O provedor não devolveu o XML desta NF-e.')
  }catch(e){
    clearTimeout(timeout);window.removeEventListener('csm:external-document-opened',onOpened);
    setStatus(e?.message||String(e),'err');go.disabled=false
  }
 }'''
s=s[:start]+new_consult+s[end:]

# Conecta configuração ao modal e carrega status quando abrir.
hook=''' go.onclick=consult;'''
if hook not in s: raise SystemExit('go.onclick não localizado')
s=s.replace(hook,''' q('csm3160-save-key').onclick=saveMeuDanfeKey;
 loadMeuDanfeStatus();
 go.onclick=consult;''',1)

# Remove referências visíveis ao fluxo público/hCaptcha deste modal.
s=s.replace("Consulta oficial aberta. Se a Receita pedir hCaptcha, valide na janela que apareceu; depois o CSM continua sozinho.","",1)

s=s.rstrip()+"\n// "+MARK+" — chave -> Meu Danfe API v2 -> XML temporário -> aba nativa do Visualizador.\n"
for tok in (MARK,'/provider/meudanfe/status','/provider/meudanfe/config','/provider/meudanfe/consult','Credential Manager','XML validado e aberto no Visualizador'):
    if tok not in s: raise SystemExit('Frontend Meu Danfe 3.16.0 incompleto: '+tok)
block=s[s.find(' async function consult(){'):s.find('\n go.onclick=consult;',s.find(' async function consult(){'))]
for forbidden in ('sefazpublica','hCaptcha','/api/nfe/by-key','waitRepository('):
    if forbidden in block: raise SystemExit('Consulta 3.16.0 ainda depende do fluxo antigo: '+forbidden)
app.write_text(s,encoding='utf-8',newline='\n')
print('3.16.0: chave consulta XML via Meu Danfe API e abre a NF-e no Visualizador.')
