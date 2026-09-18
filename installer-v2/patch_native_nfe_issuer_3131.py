from pathlib import Path
import sys

MARK='CSM_ISSUER_LOCAL_UI_3131'
if len(sys.argv)!=2:
    raise SystemExit('uso: patch_native_nfe_issuer_3131.py <pasta-web>')
app=Path(sys.argv[1])/'app.js'
if not app.is_file(): raise SystemExit('app.js não encontrado')
s=app.read_text(encoding='utf-8')
if MARK in s:
    print('Frontend NF-e própria 3.13.1 já aplicado')
    raise SystemExit(0)
if 'CSM_NATIVE_NFE_WORKFLOW_3130' not in s:
    raise SystemExit('Aplique o frontend 3.13.0 antes')

anchor='''function actionsFor(data,k){'''
if anchor not in s: raise SystemExit('actionsFor 3.13.0 não localizado')
helper=r'''
async function findLocalXML(k,quiet=false){
 try{
   if(!quiet)setStatus('Procurando o XML original nas pastas configuradas…','');
   const r=await request('/fiscal/nfe/find-local',{key:k});
   if(r?.xml_available){
     setStatus('XML original localizado. Abrindo a NF-e no Visualizador…','ok');
     setTimeout(close,280);
     return true
   }
   if(!quiet)setStatus(r?.message||'XML não localizado nas pastas configuradas.','err');
   return false
 }catch(e){
   if(!quiet)setStatus(e.message,'err');
   return false
 }
}
async function pickLocalXML(k){
 try{
   const r=await request('/fiscal/nfe/pick-local',{key:k});
   if(r?.cancelled)return false;
   if(r?.xml_available){
     setStatus('XML validado e aberto no Visualizador. A pasta também foi adicionada às fontes locais.','ok');
     setTimeout(close,280);
     return true
   }
   setStatus(r?.message||'Não foi possível abrir o XML selecionado.','err')
 }catch(e){setStatus(e.message,'err')}
 return false
}
async function showXMLFolders(k){
 let box=q('csm3131-xml-folders');
 if(!box){
   box=document.createElement('div');box.id='csm3131-xml-folders';box.className='csm3130-manage show';
   box.innerHTML='<strong>Pastas de XML / SIEG</strong><div class="csm3130-hint">Cadastre uma pasta que contenha os XMLs originais. O CSM procura a chave dentro dos XMLs e abre somente o documento correspondente.</div><div class="csm3130-row" style="margin-top:10px"><input id="csm3131-xml-path" class="csm3130-input" placeholder="Ex.: U:\\SIEG ou pasta da empresa"><button id="csm3131-xml-add" class="csm3130-btn secondary" type="button">Adicionar pasta</button></div><div id="csm3131-xml-list" class="csm3130-hint" style="margin-top:9px"></div><div class="csm3130-actions"><button id="csm3131-xml-find" class="csm3130-btn secondary" type="button">Procurar agora</button><button id="csm3131-xml-pick" class="csm3130-btn ghost" type="button">Selecionar XML</button></div>';
   result.insertAdjacentElement('afterend',box);
   box.querySelector('#csm3131-xml-add').onclick=async()=>{const path=String(box.querySelector('#csm3131-xml-path').value||'').trim();if(!path){setStatus('Informe a pasta onde estão os XMLs.','err');return}try{await request('/fiscal/xml-folders/add',{path});box.querySelector('#csm3131-xml-path').value='';await loadXMLFolderList();setStatus('Pasta de XML adicionada. Procurando a chave…','ok');await findLocalXML(k)}catch(e){setStatus(e.message,'err')}};
   box.querySelector('#csm3131-xml-find').onclick=()=>findLocalXML(k);
   box.querySelector('#csm3131-xml-pick').onclick=()=>pickLocalXML(k);
 }
 box.classList.add('show');
 async function loadXMLFolderList(){try{const r=await request('/fiscal/xml-folders',undefined,'GET');const a=Array.isArray(r?.folders)?r.folders:[];box.querySelector('#csm3131-xml-list').textContent=a.length?'Fontes: '+a.join(' • '):'Nenhuma pasta de XML cadastrada.'}catch(e){box.querySelector('#csm3131-xml-list').textContent=e.message}}
 await loadXMLFolderList()
}
'''
s=s.replace(anchor,helper+anchor,1)

