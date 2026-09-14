from pathlib import Path
import sys
BASE=Path(__file__).resolve().parent
JS=BASE/'difal_st_module.js'
CSS=BASE/'difal_st.css'
def append_once(path,payload,marker):
    text=path.read_text(encoding='utf-8')
    if marker in text:return
    path.write_text(text.rstrip()+'\n'+payload.read_text(encoding='utf-8').strip()+'\n',encoding='utf-8',newline='\n')
def main():
    if len(sys.argv)!=2:return 2
    web=Path(sys.argv[1]);app=web/'app.js';css=web/'refinement.css'
    if not app.is_file() or not css.is_file():raise SystemExit('app.js/refinement.css não encontrados')
    append_once(app,JS,'CSM_DIFAL_ST_MODULE_V1');append_once(css,CSS,'CSM_DIFAL_ST_STYLE_V1')
    final=app.read_text(encoding='utf-8')
    for tok in ('CSM_DIFAL_ST_MODULE_V1','DIFAL / ICMS ST','calculateDifal','calculateSt','get_xml_text','CSM_TAX_EXPLAINER_UI_V1','CSM_DEVOLUTION_ENTRYPOINT_V4'):
        if tok not in final:raise SystemExit('Integração DIFAL/ST incompleta: '+tok)
    print('Módulo DIFAL / ICMS ST 1.0.0 integrado preservando Tributação e Devolução.')
    return 0
if __name__=='__main__':raise SystemExit(main())
