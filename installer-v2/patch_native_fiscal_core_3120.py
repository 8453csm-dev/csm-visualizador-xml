from pathlib import Path
import sys

MARKER='CSM_NATIVE_FISCAL_CORE_3120'
if len(sys.argv)!=2:
    raise SystemExit('uso: patch_native_fiscal_core_3120.py <pasta-web>')
app=Path(sys.argv[1])/'app.js'
s=app.read_text(encoding='utf-8')
if MARKER in s:
    print('Frontend Fiscal Core 3.12.0 já aplicado')
    raise SystemExit(0)

# 1) Troca definitivamente o provedor web pelo broker fiscal nativo.
start=s.find('async function dispatchLookup(key,setStatus){')
end=s.find('\nfunction style(){',start)
if start<0 or end<0:
    raise SystemExit('dispatchLookup não encontrado')
new_dispatch=r'''// CSM_NATIVE_FISCAL_CORE_3120 — Web Services oficiais, sem navegador
async function dispatchLookup(key,setStatus){
  const cert=document.getElementById('csm-nlk-cert');
  const cnpj=String(cert?.value||'').trim();
  if(!cnpj)throw new Error('Selecione a empresa/certificado que fará a consulta.');
  setStatus('Consultando Web Services oficiais da NF-e…','work');
  const resp=await fetch('http://127.0.0.1:47878/fiscal/nfe/consultar',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({key,cnpj})
  });
  let data={};
  try{data=await resp.json()}catch(_){throw new Error('O CSM Fiscal Core retornou uma resposta inválida.')}
  if(!resp.ok)throw new Error(data?.message||`Falha local HTTP ${resp.status}.`);
  if(!data?.ok&&data?.needs_certificate)throw new Error(data?.message||'Selecione um certificado válido.');
  if(!data?.ok)throw new Error(data?.message||'A consulta oficial não pôde ser concluída.');
  saveHistory(key);
  return data;
}
'''
s=s[:start]+new_dispatch+s[end:]

# 2) Campo Empresa/Certificado dentro do modal nativo.
needle='<div class="csm-nlk-hint">Aceita chave com espaços, pontos, traços ou copiada junto com outro texto.</div>'
if needle not in s:
    raise SystemExit('Hint do modal não encontrado')
cert_markup='''<div class="csm-nlk-hint">Aceita chave com espaços, pontos, traços ou copiada junto com outro texto.</div><label class="csm-nlk-label" style="margin-top:15px">Empresa / certificado A1</label><select id="csm-nlk-cert" class="csm-nlk-input" style="width:100%;height:43px"><option value="">Carregando certificados CSM…</option></select><div id="csm-nlk-cert-hint" class="csm-nlk-hint">A consulta usa o certificado da empresa diretamente nos Web Services oficiais.</div>'''
s=s.replace(needle,cert_markup,1)

old_const="const input=o.querySelector('.csm-nlk-input'),go=o.querySelector('.csm-nlk-go'),preview=o.querySelector('.csm-nlk-preview'),status=o.querySelector('.csm-nlk-status'),hist=o.querySelector('.csm-nlk-history');"
new_const="const input=o.querySelector('.csm-nlk-input'),go=o.querySelector('.csm-nlk-go'),preview=o.querySelector('.csm-nlk-preview'),status=o.querySelector('.csm-nlk-status'),hist=o.querySelector('.csm-nlk-history'),certSelect=o.querySelector('#csm-nlk-cert'),certHint=o.querySelector('#csm-nlk-cert-hint');"
if old_const not in s:
    raise SystemExit('Constantes do modal não encontradas')
s=s.replace(old_const,new_const,1)

status_line="const setStatus=(msg,kind='')=>{status.textContent=msg;status.className='csm-nlk-status '+(kind==='err'?'err':kind==='ok'?'ok':'')};"
if status_line not in s:
    raise SystemExit('setStatus não encontrado')
loader=r'''const setStatus=(msg,kind='')=>{status.textContent=msg;status.className='csm-nlk-status '+(kind==='err'?'err':kind==='ok'?'ok':'')};
  const loadCertificates=async()=>{
    certSelect.disabled=true;certSelect.innerHTML='<option value="">Carregando certificados CSM…</option>';
    try{
      const resp=await fetch('http://127.0.0.1:47878/fiscal/certificates');
      const data=await resp.json();
      const list=Array.isArray(data?.certificates)?data.certificates.filter(x=>x&&x.available!==false):[];
      certSelect.innerHTML='';
      if(!list.length){
        certSelect.innerHTML='<option value="">Nenhum certificado A1 integrado</option>';
        certHint.textContent='Abra o CSM Certificados Digitais e atualize a integração antes de consultar.';
        certSelect.disabled=true;return;
      }
      if(list.length>1){const ph=document.createElement('option');ph.value='';ph.textContent='Selecione a empresa…';certSelect.appendChild(ph)}
      for(const c of list){
        const op=document.createElement('option');op.value=String(c.cnpj||'');
        const name=String(c.empresa||c.cnpj||'Empresa');const exp=String(c.expiry||'').trim();
        op.textContent=name+(exp?` • vence ${exp}`:'');certSelect.appendChild(op);
      }
      const current=normalizeKey(input.value);const issuer=current?current.slice(6,20):'';
      if(issuer&&[...certSelect.options].some(x=>x.value===issuer))certSelect.value=issuer;
      else if(list.length===1)certSelect.value=String(list[0].cnpj||'');
      certSelect.disabled=false;
      certHint.textContent='Consulta direta SEFAZ/Receita. Nenhum navegador ou site externo será aberto.';
    }catch(e){
      certSelect.innerHTML='<option value="">Integração de certificados indisponível</option>';certSelect.disabled=true;
      certHint.textContent='Não foi possível conversar com o CSM Fiscal Core.';
    }
  };'''
