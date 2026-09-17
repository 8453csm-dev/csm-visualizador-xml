from pathlib import Path
import shutil
import sys

MARKER='CSM_NATIVE_NFE_LOOKUP_UI_V1'


def main():
    if len(sys.argv)!=2:
        raise SystemExit('uso: patch_native_nfe_lookup_web.py <pasta-web>')
    web=Path(sys.argv[1])
    index=web/'index.html'
    refinement=web/'refinement.css'
    if not index.is_file() or not refinement.is_file():
        raise SystemExit(f'Payload web incompleto em {web}')

    source_js=Path('installer-v2/native_nfe_lookup.js')
    source_css=Path('installer-v2/native_nfe_lookup.css')
    if not source_js.is_file() or not source_css.is_file():
        raise SystemExit('Arquivos da consulta nativa NF-e nao encontrados')

    shutil.copy2(source_js,web/'native_nfe_lookup.js')
    shutil.copy2(source_css,web/'native_nfe_lookup.css')

    html=index.read_text(encoding='utf-8')
    if 'native_nfe_lookup.css' not in html:
        head='</head>'
        if head not in html: raise SystemExit('index.html sem </head>')
        html=html.replace(head,'  <link rel="stylesheet" href="native_nfe_lookup.css">\n'+head,1)
    if 'native_nfe_lookup.js' not in html:
        body='</body>'
        if body not in html: raise SystemExit('index.html sem </body>')
        html=html.replace(body,'  <script type="module" src="native_nfe_lookup.js"></script>\n'+body,1)
    index.write_text(html,encoding='utf-8',newline='\n')

    # Confere se o patch de runtime anterior ja liberou apenas o broker local na CSP.
    final=index.read_text(encoding='utf-8')
    for token in ('native_nfe_lookup.css','native_nfe_lookup.js','http://127.0.0.1:47878'):
        if token not in final:
            raise SystemExit('Integracao web incompleta: '+token)
    if MARKER not in (web/'native_nfe_lookup.js').read_text(encoding='utf-8'):
        raise SystemExit('Marcador da UI nativa ausente')
    print('Payload web atualizado: botao e modal nativos de consulta NF-e instalados.')


if __name__=='__main__':
    main()
