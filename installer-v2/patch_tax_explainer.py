from __future__ import annotations
import sys
import zlib
from pathlib import Path

BASE = Path(__file__).resolve().parent
CORE = BASE / 'tax_engine_core.js.zlib'
UI = BASE / 'tax_explainer_ui.js.zlib'
STYLE = BASE / 'tax_explainer.css.zlib'
FIX_MARKER = 'CSM_TAX_EXPLAINER_NO_FREEZE_391'


def unpack(path: Path) -> str:
    return zlib.decompress(path.read_bytes()).decode('utf-8')


def sanitize_ui(payload: str) -> str:
    # 3.9.0 podia entrar em ciclo infinito:
    # render -> innerHTML -> MutationObserver -> ensureUi -> render -> ...
    # O observer deve somente garantir que a UI exista. Renderizar a análise
    # é responsabilidade do clique/troca de documento, nunca de uma mutação DOM.
    old_render = "if(eligible&&activeView==='taxexplain')csmTaxRenderCurrent();return true}"
    if old_render not in payload:
        raise SystemExit('Ponto de renderização recursiva não encontrado na UI tributária')
    payload = payload.replace(old_render, 'return true}', 1)

    old_observer = "const csmTaxObsRoot=document.body||document.documentElement;if(csmTaxObsRoot)new MutationObserver(csmTaxQueueSync).observe(csmTaxObsRoot,{childList:true,subtree:true});"
    new_observer = (
        "const csmTaxObsRoot=document.body||document.documentElement;let csmTaxMountObserver=null;"
        "if(csmTaxObsRoot&&!document.querySelector('[data-view=\"taxexplain\"]')){"
        "csmTaxMountObserver=new MutationObserver(()=>{csmTaxQueueSync();"
        "if(document.querySelector('[data-view=\"taxexplain\"]')&&document.getElementById('taxexplainView')){"
        "csmTaxMountObserver.disconnect();csmTaxMountObserver=null}});"
        "csmTaxMountObserver.observe(csmTaxObsRoot,{childList:true,subtree:true})}"
    )
    if old_observer not in payload:
        raise SystemExit('Observer global antigo não encontrado na UI tributária')
    payload = payload.replace(old_observer, new_observer, 1)
    payload = payload.replace("const CSM_TAX_UI_VERSION='1.0.0';", "const CSM_TAX_UI_VERSION='1.0.1';", 1)
    payload = payload.rstrip() + f"\n// {FIX_MARKER}: observer somente para montagem; renderização nunca nasce de mutação DOM.\n"

    if old_render in payload:
        raise SystemExit('Renderização recursiva ainda presente após correção')
    if old_observer in payload:
        raise SystemExit('Observer global antigo ainda presente após correção')
    if FIX_MARKER not in payload:
        raise SystemExit('Marcador anti-congelamento ausente')
    return payload


def append_once(path: Path, payload: str, marker: str) -> None:
    text = path.read_text(encoding='utf-8')
    if marker in text:
        return
    path.write_text(text.rstrip() + '\n' + payload.strip() + '\n', encoding='utf-8', newline='\n')


def materialized_sources() -> tuple[str, str, str]:
    return unpack(CORE), sanitize_ui(unpack(UI)), unpack(STYLE)


def extract(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    core, ui, style = materialized_sources()
    (dest / 'tax_engine_core.js').write_text(core, encoding='utf-8', newline='\n')
    (dest / 'tax_explainer_ui.js').write_text(ui, encoding='utf-8', newline='\n')
    (dest / 'tax_explainer.css').write_text(style, encoding='utf-8', newline='\n')


def patch(web: Path) -> None:
    app = web / 'app.js'
    css = web / 'refinement.css'
    if not app.is_file() or not css.is_file():
        raise SystemExit('app.js/refinement.css não encontrados')
    for p in (CORE, UI, STYLE):
        if not p.is_file():
            raise SystemExit(f'Fonte compactada ausente: {p.name}')

    core, ui, style = materialized_sources()
    append_once(app, core, 'CSM_TAX_ENGINE_V1')
    append_once(app, ui, 'CSM_TAX_EXPLAINER_UI_V1')
    append_once(css, style, 'CSM_TAX_EXPLAINER_STYLE_V1')

    final = app.read_text(encoding='utf-8')
    for token in (
        'CSM_TAX_ENGINE_V1',
        'CSM_TAX_EXPLAINER_UI_V1',
        FIX_MARKER,
        'Entender a Tributação',
        'get_xml_text',
        'CSM_DEVOLUTION_ENGINE_V3',
        'CSM_DEVOLUTION_ENTRYPOINT_V4',
        'Criar modelo de devolução',
    ):
        if token not in final:
            raise SystemExit('Componente obrigatório ausente após integração: ' + token)
    if "if(eligible&&activeView==='taxexplain')csmTaxRenderCurrent();return true}" in final:
        raise SystemExit('Build ainda contém ciclo de renderização da 3.9.0')
    print('Entender a Tributação 1.0.1 integrado sem loop de renderização e sem alterar a Devolução.')


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == '--extract':
        extract(Path(sys.argv[2]))
        return 0
    if len(sys.argv) != 2:
        print('uso: patch_tax_explainer.py <pasta-web> | --extract <dest>', file=sys.stderr)
        return 2
    patch(Path(sys.argv[1]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
