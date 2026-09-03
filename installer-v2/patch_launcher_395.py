from pathlib import Path

p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')

old_primary='''func primaryWindow(pid uint32) (windowCandidate, bool) {
    wins := windowsForPID(pid)
    if len(wins) == 0 { return windowCandidate{}, false }
    for _, w := range wins { if strings.Contains(strings.ToLower(w.title), "csm visualizador xml") { return w, true } }
    for _, w := range wins { if w.visible { return w, true } }
    return wins[0], true
}'''
new_primary='''func primaryWindow(pid uint32) (windowCandidate, bool) {
    wins := windowsForPID(pid)
    for _, w := range wins {
        if w.visible && strings.Contains(strings.ToLower(w.title), "csm visualizador xml") { return w, true }
    }
    for _, w := range wins { if w.visible { return w, true } }
    return windowCandidate{}, false
}'''
if old_primary not in s: raise SystemExit('primaryWindow esperado não encontrado')
s=s.replace(old_primary,new_primary,1)

old_gor='''    go func() {
        if owner, ok := waitRecoverAnyCoreWindow(15 * time.Second); ok { b.setCoreState(owner, time.Time{}) }
    }()'''
new_gor='''    go func() {
        if owner, ok := waitFindVisibleCoreWindow(15 * time.Second); ok { b.setCoreState(owner, time.Time{}) }
    }()'''
if old_gor not in s: raise SystemExit('goroutine de startup esperada não encontrada')
s=s.replace(old_gor,new_gor,1)

old_self='''    if len(os.Args) > 1 && os.Args[1] == "--csm-launcher-selftest" { return }'''
new_self='''    if len(os.Args) > 1 && os.Args[1] == "--csm-launcher-selftest" {
        if !folderPickerAPIsAvailable() { os.Exit(17) }
        return
    }'''
if old_self not in s: raise SystemExit('selftest esperado não encontrado')
s=s.replace(old_self,new_self,1)

old_routes='''    mux.HandleFunc("/open", b.handleOpen)
    mux.HandleFunc("/activate", b.handleActivate)
    mux.HandleFunc("/ack", b.handleAck)
    mux.HandleFunc("/events", b.handleEvents)
    mux.HandleFunc("/health", b.handleHealth)'''
new_routes='''    mux.HandleFunc("/open", b.handleOpen)
    mux.HandleFunc("/activate", b.handleActivate)
    mux.HandleFunc("/ack", b.handleAck)
    mux.HandleFunc("/events", b.handleEvents)
    mux.HandleFunc("/health", b.handleHealth)
    mux.HandleFunc("/pick-folder", b.handlePickFolder)
    mux.HandleFunc("/list-folder", b.handleListFolder)'''
if old_routes not in s: raise SystemExit('rotas do broker esperadas não encontradas')
s=s.replace(old_routes,new_routes,1)

old_final='''    if owner, ok := waitRecoverAnyCoreWindow(15 * time.Second); ok { b.setCoreState(owner, time.Time{}) }'''
new_final='''    if owner, ok := waitFindVisibleCoreWindow(15 * time.Second); ok {
        b.setCoreState(owner, time.Time{})
        maximizeStartupWindow(owner)
    }'''
if old_final not in s: raise SystemExit('espera final esperada não encontrada')
s=s.replace(old_final,new_final,1)

p.write_text(s,encoding='utf-8',newline='\n')
final=p.read_text(encoding='utf-8')
required=(
    'w.visible && strings.Contains(strings.ToLower(w.title), "csm visualizador xml")',
    'waitFindVisibleCoreWindow(15 * time.Second)',
    'folderPickerAPIsAvailable()',
    'mux.HandleFunc("/pick-folder", b.handlePickFolder)',
    'mux.HandleFunc("/list-folder", b.handleListFolder)',
    'maximizeStartupWindow(owner)',
)
for token in required:
    if token not in final: raise SystemExit('launcher 3.9.5 incompleto: '+token)
print('Launcher 3.9.5: janela visível, seletor separado e startup maximizado.')
