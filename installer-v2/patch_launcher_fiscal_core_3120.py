from pathlib import Path

MARKER='CSM_FISCAL_CORE_BROKER_3120'
p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')
if MARKER in s:
    print('Broker Fiscal Core 3.12.0 já aplicado')
    raise SystemExit(0)

# Tipos da API local nativa.
anchor='type ackRequest struct { Path string `json:"path"` }\n'
if anchor not in s:
    raise SystemExit('ackRequest não encontrado no launcher')
s=s.replace(anchor,anchor+'type fiscalConsultRequest struct { Key string `json:"key"`; CNPJ string `json:"cnpj"` }\n',1)

# Endpoints protegidos para uso apenas pelo app local. Sites externos não podem
# acionar o certificado digital via CORS.
insert='''
// CSM_FISCAL_CORE_BROKER_3120 — API fiscal nativa, sem navegador/provedor web.
func fiscalOriginAllowed(r *http.Request) bool {
    origin := strings.TrimSpace(r.Header.Get("Origin"))
    if origin == "" || origin == "null" { return true }
    low := strings.ToLower(origin)
    return strings.HasPrefix(low, "file://") || strings.HasPrefix(low, "http://127.0.0.1") || strings.HasPrefix(low, "http://localhost") || strings.HasPrefix(low, "https://127.0.0.1") || strings.HasPrefix(low, "https://localhost")
}

func setFiscalCORS(w http.ResponseWriter, r *http.Request) bool {
    if !fiscalOriginAllowed(r) { http.Error(w, "origin not allowed", http.StatusForbidden); return false }
    origin := strings.TrimSpace(r.Header.Get("Origin"))
    if origin == "" { origin = "null" }
    w.Header().Set("Access-Control-Allow-Origin", origin)
    w.Header().Set("Vary", "Origin")
    w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
    w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    return true
}

func (b *broker) fiscalCorePath() string {
    return filepath.Join(b.dir, "_internal", "csm", "CSM Fiscal Core.exe")
}

func (b *broker) runFiscalCore(args ...string) ([]byte, error) {
    helper := b.fiscalCorePath()
    if _, err := os.Stat(helper); err != nil { return nil, fmt.Errorf("CSM Fiscal Core não encontrado: %w", err) }
    cmd := exec.Command(helper, args...)
    cmd.Dir = b.dir
    cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
    out, err := cmd.Output()
    // O helper usa códigos de saída para distinguir seleção de certificado e
    // indisponibilidade fiscal. Se houver JSON válido, ele é a resposta oficial.
    if len(out) > 0 && json.Valid(out) { return out, nil }
    if err != nil { return out, err }
    if !json.Valid(out) { return out, fmt.Errorf("CSM Fiscal Core retornou resposta inválida") }
    return out, nil
}

func (b *broker) handleFiscalCertificates(w http.ResponseWriter, r *http.Request) {
    if !setFiscalCORS(w, r) { return }
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodGet { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }
    out, err := b.runFiscalCore("list")
    if err != nil { http.Error(w, err.Error(), http.StatusInternalServerError); return }
    w.Header().Set("Content-Type", "application/json; charset=utf-8")
    _, _ = w.Write(out)
}

func (b *broker) handleFiscalConsult(w http.ResponseWriter, r *http.Request) {
    if !setFiscalCORS(w, r) { return }
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }
    var req fiscalConsultRequest
    if err := json.NewDecoder(io.LimitReader(r.Body, 64<<10)).Decode(&req); err != nil { http.Error(w, "invalid request", http.StatusBadRequest); return }
    req.Key = strings.TrimSpace(req.Key)
    req.CNPJ = strings.TrimSpace(req.CNPJ)
    if len(req.Key) != 44 { http.Error(w, "invalid access key", http.StatusBadRequest); return }
    args := []string{"consult", "--key", req.Key}
    if req.CNPJ != "" { args = append(args, "--cnpj", req.CNPJ) }
    out, err := b.runFiscalCore(args...)
    if err != nil { http.Error(w, err.Error(), http.StatusInternalServerError); return }

    // Se o Web Service oficial entregou o XML completo, encaminha o mesmo
    // arquivo para o pipeline normal de abas do Visualizador.
    var result map[string]any
    if json.Unmarshal(out, &result) == nil {
        if raw, ok := result["xml_path"]; ok {
            if path, ok := raw.(string); ok && strings.EqualFold(filepath.Ext(path), ".xml") {
                if _, statErr := os.Stat(path); statErr == nil {
                    if err := b.ensureHealthyCore(); err == nil { b.queuePath(path) }
                }
            }
        }
    }
    w.Header().Set("Content-Type", "application/json; charset=utf-8")
    _, _ = w.Write(out)
}

'''
anchor2='func (b *broker) handleHealth(w http.ResponseWriter, r *http.Request) {'
if anchor2 not in s:
    raise SystemExit('handleHealth não encontrado')
s=s.replace(anchor2,insert+anchor2,1)

mux='''    mux.HandleFunc("/health", b.handleHealth)'''
if mux not in s:
    raise SystemExit('registro /health não encontrado')
s=s.replace(mux,''''    mux.HandleFunc("/fiscal/certificates", b.handleFiscalCertificates)
    mux.HandleFunc("/fiscal/nfe/consultar", b.handleFiscalConsult)
    mux.HandleFunc("/health", b.handleHealth)''',1)

for token in (MARKER,'/fiscal/certificates','/fiscal/nfe/consultar','CSM Fiscal Core.exe','fiscalOriginAllowed','handleFiscalConsult'):
    if token not in s: raise SystemExit('Patch do broker fiscal incompleto: '+token)
p.write_text(s,encoding='utf-8',newline='\n')
print('3.12.0: broker local conectado ao CSM Fiscal Core nativo; navegador removido do fluxo principal.')
