from pathlib import Path
import sys

MARKER='CSM_TAX_EXPLAINER_ENTRYPOINT_V2'
BASE=Path(__file__).resolve().parent
SNIPPET=BASE/'tax_explainer_entrypoint_v2.js'


def main():
    if len(sys.argv)!=2:
        print('uso: patch_tax_explainer_entrypoint_v2.py <pasta-web>',file=sys.stderr);return 2
    web=Path(sys.argv[1]);app=web/'app.js'
    if not app.is_file():raise SystemExit('app.js nao encontrado')
    if not SNIPPET.is_file():raise SystemExit('snippet de entrada tributaria ausente')
    text=app.read_text(encoding='utf-8')
    if MARKER not in text:
        text=text.rstrip()+'\n'+SNIPPET.read_text(encoding='utf-8').strip()+'\n'
        app.write_text(text,encoding='utf-8',newline='\n')
    final=app.read_text(encoding='utf-8')
    for tok in (MARKER,'activateDocument=async function','csmTaxSyncForActiveDocument','CSM_TAX_EXPLAINER_NO_FREEZE_391'):
        if tok not in final:raise SystemExit('Entrada tributaria 3.9.2 incompleta: '+tok)
    print('Entrada tributaria deterministica integrada ao activateDocument real.')
    return 0

if __name__=='__main__':raise SystemExit(main())
