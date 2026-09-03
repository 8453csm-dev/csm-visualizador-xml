//go:build windows

package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "os"
    "path/filepath"
    "runtime"
    "sort"
    "strings"
    "syscall"
    "time"
    "unsafe"
)

const (
    bifReturnOnlyFSDirs = 0x0001
    bifEditBox          = 0x0010
    bifNewDialogStyle   = 0x0040
    folderMaxFiles      = 5000
    swMaximize          = 3
)

var (
    shell32Picker = syscall.NewLazyDLL("shell32.dll")
    ole32Picker   = syscall.NewLazyDLL("ole32.dll")

    procSHBrowseForFolderW     = shell32Picker.NewProc("SHBrowseForFolderW")
    procSHGetPathFromIDListW   = shell32Picker.NewProc("SHGetPathFromIDListW")
    procCoTaskMemFree          = ole32Picker.NewProc("CoTaskMemFree")
    procOleInitialize          = ole32Picker.NewProc("OleInitialize")
    procOleUninitialize        = ole32Picker.NewProc("OleUninitialize")
)

type browseInfoW struct {
    hwndOwner       uintptr
    pidlRoot        uintptr
    pszDisplayName  *uint16
    lpszTitle       *uint16
    ulFlags         uint32
    lpfn            uintptr
    lParam          uintptr
    iImage          int32
}

type folderPathRequest struct {
    Path string `json:"path"`
}

func folderPickerAPIsAvailable() bool {
    return procSHBrowseForFolderW.Find() == nil &&
        procSHGetPathFromIDListW.Find() == nil &&
        procCoTaskMemFree.Find() == nil &&
        procOleInitialize.Find() == nil &&
        procOleUninitialize.Find() == nil
}

func currentMainWindowHandle(b *broker) uintptr {
    pid, _ := b.getCoreState()
    if pid != 0 {
        if w, ok := primaryWindow(pid); ok && w.visible { return w.hwnd }
    }
    for _, candidate := range processIDsByName(coreName) {
        if w, ok := primaryWindow(candidate); ok && w.visible { return w.hwnd }
    }
    return 0
}

func chooseFolderNative(owner uintptr) (string, bool, error) {
    runtime.LockOSThread()
    defer runtime.UnlockOSThread()

    hr, _, _ := procOleInitialize.Call(0)
    if hr != 0 && hr != 1 {
        return "", false, fmt.Errorf("não foi possível inicializar o seletor de pastas do Windows")
    }
    defer procOleUninitialize.Call()

    title, _ := syscall.UTF16PtrFromString("Selecione a pasta com os XMLs/PDFs")
    display := make([]uint16, 260)
    info := browseInfoW{
        hwndOwner: owner,
        pszDisplayName: &display[0],
        lpszTitle: title,
        ulFlags: bifReturnOnlyFSDirs | bifEditBox | bifNewDialogStyle,
    }
    pidl, _, _ := procSHBrowseForFolderW.Call(uintptr(unsafe.Pointer(&info)))
    if pidl == 0 { return "", true, nil }
    defer procCoTaskMemFree.Call(pidl)

    buffer := make([]uint16, 32768)
    ok, _, _ := procSHGetPathFromIDListW.Call(pidl, uintptr(unsafe.Pointer(&buffer[0])))
    if ok == 0 { return "", false, fmt.Errorf("o Windows não retornou o caminho da pasta selecionada") }
    path := strings.TrimSpace(syscall.UTF16ToString(buffer))
    if path == "" { return "", false, fmt.Errorf("a pasta selecionada não possui um caminho válido") }
    if stat, err := os.Stat(path); err != nil || !stat.IsDir() {
        return "", false, fmt.Errorf("a pasta selecionada não está acessível")
    }
    return path, false, nil
}

func (b *broker) handlePickFolder(w http.ResponseWriter, r *http.Request) {
    setCORS(w)
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }

    path, cancelled, err := chooseFolderNative(currentMainWindowHandle(b))
    w.Header().Set("Content-Type", "application/json; charset=utf-8")
    if err != nil {
        w.WriteHeader(http.StatusInternalServerError)
        _ = json.NewEncoder(w).Encode(map[string]any{"ok": false, "error": err.Error()})
        return
    }
    if cancelled {
        _ = json.NewEncoder(w).Encode(map[string]any{"ok": true, "cancelled": true})
        return
    }
    _ = json.NewEncoder(w).Encode(map[string]any{"ok": true, "cancelled": false, "path": path})
}

func listFiscalFiles(folder string) ([]string, int, error) {
    folder = strings.TrimSpace(folder)
    if folder == "" { return nil, 0, fmt.Errorf("pasta não informada") }
    stat, err := os.Stat(folder)
    if err != nil || !stat.IsDir() { return nil, 0, fmt.Errorf("a pasta selecionada não está acessível") }

    paths := make([]string, 0, 512)
    total := 0
    err = filepath.WalkDir(folder, func(path string, entry os.DirEntry, walkErr error) error {
        if walkErr != nil { return walkErr }
        if entry.IsDir() { return nil }
        ext := strings.ToLower(filepath.Ext(entry.Name()))
        if ext != ".xml" && ext != ".pdf" { return nil }
        total++
        if total <= folderMaxFiles { paths = append(paths, path) }
        return nil
    })
    if err != nil { return nil, total, err }
    sort.Strings(paths)
    return paths, total, nil
}

func (b *broker) handleListFolder(w http.ResponseWriter, r *http.Request) {
    setCORS(w)
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }

    var req folderPathRequest
    if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 64<<10)).Decode(&req); err != nil {
        http.Error(w, "invalid request", http.StatusBadRequest); return
    }
    paths, total, err := listFiscalFiles(req.Path)
    w.Header().Set("Content-Type", "application/json; charset=utf-8")
    if err != nil {
        w.WriteHeader(http.StatusBadRequest)
        _ = json.NewEncoder(w).Encode(map[string]any{"ok": false, "error": err.Error()})
        return
    }
    if total > folderMaxFiles {
        _ = json.NewEncoder(w).Encode(map[string]any{
            "ok": false,
            "error": fmt.Sprintf("A pasta possui %d XMLs/PDFs. O limite por carga é %d.", total, folderMaxFiles),
            "count": total,
            "limit": folderMaxFiles,
        })
        return
    }
    _ = json.NewEncoder(w).Encode(map[string]any{"ok": true, "count": total, "paths": paths})
}

// maximizeStartupWindow é chamado somente na primeira abertura do CSM.
// Aberturas posteriores de XML na instância já existente não alteram o estado da janela.
func maximizeStartupWindow(pid uint32) bool {
    w, ok := primaryWindow(pid)
    if !ok || !w.visible { return false }
    procShowWindowAsync.Call(w.hwnd, swMaximize)
    procBringWindowToTop.Call(w.hwnd)
    procSetForegroundWindow.Call(w.hwnd)
    return true
}

func findVisibleCoreWindow() (uint32, bool) {
    for _, pid := range processIDsByName(coreName) {
        if w, ok := primaryWindow(pid); ok && w.visible { return pid, true }
    }
    return 0, false
}

func waitFindVisibleCoreWindow(timeout time.Duration) (uint32, bool) {
    deadline := time.Now().Add(timeout)
    for time.Now().Before(deadline) {
        if pid, ok := findVisibleCoreWindow(); ok { return pid, true }
        if len(processIDsByName(coreName)) == 0 { return 0, false }
        time.Sleep(120 * time.Millisecond)
    }
    return 0, false
}
