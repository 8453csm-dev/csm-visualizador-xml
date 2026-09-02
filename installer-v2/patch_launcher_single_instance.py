from pathlib import Path

MARKER_V2 = "CSM_SINGLE_INSTANCE_STRICT_V2"
MARKER_V3 = "CSM_SINGLE_INSTANCE_STRICT_V3"
path = Path("installer-v2/launcher/main.go")
text = path.read_text(encoding="utf-8")

if MARKER_V3 in text:
    print("Launcher ja possui o patch V3 de instancia unica e janela visivel")
    raise SystemExit(0)

# Mantem a protecao V2 contra abertura de um segundo Core.
if MARKER_V2 not in text:
    anchor = 'func (b *broker) removeSubscriber(ch chan string) { b.mu.Lock(); delete(b.subscribers, ch); b.mu.Unlock() }\n'
    if anchor not in text:
        raise RuntimeError("Ancora removeSubscriber nao encontrada")
    text = text.replace(anchor, anchor + '''\n// CSM_SINGLE_INSTANCE_STRICT_V2\nfunc (b *broker) subscriberCount() int {\n    b.mu.Lock()\n    defer b.mu.Unlock()\n    return len(b.subscribers)\n}\n''', 1)

    old_open = '''    paths := normalizePaths(req.Paths)\n    if err := b.ensureHealthyCore(); err != nil { http.Error(w, err.Error(), http.StatusInternalServerError); return }\n    for _, p := range paths { b.queuePath(p) }\n'''
    new_open = '''    paths := normalizePaths(req.Paths)\n    // Se a interface existente esta conectada ao broker, ela e a fonte da verdade.\n    // Nunca iniciar outro Core apenas porque a enumeracao de processos/janelas falhou.\n    if b.subscriberCount() == 0 {\n        if err := b.ensureHealthyCore(); err != nil { http.Error(w, err.Error(), http.StatusInternalServerError); return }\n    } else {\n        _, _ = recoverAnyCoreWindow()\n    }\n    for _, p := range paths { b.queuePath(p) }\n'''
    if old_open not in text:
        raise RuntimeError("Ancora handleOpen nao encontrada")
    text = text.replace(old_open, new_open, 1)

    old_activate = '''    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }\n    if err := b.ensureHealthyCore(); err != nil { http.Error(w, err.Error(), http.StatusInternalServerError); return }\n    w.Header().Set("Content-Type", "application/json")\n'''
    new_activate = '''    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }\n    if b.subscriberCount() == 0 {\n        if err := b.ensureHealthyCore(); err != nil { http.Error(w, err.Error(), http.StatusInternalServerError); return }\n    } else {\n        _, _ = recoverAnyCoreWindow()\n    }\n    w.Header().Set("Content-Type", "application/json")\n'''
    if old_activate not in text:
        raise RuntimeError("Ancora handleActivate nao encontrada")
    text = text.replace(old_activate, new_activate, 1)

    old_supervise = '''func (b *broker) supervise() {\n    ticker := time.NewTicker(1 * time.Second)\n    defer ticker.Stop()\n    var noCoreSince time.Time\n    for range ticker.C {\n        if len(processIDsByName(coreName)) > 0 { noCoreSince = time.Time{}; continue }\n        if noCoreSince.IsZero() { noCoreSince = time.Now(); continue }\n        if time.Since(noCoreSince) > 4*time.Second { os.Exit(0) }\n    }\n}\n'''
    new_supervise = '''func (b *broker) supervise() {\n    ticker := time.NewTicker(1 * time.Second)\n    defer ticker.Stop()\n    var noCoreSince time.Time\n    for range ticker.C {\n        // Uma interface SSE conectada prova que a sessao real do Visualizador ainda esta viva.\n        // Nao encerrar o broker por uma leitura transitoria/incorreta da arvore de processos.\n        if b.subscriberCount() > 0 { noCoreSince = time.Time{}; continue }\n        if len(processIDsByName(coreName)) > 0 { noCoreSince = time.Time{}; continue }\n        if noCoreSince.IsZero() { noCoreSince = time.Now(); continue }\n        if time.Since(noCoreSince) > 30*time.Second { os.Exit(0) }\n    }\n}\n'''
    if old_supervise not in text:
        raise RuntimeError("Ancora supervise nao encontrada")
    text = text.replace(old_supervise, new_supervise, 1)

# V3: nunca forca para a tela uma janela top-level que o WebView criou oculta.
# A versao anterior priorizava o titulo antes de IsWindowVisible; isso podia escolher
# o host interno/oculto do PyWebView e transforma-lo em uma segunda janela vazia.
old_primary = '''func primaryWindow(pid uint32) (windowCandidate, bool) {\n    wins := windowsForPID(pid)\n    if len(wins) == 0 { return windowCandidate{}, false }\n    for _, w := range wins { if strings.Contains(strings.ToLower(w.title), "csm visualizador xml") { return w, true } }\n    for _, w := range wins { if w.visible { return w, true } }\n    return wins[0], true\n}\n'''
new_primary = '''// CSM_SINGLE_INSTANCE_STRICT_V3\nfunc primaryWindow(pid uint32) (windowCandidate, bool) {\n    wins := windowsForPID(pid)\n    if len(wins) == 0 { return windowCandidate{}, false }\n    // Primeiro: janela real do aplicativo que ja esta visivel.\n    for _, w := range wins {\n        if w.visible && strings.Contains(strings.ToLower(w.title), "csm visualizador xml") { return w, true }\n    }\n    // Segundo: qualquer outra janela top-level visivel do Core.\n    for _, w := range wins { if w.visible { return w, true } }\n    // Importante: se so existem hosts ocultos, espere o PyWebView mostrar a janela real.\n    // Nao chame ShowWindow em uma janela interna/oculta.\n    return windowCandidate{}, false\n}\n'''
if old_primary not in text:
    raise RuntimeError("Ancora primaryWindow nao encontrada; nao foi possivel proteger a janela oculta do WebView")
text = text.replace(old_primary, new_primary, 1)

path.write_text(text, encoding="utf-8", newline="\n")
print("Launcher V3 atualizado: instancia unica preservada e hosts ocultos do WebView nao sao exibidos")
