from pathlib import Path

p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')
MARK='CSM_NFE_ACTIONS_3130'
if MARK in s:
    print('Ações NF-e 3.13.0 já aplicadas')
    raise SystemExit(0)
if 'CSM_LAUNCHER_MANIFESTACAO_3130' not in s:
    raise SystemExit('Aplique o broker de manifestação antes')

# runtime é usado para manter o diálogo do Windows no mesmo OS thread.
if '"runtime"' not in s:
    s=s.replace('    "path/filepath"\n','    "path/filepath"\n    "runtime"\n',1)

# Comdlg32.
old='''    kernel32 = syscall.NewLazyDLL("kernel32.dll")\n    user32   = syscall.NewLazyDLL("user32.dll")'''
new='''    kernel32  = syscall.NewLazyDLL("kernel32.dll")\n    user32    = syscall.NewLazyDLL("user32.dll")\n    comdlg32  = syscall.NewLazyDLL("comdlg32.dll")'''
if old not in s: raise SystemExit('DLL vars não localizadas')
s=s.replace(old,new,1)
old='''    procMessageBoxW              = user32.NewProc("MessageBoxW")\n)'''
new='''    procMessageBoxW              = user32.NewProc("MessageBoxW")\n    procGetSaveFileNameW         = comdlg32.NewProc("GetSaveFileNameW")\n)'''
if old not in s: raise SystemExit('proc vars não localizadas')
s=s.replace(old,new,1)

# Estrutura Win32 OPENFILENAMEW.
anchor='type rect struct{ Left, Top, Right, Bottom int32 }\n'
struct=r'''type openFileNameW struct {
    LStructSize       uint32
    HwndOwner         uintptr
    HInstance         uintptr
    LpstrFilter       *uint16
    LpstrCustomFilter *uint16
    NMaxCustFilter    uint32
    NFilterIndex      uint32
    LpstrFile         *uint16
    NMaxFile          uint32
    LpstrFileTitle    *uint16
    NMaxFileTitle     uint32
    LpstrInitialDir   *uint16
    LpstrTitle        *uint16
    Flags              uint32
    NFileOffset        uint16
    NFileExtension     uint16
    LpstrDefExt       *uint16
    LCustData          uintptr
    LpfnHook           uintptr
    LpTemplateName     *uint16
    PvReserved         uintptr
    DwReserved         uint32
    FlagsEx            uint32
}

'''
if anchor not in s: raise SystemExit('rect não localizado')
s=s.replace(anchor,struct+anchor,1)

