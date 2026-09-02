from __future__ import annotations
import sys
from pathlib import Path

MARKER = 'CSM_DEVOLUTION_ENGINE_V1'
BASE = Path(__file__).resolve().parent
SNIPPET = BASE / 'devolution_engine_snippet.js'
STYLE = BASE / 'devolution_engine.css'


def append_once(path: Path, payload: str, label: str) -> None:
    text = path.read_text(encoding='utf-8')
    if MARKER in text:
        print(f'{label} já contém {MARKER}')
        return
    path.write_text(text.rstrip() + '\n' + payload.strip() + '\n', encoding='utf-8', newline='\n')
    print(f'{label} atualizado com Motor Fiscal de Devolução')


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_devolution_engine.py <pasta-web>', file=sys.stderr)
        return 2
    web = Path(sys.argv[1])
    app = web / 'app.js'
    css = web / 'refinement.css'
    if not app.is_file() or not css.is_file():
        raise SystemExit(f'Arquivos web não encontrados em {web}')
    if not SNIPPET.is_file() or not STYLE.is_file():
        raise SystemExit('Arquivos-fonte do Motor de Devolução ausentes')
    append_once(app, SNIPPET.read_text(encoding='utf-8'), 'app.js')
    append_once(css, STYLE.read_text(encoding='utf-8'), 'refinement.css')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