old='''}else if(data?.requires_manifestation){const m=document.createElement('button');m.className='csm3130-btn warn';m.textContent='Obter XML completo';m.onclick=()=>manifest(k,data);a.appendChild(m)}}'''
new='''}else if(data?.issuer_document||data?.distribution_restricted){const f=document.createElement('button');f.className='csm3130-btn';f.textContent='Procurar XML';f.onclick=()=>findLocalXML(k);a.appendChild(f);const p=document.createElement('button');p.className='csm3130-btn secondary';p.textContent='Selecionar XML';p.onclick=()=>pickLocalXML(k);a.appendChild(p);const g=document.createElement('button');g.className='csm3130-btn ghost';g.textContent='Pastas XML / SIEG';g.onclick=()=>showXMLFolders(k);a.appendChild(g)}else if(data?.requires_manifestation){const m=document.createElement('button');m.className='csm3130-btn warn';m.textContent='Obter XML completo';m.onclick=()=>manifest(k,data);a.appendChild(m)}}'''
if old not in s: raise SystemExit('Ramo de ações 3.13.0 não localizado')
s=s.replace(old,new,1)

old='''if(data.xml_available)setStatus(`NF-e ${st}. XML oficial disponível no CSM.`,'ok');else if(data.requires_manifestation)setStatus(`NF-e ${st}. A Receita retornou apenas o resumo. Você pode registrar Ciência para solicitar o XML completo.`,'');else setStatus(`NF-e ${st}: ${data.message||'consulta concluída.'}`,st==='CANCELADA'||st==='DENEGADA'?'err':'ok');actionsFor(data,k)'''
new='''if(data.xml_available){setStatus(`NF-e ${st}. XML disponível. Abrindo no Visualizador…`,'ok');actionsFor(data,k);setTimeout(close,320);return}else if(data.issuer_document){setStatus(`NF-e ${st}. Esta NF-e foi emitida pela própria empresa. Procurando o XML original nas pastas configuradas…`,'');const found=await findLocalXML(k,true);if(found)return;setStatus(`NF-e ${st}. A Receita confirma a autorização, mas não redistribui o XML ao próprio emitente pela consulta por chave. Cadastre a pasta dos XMLs/SIEG ou selecione o XML original.`,'');actionsFor(data,k);return}else if(data.requires_manifestation)setStatus(`NF-e ${st}. A Receita retornou apenas o resumo. Você pode registrar Ciência para solicitar o XML completo.`,'');else if(data.distribution_message)setStatus(`NF-e ${st}: ${data.distribution_message}`,st==='CANCELADA'||st==='DENEGADA'?'err':'');else setStatus(`NF-e ${st}: ${data.message||'consulta concluída.'}`,st==='CANCELADA'||st==='DENEGADA'?'err':'ok');actionsFor(data,k)'''
if old not in s: raise SystemExit('Fluxo consult() 3.13.0 não localizado')
s=s.replace(old,new,1)

s=s.rstrip()+"\n// "+MARK+" — emitente: procura XML em fontes locais/SIEG; XML recebido abre e fecha o modal automaticamente.\n"
for tok in (MARK,'Procurar XML','Selecionar XML','Pastas XML / SIEG','/fiscal/nfe/find-local','/fiscal/nfe/pick-local','/fiscal/xml-folders/add','setTimeout(close,320)'):
    if tok not in s: raise SystemExit('Frontend 3.13.1 incompleto: '+tok)
app.write_text(s,encoding='utf-8',newline='\n')
print('3.13.1: UI trata NF-e própria, fontes XML/SIEG e abertura automática no Visualizador.')
