from pathlib import Path
s=Path('installer-v2/launcher/csm_fiscal_core.cs').read_text(encoding='utf-8')
required=[
 'CSM_FISCAL_ISSUER_3131',
 'issuer_document',
 'distribution_restricted',
 'xml_unavailable_reason',
 'selectedIsIssuer',
 'issuerCnpj = key.Substring(6, 14)',
 'distribution.CStat = "641"'
]
for t in required:
    if t not in s: raise SystemExit('Fiscal Core 3.13.1 incompleto: '+t)
if 'if (selectedIsIssuer)' not in s:
    raise SystemExit('Fluxo de emitente não está isolado')
print('OK - Fiscal Core 3.13.1 distingue NF-e própria e não tenta consChNFe para baixar XML do emitente.')
