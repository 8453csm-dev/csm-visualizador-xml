from pathlib import Path

p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')
old='''func (b *broker) adoptOrStartCore() error {\n\tb.coreMu.Lock()\n\tdefer b.coreMu.Unlock()\n\tif len(processIDsByName(coreName)) > 0 {\n\t\tif owner, ok := waitRecoverAnyCoreWindow(5 * time.Second); ok {\n\t\t\tb.setCoreState(owner, time.Now().Add(-30*time.Second))\n\t\t\treturn nil\n\t\t}\n\t\tkillAllCoreProcesses()\n\t}\n\treturn b.startCoreUnlocked()\n}\n'''
if old not in s:
    # aceita formatacao compacta da origem
    old='''func (b *broker) adoptOrStartCore() error {\n    b.coreMu.Lock(); defer b.coreMu.Unlock()\n    if len(processIDsByName(coreName)) > 0 {\n        if owner, ok := waitRecoverAnyCoreWindow(5 * time.Second); ok {\n            b.setCoreState(owner, time.Now().Add(-30*time.Second)); return nil\n        }\n        killAllCoreProcesses()\n    }\n    return b.startCoreUnlocked()\n}\n'''
new='''func (b *broker) adoptOrStartCore() error {\n    b.coreMu.Lock(); defer b.coreMu.Unlock()\n    // Se nao existe broker respondendo, qualquer Core remanescente e orfao ou de versao anterior.\n    // Nunca adotar um Core apenas pelo nome do processo: isso podia abrir a interface antiga logo apos atualizar.\n    if len(processIDsByName(coreName)) > 0 {\n        killAllCoreProcesses()\n        b.setCoreState(0, time.Time{})\n    }\n    return b.startCoreUnlocked()\n}\n'''
if old not in s:raise SystemExit('Bloco adoptOrStartCore esperado nao encontrado')
s=s.replace(old,new,1)
if 'Nunca adotar um Core apenas pelo nome do processo' not in s:raise SystemExit('Patch fresh-core nao aplicado')
p.write_text(s,encoding='utf-8',newline='\n')
print('Launcher 3.10.2: Core antigo/orfao nao sera mais adotado.')
