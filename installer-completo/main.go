//go:build windows

package main

import (
    "crypto/sha256"
    _ "embed"
    "encoding/hex"
    "fmt"
    "os"
    "path/filepath"
    "regexp"
    "runtime"
    "strings"
    "syscall"
    "time"
    "unsafe"
)

const (
    productName = "CSM Visualizador XML"
    packageName = "Instalador Completo Atualizado"
    baseSHA256  = "d6086b661fb40d4c05ce76d38ecec836a8ff7d5c4c55a6df35c68ed03b484b74"

    MB_OK              = 0x00000000
    MB_YESNO           = 0x00000004
    MB_ICONERROR       = 0x00000010
    MB_ICONQUESTION    = 0x00000020
    MB_ICONWARNING     = 0x00000030
    MB_ICONINFORMATION = 0x00000040
    IDYES              = 6
    SW_SHOWNORMAL      = 1
    SEE_MASK_NOCLOSEPROCESS = 0x00000040
    INFINITE           = 0xFFFFFFFF
)

//go:embed payload/CSMVisualizadorXML-3.7.8-Instalador-Completo.exe
var baseInstaller []byte

//go:embed enhancer_v8.html
var enhancerV8 []byte

var (
    user32 = syscall.NewLazyDLL("user32.dll")
    shell32 = syscall.NewLazyDLL("shell32.dll")
    kernel32 = syscall.NewLazyDLL("kernel32.dll")
    pMessageBoxW = user32.NewProc("MessageBoxW")
    pShellExecuteExW = shell32.NewProc("ShellExecuteExW")
    pWaitForSingleObject = kernel32.NewProc("WaitForSingleObject")
    pGetExitCodeProcess = kernel32.NewProc("GetExitCodeProcess")
    pCloseHandle = kernel32.NewProc("CloseHandle")
)

type shellExecuteInfo struct {
    cbSize uint32
    fMask uint32
    hwnd uintptr
    lpVerb *uint16
    lpFile *uint16
    lpParameters *uint16
    lpDirectory *uint16
    nShow int32
    hInstApp uintptr
    lpIDList uintptr
    lpClass *uint16
    hkeyClass uintptr
    dwHotKey uint32
    hIconOrMonitor uintptr
    hProcess uintptr
}

func u16(s string) *uint16 { return syscall.StringToUTF16Ptr(s) }

func msg(text, title string, flags uintptr) int {
    r, _, _ := pMessageBoxW.Call(0, uintptr(unsafe.Pointer(u16(text))), uintptr(unsafe.Pointer(u16(title))), flags)
    return int(r)
}

