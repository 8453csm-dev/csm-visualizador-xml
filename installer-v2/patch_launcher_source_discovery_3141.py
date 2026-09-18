from pathlib import Path

p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')
MARK='CSM_XML_SOURCE_DISCOVERY_3141'
if MARK in s:
    print('Descoberta automática XML/SIEG 3.14.1 já aplicada')
    raise SystemExit(0)
if 'CSM_OWN_NFE_API_3140' not in s:
    raise SystemExit('Aplique a API própria 3.14.0 antes')

old=r'''func findLocalNFeXML(key string) (string,[]byte,error) {
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
}'''

new=r'''func onlyDigitsText(v string) string {
    var b strings.Builder
    for _,r:=range v { if r>='0' && r<='9' { b.WriteRune(r) } }
    return b.String()
}

func existingXMLSourceRoots() []string {
    roots:=append([]string{},loadFiscalXMLFolders()...)
    if env:=strings.TrimSpace(os.Getenv("CSM_SIEG_ROOT"));env!="" { roots=append(roots,env) }
    // Descoberta genérica: em escritórios o SIEG costuma estar em unidade mapeada.
    // Não hardcodamos letra de unidade; testamos C:..Z: e só usamos o que realmente existe.
    for drive:='C';drive<='Z';drive++ {
        roots=append(roots,fmt.Sprintf("%c:\\SIEG",drive))
    }
    seen:=map[string]bool{};out:=make([]string,0,len(roots))
    for _,root:=range roots {
        root=strings.TrimSpace(root);if root=="" { continue }
        root=filepath.Clean(root)
        key:=strings.ToLower(root);if seen[key] { continue }
        st,err:=os.Stat(root);if err!=nil || !st.IsDir() { continue }
        seen[key]=true;out=append(out,root)
    }
    return out
}

func sourceSearchRootsForKey(root,key string) []string {
    issuer:=""
    if len(key)>=20 { issuer=key[6:20] }
    out:=[]string{}
    seen:=map[string]bool{}
    add:=func(v string){
        v=filepath.Clean(v);k:=strings.ToLower(v)
        if seen[k] { return }
        if st,err:=os.Stat(v);err==nil && st.IsDir() { seen[k]=true;out=append(out,v) }
    }
    if issuer!="" {
        add(filepath.Join(root,issuer))
        if entries,err:=os.ReadDir(root);err==nil {
            for _,entry:=range entries {
                if !entry.IsDir() { continue }
                if onlyDigitsText(entry.Name())==issuer { add(filepath.Join(root,entry.Name())) }
            }
        }
    }
    // Fallback para estruturas que não separam por CNPJ.
    add(root)
    return out
}

func readXMLIfMatches(path,key string,info os.FileInfo) ([]byte,bool) {
    if info==nil || info.IsDir() || !strings.EqualFold(filepath.Ext(path),".xml") { return nil,false }
    if info.Size()<=0 || info.Size()>32*1024*1024 { return nil,false }

    // Primeiro tenta o nome do arquivo e só então lê o conteúdo.
    if strings.Contains(info.Name(),key) {
        raw,err:=os.ReadFile(path);if err==nil && xmlBytesMatchNFeKey(raw,key) { return raw,true }
    }

    // A chave da NF-e aparece no início do XML. Lemos só 64 KiB para filtrar,
    // evitando carregar milhares de XMLs inteiros em compartilhamentos de rede.
    f,err:=os.Open(path);if err!=nil { return nil,false }
    head:=make([]byte,64*1024);n,_:=f.Read(head);_ = f.Close()
    if n<=0 || !xmlBytesMatchNFeKey(head[:n],key) { return nil,false }
    raw,err:=os.ReadFile(path);if err!=nil || !xmlBytesMatchNFeKey(raw,key) { return nil,false }
    return raw,true
}

func findLocalNFeXML(key string) (string,[]byte,error) {
    if !validNFeKeyText(key) { return "",nil,fmt.Errorf("chave inválida") }
    folders:=existingXMLSourceRoots()
    if len(folders)==0 { return "",nil,fmt.Errorf("nenhuma fonte XML/SIEG disponível neste computador") }
    const foundSignal="__CSM_LOCAL_XML_FOUND__"
    var found string;var raw []byte
    for _,base:=range folders {
        for _,root:=range sourceSearchRootsForKey(base,key) {
            err:=filepath.Walk(root,func(path string,info os.FileInfo,walkErr error) error {
                if walkErr!=nil || info==nil { return nil }
                if info.IsDir() { return nil }
                if candidate,ok:=readXMLIfMatches(path,key,info);ok {
                    found=path;raw=candidate
                    return fmt.Errorf(foundSignal)
                }
                return nil
            })
            if found!="" { return found,raw,nil }
            if err!=nil && err.Error()!=foundSignal { continue }
        }
    }
    return "",nil,fmt.Errorf("XML não localizado na Base CSM nem nas fontes XML/SIEG disponíveis")
}'''

