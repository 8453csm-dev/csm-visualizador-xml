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
s=s.replace('CSM Consulta DANFE Helper.exe','CSM Consulta DANFE Helper.exe',1)
s=s.rstrip()+"\n// "+MARK+" — lookup-automation agora inicia somente consulta pública oficial.\n"
if '"sefazpublica"' not in s: raise SystemExit('Provider sefazpublica ausente')
p.write_text(s,encoding='utf-8',newline='\n')
print('3.15.0: lookup-automation usa provider sefazpublica.')
