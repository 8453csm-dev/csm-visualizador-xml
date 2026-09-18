from pathlib import Path

p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')
MARK='CSM_PUBLIC_PROVIDER_3150'
if MARK in s:
    print('Provider público 3.15.0 já aplicado')
    raise SystemExit(0)
old='''    if !strings.EqualFold(strings.TrimSpace(req.Provider), "consultadanfe") {
        w.Header().Set("Content-Type", "application/json")
        _, _ = w.Write([]byte(`{"ok":true,"started":false}`))
        return
    }'''
new='''    if !strings.EqualFold(strings.TrimSpace(req.Provider), "sefazpublica") {
        w.Header().Set("Content-Type", "application/json")
        _, _ = w.Write([]byte(`{"ok":true,"started":false}`))
        return
    }'''
if old not in s: raise SystemExit('Validação de provider 3.11 não localizada')
s=s.replace(old,new,1)
s=s.replace('''    go b.repositorySyncLoop()
''','''    // 3.15.0: sem sincronização automática da Base CSM; consulta principal é pública/visual.
''',1)
s=s.rstrip()+"\n// "+MARK+" — lookup-automation agora inicia somente consulta pública oficial.\n"
if '"sefazpublica"' not in s: raise SystemExit('Provider sefazpublica ausente')
if 'go b.repositorySyncLoop()' in s: raise SystemExit('Base CSM ainda sincroniza automaticamente')
p.write_text(s,encoding='utf-8',newline='\n')
print('3.15.0: lookup-automation usa provider sefazpublica.')
