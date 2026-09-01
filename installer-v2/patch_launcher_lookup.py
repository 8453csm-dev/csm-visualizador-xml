from pathlib import Path

MARKER = "CSM_LOOKUP_AUTOMATION_V1"
path = Path("installer-v2/launcher/main.go")
text = path.read_text(encoding="utf-8")

if MARKER in text:
    print("Launcher ja possui automacao reforcada do Localizador")
    raise SystemExit(0)

anchor_types = 'type openRequest struct { Paths []string `json:"paths"` }\ntype ackRequest struct { Path string `json:"path"` }\n'
if anchor_types not in text:
    raise RuntimeError("Ancora de tipos nao encontrada")
text = text.replace(anchor_types, anchor_types + '''type lookupAutomationRequest struct {\n    Key      string `json:"key"`\n    Provider string `json:"provider"`\n    Format   string `json:"format"`\n}\n''', 1)

anchor_cors = 'func setCORS(w http.ResponseWriter) {\n'
if anchor_cors not in text:
    raise RuntimeError("Ancora setCORS nao encontrada")
helpers = r'''// CSM_LOOKUP_AUTOMATION_V1
func validLookupKey(value string) string {
    value = strings.ToUpper(strings.TrimSpace(value))
    var b strings.Builder
    for _, r := range value {
        if (r >= '0' && r <= '9') || (r >= 'A' && r <= 'Z') { b.WriteRune(r) }
    }
    out := b.String()
    if len(out) != 44 { return "" }
    return out
}

func (b *broker) handleLookupAutomation(w http.ResponseWriter, r *http.Request) {
    setCORS(w)
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }
    var req lookupAutomationRequest
    if err := json.NewDecoder(io.LimitReader(r.Body, 4096)).Decode(&req); err != nil { http.Error(w, "invalid request", http.StatusBadRequest); return }
    key := validLookupKey(req.Key)
    if key == "" { http.Error(w, "invalid access key", http.StatusBadRequest); return }
    if !strings.EqualFold(strings.TrimSpace(req.Provider), "consultadanfe") {
        w.Header().Set("Content-Type", "application/json")
        _, _ = w.Write([]byte(`{"ok":true,"started":false}`))
        return
    }
    script := filepath.Join(b.dir, "_internal", "csm", "consulta_danfe_uia.ps1")
    if _, err := os.Stat(script); err != nil { http.Error(w, "lookup helper unavailable", http.StatusInternalServerError); return }
    cmd := exec.Command("powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", script, "-Key", key)
    cmd.Dir = b.dir
    cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
    if err := cmd.Start(); err != nil { http.Error(w, err.Error(), http.StatusInternalServerError); return }
    _ = cmd.Process.Release()
    w.Header().Set("Content-Type", "application/json")
    _, _ = w.Write([]byte(`{"ok":true,"started":true}`))
}

'''
text = text.replace(anchor_cors, helpers + anchor_cors, 1)

mux_anchor = '    mux.HandleFunc("/activate", b.handleActivate)\n'
if mux_anchor not in text:
    raise RuntimeError("Ancora do mux nao encontrada")
text = text.replace(mux_anchor, mux_anchor + '    mux.HandleFunc("/lookup-automation", b.handleLookupAutomation)\n', 1)

path.write_text(text, encoding="utf-8", newline="\n")
print("Launcher atualizado: broker pode reforcar o preenchimento do Consulta DANFE")
