from pathlib import Path
p=Path('installer-v2/launcher/csm_fiscal_core.cs')
s=p.read_text(encoding='utf-8')
checks={
 'marker':'CSM_FISCAL_CORE_SOAP_3121',
 'protocol direct':'BuildProtocolEnvelope',
 'no wrapper':'<nfeConsultaNF',
 'distribution uf':'<cUFAutor>',
 'protocol call':'PostProtocolSoap(cert, url, payload)',
 'uf resolver':'GetAuthorCUF(cert, key)'
}
for label,tok in checks.items():
    if tok not in s: raise SystemExit(f'ausente {label}: {tok}')
# O wrapper literal só pode existir na asserção do self-test, não na montagem do envelope.
segment=s[s.index('private static string BuildProtocolEnvelope'):s.index('private static string PostProtocolSoap')]
if '<nfeConsultaNF' in segment: raise SystemExit('BuildProtocolEnvelope ainda contém wrapper nfeConsultaNF')
if '<nfeDadosMsg xmlns=\\\"" + ConsultWsNs + "\\\">' not in segment: raise SystemExit('nfeDadosMsg direto ausente')
print('OK - SOAP Consulta Protocolo 4.00 direto e Distribuicao DF-e com cUFAutor.')
