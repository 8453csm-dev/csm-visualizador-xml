from pathlib import Path
import sys

MARK='CSM_SOURCE_AWARE_UI_3141'
if len(sys.argv)!=2: raise SystemExit('uso: patch_native_nfe_sources_3141.py <pasta-web>')
app=Path(sys.argv[1])/'app.js'
if not app.is_file(): raise SystemExit('app.js não encontrado')
s=app.read_text(encoding='utf-8')
if MARK in s:
    print('UI de fontes 3.14.1 já aplicada')
    raise SystemExit(0)
if 'CSM_OWN_NFE_UI_3140' not in s:
    raise SystemExit('Aplique a UI 3.14.0 antes')

old=r'''    if(data?.syncing){
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
    result.querySelector('#csm3140-open-settings').onclick=()=>manage.classList.add('show')'''

new=r'''    setStatus(data?.message||'O XML não foi localizado nas fontes disponíveis.','');
    result.className='csm3130-result show';
    result.innerHTML='<strong>XML não localizado agora</strong><div class="csm3130-hint">O CSM já pesquisou a Base CSM e as fontes XML/SIEG disponíveis neste computador. A sincronização DF-e pode continuar em segundo plano, mas ela só traz documentos liberados para os certificados autorizados.</div><div class="csm3130-actions"><button id="csm3141-retry" class="csm3130-btn" type="button">Tentar novamente</button><button id="csm3140-open-settings" class="csm3130-btn secondary" type="button">Base CSM / Configurações</button></div>';
    result.querySelector('#csm3141-retry').onclick=consult;
    result.querySelector('#csm3140-open-settings').onclick=()=>manage.classList.add('show')'''

if old not in s:
    raise SystemExit('Bloco de espera automática 3.14.0 não localizado')
s=s.replace(old,new,1)

# Ajusta texto inicial para deixar claro que SIEG/fontes reais entram antes do DF-e.
old2='''setStatus('Consultando a Base CSM…','');'''
new2='''setStatus('Procurando na Base CSM e nas fontes XML/SIEG…','');'''
if old2 not in s: raise SystemExit('Status inicial 3.14.0 não localizado')
s=s.replace(old2,new2,1)

s=s.rstrip()+"\n// "+MARK+" — sem espera enganosa: Base CSM + SIEG primeiro; DF-e fica em segundo plano.\n"
for tok in (MARK,'XML não localizado agora','Tentar novamente','fontes XML/SIEG disponíveis','Procurando na Base CSM e nas fontes XML/SIEG'):
    if tok not in s: raise SystemExit('Frontend 3.14.1 incompleto: '+tok)
app.write_text(s,encoding='utf-8',newline='\n')
print('3.14.1: UI não fica presa em sincronização e informa corretamente as fontes pesquisadas.')
