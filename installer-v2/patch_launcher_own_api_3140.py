from pathlib import Path

p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')
MARK='CSM_OWN_NFE_API_3140'
if MARK in s:
    print('CSM Consulta NF-e API 3.14.0 já aplicada')
    raise SystemExit(0)
if 'CSM_ISSUER_LOCAL_XML_3131' not in s:
    raise SystemExit('Aplique launcher 3.13.1 antes')
if 'CSM_FISCAL_CORE_BROKER_3120' not in s:
    raise SystemExit('Broker Fiscal Core ausente')

# Indexa automaticamente todo XML NF-e que passa pelo pipeline normal.
old='''func (b *broker) queuePath(path string) {
    path = strings.TrimSpace(path)
    if path == "" { return }'''
new='''func (b *broker) queuePath(path string) {
    path = strings.TrimSpace(path)
    if path == "" { return }
    indexNFeFileInRepository(path)'''
if old not in s: raise SystemExit('queuePath não localizado')
s=s.replace(old,new,1)

anchor='''func (b *broker) handleFiscalManifest(w http.ResponseWriter, r *http.Request) {'''
if anchor not in s: raise SystemExit('handleFiscalManifest não localizado')

block=r'''
// CSM_OWN_NFE_API_3140 — nossa API local: chave -> Base CSM -> XML -> aba.
var csmRepositorySyncMu sync.Mutex
var csmRepositorySyncRunning bool
var csmRepositorySyncStarted time.Time
var csmRepositorySyncFinished time.Time
var csmRepositorySyncLastError string
var csmRepositorySyncProcessed int

func csmRepositoryRoot() string {
    base:=strings.TrimSpace(os.Getenv("LOCALAPPDATA"))
    if base=="" { if v,err:=os.UserConfigDir();err==nil { base=v } }
    return filepath.Join(base,"CSM Visualizador XML","repository")
}
func csmRepositoryNFeDir() string { return filepath.Join(csmRepositoryRoot(),"nfe") }
func csmRepositoryXMLPath(key string) string { return filepath.Join(csmRepositoryNFeDir(),key+".xml") }

func extractNFeKeyFromText(text string) string {
    markers:=[]string{"Id=\"NFe","Id='NFe","<chNFe>"}
    for _,m:=range markers {
        pos:=strings.Index(text,m);if pos<0 { continue }
        start:=pos+len(m)
        if m=="<chNFe>" { start=pos+len(m) }
        if start+44>len(text) { continue }
        key:=text[start:start+44]
        if validNFeKeyText(key) { return key }
    }
    return ""
}

func indexNFeFileInRepository(path string) {
    if !strings.EqualFold(filepath.Ext(path),".xml") { return }
    st,err:=os.Stat(path);if err!=nil || st.IsDir() || st.Size()<=0 || st.Size()>32*1024*1024 { return }
    raw,err:=os.ReadFile(path);if err!=nil { return }
    text:=string(raw)
    if !strings.Contains(text,"<NFe") && !strings.Contains(text,"<nfeProc") { return }
    key:=extractNFeKeyFromText(text);if key=="" { return }
    dir:=csmRepositoryNFeDir();if os.MkdirAll(dir,0755)!=nil { return }
    dst:=csmRepositoryXMLPath(key)
    if same,err:=filepath.Abs(path);err==nil {
        if target,e:=filepath.Abs(dst);e==nil && strings.EqualFold(same,target) { return }
    }
    _=os.WriteFile(dst,raw,0644)
}

func repositoryLookup(b *broker,key string) map[string]any {
    if !validNFeKeyText(key) { return map[string]any{"ok":false,"message":"Chave de acesso inválida."} }
    // 1. Base CSM construída pelo distNSU e pelos XMLs já abertos.
    if out,err:=b.runFiscalCore("repo","get","--key",key);err==nil {
        var data map[string]any
        if json.Unmarshal(out,&data)==nil {
            if available,_:=data["xml_available"].(bool);available {
                if p,_:=data["xml_path"].(string);p!="" {
                    if _,err:=os.Stat(p);err==nil {
                        if b.ensureHealthyCore()==nil { b.queuePath(p) }
                        data["opened"]=true
                        data["api"]="CSM Consulta NF-e"
                        return data
                    }
                }
            }
            if found,_:=data["found"].(bool);found {
                data["api"]="CSM Consulta NF-e"
                return data
            }
        }
    }
    // 2. Fontes locais/SIEG: se achar, valida a chave e incorpora à Base CSM.
    if src,raw,err:=findLocalNFeXML(key);err==nil && src!="" {
        if dst,e:=cacheAndOpenLocalNFe(b,key,src,raw);e==nil {
            indexNFeFileInRepository(dst)
            return map[string]any{"ok":true,"found":true,"xml_available":true,"opened":true,"key":key,"source":"Base CSM • XML local/SIEG","api":"CSM Consulta NF-e"}
        }
    }
    return map[string]any{"ok":true,"found":false,"xml_available":false,"key":key,"syncing":repositorySyncIsRunning(),"source":"Base CSM","api":"CSM Consulta NF-e","message":"Esta chave ainda não está indexada na Base CSM. A sincronização oficial DF-e continuará em segundo plano."}
}

func repositorySyncIsRunning() bool {
    csmRepositorySyncMu.Lock();defer csmRepositorySyncMu.Unlock()
    return csmRepositorySyncRunning
}

func (b *broker) repositorySyncPass() {
    csmRepositorySyncMu.Lock()
    if csmRepositorySyncRunning { csmRepositorySyncMu.Unlock();return }
    csmRepositorySyncRunning=true;csmRepositorySyncStarted=time.Now();csmRepositorySyncLastError="";csmRepositorySyncProcessed=0
    csmRepositorySyncMu.Unlock()
    defer func(){csmRepositorySyncMu.Lock();csmRepositorySyncRunning=false;csmRepositorySyncFinished=time.Now();csmRepositorySyncMu.Unlock()}()

    out,err:=b.runFiscalCore("list")
    if err!=nil {
        csmRepositorySyncMu.Lock();csmRepositorySyncLastError=err.Error();csmRepositorySyncMu.Unlock();return
    }
    var listing struct {
        Certificates []struct {
            CNPJ string `json:"cnpj"`
            Available bool `json:"available"`
            Status string `json:"status"`
        } `json:"certificates"`
    }
    if json.Unmarshal(out,&listing)!=nil { return }
    seen:=map[string]bool{}
    for _,cert:=range listing.Certificates {
        cnpj:=strings.TrimSpace(cert.CNPJ)
        if len(cnpj)!=14 || seen[cnpj] || !cert.Available { continue }
        seen[cnpj]=true
        _,syncErr:=b.runFiscalCore("sync","--cnpj",cnpj,"--batches","3")
        csmRepositorySyncMu.Lock()
        csmRepositorySyncProcessed++
        if syncErr!=nil { csmRepositorySyncLastError=syncErr.Error() }
        csmRepositorySyncMu.Unlock()
        time.Sleep(180*time.Millisecond)
    }
}

func (b *broker) repositorySyncLoop() {
    // Dá prioridade à abertura da interface e só depois inicia a base.
    time.Sleep(12*time.Second)
    for {
        b.repositorySyncPass()
        time.Sleep(20*time.Minute)
    }
}

func (b *broker) handleCSMNFeByKey(w http.ResponseWriter,r *http.Request) {
    if !setFiscalCORS(w,r) { return }
    if r.Method==http.MethodOptions { w.WriteHeader(http.StatusNoContent);return }
    if r.Method!=http.MethodPost { http.Error(w,"method not allowed",http.StatusMethodNotAllowed);return }
    var req fiscalManifestRequest
    if json.NewDecoder(io.LimitReader(r.Body,64<<10)).Decode(&req)!=nil { http.Error(w,"invalid request",http.StatusBadRequest);return }
    key:=strings.TrimSpace(req.Key)
    data:=repositoryLookup(b,key)
    if ok,_:=data["ok"].(bool);ok {
        if found,_:=data["found"].(bool);!found && !repositorySyncIsRunning() { go b.repositorySyncPass(); data["syncing"]=true }
    }
    w.Header().Set("Content-Type","application/json; charset=utf-8")
    _=json.NewEncoder(w).Encode(data)
}

func (b *broker) handleCSMRepositorySync(w http.ResponseWriter,r *http.Request) {
    if !setFiscalCORS(w,r) { return }
    if r.Method==http.MethodOptions { w.WriteHeader(http.StatusNoContent);return }
    if r.Method!=http.MethodPost { http.Error(w,"method not allowed",http.StatusMethodNotAllowed);return }
    if !repositorySyncIsRunning() { go b.repositorySyncPass() }
    w.Header().Set("Content-Type","application/json; charset=utf-8")
    _=json.NewEncoder(w).Encode(map[string]any{"ok":true,"started":true,"running":true})
}

func (b *broker) handleCSMRepositoryStatus(w http.ResponseWriter,r *http.Request) {
    if !setFiscalCORS(w,r) { return }
    if r.Method==http.MethodOptions { w.WriteHeader(http.StatusNoContent);return }
    if r.Method!=http.MethodGet { http.Error(w,"method not allowed",http.StatusMethodNotAllowed);return }
    stats:=map[string]any{}
    if out,err:=b.runFiscalCore("repo","stats");err==nil { _=json.Unmarshal(out,&stats) }
    csmRepositorySyncMu.Lock()
    stats["sync_running"]=csmRepositorySyncRunning
    stats["sync_started"]=csmRepositorySyncStarted.Format(time.RFC3339)
    stats["sync_finished"]=csmRepositorySyncFinished.Format(time.RFC3339)
    stats["sync_processed"]=csmRepositorySyncProcessed
    stats["sync_error"]=csmRepositorySyncLastError
    csmRepositorySyncMu.Unlock()
    stats["ok"]=true;stats["api"]="CSM Consulta NF-e"
    w.Header().Set("Content-Type","application/json; charset=utf-8")
    _=json.NewEncoder(w).Encode(stats)
}

'''
s=s.replace(anchor,block+anchor,1)

