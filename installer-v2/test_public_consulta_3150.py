from pathlib import Path
h=Path('installer-v2/launcher/consulta_danfe_helper.cs').read_text(encoding='utf-8')
g=Path('installer-v2/launcher/main.go').read_text(encoding='utf-8')
for t in ('consultaRecaptcha.aspx?tipoConsulta=completa','hCaptcha','NotifyBrokerOpen','RenderHtmlToPdf'):
    if t not in h: raise SystemExit('Helper público incompleto: '+t)
for t in ('CSM_PUBLIC_PROVIDER_3150','"sefazpublica"','/lookup-automation'):
    if t not in g: raise SystemExit('Broker público incompleto: '+t)
print('OK - 3.15.0 usa portal oficial público, hCaptcha assistido e abre PDF no Visualizador.')
