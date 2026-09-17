from pathlib import Path

MARKER='CSM_POSTINSTALL_LAUNCHER_3112'
p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')
if MARKER in s:
    print('Launcher pós-instalação 3.11.2 já aplicado')
    raise SystemExit(0)

old='''func killAllCoreProcesses() {\n    cmd := exec.Command("taskkill.exe", "/F", "/IM", coreName)'''
new='''func killAllCoreProcesses() {\n    // CSM_POSTINSTALL_LAUNCHER_3112: /T encerra também o WebView2 filho do Core antigo.\n    cmd := exec.Command("taskkill.exe", "/F", "/T", "/IM", coreName)'''
if old not in s:
    raise RuntimeError('killAllCoreProcesses esperado não encontrado')
s=s.replace(old,new,1)

anchor='    paths := normalizePaths(os.Args[1:])\n'
if anchor not in s:
    raise RuntimeError('Âncora normalizePaths do main não encontrada')
insert='''    freshPostInstall := false\n    for _, a := range os.Args[1:] {\n        if strings.EqualFold(strings.TrimSpace(a), "--post-install-fresh") { freshPostInstall = true; break }\n    }\n    if freshPostInstall {\n        // Aguarda o instalador encerrar e elimina Core + árvore WebView2 da versão anterior.\n        time.Sleep(3 * time.Second)\n        killAllCoreProcesses()\n    }\n'''
s=s.replace(anchor,insert+anchor,1)

old_post='    if postExisting(paths) { return }'
count=s.count(old_post)
if count < 1:
    raise RuntimeError('Chamadas postExisting esperadas não encontradas')
s=s.replace(old_post,'    if !freshPostInstall && postExisting(paths) { return }')

p.write_text(s,encoding='utf-8',newline='\n')
print(f'Launcher 3.11.2: modo fresh aplicado; {count} reutilizações de broker protegidas.')
