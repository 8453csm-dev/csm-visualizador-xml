from pathlib import Path

src=Path('installer-v2/launcher/csm_public_nfe_viewer.cs')
dst=Path('installer-v2/launcher/consulta_danfe_helper.cs')
if not src.is_file(): raise SystemExit('csm_public_nfe_viewer.cs não encontrado')
text=src.read_text(encoding='utf-8')
for tok in ('consultaRecaptcha.aspx?tipoConsulta=completa','hCaptcha','NotifyBrokerOpen','RenderHtmlToPdf','--selftest'):
    if tok not in text: raise SystemExit('Helper público 3.15.0 incompleto: '+tok)
dst.write_text(text,encoding='utf-8',newline='\n')
print('3.15.0: helper legado substituído pela consulta pública oficial da NF-e.')
