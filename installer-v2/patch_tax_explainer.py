from __future__ import annotations
import sys
import zlib
from pathlib import Path

BASE = Path(__file__).resolve().parent
CORE = BASE / 'tax_engine_core.js.zlib'
UI = BASE / 'tax_explainer_ui.js.zlib'
STYLE = BASE / 'tax_explainer.css.zlib'


def unpack(path: Path) -> str:
    return zlib.decompress(path.read_bytes()).decode('utf-8')


def append_once(path: Path, payload: str, marker: str) -> None:
    text = path.read_text(encoding='utf-8')
    if marker in text:
        return
    path.write_text(text.rstrip() + '\n' + payload.strip() + '\n', encoding='utf-8', newline='\n')


def extract(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'tax_engine_core.js').write_text(unpack(CORE), encoding='utf-8', newline='\n')
    (dest / 'tax_explainer_ui.js').write_text(unpack(UI), encoding='utf-8', newline='\n')
    (dest / 'tax_explainer.css').write_text(unpack(STYLE), encoding='utf-8', newline='\n')


def patch(web: Path) -> None:
    app = web / 'app.js'
    css = web / 'refinement.css'
    if not app.is_file() or not css.is_file():
        raise SystemExit('app.js/refinement.css não encontrados')
    for p in (CORE, UI, STYLE):
        if not p.is_file():
            raise SystemExit(f'Fonte compactada ausente: {p.name}')

    append_once(app, unpack(CORE), 'CSM_TAX_ENGINE_V1')
    append_once(app, unpack(UI), 'CSM_TAX_EXPLAINER_UI_V1')
    append_once(css, unpack(STYLE), 'CSM_TAX_EXPLAINER_STYLE_V1')

    final = app.read_text(encoding='utf-8')
    for token in (
        'CSM_TAX_ENGINE_V1',
        'CSM_TAX_EXPLAINER_UI_V1',
        'Entender a Tributação',
        'get_xml_text',
        'CSM_DEVOLUTION_ENGINE_V3',
        'CSM_DEVOLUTION_ENTRYPOINT_V4',
        'Criar modelo de devolução',
    ):
        if token not in final:
            raise SystemExit('Componente obrigatório ausente após integração: ' + token)
    print('Entender a Tributação integrado sem alterar o Motor de Devolução.')


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
