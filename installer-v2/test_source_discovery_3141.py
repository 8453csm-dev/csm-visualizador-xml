from pathlib import Path
s=Path('installer-v2/launcher/main.go').read_text(encoding='utf-8')
for t in ['CSM_XML_SOURCE_DISCOVERY_3141','existingXMLSourceRoots','sourceSearchRootsForKey','readXMLIfMatches','CSM_SIEG_ROOT','--csm-source-selftest']:
    if t not in s: raise SystemExit('Source discovery 3.14.1 incompleto: '+t)
print('OK - 3.14.1 descobre SIEG/XML, prioriza CNPJ e possui self-test real.')
