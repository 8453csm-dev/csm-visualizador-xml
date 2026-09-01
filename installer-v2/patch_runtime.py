from __future__ import annotations

import sys
from pathlib import Path

MARKER = "CSM_MULTI_TAB_BRIDGE_V1"
BROKER = "http://127.0.0.1:47878"


def patch_index(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if BROKER in text:
        print("index.html já permite o broker local")
        return
    old = "connect-src 'self';"
    new = f"connect-src 'self' {BROKER};"
    if old not in text:
        raise RuntimeError("Diretiva connect-src esperada não encontrada em index.html")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8", newline="\n")
    print("index.html atualizado: CSP permite somente o broker local 127.0.0.1:47878")


def patch_app_js(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"app.js já contém {MARKER}")
        return

    anchor = "function statusClass(s){s=(s||'').toUpperCase();return s.includes('AUTORIZ')||s==='EMITIDA'?'good':s.includes('CANCEL')||s.includes('DENEG')?'bad':'warn'}\n"
    if anchor not in text:
        raise RuntimeError("Âncora statusClass não encontrada em app.js")

    helpers = r'''// CSM_MULTI_TAB_BRIDGE_V1
function companyTabLabel(doc){
 const raw=String(doc?.issuer_name||'').trim();if(!raw)return '';
 const first=(raw.split(/\s+/)[0]||'').replace(/[.,;:]+$/,'');
 const digits=String(doc?.issuer_doc||'').replace(/\D/g,'');let branch='';
 if(digits.length===14){const establishment=digits.slice(8,12);branch=establishment==='0001'?'MATRIZ':'FILIAL'}
 return [first,branch].filter(Boolean).join(' • ')
}
async function acknowledgeExternalDocument(path){
 try{await fetch('http://127.0.0.1:47878/ack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path})})}catch(_){}
}
async function openExternalDocument(path){
 path=String(path||'').trim();if(!path)return;
 try{await waitApi();const result=await window.pywebview.api.open_recent(path);handleLoadResult(result);await acknowledgeExternalDocument(path)}catch(e){toast(`Não foi possível abrir ${path.split(/[\\/]/).pop()||'o XML'}: ${e?.message||e}`,true)}
}
function setupExternalOpenBridge(){
 if(!('EventSource' in window))return;
 let source=null;
 try{
  source=new EventSource('http://127.0.0.1:47878/events');
  source.onmessage=e=>{try{const msg=JSON.parse(e.data||'{}');if(msg.path)void openExternalDocument(msg.path)}catch(err){console.warn('CSM broker: mensagem inválida',err)}};
  source.onerror=()=>{};
  window.addEventListener('beforeunload',()=>{try{source?.close()}catch(_){}},{once:true});
 }catch(e){console.warn('CSM broker indisponível',e)}
}
'''
    text = text.replace(anchor, anchor + helpers, 1)

    old_tab = '''function createDocumentTab(doc){\n if(els.docTabs.querySelector(`.doc-tab[data-id="${doc.document_id}"]`))return;\n const tab=document.createElement('div');tab.className='doc-tab';tab.dataset.id=doc.document_id;tab.innerHTML=`<span class="tab-type">${esc(doc.type_label)}</span><span class="tab-name" title="${esc(doc.title)}">${esc(doc.title)}</span><span class="tab-close">×</span>`;\n tab.onclick=e=>e.target.closest('.tab-close')?closeDocument(doc.document_id):activateDocument(doc.document_id);els.docTabs.appendChild(tab)\n}'''
    new_tab = '''function createDocumentTab(doc){\n if(els.docTabs.querySelector(`.doc-tab[data-id="${doc.document_id}"]`))return;\n const company=companyTabLabel(doc),tab=document.createElement('div');tab.className='doc-tab';tab.dataset.id=doc.document_id;tab.innerHTML=`<span class="tab-type">${esc(doc.type_label)}</span><span class="tab-copy"><span class="tab-name" title="${esc(doc.title)}">${esc(doc.title)}</span>${company?`<span class="tab-company" title="${esc(doc.issuer_name||company)}">${esc(company)}</span>`:''}</span><span class="tab-close">×</span>`;\n tab.onclick=e=>e.target.closest('.tab-close')?closeDocument(doc.document_id):activateDocument(doc.document_id);els.docTabs.appendChild(tab)\n}'''
    if old_tab not in text:
        raise RuntimeError("Função createDocumentTab original não encontrada")
    text = text.replace(old_tab, new_tab, 1)

    startup = "setupDragDrop();setupShortcuts();await waitApi();await loadPreferences();showWelcome();const startup=await window.pywebview.api.consume_startup_documents();handleLoadResult(startup);setTimeout(checkUpdatesOnStartup,1800);"
    replacement = "setupDragDrop();setupShortcuts();await waitApi();await loadPreferences();showWelcome();setupExternalOpenBridge();const startup=await window.pywebview.api.consume_startup_documents();handleLoadResult(startup);setTimeout(checkUpdatesOnStartup,1800);"
    if startup not in text:
        raise RuntimeError("Inicialização principal não encontrada em app.js")
    text = text.replace(startup, replacement, 1)

    path.write_text(text, encoding="utf-8", newline="\n")
    print("app.js atualizado: instância única + abertura externa em abas + etiqueta da empresa")


def patch_css(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"{path.name} já contém {MARKER}")
        return
    block = r'''

/* CSM_MULTI_TAB_BRIDGE_V1 — abas externas, etiqueta da empresa e contraste do tema claro */
.tabs-shell{height:56px}
.tabs-shell .doc-tabs{height:55px}
.workspace{height:calc(100% - 120px)}
body.tools-open .workspace{height:calc(100% - 164px)}
.doc-tab{min-width:192px;max-width:285px;gap:8px;padding-top:4px;padding-bottom:4px}
.doc-tab .tab-copy{display:flex;flex:1;min-width:0;flex-direction:column;justify-content:center;gap:2px;line-height:1.1}
.doc-tab .tab-name{display:block;flex:none;max-width:100%;font-size:11px;font-weight:650;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.doc-tab .tab-company{display:block;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#7f9abd;font-size:8px;font-weight:800;letter-spacing:.42px;text-transform:uppercase}
.doc-tab.active .tab-company{color:#8fbfff}
body.light .doc-tab .tab-company{color:#587794}
body.light .doc-tab.active .tab-company{color:#2f6fae}
body.light .meta-header h2{color:#153b65}
body.light .meta-header .doc-kind{background:#e7f2ff;color:#2c6da9}
body.light .meta-section h3{color:#587697}
body.light .meta-row .label{color:#5b7693}
body.light .meta-row .value{color:#203a57!important}
body.light .meta-total span:first-child{color:#5b7693}
body.light .meta-total strong{color:#163958!important}
body.light .meta-total.grand{color:#163958}
body.light .copy-mini{color:#2f6fae}
'''
    path.write_text(text.rstrip() + block + "\n", encoding="utf-8", newline="\n")
    print(f"{path.name} atualizado: tabs + tema claro")


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: patch_runtime.py <pasta-web>", file=sys.stderr)
        return 2
    web = Path(sys.argv[1])
    index = web / "index.html"
    app = web / "app.js"
    refinement = web / "refinement.css"
    if not index.is_file() or not app.is_file() or not refinement.is_file():
        raise SystemExit(f"Arquivos web não encontrados em {web}")
    patch_index(index)
    patch_app_js(app)
    patch_css(refinement)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