old='''    mux.HandleFunc("/fiscal/nfe/manifestar", b.handleFiscalManifest)'''
new='''    mux.HandleFunc("/api/nfe/by-key", b.handleCSMNFeByKey)
    mux.HandleFunc("/api/nfe/repository/sync", b.handleCSMRepositorySync)
    mux.HandleFunc("/api/nfe/repository/status", b.handleCSMRepositoryStatus)
    mux.HandleFunc("/fiscal/nfe/manifestar", b.handleFiscalManifest)'''
if old not in s: raise SystemExit('Rota manifestação não localizada')
s=s.replace(old,new,1)

# Inicia a alimentação automática sem bloquear o app.
old='''    go b.supervise()

    if err := b.adoptOrStartCore(); err != nil {'''
new='''    go b.supervise()
    go b.repositorySyncLoop()

    if err := b.adoptOrStartCore(); err != nil {'''
if old not in s: raise SystemExit('Inicialização do broker não localizada')
s=s.replace(old,new,1)

s=s.rstrip()+"\n// "+MARK+" — chave simples usa nossa Base CSM; distNSU alimenta o repositório em segundo plano.\n"
for tok in (MARK,'/api/nfe/by-key','/api/nfe/repository/sync','repositorySyncLoop','repositoryLookup','indexNFeFileInRepository'):
    if tok not in s: raise SystemExit('Launcher/API 3.14.0 incompleto: '+tok)
p.write_text(s,encoding='utf-8',newline='\n')
print('3.14.0: CSM Consulta NF-e API própria + Base CSM + sync em segundo plano aplicados.')
