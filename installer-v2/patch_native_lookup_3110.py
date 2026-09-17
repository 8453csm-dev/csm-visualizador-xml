from pathlib import Path
import sys

MARKER = 'CSM_NATIVE_KEY_LOOKUP_V1'
CSS_MARKER = 'CSM_NATIVE_KEY_LOOKUP_CSS_V1'


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_native_lookup_3110.py <pasta-web>', file=sys.stderr)
        return 2
    web = Path(sys.argv[1])
    app = web / 'app.js'
    css = web / 'refinement.css'
    module_path = Path('installer-v2/native_lookup_module.js')
    if not app.is_file() or not css.is_file() or not module_path.is_file():
        raise SystemExit('Arquivos necessários da consulta nativa não encontrados')

    text = app.read_text(encoding='utf-8')
    module = module_path.read_text(encoding='utf-8').strip()
    if MARKER not in text:
        text = text.rstrip() + '\n\n' + module + '\n'
        app.write_text(text, encoding='utf-8', newline='\n')

    style = css.read_text(encoding='utf-8')
    if CSS_MARKER not in style:
        style += '''\n\n/* CSM_NATIVE_KEY_LOOKUP_CSS_V1 — integração do botão com barras existentes */\n[data-csm-native-lookup="1"]{white-space:nowrap}\n[data-csm-native-lookup="1"]:focus-visible{outline:2px solid rgba(67,160,255,.75);outline-offset:2px}\n'''
        css.write_text(style, encoding='utf-8', newline='\n')

    final = app.read_text(encoding='utf-8')
    for token in (MARKER, 'Consultar NF-e pela chave', 'CSMNativeKeyLookup', 'Ctrl+L', 'dispatchLookup', 'calcDv'):
        if token not in final:
            raise SystemExit('Consulta nativa incompleta: ' + token)
    print('Consulta NF-e nativa por chave aplicada ao frontend 3.11.0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
