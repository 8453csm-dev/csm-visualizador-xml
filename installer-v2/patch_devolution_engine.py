from __future__ import annotations
import sys
from pathlib import Path

MARKER_V1 = 'CSM_DEVOLUTION_ENGINE_V1'
MARKER_V2 = 'CSM_DEVOLUTION_ENGINE_V2'
BASE = Path(__file__).resolve().parent
SNIPPET_V1 = BASE / 'devolution_engine_snippet.js'
STYLE_V1 = BASE / 'devolution_engine.css'
SNIPPET_V2 = BASE / 'devolution_engine_v2_patch.js'
STYLE_V2 = BASE / 'devolution_engine_v2.css'


def append_marker(path: Path, payload: str, marker: str, label: str) -> None:
    text = path.read_text(encoding='utf-8')
    if marker in text:
        print(f'{label} já contém {marker}')
        return
    path.write_text(text.rstrip() + '\n' + payload.strip() + '\n', encoding='utf-8', newline='\n')
    print(f'{label} atualizado com {marker}')


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_devolution_engine.py <pasta-web>', file=sys.stderr)
        return 2
    web = Path(sys.argv[1])
    app = web / 'app.js'
    css = web / 'refinement.css'
    if not app.is_file() or not css.is_file():
        raise SystemExit(f'Arquivos web não encontrados em {web}')
    required = [SNIPPET_V1, STYLE_V1, SNIPPET_V2, STYLE_V2]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise SystemExit('Arquivos-fonte do Motor de Devolução ausentes: ' + ', '.join(missing))
    append_marker(app, SNIPPET_V1.read_text(encoding='utf-8'), MARKER_V1, 'app.js')
    append_marker(css, STYLE_V1.read_text(encoding='utf-8'), MARKER_V1, 'refinement.css')
    append_marker(app, SNIPPET_V2.read_text(encoding='utf-8'), MARKER_V2, 'app.js')
    append_marker(css, STYLE_V2.read_text(encoding='utf-8'), MARKER_V2, 'refinement.css')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
