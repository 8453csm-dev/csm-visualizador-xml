from pathlib import Path
p=Path('installer-v2/prepare_release_3111.py')
if not p.exists(): p=Path('installer-v2/prepare_release_3110.py')
s=p.read_text(encoding='utf-8')
for token in ('CSM_POSTINSTALL_FRESH_3112','timeout /T 3','--post-install-fresh','Abrir CSM Visualizador XML 3.11.2'):
    if token not in s: raise SystemExit('Pós-instalação 3.11.2 sem '+token)
print('Pós-instalação fresh 3.11.2 validado.')
