from pathlib import Path

p = Path('installer-v2/launcher/main.go')
s = p.read_text(encoding='utf-8')

required = [
    '/fiscal/certificates',
    '/fiscal/certificate-folders',
    '/fiscal/certificate-folders/add',
    '/fiscal/certificate-folders/remove',
    '/fiscal/certificates/scan',
    '/fiscal/certificate/validate',
    '/fiscal/nfe/manifestar',
    '/fiscal/nfe/open-cached',
    '/fiscal/nfe/export-xml',
    'handleFiscalCertificateFolders',
    'handleFiscalCertificateValidate',
    'handleFiscalManifest',
    'handleFiscalOpenCached',
    'handleFiscalExportXML',
    'runFiscalCoreWithInput',
    'GetSaveFileNameW',
    'cachedNFePath',
    'io.LimitReader',
    'fiscalOriginAllowed',
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit('API local fiscal 3.13.0 incompleta: ' + ', '.join(missing))

validate_start = s.find('func (b *broker) handleFiscalCertificateValidate')
validate_end = s.find('\nfunc ', validate_start + 10)
if validate_start < 0:
    raise SystemExit('handler validate ausente')
block = s[validate_start: validate_end if validate_end > validate_start else len(s)]
for forbidden in ['"--password"', 'URL.Query().Get("password")', 'URL.Query().Get("senha")']:
    if forbidden in block:
        raise SystemExit('Senha exposta no broker: ' + forbidden)
if 'runFiscalCoreWithInput(req.Password' not in block:
    raise SystemExit('Senha não está sendo encaminhada por stdin')
if 'req.ID' not in block or '"--id", req.ID' not in block:
    raise SystemExit('Validação do A1 não usa ID opaco')

manifest_start=s.find('func (b *broker) handleFiscalManifest')
manifest_end=s.find('\nfunc ',manifest_start+10)
if manifest_start < 0:
    raise SystemExit('handler da manifestação ausente')
manifest=s[manifest_start:manifest_end if manifest_end>manifest_start else len(s)]
for token in ['req.Event != "210210"','"manifest", "--key", req.Key','"--event", "210210"']:
    if token not in manifest:
        raise SystemExit('Manifestação sem trava obrigatória: '+token)

# Export deve copiar bytes do cache validado, não reconstruir o XML.
export_start=s.find('func (b *broker) handleFiscalExportXML')
export_end=s.find('\nfunc ',export_start+10)
export=s[export_start:export_end if export_end>export_start else len(s)]
for token in ['cachedNFePath(req.Key)','os.ReadFile(src)','os.WriteFile(dst,raw','chooseXMLSavePath']:
    if token not in export:
        raise SystemExit('Exportação XML não preserva cache oficial: '+token)

if 'origin not allowed' not in s or 'pywebview.local' not in s:
    raise SystemExit('Proteção de origem fiscal ausente')

print('OK - certificados, Ciência, reabertura e exportação XML protegidos pelo broker local.')