s=s.replace(status_line,loader,1)

# 3) Resultado oficial permanece no modal quando só houver status/resumo; fecha
# somente quando o XML completo realmente chegou ao Visualizador.
start_go=s.find('go.onclick=async()=>{',s.find("const onResult=e=>"))
end_go=s.find('\n  renderHistory(hist,input,preview);',start_go)
if start_go<0 or end_go<0:
    raise SystemExit('Handler Consultar 3.11.5 não encontrado')
new_go=r'''go.onclick=async()=>{
    const key=refresh();
    if(!key){setStatus('A chave precisa ter 44 dígitos e um dígito verificador válido.','err');return}
    if(!String(certSelect?.value||'').trim()){setStatus('Selecione a empresa/certificado A1 que fará a consulta.','err');return}
    go.disabled=true;certSelect.disabled=true;window.addEventListener('csm:external-document-opened',onResult);
    try{
      const result=await dispatchLookup(key,setStatus);const st=String(result?.status||'ENCONTRADA').toUpperCase();renderHistory(hist,input,preview);
      if(result?.xml_available&&result?.xml_path){
        setStatus(`NF-e ${st}. XML oficial localizado e validado; abrindo no CSM…`,'ok');
        resultTimer=setTimeout(()=>{if(o.isConnected)setStatus(`NF-e ${st}. XML recebido; aguardando a abertura da aba…`,'work')},12000);
      }else{
        cleanup();go.disabled=false;certSelect.disabled=false;
        const msg=String(result?.message||result?.distribution_message||'Consulta concluída.');
        if(result?.requires_manifestation){setStatus(`NF-e ${st}. Documento localizado, mas o XML completo ainda não está liberado para esta empresa. A Receita retornou apenas o resumo; será necessária manifestação do destinatário para obter o XML completo.`,'work')}
        else if(st==='CANCELADA'||st==='DENEGADA'||st==='NÃO LOCALIZADA'){setStatus(`NF-e ${st}: ${msg}`,'err')}
        else setStatus(`NF-e ${st}: ${msg}`,'ok');
      }
    }catch(e){cleanup();go.disabled=false;certSelect.disabled=false;setStatus(e?.message||String(e),'err')}
  };'''
s=s[:start_go]+new_go+s[end_go:]

# Carrega certificados quando o modal abre.
needle2="renderHistory(hist,input,preview);input.value=prefill||'';refresh();setTimeout(()=>{input.focus();input.select()},30);"
replace2="renderHistory(hist,input,preview);input.value=prefill||'';refresh();loadCertificates();setTimeout(()=>{input.focus();input.select()},30);"
if needle2 not in s:
    raise SystemExit('Inicialização do modal não encontrada')
s=s.replace(needle2,replace2,1)

# Ao colar uma chave, se houver certificado do próprio emitente disponível,
# seleciona-o automaticamente sem sobrescrever uma escolha manual válida.
needle3="input.addEventListener('input',refresh);"
replace3="input.addEventListener('input',()=>{const key=refresh();if(key&&certSelect&&!certSelect.value){const issuer=key.slice(6,20);if([...certSelect.options].some(x=>x.value===issuer))certSelect.value=issuer}});"
if needle3 not in s:
    raise SystemExit('Listener do input não encontrado')
s=s.replace(needle3,replace3,1)

s=s.replace("version:'3.11.5'","version:'3.12.0'",1)
s=s.rstrip()+"\n// "+MARKER+" — NFeConsultaProtocolo + NFeDistribuicaoDFe oficiais; zero navegador no fluxo principal.\n"

final=s[s.find(MARKER)-12000:]
for token in (MARKER,'/fiscal/certificates','/fiscal/nfe/consultar','Empresa / certificado A1','Consulta direta SEFAZ/Receita','requires_manifestation'):
    if token not in s:raise SystemExit('Frontend Fiscal Core incompleto: '+token)
# O dispatch atual não pode voltar ao site antigo.
dispatch=s[s.find('async function dispatchLookup'):s.find('\nfunction style(){',s.find('async function dispatchLookup'))]
for forbidden in ('/lookup-automation','open_lookup_site(','consultadanfe'):
    if forbidden in dispatch:raise SystemExit('Fluxo 3.12.0 ainda depende do site: '+forbidden)
app.write_text(s,encoding='utf-8',newline='\n')
print('3.12.0: Consulta NF-e usa CSM Fiscal Core + certificados A1 + Web Services oficiais, sem navegador.')
