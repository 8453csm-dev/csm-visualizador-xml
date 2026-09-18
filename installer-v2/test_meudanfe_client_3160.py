from pathlib import Path
s=Path('installer-v2/launcher/csm_meudanfe_client.cs').read_text(encoding='utf-8')
for t in [
 'https://api.meudanfe.com.br/v2',
 '/fd/get/xml/',
 '/fd/add/',
 'Api-Key',
 'CredentialTarget',
 'CredWrite',
 'CredRead',
 'Thread.Sleep(1200)',
 'XmlMatchesKey'
]:
    if t not in s: raise SystemExit('Meu Danfe Client 3.16.0 incompleto: '+t)
if 'Console.WriteLine(apiKey)' in s or 'api_key" }, { "' in s:
    raise SystemExit('Risco de vazamento de Api-Key')
print('OK - cliente Meu Danfe v2 usa Credential Manager, espera >=1s e valida XML pela chave.')
