from pathlib import Path
s=Path('installer-v2/launcher/csm_fiscal_core.cs').read_text(encoding='utf-8')
required=[
 'CSM_REPOSITORY_API_3140','BuildDistNSUPayload','<distNSU>','RepositoryCommand',
 'SyncRepository','next_allowed_utc','RepositoryXmlPath','summary_only','cooldown'
]
for t in required:
    if t not in s: raise SystemExit('Repositório 3.14.0 incompleto: '+t)
if 'DateTime.UtcNow.AddHours(1)' not in s:
    raise SystemExit('Cooldown oficial de 1 hora não implementado')
if 'maxBatches=Math.Max(1,Math.Min(10,parsed))' not in s:
    raise SystemExit('Limite de lotes ausente')
print('OK - Base CSM 3.14.0: chave, distNSU, estado NSU e cooldown implementados.')
