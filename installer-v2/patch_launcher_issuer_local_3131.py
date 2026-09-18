from pathlib import Path

p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')
MARK='CSM_ISSUER_LOCAL_XML_3131'
if MARK in s:
    print('Fontes XML locais 3.13.1 já aplicadas')
    raise SystemExit(0)
if 'CSM_NFE_ACTIONS_3130' not in s:
    raise SystemExit('Aplique as ações NF-e 3.13.0 antes')

anchor='''func (b *broker) handleFiscalManifest(w http.ResponseWriter, r *http.Request) {'''
if anchor not in s: raise SystemExit('handleFiscalManifest não localizado')

insert=r'''
type fiscalXMLFolderRequest struct { Path string `json:"path"` }

func fiscalXMLFolderConfigPath() string {
    base := strings.TrimSpace(os.Getenv("LOCALAPPDATA"))
    if base == "" {
        if v, err := os.UserConfigDir(); err == nil { base = v }
    }
    return filepath.Join(base, "CSM Visualizador XML", "xml-folders.json")
}

func loadFiscalXMLFolders() []string {
    path := fiscalXMLFolderConfigPath()
    raw, err := os.ReadFile(path)
    if err != nil { return nil }
    var state struct { Folders []string `json:"folders"` }
    if json.Unmarshal(raw, &state) != nil { return nil }
    seen := map[string]bool{}
    out := make([]string,0,len(state.Folders))
    for _, v := range state.Folders {
        v = strings.TrimSpace(v)
        if v == "" { continue }
        if abs, err := filepath.Abs(v); err == nil { v = abs }
        v = filepath.Clean(v)
        key := strings.ToLower(v)
        if !seen[key] { seen[key]=true; out=append(out,v) }
    }
    return out
}

func saveFiscalXMLFolders(folders []string) error {
    clean := make([]string,0,len(folders)); seen:=map[string]bool{}
    for _, v := range folders {
        v=strings.TrimSpace(v); if v=="" { continue }
        if abs,err:=filepath.Abs(v);err==nil { v=abs }
        v=filepath.Clean(v); key:=strings.ToLower(v)
        if !seen[key] { seen[key]=true; clean=append(clean,v) }
    }
    path:=fiscalXMLFolderConfigPath()
    if err:=os.MkdirAll(filepath.Dir(path),0755);err!=nil { return err }
    raw,_:=json.MarshalIndent(map[string]any{"folders":clean},"","  ")
    return os.WriteFile(path,raw,0644)
}

func xmlBytesMatchNFeKey(raw []byte, key string) bool {
    if !validNFeKeyText(key) || len(raw)==0 { return false }
    text:=string(raw)
    return strings.Contains(text,"NFe"+key) || strings.Contains(text,"<chNFe>"+key+"</chNFe>")
}

func verifyLocalNFeXML(path,key string) ([]byte,error) {
    if !strings.EqualFold(filepath.Ext(path),".xml") { return nil,fmt.Errorf("o arquivo selecionado não é XML") }
    st,err:=os.Stat(path);if err!=nil { return nil,err }
    if st.IsDir() || st.Size()<=0 || st.Size()>32*1024*1024 { return nil,fmt.Errorf("XML inválido ou grande demais") }
    raw,err:=os.ReadFile(path);if err!=nil { return nil,err }
    if !xmlBytesMatchNFeKey(raw,key) { return nil,fmt.Errorf("o XML não corresponde à chave consultada") }
    return raw,nil
}

func findLocalNFeXML(key string) (string,[]byte,error) {
    if !validNFeKeyText(key) { return "",nil,fmt.Errorf("chave inválida") }
    folders:=loadFiscalXMLFolders()
    if len(folders)==0 { return "",nil,fmt.Errorf("nenhuma pasta de XML foi configurada") }
    const foundSignal="__CSM_LOCAL_XML_FOUND__"
    var found string
    var raw []byte
    for _, root:=range folders {
        if st,err:=os.Stat(root);err!=nil || !st.IsDir() { continue }
        err:=filepath.Walk(root,func(path string,info os.FileInfo,walkErr error) error {
            if walkErr!=nil || info==nil { return nil }
            if info.IsDir() { return nil }
            if !strings.EqualFold(filepath.Ext(path),".xml") { return nil }
            if info.Size()<=0 || info.Size()>32*1024*1024 { return nil }
            candidate,err:=os.ReadFile(path);if err!=nil { return nil }
            if xmlBytesMatchNFeKey(candidate,key) {
                found=path;raw=candidate
                return fmt.Errorf(foundSignal)
            }
            return nil
        })
        if found!="" { return found,raw,nil }
        if err!=nil && err.Error()!=foundSignal { continue }
    }
    return "",nil,fmt.Errorf("XML não localizado nas pastas configuradas")
}

func cacheAndOpenLocalNFe(b *broker,key,source string,raw []byte) (string,error) {
    if !xmlBytesMatchNFeKey(raw,key) { return "",fmt.Errorf("XML não corresponde à chave consultada") }
    base,err:=os.UserCacheDir();if err!=nil || strings.TrimSpace(base)=="" { base=os.Getenv("LOCALAPPDATA") }
    dir:=filepath.Join(base,"CSM Visualizador XML","cache","nfe")
    if err:=os.MkdirAll(dir,0755);err!=nil { return "",err }
    dst:=filepath.Join(dir,"NF-e LOCAL - "+key+".xml")
    if err:=os.WriteFile(dst,raw,0644);err!=nil { return "",err }
    if err:=b.ensureHealthyCore();err!=nil { return "",err }
    b.queuePath(dst)
    _=source
    return dst,nil
}

func chooseNFeXMLFile() (string,bool) {
    runtime.LockOSThread(); defer runtime.UnlockOSThread()
    var file [4096]uint16
    title,_:=syscall.UTF16PtrFromString("Selecionar XML da NF-e")
    ofn:=openFileNameW{LStructSize:uint32(unsafe.Sizeof(openFileNameW{})),LpstrFile:&file[0],NMaxFile:uint32(len(file)),LpstrTitle:title,Flags:0x00001000|0x00000800|0x00000008}
    ret,_,_:=procGetOpenFileNameW.Call(uintptr(unsafe.Pointer(&ofn)))
    if ret==0 { return "",false }
    path:=syscall.UTF16ToString(file[:])
    if !strings.EqualFold(filepath.Ext(path),".xml") { return "",false }
    return path,true
}

func (b *broker) handleFiscalXMLFolders(w http.ResponseWriter,r *http.Request) {
    if !setFiscalCORS(w,r) { return }
    if r.Method==http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method!=http.MethodGet { http.Error(w,"method not allowed",http.StatusMethodNotAllowed);return }
    w.Header().Set("Content-Type","application/json; charset=utf-8")
    _=json.NewEncoder(w).Encode(map[string]any{"ok":true,"folders":loadFiscalXMLFolders()})
}

func (b *broker) handleFiscalXMLFolderAdd(w http.ResponseWriter,r *http.Request) {
    if !setFiscalCORS(w,r) { return }
    if r.Method==http.MethodOptions { w.WriteHeader(http.StatusNoContent);return }
    if r.Method!=http.MethodPost { http.Error(w,"method not allowed",http.StatusMethodNotAllowed);return }
    var req fiscalXMLFolderRequest
    if json.NewDecoder(io.LimitReader(r.Body,64<<10)).Decode(&req)!=nil { http.Error(w,"invalid request",http.StatusBadRequest);return }
    path:=strings.TrimSpace(req.Path);if path=="" { http.Error(w,"path required",http.StatusBadRequest);return }
    if abs,err:=filepath.Abs(path);err==nil { path=abs };path=filepath.Clean(path)
    if st,err:=os.Stat(path);err!=nil || !st.IsDir() { http.Error(w,"pasta não encontrada",http.StatusBadRequest);return }
    folders:=loadFiscalXMLFolders()
    exists:=false;for _,f:=range folders { if strings.EqualFold(f,path) { exists=true;break } }
    if !exists { folders=append(folders,path) }
    if err:=saveFiscalXMLFolders(folders);err!=nil { http.Error(w,err.Error(),http.StatusInternalServerError);return }
    w.Header().Set("Content-Type","application/json; charset=utf-8")
    _=json.NewEncoder(w).Encode(map[string]any{"ok":true,"folders":loadFiscalXMLFolders()})
}

func (b *broker) handleFiscalFindLocalXML(w http.ResponseWriter,r *http.Request) {
    if !setFiscalCORS(w,r) { return }
    if r.Method==http.MethodOptions { w.WriteHeader(http.StatusNoContent);return }
    if r.Method!=http.MethodPost { http.Error(w,"method not allowed",http.StatusMethodNotAllowed);return }
    var req fiscalManifestRequest
    if json.NewDecoder(io.LimitReader(r.Body,64<<10)).Decode(&req)!=nil { http.Error(w,"invalid request",http.StatusBadRequest);return }
    key:=strings.TrimSpace(req.Key)
    if cached,err:=cachedNFePath(key);err==nil {
        if raw,e:=os.ReadFile(cached);e==nil && xmlBytesMatchNFeKey(raw,key) {
            if err:=b.ensureHealthyCore();err==nil { b.queuePath(cached) }
            w.Header().Set("Content-Type","application/json; charset=utf-8")
            _=json.NewEncoder(w).Encode(map[string]any{"ok":true,"xml_available":true,"opened":true,"source":"cache","file_name":filepath.Base(cached)})
            return
        }
    }
    src,raw,err:=findLocalNFeXML(key)
    if err!=nil {
        w.Header().Set("Content-Type","application/json; charset=utf-8")
        _=json.NewEncoder(w).Encode(map[string]any{"ok":true,"xml_available":false,"message":err.Error()})
        return
    }
    dst,err:=cacheAndOpenLocalNFe(b,key,src,raw);if err!=nil { http.Error(w,err.Error(),http.StatusInternalServerError);return }
    w.Header().Set("Content-Type","application/json; charset=utf-8")
    _=json.NewEncoder(w).Encode(map[string]any{"ok":true,"xml_available":true,"opened":true,"local_source":true,"source":"pasta XML local","file_name":filepath.Base(dst)})
}

func (b *broker) handleFiscalPickLocalXML(w http.ResponseWriter,r *http.Request) {
    if !setFiscalCORS(w,r) { return }
    if r.Method==http.MethodOptions { w.WriteHeader(http.StatusNoContent);return }
    if r.Method!=http.MethodPost { http.Error(w,"method not allowed",http.StatusMethodNotAllowed);return }
    var req fiscalManifestRequest
    if json.NewDecoder(io.LimitReader(r.Body,64<<10)).Decode(&req)!=nil { http.Error(w,"invalid request",http.StatusBadRequest);return }
    key:=strings.TrimSpace(req.Key)
    src,ok:=chooseNFeXMLFile();if !ok {
        w.Header().Set("Content-Type","application/json");_=json.NewEncoder(w).Encode(map[string]any{"ok":false,"cancelled":true});return
    }
    raw,err:=verifyLocalNFeXML(src,key);if err!=nil { http.Error(w,err.Error(),http.StatusBadRequest);return }
    folders:=loadFiscalXMLFolders();dir:=filepath.Dir(src);exists:=false
    for _,f:=range folders { if strings.EqualFold(f,dir) { exists=true;break } }
    if !exists { folders=append(folders,dir);_=saveFiscalXMLFolders(folders) }
    dst,err:=cacheAndOpenLocalNFe(b,key,src,raw);if err!=nil { http.Error(w,err.Error(),http.StatusInternalServerError);return }
    w.Header().Set("Content-Type","application/json; charset=utf-8")
    _=json.NewEncoder(w).Encode(map[string]any{"ok":true,"xml_available":true,"opened":true,"local_source":true,"source":"XML selecionado","file_name":filepath.Base(dst)})
}

'''
s=s.replace(anchor,insert+anchor,1)

