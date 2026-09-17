from pathlib import Path

p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')
MARK='CSM_LAUNCHER_CERT_MANAGER_3130'
if MARK in s:
    print('Broker de certificados 3.13.0 já aplicado')
    raise SystemExit(0)
if 'CSM_FISCAL_CORE_BROKER_3120' not in s:
    raise SystemExit('Aplique patch_launcher_fiscal_core_3120.py antes')

anchor='type fiscalConsultRequest struct { Key string `json:"key"`; CNPJ string `json:"cnpj"` }\n'
if anchor not in s: raise SystemExit('fiscalConsultRequest ausente')
s=s.replace(anchor, anchor + '''type fiscalFolderRequest struct { Path string `json:"path"` }\ntype fiscalCertificateValidateRequest struct { Path string `json:"path"`; Password string `json:"password"` }\n''',1)

anchor='''func (b *broker) handleFiscalCertificates(w http.ResponseWriter, r *http.Request) {'''
if anchor not in s: raise SystemExit('handleFiscalCertificates ausente')
insert=r'''
func (b *broker) runFiscalCoreWithInput(input string, args ...string) ([]byte, error) {
    helper := b.fiscalCorePath()
    if _, err := os.Stat(helper); err != nil { return nil, fmt.Errorf("CSM Fiscal Core não encontrado: %w", err) }
    cmd := exec.Command(helper, args...)
    cmd.Dir = b.dir
    cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
    cmd.Stdin = strings.NewReader(input)
    out, err := cmd.Output()
    if len(out) > 0 && json.Valid(out) { return out, nil }
    if err != nil { return out, err }
    if !json.Valid(out) { return out, fmt.Errorf("CSM Fiscal Core retornou resposta inválida") }
    return out, nil
}

func writeFiscalJSON(w http.ResponseWriter, out []byte, err error) {
    if err != nil { http.Error(w, err.Error(), http.StatusInternalServerError); return }
    w.Header().Set("Content-Type", "application/json; charset=utf-8")
    _, _ = w.Write(out)
}

func (b *broker) handleFiscalCertificateFolders(w http.ResponseWriter, r *http.Request) {
    if !setFiscalCORS(w, r) { return }
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodGet { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }
    out, err := b.runFiscalCore("folders", "list")
    writeFiscalJSON(w, out, err)
}

func (b *broker) handleFiscalCertificateFolderMutation(op string, w http.ResponseWriter, r *http.Request) {
    if !setFiscalCORS(w, r) { return }
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }
    var req fiscalFolderRequest
    if err := json.NewDecoder(io.LimitReader(r.Body, 64<<10)).Decode(&req); err != nil { http.Error(w, "invalid request", http.StatusBadRequest); return }
    req.Path = strings.TrimSpace(req.Path)
    if req.Path == "" { http.Error(w, "path required", http.StatusBadRequest); return }
    out, err := b.runFiscalCore("folders", op, "--path", req.Path)
    writeFiscalJSON(w, out, err)
}

func (b *broker) handleFiscalCertificateFolderAdd(w http.ResponseWriter, r *http.Request) {
    b.handleFiscalCertificateFolderMutation("add", w, r)
}
func (b *broker) handleFiscalCertificateFolderRemove(w http.ResponseWriter, r *http.Request) {
    b.handleFiscalCertificateFolderMutation("remove", w, r)
}

func (b *broker) handleFiscalCertificatesScan(w http.ResponseWriter, r *http.Request) {
    if !setFiscalCORS(w, r) { return }
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }
    out, err := b.runFiscalCore("scan")
    writeFiscalJSON(w, out, err)
}

func (b *broker) handleFiscalCertificateValidate(w http.ResponseWriter, r *http.Request) {
    if !setFiscalCORS(w, r) { return }
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }
    var req fiscalCertificateValidateRequest
    if err := json.NewDecoder(io.LimitReader(r.Body, 64<<10)).Decode(&req); err != nil { http.Error(w, "invalid request", http.StatusBadRequest); return }
    req.Path = strings.TrimSpace(req.Path)
    if req.Path == "" { http.Error(w, "path required", http.StatusBadRequest); return }
    out, err := b.runFiscalCoreWithInput(req.Password, "cert", "validate", "--path", req.Path)
    req.Password = ""
    writeFiscalJSON(w, out, err)
}

'''
s=s.replace(anchor,insert+anchor,1)

old='''    mux.HandleFunc("/fiscal/certificates", b.handleFiscalCertificates)\n    mux.HandleFunc("/fiscal/nfe/consultar", b.handleFiscalConsult)'''
new='''    mux.HandleFunc("/fiscal/certificates", b.handleFiscalCertificates)\n    mux.HandleFunc("/fiscal/certificate-folders", b.handleFiscalCertificateFolders)\n    mux.HandleFunc("/fiscal/certificate-folders/add", b.handleFiscalCertificateFolderAdd)\n    mux.HandleFunc("/fiscal/certificate-folders/remove", b.handleFiscalCertificateFolderRemove)\n    mux.HandleFunc("/fiscal/certificates/scan", b.handleFiscalCertificatesScan)\n    mux.HandleFunc("/fiscal/certificate/validate", b.handleFiscalCertificateValidate)\n    mux.HandleFunc("/fiscal/nfe/consultar", b.handleFiscalConsult)'''
if old not in s: raise SystemExit('Registro fiscal no mux não localizado')
s=s.replace(old,new,1)

s=s.rstrip()+"\n// "+MARK+" — gestão A1 local; senha transmitida ao child somente por stdin.\n"
p.write_text(s,encoding='utf-8',newline='\n')
print('3.13.0: endpoints locais de certificados adicionados ao broker.')