func logLine(format string, args ...any) {
    root := os.Getenv("LOCALAPPDATA")
    if root == "" { root = os.TempDir() }
    dir := filepath.Join(root, "CSM Visualizador XML")
    _ = os.MkdirAll(dir, 0755)
    f, err := os.OpenFile(filepath.Join(dir, "InstaladorCompleto.log"), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
    if err != nil { return }
    defer f.Close()
    fmt.Fprintf(f, "%s "+format+"\r\n", append([]any{time.Now().Format("2006-01-02 15:04:05")}, args...)...)
}

func verifyEmbedded() error {
    h := sha256.Sum256(baseInstaller)
    got := hex.EncodeToString(h[:])
    if got != baseSHA256 {
        return fmt.Errorf("SHA-256 do instalador base inválido: %s", got)
    }
    s := string(enhancerV8)
    if !strings.Contains(s, "<!-- CSM_XML_ENHANCER_V8 -->") || !strings.Contains(s, "<!-- /CSM_XML_ENHANCER_V8 -->") {
        return fmt.Errorf("componente da aba XML v8 inválido")
    }
    return nil
}

func shellExecuteAndWait(path string) (uint32, error) {
    sei := shellExecuteInfo{
        cbSize: uint32(unsafe.Sizeof(shellExecuteInfo{})),
        fMask: SEE_MASK_NOCLOSEPROCESS,
        lpVerb: u16("open"),
        lpFile: u16(path),
        nShow: SW_SHOWNORMAL,
    }
    r, _, e := pShellExecuteExW.Call(uintptr(unsafe.Pointer(&sei)))
    if r == 0 {
        return 0, fmt.Errorf("não foi possível iniciar o instalador base: %v", e)
    }
    if sei.hProcess == 0 { return 0, nil }
    defer pCloseHandle.Call(sei.hProcess)
    pWaitForSingleObject.Call(sei.hProcess, INFINITE)
    var code uint32
    pGetExitCodeProcess.Call(sei.hProcess, uintptr(unsafe.Pointer(&code)))
    return code, nil
}

func normalizedName(s string) string {
    s = strings.ToLower(s)
    repl := strings.NewReplacer(" ", "", "-", "", "_", "", ".", "")
    return repl.Replace(s)
}

func addRoot(set map[string]bool, p string) {
    if p == "" { return }
    p = filepath.Clean(p)
    st, err := os.Stat(p)
    if err == nil && st.IsDir() { set[p] = true }
}

func discoverRoots() []string {
    set := map[string]bool{}
    local := os.Getenv("LOCALAPPDATA")
    pf := os.Getenv("ProgramFiles")
    pf86 := os.Getenv("ProgramFiles(x86)")
    explicit := []string{
        filepath.Join(local, "CSM Visualizador XML"),
        filepath.Join(local, "CSMVisualizadorXML"),
        filepath.Join(local, "Programs", "CSM Visualizador XML"),
        filepath.Join(local, "Programs", "CSMVisualizadorXML"),
        filepath.Join(pf, "CSM Visualizador XML"),
        filepath.Join(pf86, "CSM Visualizador XML"),
    }
    for _, p := range explicit { addRoot(set, p) }
    parents := []string{local, filepath.Join(local, "Programs"), pf, pf86}
    for _, parent := range parents {
        entries, err := os.ReadDir(parent)
        if err != nil { continue }
        for _, e := range entries {
            if !e.IsDir() { continue }
            n := normalizedName(e.Name())
            if strings.Contains(n, "csm") && (strings.Contains(n, "visualizador") || strings.Contains(n, "xml")) {
                addRoot(set, filepath.Join(parent, e.Name()))
            }
        }
    }
    out := make([]string, 0, len(set))
    for p := range set { out = append(out, p) }
    return out
}

var oldEnhancer = regexp.MustCompile(`(?s)<!-- CSM_XML_ENHANCER_V[1-8] -->.*?<!-- /CSM_XML_ENHANCER_V[1-8] -->`)

func excludedPath(p string) bool {
    s := strings.ToLower(filepath.ToSlash(p))
    bad := []string{"node_modules/", "/pdfjs/", "/pdf.js/", "/webview2/", "/edge/", "/runtime/"}
    for _, x := range bad { if strings.Contains(s, x) { return true } }
    return false
}

func patchHTML(path string) (bool, bool, error) {
    st, err := os.Stat(path)
    if err != nil || st.IsDir() || st.Size() < 100 || st.Size() > 12*1024*1024 { return false, false, err }
    data, err := os.ReadFile(path)
    if err != nil { return false, false, err }
    lower := strings.ToLower(string(data))
    idx := strings.LastIndex(lower, "</body>")
    if idx < 0 { return false, false, nil }
    cleaned := oldEnhancer.ReplaceAll(data, nil)
    lowerClean := strings.ToLower(string(cleaned))
    idx = strings.LastIndex(lowerClean, "</body>")
    if idx < 0 { return false, false, nil }
    merged := make([]byte, 0, len(cleaned)+len(enhancerV8)+4)
    merged = append(merged, cleaned[:idx]...)
    merged = append(merged, '\n')
    merged = append(merged, enhancerV8...)
    merged = append(merged, '\n')
    merged = append(merged, cleaned[idx:]...)
    if string(merged) == string(data) { return false, false, nil }

    backup := path + ".csmxml-pre-v8.bak"
    madeBackup := false
    if _, err := os.Stat(backup); os.IsNotExist(err) {
        if err := os.WriteFile(backup, data, st.Mode()); err == nil { madeBackup = true }
    }
    tmp := path + ".csmxml.tmp"
    if err := os.WriteFile(tmp, merged, st.Mode()); err != nil { return false, madeBackup, err }
    if err := os.Rename(tmp, path); err != nil { _ = os.Remove(tmp); return false, madeBackup, err }
    return true, madeBackup, nil
}

func patchInstalledUI() (int, int, []string) {
    roots := discoverRoots()
    patched, backups := 0, 0
    var errs []string
    seen := map[string]bool{}
    for _, root := range roots {
        _ = filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
            if err != nil { return nil }
            if d.IsDir() {
                if excludedPath(path) { return filepath.SkipDir }
                return nil
            }
            ext := strings.ToLower(filepath.Ext(path))
            if ext != ".html" && ext != ".htm" { return nil }
            if excludedPath(path) || seen[path] { return nil }
            seen[path] = true
            ok, bak, e := patchHTML(path)
            if e != nil { errs = append(errs, fmt.Sprintf("%s: %v", path, e)); return nil }
            if ok { patched++; logLine("Interface atualizada: %s", path) }
            if bak { backups++ }
            return nil
        })
    }
    return patched, backups, errs
}