old='''    mux.HandleFunc("/fiscal/nfe/manifestar", b.handleFiscalManifest)
    mux.HandleFunc("/fiscal/nfe/open-cached", b.handleFiscalOpenCached)
    mux.HandleFunc("/fiscal/nfe/export-xml", b.handleFiscalExportXML)
    mux.HandleFunc("/fiscal/certificate/pick", b.handleFiscalCertificatePick)'''
new='''    mux.HandleFunc("/fiscal/nfe/manifestar", b.handleFiscalManifest)
    mux.HandleFunc("/fiscal/nfe/open-cached", b.handleFiscalOpenCached)
    mux.HandleFunc("/fiscal/nfe/export-xml", b.handleFiscalExportXML)
    mux.HandleFunc("/fiscal/nfe/find-local", b.handleFiscalFindLocalXML)
    mux.HandleFunc("/fiscal/nfe/pick-local", b.handleFiscalPickLocalXML)
    mux.HandleFunc("/fiscal/xml-folders", b.handleFiscalXMLFolders)
    mux.HandleFunc("/fiscal/xml-folders/add", b.handleFiscalXMLFolderAdd)
    mux.HandleFunc("/fiscal/certificate/pick", b.handleFiscalCertificatePick)'''
if old not in s: raise SystemExit('Rotas NF-e 3.13.0 não localizadas')
s=s.replace(old,new,1)

s=s.rstrip()+"\n// "+MARK+" — NF-e própria busca XML original em fontes locais/SIEG e abre no Visualizador.\n"
for tok in (MARK,'/fiscal/nfe/find-local','/fiscal/nfe/pick-local','/fiscal/xml-folders/add','findLocalNFeXML','cacheAndOpenLocalNFe'):
    if tok not in s: raise SystemExit('Patch launcher 3.13.1 incompleto: '+tok)
p.write_text(s,encoding='utf-8',newline='\n')
print('3.13.1: fontes XML locais/SIEG e abertura de NF-e própria adicionadas ao launcher.')
