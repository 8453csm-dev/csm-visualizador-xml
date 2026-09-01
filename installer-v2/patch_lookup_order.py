from pathlib import Path

MARKER = "CSM_LOCATOR_HELPER_AFTER_WINDOW_V2"
path = Path("installer-v2/payload/_internal/web/app.js")
text = path.read_text(encoding="utf-8")

if MARKER in text:
    print("Ordem do helper do Localizador ja corrigida")
    raise SystemExit(0)

old = "if(provider==='consultadanfe'){try{await fetch('http://127.0.0.1:47878/lookup-automation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({provider,key,format:desired})})}catch(_){}}const r=await window.pywebview.api.open_lookup_site(provider,key,desired);if(!r?.ok){toast(r?.error||'Não foi possível abrir a consulta.',true);return}"
new = "const r=await window.pywebview.api.open_lookup_site(provider,key,desired);if(!r?.ok){toast(r?.error||'Não foi possível abrir a consulta.',true);return}if(provider==='consultadanfe'){try{await fetch('http://127.0.0.1:47878/lookup-automation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({provider,key,format:desired})})}catch(_){}}/* CSM_LOCATOR_HELPER_AFTER_WINDOW_V2 */"

if old not in text:
    raise RuntimeError("Fluxo antigo de inicializacao do helper nao encontrado")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8", newline="\n")
print("Localizador atualizado: helper inicia somente depois que a janela Consulta DANFE existe")
