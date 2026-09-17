from pathlib import Path

p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')
MARK='CSM_LAUNCHER_MANIFESTACAO_3130'
if MARK in s:
    print('Broker de manifestação 3.13.0 já aplicado')
    raise SystemExit(0)
if 'CSM_LAUNCHER_CERT_MANAGER_3130' not in s:
    raise SystemExit('Aplique patch_launcher_cert_manager_3130.py antes')

anchor='type fiscalCertificateValidateRequest struct { Path string `json:"path"`; Password string `json:"password"` }\n'
if anchor not in s: raise SystemExit('tipo fiscalCertificateValidateRequest ausente')
s=s.replace(anchor,anchor+'type fiscalManifestRequest struct { Key string `json:"key"`; CNPJ string `json:"cnpj"`; Event string `json:"event"` }\n',1)

anchor='''func (b *broker) handleFiscalConsult(w http.ResponseWriter, r *http.Request) {'''
if anchor not in s: raise SystemExit('handleFiscalConsult ausente')
insert=r'''
func (b *broker) queueXMLFromFiscalResult(out []byte) {
    var result map[string]any
    if json.Unmarshal(out, &result) != nil { return }
    raw, ok := result["xml_path"]
    if !ok { return }
    path, ok := raw.(string)
    if !ok || !strings.EqualFold(filepath.Ext(path), ".xml") { return }
    if _, err := os.Stat(path); err != nil { return }
    if err := b.ensureHealthyCore(); err == nil { b.queuePath(path) }
}

func (b *broker) handleFiscalManifest(w http.ResponseWriter, r *http.Request) {
    if !setFiscalCORS(w, r) { return }
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }
    var req fiscalManifestRequest
    if err := json.NewDecoder(io.LimitReader(r.Body, 64<<10)).Decode(&req); err != nil { http.Error(w, "invalid request", http.StatusBadRequest); return }
    req.Key = strings.TrimSpace(req.Key)
    req.CNPJ = strings.TrimSpace(req.CNPJ)
    req.Event = strings.TrimSpace(req.Event)
    if len(req.Key) != 44 { http.Error(w, "invalid access key", http.StatusBadRequest); return }
    if req.CNPJ == "" { http.Error(w, "cnpj required", http.StatusBadRequest); return }
    if req.Event != "210210" { http.Error(w, "only Ciencia da Operacao (210210) is allowed", http.StatusBadRequest); return }
    out, err := b.runFiscalCore("manifest", "--key", req.Key, "--cnpj", req.CNPJ, "--event", "210210")
    if err != nil { http.Error(w, err.Error(), http.StatusInternalServerError); return }
    b.queueXMLFromFiscalResult(out)
    w.Header().Set("Content-Type", "application/json; charset=utf-8")
    _, _ = w.Write(out)
}

'''
s=s.replace(anchor,insert+anchor,1)

# Reusa helper de queue para a consulta normal, evitando divergência entre consultar/manifestar.
old=r'''    // Se o Web Service oficial entregou o XML completo, encaminha o mesmo
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
    }'''
if old in s:
    s=s.replace(old,'''    // XML oficial validado é encaminhado ao mesmo pipeline de abas.\n    b.queueXMLFromFiscalResult(out)''',1)

old='''    mux.HandleFunc("/fiscal/nfe/consultar", b.handleFiscalConsult)'''
new='''    mux.HandleFunc("/fiscal/nfe/consultar", b.handleFiscalConsult)\n    mux.HandleFunc("/fiscal/nfe/manifestar", b.handleFiscalManifest)'''
if old not in s: raise SystemExit('rota consultar ausente no mux')
s=s.replace(old,new,1)

for tok in (MARK,'/fiscal/nfe/manifestar','handleFiscalManifest','req.Event != "210210"','"manifest", "--key", req.Key','"--event", "210210"','queueXMLFromFiscalResult'):
    if tok not in s: raise SystemExit('Manifestação broker incompleta: '+tok)
s=s.rstrip()+"\n// "+MARK+" — Ciência 210210 protegida e XML encaminhado ao Visualizador.\n"
p.write_text(s,encoding='utf-8',newline='\n')
print('3.13.0: Ciência da Operação conectada ao broker local.')