if old not in s:
    raise SystemExit('findLocalNFeXML 3.13.1 não localizado')
s=s.replace(old,new,1)

# Torna a resposta da API explícita sobre as fontes consultadas, sem prometer que distNSU obterá qualquer nota.
oldmsg='''return map[string]any{"ok":true,"found":false,"xml_available":false,"key":key,"syncing":repositorySyncIsRunning(),"source":"Base CSM","api":"CSM Consulta NF-e","message":"Esta chave ainda não está indexada na Base CSM. A sincronização oficial DF-e continuará em segundo plano."}'''
newmsg='''return map[string]any{"ok":true,"found":false,"xml_available":false,"key":key,"syncing":repositorySyncIsRunning(),"source":"Base CSM + XML/SIEG + DF-e","api":"CSM Consulta NF-e","message":"O XML ainda não foi localizado na Base CSM nem nas fontes XML/SIEG disponíveis. A Distribuição DF-e só consegue trazer documentos liberados para os certificados autorizados."}'''
if oldmsg not in s: raise SystemExit('Mensagem final repositoryLookup não localizada')
s=s.replace(oldmsg,newmsg,1)

selftest=r'''
func runXMLSourceDiscoverySelftest() bool {
    root,err:=os.MkdirTemp("","csm-xml-source-selftest-")
    if err!=nil { return false }
    defer os.RemoveAll(root)
    key:="35260802562527000135550010000194421659945019"
    issuer:=key[6:20]
    dir:=filepath.Join(root,issuer)
    if os.MkdirAll(dir,0755)!=nil { return false }
    xml:="<?xml version=\\\"1.0\\\" encoding=\\\"utf-8\\\"?><nfeProc xmlns=\\\"http://www.portalfiscal.inf.br/nfe\\\"><NFe><infNFe Id=\\\"NFe"+key+"\\\"></infNFe></NFe><protNFe><infProt><chNFe>"+key+"</chNFe></infProt></protNFe></nfeProc>"
    path:=filepath.Join(dir,"nota-"+key+".xml")
    if os.WriteFile(path,[]byte(xml),0644)!=nil { return false }
    old:=os.Getenv("CSM_SIEG_ROOT")
    _=os.Setenv("CSM_SIEG_ROOT",root)
    defer func(){ _=os.Setenv("CSM_SIEG_ROOT",old) }()
    found,raw,e:=findLocalNFeXML(key)
    return e==nil && strings.EqualFold(found,path) && xmlBytesMatchNFeKey(raw,key)
}

'''
main_old='''func main() {'''
main_new='''func main() {
    if len(os.Args)>1 && os.Args[1]=="--csm-source-selftest" {
        if !runXMLSourceDiscoverySelftest() { os.Exit(71) }
        return
    }'''
if main_old not in s: raise SystemExit('main() não localizado para self-test 3.14.1')
s=s.replace(main_old,main_new,1)
s=s.replace('// CSM_XML_SOURCE_DISCOVERY_3141',selftest+'// CSM_XML_SOURCE_DISCOVERY_3141',1)
s=s.rstrip()+"\n// "+MARK+" — descobre SIEG em unidades mapeadas, prioriza CNPJ da chave e reduz I/O em rede.\n"
for tok in (MARK,'existingXMLSourceRoots','sourceSearchRootsForKey','readXMLIfMatches','CSM_SIEG_ROOT','Base CSM + XML/SIEG + DF-e','runXMLSourceDiscoverySelftest','--csm-source-selftest'):
    if tok not in s: raise SystemExit('Patch 3.14.1 incompleto: '+tok)
p.write_text(s,encoding='utf-8',newline='\n')
print('3.14.1: SIEG/XML autodetectado e consulta por chave busca fontes reais antes de aguardar DF-e.')
