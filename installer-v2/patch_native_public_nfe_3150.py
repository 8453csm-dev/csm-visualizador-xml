from pathlib import Path
import sys

MARK='CSM_PUBLIC_NFE_UI_3150'
if len(sys.argv)!=2: raise SystemExit('uso: patch_native_public_nfe_3150.py <pasta-web>')
app=Path(sys.argv[1])/'app.js'
if not app.is_file(): raise SystemExit('app.js não encontrado')
s=app.read_text(encoding='utf-8')
if MARK in s:
    print('UI pública 3.15.0 já aplicada')
    raise SystemExit(0)
if 'CSM_SOURCE_AWARE_UI_3141' not in s:
    raise SystemExit('Aplique a UI 3.14.1 antes')

s=s.replace(
'''<div class="csm3130-title">Consultar NF-e</div><div class="csm3130-sub">Cole a chave de acesso. A Base CSM localiza o XML e abre a nota diretamente no Visualizador.</div>''',
'''<div class="csm3130-title">Consultar NF-e</div><div class="csm3130-sub">Cole a chave de acesso. O CSM consulta a página pública oficial da NF-e e abre a visualização dentro do software.</div>''',
1)

old_controls='''<select id="csm3130-cert" class="csm3130-select" style="display:none"><option value="">Automático</option></select><div class="csm3130-actions" style="margin-top:9px"><button id="csm3130-manage-toggle" class="csm3130-btn ghost" type="button">Base CSM / Configurações</button></div><div class="csm3130-hint">A consulta principal usa somente a chave. Certificados e fontes XML trabalham em segundo plano para alimentar a Base CSM.</div>'''
new_controls='''<select id="csm3130-cert" class="csm3130-select" style="display:none"><option value="">Automático</option></select><div class="csm3130-hint">Consulta pública apenas para visualização. Não precisa de XML, certificado digital ou Base CSM. Se a Receita solicitar hCaptcha, faça a validação na janela oficial que abrir.</div>'''
if old_controls not in s: raise SystemExit('Controles Base CSM 3.14.0 não localizados')
s=s.replace(old_controls,new_controls,1)

# Esconde o painel avançado legado deste modal. Ele continua no código para outros recursos, mas não faz parte da consulta pública.
s=s.replace('''<div id="csm3130-manage" class="csm3130-manage">''','''<div id="csm3130-manage" class="csm3130-manage" style="display:none!important">''',1)

start=s.find(' async function consult(){')
end=s.find('\n go.onclick=consult;',start)
if start<0 or end<0: raise SystemExit('consult() 3.14.1 não localizada')

new_consult=r''' async function consult(){
  const k=keyOf(key.value);if(!k){setStatus('A chave precisa ter 44 dígitos e DV válido.','err');return}
  go.disabled=true;result.className='csm3130-result';
  setStatus('Abrindo a consulta pública oficial da NF-e…','');
  let timeout=null;
  const onOpened=e=>{
    const path=String(e?.detail?.path||'');
    if(!/\.pdf$/i.test(path))return;
    clearTimeout(timeout);window.removeEventListener('csm:external-document-opened',onOpened);
    setStatus('NF-e localizada. A consulta foi aberta no Visualizador.','ok');
    saveHistory(k);
    setTimeout(close,450)
  };
  window.addEventListener('csm:external-document-opened',onOpened);
  try{
    await waitApi();
    const resp=await fetch('http://127.0.0.1:47878/lookup-automation',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({provider:'sefazpublica',key:k,format:'visual'})
    });
    if(!resp.ok){let d='';try{d=await resp.text()}catch(_){}
      throw new Error(d||'Não foi possível iniciar a consulta pública da NF-e.')}
    const data=await resp.json().catch(()=>({started:true}));
    if(data?.started===false)throw new Error('O módulo de consulta pública não foi iniciado.');
    setStatus('Consulta oficial aberta. Se a Receita pedir hCaptcha, valide na janela que apareceu; depois o CSM continua sozinho.','');
    timeout=setTimeout(()=>{
      window.removeEventListener('csm:external-document-opened',onOpened);
      if(document.body.contains(result)){
        setStatus('A consulta continua aguardando a validação ou a resposta da Receita.','');
        go.disabled=false
      }
    },10*60*1000);
  }catch(e){
    clearTimeout(timeout);window.removeEventListener('csm:external-document-opened',onOpened);
    setStatus(e?.message||String(e),'err');go.disabled=false
  }
 }'''
s=s[:start]+new_consult+s[end:]

# O antigo botão de configurações pode continuar referenciado por código auxiliar; proteja contra null.
s=s.replace(
''' q('csm3130-manage-toggle').onclick=()=>{manage.classList.toggle('show');if(manage.classList.contains('show'))loadRepoStatus()};''',
''' const legacyManageToggle=q('csm3130-manage-toggle');if(legacyManageToggle)legacyManageToggle.onclick=()=>{manage.classList.toggle('show');if(manage.classList.contains('show'))loadRepoStatus()};''',
1)

s=s.rstrip()+"\n// "+MARK+" — consulta principal somente visual: chave -> portal público oficial -> PDF fiscal no Visualizador.\n"
for tok in (MARK,"provider:'sefazpublica'","Consulta pública apenas para visualização","hCaptcha","csm:external-document-opened"):
    if tok not in s: raise SystemExit('Frontend público 3.15.0 incompleto: '+tok)
block=s[s.find(' async function consult(){'):s.find('\n go.onclick=consult;',s.find(' async function consult(){'))]
for forbidden in ('/api/nfe/by-key','waitRepository(','findLocalXML(','repository'):
    if forbidden in block: raise SystemExit('Consulta pública ainda depende da Base CSM: '+forbidden)
app.write_text(s,encoding='utf-8',newline='\n')
print('3.15.0: consulta principal agora é somente visual via portal público oficial da NF-e.')
