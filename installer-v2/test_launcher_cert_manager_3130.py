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
    'handleFiscalCertificateFolders',
    'handleFiscalCertificateValidate',
    'runFiscalCoreWithInput',
    'io.LimitReader',
    'fiscalOriginAllowed',
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit('API local de certificados incompleta: ' + ', '.join(missing))

# A senha nunca pode ser enviada por query string nem argumento do processo.
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

# CORS deve continuar restrito ao app/local host.
if 'origin not allowed' not in s or 'pywebview.local' not in s:
    raise SystemExit('Proteção de origem fiscal ausente')

print('OK - endpoints locais de certificados protegidos e senha via stdin.')