anchor='''func (b *broker) handleFiscalManifest(w http.ResponseWriter, r *http.Request) {'''
if anchor not in s: raise SystemExit('handleFiscalManifest ausente')
insert=r'''
func validNFeKeyText(key string) bool {
    if len(key) != 44 { return false }
    for _, ch := range key { if ch < '0' || ch > '9' { return false } }
    return true
}

func cachedNFePath(key string) (string, error) {
    if !validNFeKeyText(key) { return "", fmt.Errorf("invalid access key") }
    local, err := os.UserCacheDir()
    if err != nil || strings.TrimSpace(local) == "" { local = os.Getenv("LOCALAPPDATA") }
    dir := filepath.Join(local, "CSM Visualizador XML", "cache", "nfe")
    entries, err := os.ReadDir(dir)
    if err != nil { return "", fmt.Errorf("XML da NF-e ainda não está no cache") }
    for _, e := range entries {
        if e.IsDir() || !strings.EqualFold(filepath.Ext(e.Name()), ".xml") || !strings.Contains(e.Name(), key) { continue }
        path := filepath.Join(dir, e.Name())
        raw, err := os.ReadFile(path); if err != nil { continue }
        text := string(raw)
        if strings.Contains(text, "NFe"+key) || strings.Contains(text, "<chNFe>"+key+"</chNFe>") { return path, nil }
    }
    return "", fmt.Errorf("XML completo desta NF-e ainda não está disponível no cache")
}

func chooseXMLSavePath(defaultName string) (string, bool) {
    runtime.LockOSThread(); defer runtime.UnlockOSThread()
    var file [4096]uint16
    initial, _ := syscall.UTF16FromString(defaultName)
    copy(file[:], initial)
    title, _ := syscall.UTF16PtrFromString("Salvar XML oficial da NF-e")
    ext, _ := syscall.UTF16PtrFromString("xml")
    ofn := openFileNameW{LStructSize:uint32(unsafe.Sizeof(openFileNameW{})), LpstrFile:&file[0], NMaxFile:uint32(len(file)), LpstrTitle:title, LpstrDefExt:ext, Flags:0x00000002|0x00000800|0x00000008}
    ret,_,_ := procGetSaveFileNameW.Call(uintptr(unsafe.Pointer(&ofn)))
    if ret == 0 { return "", false }
    return syscall.UTF16ToString(file[:]), true
}

func (b *broker) handleFiscalOpenCached(w http.ResponseWriter, r *http.Request) {
    if !setFiscalCORS(w,r) { return }
    if r.Method==http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method!=http.MethodPost { http.Error(w,"method not allowed",http.StatusMethodNotAllowed); return }
    var req fiscalManifestRequest
    if err:=json.NewDecoder(io.LimitReader(r.Body,64<<10)).Decode(&req);err!=nil { http.Error(w,"invalid request",http.StatusBadRequest); return }
    req.Key=strings.TrimSpace(req.Key)
    path,err:=cachedNFePath(req.Key);if err!=nil { http.Error(w,err.Error(),http.StatusNotFound); return }
    if err:=b.ensureHealthyCore();err!=nil { http.Error(w,err.Error(),http.StatusInternalServerError); return }
    b.queuePath(path)
    w.Header().Set("Content-Type","application/json; charset=utf-8")
    _=json.NewEncoder(w).Encode(map[string]any{"ok":true,"opened":true,"key":req.Key})
}

func (b *broker) handleFiscalExportXML(w http.ResponseWriter, r *http.Request) {
    if !setFiscalCORS(w,r) { return }
    if r.Method==http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method!=http.MethodPost { http.Error(w,"method not allowed",http.StatusMethodNotAllowed); return }
    var req fiscalManifestRequest
    if err:=json.NewDecoder(io.LimitReader(r.Body,64<<10)).Decode(&req);err!=nil { http.Error(w,"invalid request",http.StatusBadRequest); return }
    req.Key=strings.TrimSpace(req.Key)
    src,err:=cachedNFePath(req.Key);if err!=nil { http.Error(w,err.Error(),http.StatusNotFound); return }
    dst,ok:=chooseXMLSavePath(filepath.Base(src));if !ok { w.Header().Set("Content-Type","application/json"); _=json.NewEncoder(w).Encode(map[string]any{"ok":false,"cancelled":true}); return }
    raw,err:=os.ReadFile(src);if err!=nil { http.Error(w,err.Error(),http.StatusInternalServerError); return }
    if err=os.WriteFile(dst,raw,0644);err!=nil { http.Error(w,err.Error(),http.StatusInternalServerError); return }
    w.Header().Set("Content-Type","application/json; charset=utf-8")
    _=json.NewEncoder(w).Encode(map[string]any{"ok":true,"saved":true,"file_name":filepath.Base(dst)})
}

'''
s=s.replace(anchor,insert+anchor,1)

old='''    mux.HandleFunc("/fiscal/nfe/manifestar", b.handleFiscalManifest)'''
new='''    mux.HandleFunc("/fiscal/nfe/manifestar", b.handleFiscalManifest)\n    mux.HandleFunc("/fiscal/nfe/open-cached", b.handleFiscalOpenCached)\n    mux.HandleFunc("/fiscal/nfe/export-xml", b.handleFiscalExportXML)'''
if old not in s: raise SystemExit('rota manifestar ausente')
s=s.replace(old,new,1)
s=s.rstrip()+"\n// "+MARK+" — reabertura do cache e Save As nativo do XML oficial.\n"
for tok in (MARK,'/fiscal/nfe/open-cached','/fiscal/nfe/export-xml','GetSaveFileNameW','cachedNFePath','os.WriteFile(dst,raw'):
    if tok not in s: raise SystemExit('Ações NF-e incompletas: '+tok)
p.write_text(s,encoding='utf-8',newline='\n')
print('3.13.0: abrir cache e Salvar XML nativo adicionados.')
