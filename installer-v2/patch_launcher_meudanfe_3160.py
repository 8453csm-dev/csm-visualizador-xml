from pathlib import Path

p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')
MARK='CSM_MEUDANFE_API_3160'
if MARK in s:
    print('Broker Meu Danfe 3.16.0 já aplicado')
    raise SystemExit(0)
if 'CSM_FISCAL_CORE_BROKER_3120' not in s:
    raise SystemExit('Broker fiscal local ausente')

anchor='type fiscalConsultRequest struct { Key string `json:"key"`; CNPJ string `json:"cnpj"` }\n'
if anchor not in s:
    raise SystemExit('Tipo fiscalConsultRequest não localizado')
s=s.replace(anchor,anchor+'''type meuDanfeConfigRequest struct { ApiKey string `json:"api_key"` }
type meuDanfeConsultRequest struct { Key string `json:"key"` }
''',1)

anchor2='func (b *broker) handleFiscalCertificates(w http.ResponseWriter, r *http.Request) {'
if anchor2 not in s:
    raise SystemExit('Handler fiscal não localizado')

block=r'''
// CSM_MEUDANFE_API_3160 — chave -> API oficial Meu Danfe -> XML -> Visualizador.
func (b *broker) meuDanfeClientPath() string {
    return filepath.Join(b.dir, "_internal", "csm", "CSM Meu Danfe Client.exe")
}

func (b *broker) runMeuDanfe(stdin string,args ...string) ([]byte,error) {
    helper:=b.meuDanfeClientPath()
    if _,err:=os.Stat(helper);err!=nil { return nil,fmt.Errorf("CSM Meu Danfe Client não encontrado: %w",err) }
    cmd:=exec.Command(helper,args...)
    cmd.Dir=b.dir
    cmd.SysProcAttr=&syscall.SysProcAttr{HideWindow:true}
    if stdin!="" { cmd.Stdin=strings.NewReader(stdin) }
    out,err:=cmd.Output()
    if len(out)>0 && json.Valid(out) { return out,nil }
    if err!=nil { return out,err }
    return out,fmt.Errorf("Meu Danfe Client retornou resposta inválida")
}

func (b *broker) handleMeuDanfeStatus(w http.ResponseWriter,r *http.Request) {
    if !setFiscalCORS(w,r) { return }
    if r.Method==http.MethodOptions { w.WriteHeader(http.StatusNoContent);return }
    if r.Method!=http.MethodGet { http.Error(w,"method not allowed",http.StatusMethodNotAllowed);return }
    out,err:=b.runMeuDanfe("","status")
    if err!=nil { http.Error(w,err.Error(),http.StatusInternalServerError);return }
    w.Header().Set("Content-Type","application/json; charset=utf-8")
    _,_=w.Write(out)
}

func (b *broker) handleMeuDanfeConfig(w http.ResponseWriter,r *http.Request) {
    if !setFiscalCORS(w,r) { return }
    if r.Method==http.MethodOptions { w.WriteHeader(http.StatusNoContent);return }
    if r.Method==http.MethodDelete {
        out,err:=b.runMeuDanfe("","clear-key")
        if err!=nil { http.Error(w,err.Error(),http.StatusInternalServerError);return }
        w.Header().Set("Content-Type","application/json; charset=utf-8");_,_=w.Write(out);return
    }
    if r.Method!=http.MethodPost { http.Error(w,"method not allowed",http.StatusMethodNotAllowed);return }
    var req meuDanfeConfigRequest
    if json.NewDecoder(io.LimitReader(r.Body,8<<10)).Decode(&req)!=nil { http.Error(w,"invalid request",http.StatusBadRequest);return }
    req.ApiKey=strings.TrimSpace(req.ApiKey)
    if len(req.ApiKey)<8 || len(req.ApiKey)>512 { http.Error(w,"Api-Key inválida",http.StatusBadRequest);return }
    out,err:=b.runMeuDanfe(req.ApiKey,"set-key")
    if err!=nil { http.Error(w,err.Error(),http.StatusInternalServerError);return }
    w.Header().Set("Content-Type","application/json; charset=utf-8");_,_=w.Write(out)
}

func (b *broker) handleMeuDanfeConsult(w http.ResponseWriter,r *http.Request) {
    if !setFiscalCORS(w,r) { return }
    if r.Method==http.MethodOptions { w.WriteHeader(http.StatusNoContent);return }
    if r.Method!=http.MethodPost { http.Error(w,"method not allowed",http.StatusMethodNotAllowed);return }
    var req meuDanfeConsultRequest
    if json.NewDecoder(io.LimitReader(r.Body,8<<10)).Decode(&req)!=nil { http.Error(w,"invalid request",http.StatusBadRequest);return }
    key:=strings.TrimSpace(req.Key)
    if !validNFeKeyText(key) { http.Error(w,"chave de acesso inválida",http.StatusBadRequest);return }

    out,err:=b.runMeuDanfe("","consult","--key",key)
    if err!=nil && len(out)==0 { http.Error(w,err.Error(),http.StatusBadGateway);return }

    var result map[string]any
    if json.Unmarshal(out,&result)==nil {
        if raw,ok:=result["xml_path"];ok {
            if path,ok:=raw.(string);ok && strings.EqualFold(filepath.Ext(path),".xml") {
                if _,statErr:=os.Stat(path);statErr==nil {
                    if e:=b.ensureHealthyCore();e==nil {
                        b.queuePath(path)
                        result["opened"]=true
                        if updated,e2:=json.Marshal(result);e2==nil { out=updated }
                    }
                }
            }
        }
    }
    w.Header().Set("Content-Type","application/json; charset=utf-8")
    _,_=w.Write(out)
}

'''
s=s.replace(anchor2,block+anchor2,1)

mux='''    mux.HandleFunc("/fiscal/certificates", b.handleFiscalCertificates)'''
if mux not in s: raise SystemExit('Rota fiscal não localizada')
s=s.replace(mux,'''    mux.HandleFunc("/provider/meudanfe/status", b.handleMeuDanfeStatus)
    mux.HandleFunc("/provider/meudanfe/config", b.handleMeuDanfeConfig)
    mux.HandleFunc("/provider/meudanfe/consult", b.handleMeuDanfeConsult)
    mux.HandleFunc("/fiscal/certificates", b.handleFiscalCertificates)''',1)

s=s.rstrip()+"\n// "+MARK+" — Api-Key no Credential Manager; XML validado abre pelo pipeline normal do CSM.\n"
for tok in (MARK,'/provider/meudanfe/status','/provider/meudanfe/config','/provider/meudanfe/consult','CSM Meu Danfe Client.exe','handleMeuDanfeConsult'):
    if tok not in s: raise SystemExit('Broker Meu Danfe 3.16.0 incompleto: '+tok)
p.write_text(s,encoding='utf-8',newline='\n')
print('3.16.0: broker Meu Danfe API integrado com Credential Manager e abertura automática do XML.')
