from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
PATCH=BASE/'difal_st_display_3102.js'
MARKER='CSM_DIFAL_ST_DISPLAY_3102'

def main():
    if len(sys.argv)!=2:return 2
    web=Path(sys.argv[1]); app=web/'app.js'
    if not app.is_file():raise SystemExit('app.js nao encontrado')
    text=app.read_text(encoding='utf-8')
    if MARKER not in text:
        text=text.rstrip()+'\n'+PATCH.read_text(encoding='utf-8').strip()+'\n'
        app.write_text(text,encoding='utf-8',newline='\n')
    final=app.read_text(encoding='utf-8')
    for token in ('CSM_DIFAL_ST_MODULE_V1',MARKER,'Resumo por alíquota','Alíquota interestadual'):
        if token not in final:raise SystemExit('Patch visual DIFAL incompleto: '+token)
    print('Patch 3.10.2 aplicado: calculo permanece isolado por CFOP/aliquota, exibicao mostra apenas aliquota.')
    return 0

if __name__=='__main__':raise SystemExit(main())
