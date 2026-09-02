from __future__ import annotations
import sys
from pathlib import Path

MARKER_V1 = 'CSM_DEVOLUTION_ENGINE_V1'
MARKER_V2 = 'CSM_DEVOLUTION_ENGINE_V2'
MARKER_V3 = 'CSM_DEVOLUTION_ENGINE_V3'
MARKER_V4 = 'CSM_DEVOLUTION_ENTRYPOINT_V4'
BASE = Path(__file__).resolve().parent
SNIPPET_V1 = BASE / 'devolution_engine_snippet.js'
STYLE_V1 = BASE / 'devolution_engine.css'
SNIPPET_V2 = BASE / 'devolution_engine_v2_patch.js'
STYLE_V2 = BASE / 'devolution_engine_v2.css'
SNIPPET_V3 = BASE / 'devolution_engine_v3_patch.js'
STYLE_V3 = BASE / 'devolution_engine_v3.css'
SNIPPET_V4 = BASE / 'devolution_entrypoint_v4_patch.js'

# Funcoes que ja existem na V1. Em app.js carregado como ES module, declarar
# novamente o mesmo identificador pode impedir o modulo inteiro de carregar.
V2_OVERRIDES = (
    'csmDevLoadDraft',
    'csmDevGeneralFields',
    'csmDevLineCard',
    'csmDevRender',
    'csmDevBind',
    'csmDevGuideHtml',
    'csmDevDownloadGuide',
    'csmDevPrintGuide',
    'csmDevOpen',
)


def append_marker(path: Path, payload: str, marker: str, label: str) -> None:
    text = path.read_text(encoding='utf-8')
    if marker in text:
        print(f'{label} já contém {marker}')
        return
    path.write_text(text.rstrip() + '\n' + payload.strip() + '\n', encoding='utf-8', newline='\n')
    print(f'{label} atualizado com {marker}')


def sanitize_v2(payload: str) -> str:
    broken = "replace(/\\\n/g,'<br>')"
    fixed = "replace(/\\n/g,'<br>')"
    payload = payload.replace(broken, fixed)
    for name in V2_OVERRIDES:
        declaration = f'function {name}('
        assignment = f'{name}=function('
        if declaration not in payload:
            raise SystemExit(f'Override esperado ausente na Beta 2: {name}')
        payload = payload.replace(declaration, assignment, 1)
    for name in V2_OVERRIDES:
        if f'function {name}(' in payload:
            raise SystemExit(f'Redeclaracao ES module ainda presente: {name}')
    if "replace(/\\\n/g,'<br>')" in payload:
        raise SystemExit('Regex inválido da Beta 2 ainda presente após saneamento')
    return payload


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_devolution_engine.py <pasta-web>', file=sys.stderr)
        return 2
    web = Path(sys.argv[1])
    app = web / 'app.js'
    css = web / 'refinement.css'
    if not app.is_file() or not css.is_file():
        raise SystemExit(f'Arquivos web não encontrados em {web}')
    required = [SNIPPET_V1, STYLE_V1, SNIPPET_V2, STYLE_V2, SNIPPET_V3, STYLE_V3, SNIPPET_V4]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise SystemExit('Arquivos-fonte do Motor de Devolução ausentes: ' + ', '.join(missing))

    append_marker(app, SNIPPET_V1.read_text(encoding='utf-8'), MARKER_V1, 'app.js')
    append_marker(css, STYLE_V1.read_text(encoding='utf-8'), MARKER_V1, 'refinement.css')
    append_marker(app, sanitize_v2(SNIPPET_V2.read_text(encoding='utf-8')), MARKER_V2, 'app.js')
    append_marker(css, STYLE_V2.read_text(encoding='utf-8'), MARKER_V2, 'refinement.css')
    append_marker(app, SNIPPET_V3.read_text(encoding='utf-8'), MARKER_V3, 'app.js')
    append_marker(css, STYLE_V3.read_text(encoding='utf-8'), MARKER_V3, 'refinement.css')
    append_marker(app, SNIPPET_V4.read_text(encoding='utf-8'), MARKER_V4, 'app.js')

    final = app.read_text(encoding='utf-8')
    if any(marker not in final for marker in (MARKER_V1, MARKER_V2, MARKER_V3, MARKER_V4)):
        raise SystemExit('Motor Fiscal incompleto no app.js final')
    if 'entrypointVersion=CSM_DEV_ENTRYPOINT_VERSION' not in final:
        raise SystemExit('Entrada determinística do Motor Fiscal não foi integrada')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
