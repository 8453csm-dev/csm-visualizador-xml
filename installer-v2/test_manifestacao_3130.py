from pathlib import Path

src = Path('installer-v2/launcher/csm_fiscal_core.cs').read_text(encoding='utf-8')

required = [
    'CSM_MANIFESTACAO_3130',
    'cmd == "manifest"',
    '210210',
    'Ciencia da Operacao',
    'ID210210',
    'envEvento',
    'infEvento',
    'nSeqEvento',
    'verEvento',
    'System.Security.Cryptography.Xml',
    'SignedXml',
    'XmlDsigRSASHA1Url',
    'XmlDsigSHA1Url',
    'NFeRecepcaoEvento4',
    'nfeRecepcaoEvento',
    'nfeDadosMsg',
    'event_registered',
    'distribution_retried',
]
missing=[x for x in required if x not in src]
if missing:
    raise SystemExit('Manifestação 3.13.0 incompleta: '+', '.join(missing))

# A Ciência deve ser a única manifestação que o fluxo de obtenção automática conhece.
manifest_start=src.find('private static int Manifest')
manifest_end=src.find('\n    private static ', manifest_start+20)
if manifest_start < 0:
    raise SystemExit('Manifest() ausente')
block=src[manifest_start: manifest_end if manifest_end > manifest_start else len(src)]
if 'eventType != "210210"' not in block and 'eventType == "210210"' not in block:
    raise SystemExit('Manifest() não restringe o evento a 210210')
for forbidden in ['210200', '210220', '210240']:
    if forbidden in block:
        raise SystemExit('Manifest() não pode transmitir manifestação conclusiva automaticamente: '+forbidden)

# Deve haver um único retry de distribuição depois de evento aceito/idempotente.
if block.count('QueryDistribution(') != 1:
    raise SystemExit('Manifest() deve repetir NFeDistribuicaoDFe exatamente uma vez')

# Duplicidade significa que a Ciência já existe e pode seguir para a distribuição.
if '573' not in src or '135' not in src:
    raise SystemExit('Tratamento de evento aceito/duplicado ausente')

print('OK - contrato da Ciência da Operação 210210 e retry único da distribuição validados.')