func main() {
    runtime.LockOSThread()
    if len(os.Args) > 1 && (os.Args[1] == "--self-test" || os.Args[1] == "/selftest") {
        if err := verifyEmbedded(); err != nil { os.Exit(10) }
        os.Exit(0)
    }
    if err := verifyEmbedded(); err != nil {
        msg("O pacote do instalador está corrompido e não será executado.\n\n"+err.Error(), productName, MB_OK|MB_ICONERROR)
        return
    }
    intro := "Este instalador instala a base estável 3.7.8 do CSM Visualizador XML e aplica automaticamente a Aba XML otimizada v8.\n\nO design e as funções da versão estável são preservados.\n\nDeseja continuar?"
    if msg(intro, productName+" - "+packageName, MB_YESNO|MB_ICONQUESTION) != IDYES { return }

    dir, err := os.MkdirTemp("", "CSMVisualizadorXML-Setup-")
    if err != nil { msg("Não foi possível preparar a instalação.\n\n"+err.Error(), productName, MB_OK|MB_ICONERROR); return }
    defer os.RemoveAll(dir)
    basePath := filepath.Join(dir, "CSMVisualizadorXML-3.7.8-Instalador-Completo.exe")
    if err := os.WriteFile(basePath, baseInstaller, 0755); err != nil {
        msg("Não foi possível extrair o instalador base.\n\n"+err.Error(), productName, MB_OK|MB_ICONERROR); return
    }
    logLine("Iniciando instalador base 3.7.8")
    code, err := shellExecuteAndWait(basePath)
    if err != nil {
        msg("Falha ao iniciar a instalação base.\n\n"+err.Error(), productName, MB_OK|MB_ICONERROR); return
    }
    logLine("Instalador base finalizado com código %d", code)
    if code != 0 {
        msg(fmt.Sprintf("A instalação base foi encerrada com código %d. A Aba XML não será alterada.", code), productName, MB_OK|MB_ICONWARNING)
        return
    }
    patched, backups, errs := patchInstalledUI()
    logLine("Hotfix XML v8: arquivos=%d backups=%d erros=%d", patched, backups, len(errs))
    if patched == 0 {
        text := "A instalação base foi concluída, mas não localizei a interface HTML para aplicar a Aba XML v8.\n\nO software permanece instalado sem perda de arquivos."
        if len(errs) > 0 { text += "\n\nDetalhe: " + errs[0] }
        msg(text, productName, MB_OK|MB_ICONWARNING)
        return
    }
    msg(fmt.Sprintf("Instalação concluída com sucesso!\n\nBase estável: 3.7.8\nAba XML: v8 otimizada\nArquivos de interface atualizados: %d\nBackups de segurança: %d\n\nO design e os recursos da versão estável foram preservados.", patched, backups), productName, MB_OK|MB_ICONINFORMATION)
}
