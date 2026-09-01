//go:build windows

package main

import (
    "encoding/json"
    "fmt"
    "io"
    "net"
    "net/http"
    "os"
    "os/exec"
    "path/filepath"
    "strings"
    "sync"
    "syscall"
    "time"
    "unsafe"
)

const (
    coreName          = "CSM Visualizador XML Core.exe"
    th32csSnapProcess = 0x00000002
    swShow            = 5
    swRestore         = 9
    swpShowWindow     = 0x0040
    swpNoSize         = 0x0001
    swpNoMove         = 0x0002
    smXVirtualScreen  = 76
    smYVirtualScreen  = 77
    smCXVirtualScreen = 78
    smCYVirtualScreen = 79
    brokerAddress     = "127.0.0.1:47878"
    brokerURL         = "http://127.0.0.1:47878"
)

var (
    kernel32 = syscall.NewLazyDLL("kernel32.dll")
    user32   = syscall.NewLazyDLL("user32.dll")

    procCreateToolhelp32Snapshot = kernel32.NewProc("CreateToolhelp32Snapshot")
    procProcess32FirstW          = kernel32.NewProc("Process32FirstW")
    procProcess32NextW           = kernel32.NewProc("Process32NextW")
    procEnumWindows              = user32.NewProc("EnumWindows")
    procGetWindowThreadProcessId = user32.NewProc("GetWindowThreadProcessId")
    procIsWindowVisible          = user32.NewProc("IsWindowVisible")
    procShowWindow               = user32.NewProc("ShowWindow")
    procShowWindowAsync          = user32.NewProc("ShowWindowAsync")
    procSetForegroundWindow      = user32.NewProc("SetForegroundWindow")
    procBringWindowToTop         = user32.NewProc("BringWindowToTop")
    procSetWindowPos             = user32.NewProc("SetWindowPos")
    procGetWindowRect            = user32.NewProc("GetWindowRect")
    procGetWindowTextLengthW     = user32.NewProc("GetWindowTextLengthW")
    procGetWindowTextW           = user32.NewProc("GetWindowTextW")
    procGetSystemMetrics         = user32.NewProc("GetSystemMetrics")
    procMessageBoxW              = user32.NewProc("MessageBoxW")
)

type processEntry32 struct {
    Size            uint32
    CntUsage        uint32
    ProcessID       uint32
    DefaultHeapID   uintptr
    ModuleID        uint32
    CntThreads      uint32
    ParentProcessID uint32
    PriClassBase    int32
    Flags           uint32
    ExeFile         [260]uint16
}

type rect struct{ Left, Top, Right, Bottom int32 }

type windowCandidate struct {
    hwnd    uintptr
    title   string
    visible bool
    rect    rect
}

type openRequest struct { Paths []string `json:"paths"` }
type ackRequest struct { Path string `json:"path"` }

type broker struct {
    mu          sync.Mutex
    coreMu      sync.Mutex
    core        string
    dir         string
    corePID     uint32
    coreStarted time.Time
    pending     []string
    subscribers map[chan string]struct{}
    ackCount    int
    lastAck     string
    lastActive  time.Time
}

func utf16ToString(v []uint16) string {
    n := 0
    for n < len(v) && v[n] != 0 { n++ }
    return syscall.UTF16ToString(v[:n])
}

func processIDsByName(name string) []uint32 {
    snap, _, _ := procCreateToolhelp32Snapshot.Call(th32csSnapProcess, 0)
    if snap == ^uintptr(0) || snap == 0 { return nil }
    defer syscall.CloseHandle(syscall.Handle(snap))
    var pe processEntry32
    pe.Size = uint32(unsafe.Sizeof(pe))
    var result []uint32
    ok, _, _ := procProcess32FirstW.Call(snap, uintptr(unsafe.Pointer(&pe)))
    for ok != 0 {
        if strings.EqualFold(utf16ToString(pe.ExeFile[:]), name) { result = append(result, pe.ProcessID) }
        ok, _, _ = procProcess32NextW.Call(snap, uintptr(unsafe.Pointer(&pe)))
    }
    return result
}

func windowTitle(hwnd uintptr) string {
    n, _, _ := procGetWindowTextLengthW.Call(hwnd)
    if n == 0 { return "" }
    buf := make([]uint16, n+1)
    procGetWindowTextW.Call(hwnd, uintptr(unsafe.Pointer(&buf[0])), uintptr(len(buf)))
    return syscall.UTF16ToString(buf)
}

func windowsForPID(pid uint32) []windowCandidate {
    var out []windowCandidate
    cb := syscall.NewCallback(func(hwnd uintptr, lparam uintptr) uintptr {
        var winPID uint32
        procGetWindowThreadProcessId.Call(hwnd, uintptr(unsafe.Pointer(&winPID)))
        if winPID != pid { return 1 }
        title := strings.TrimSpace(windowTitle(hwnd))
        if title == "" { return 1 }
        var r rect
        procGetWindowRect.Call(hwnd, uintptr(unsafe.Pointer(&r)))
        vis, _, _ := procIsWindowVisible.Call(hwnd)
        out = append(out, windowCandidate{hwnd: hwnd, title: title, visible: vis != 0, rect: r})
        return 1
    })
    procEnumWindows.Call(cb, 0)
    return out
}

func primaryWindow(pid uint32) (windowCandidate, bool) {
    wins := windowsForPID(pid)
    if len(wins) == 0 { return windowCandidate{}, false }
    for _, w := range wins { if strings.Contains(strings.ToLower(w.title), "csm visualizador xml") { return w, true } }
    for _, w := range wins { if w.visible { return w, true } }
    return wins[0], true
}

func isOffScreen(r rect) bool {
    x, _, _ := procGetSystemMetrics.Call(smXVirtualScreen)
    y, _, _ := procGetSystemMetrics.Call(smYVirtualScreen)
    w, _, _ := procGetSystemMetrics.Call(smCXVirtualScreen)
    h, _, _ := procGetSystemMetrics.Call(smCYVirtualScreen)
    vx, vy, vw, vh := int32(x), int32(y), int32(w), int32(h)
    if vw <= 0 || vh <= 0 { return false }
    return r.Right <= vx || r.Left >= vx+vw || r.Bottom <= vy || r.Top >= vy+vh
}

func recoverWindow(pid uint32) bool {
    w, ok := primaryWindow(pid)
    if !ok { return false }
    width, height := w.rect.Right-w.rect.Left, w.rect.Bottom-w.rect.Top
    if width < 300 { width = 1280 }
    if height < 200 { height = 820 }
    procShowWindowAsync.Call(w.hwnd, swRestore)
    procShowWindow.Call(w.hwnd, swShow)
    if isOffScreen(w.rect) || w.rect.Left < -30000 || w.rect.Top < -30000 {
        x, _, _ := procGetSystemMetrics.Call(smXVirtualScreen)
        y, _, _ := procGetSystemMetrics.Call(smYVirtualScreen)
        nx, ny := int32(x)+80, int32(y)+80
        procSetWindowPos.Call(w.hwnd, 0, uintptr(nx), uintptr(ny), uintptr(width), uintptr(height), swpShowWindow)
    } else {
        procSetWindowPos.Call(w.hwnd, 0, 0, 0, 0, 0, swpShowWindow|swpNoSize|swpNoMove)
    }
    procBringWindowToTop.Call(w.hwnd)
    procSetForegroundWindow.Call(w.hwnd)
    return true
}

func recoverAnyCoreWindow() (uint32, bool) {
    pids := processIDsByName(coreName)
    for _, pid := range pids {
        if w, ok := primaryWindow(pid); ok && strings.Contains(strings.ToLower(w.title), "csm visualizador xml") {
            if recoverWindow(pid) { return pid, true }
        }
    }
    for _, pid := range pids { if recoverWindow(pid) { return pid, true } }
    return 0, false
}

func waitRecoverAnyCoreWindow(timeout time.Duration) (uint32, bool) {
    deadline := time.Now().Add(timeout)
    for time.Now().Before(deadline) {
        if pid, ok := recoverAnyCoreWindow(); ok { return pid, true }
        if len(processIDsByName(coreName)) == 0 { return 0, false }
        time.Sleep(120 * time.Millisecond)
    }
    return 0, false
}

func killAllCoreProcesses() {
    cmd := exec.Command("taskkill.exe", "/F", "/IM", coreName)
    cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
    _ = cmd.Run()
    deadline := time.Now().Add(2500 * time.Millisecond)
    for time.Now().Before(deadline) {
        if len(processIDsByName(coreName)) == 0 { return }
        time.Sleep(80 * time.Millisecond)
    }
}

func messageBox(text, title string) {
    t, _ := syscall.UTF16PtrFromString(text)
    c, _ := syscall.UTF16PtrFromString(title)
    procMessageBoxW.Call(0, uintptr(unsafe.Pointer(t)), uintptr(unsafe.Pointer(c)), 0x10)
}

func corePath() (string, string, error) {
    exe, err := os.Executable()
    if err != nil { return "", "", err }
    dir := filepath.Dir(exe)
    core := filepath.Join(dir, coreName)
    if _, err := os.Stat(core); err != nil { return "", dir, err }
    return core, dir, nil
}

func normalizePaths(args []string) []string {
    seen := map[string]bool{}
    out := make([]string, 0, len(args))
    for _, a := range args {
        if strings.HasPrefix(a, "--") || strings.TrimSpace(a) == "" { continue }
        p := strings.Trim(strings.TrimSpace(a), "\"")
        if abs, err := filepath.Abs(p); err == nil { p = abs }
        if _, err := os.Stat(p); err != nil { continue }
        key := strings.ToLower(p)
        if !seen[key] { seen[key] = true; out = append(out, p) }
    }
    return out
}

func postExisting(paths []string) bool {
    client := &http.Client{Timeout: 4 * time.Second}
    endpoint := brokerURL + "/activate"
    var body io.Reader
    if len(paths) > 0 {
        endpoint = brokerURL + "/open"
        data, _ := json.Marshal(openRequest{Paths: paths})
        body = strings.NewReader(string(data))
    }
    req, err := http.NewRequest(http.MethodPost, endpoint, body)
    if err != nil { return false }
    req.Header.Set("Content-Type", "application/json")
    resp, err := client.Do(req)
    if err != nil { return false }
    defer resp.Body.Close()
    return resp.StatusCode >= 200 && resp.StatusCode < 300
}

func newBroker(core, dir string) *broker {
    return &broker{core: core, dir: dir, subscribers: make(map[chan string]struct{}), lastActive: time.Now()}
}

func (b *broker) setCoreState(pid uint32, started time.Time) {
    b.mu.Lock()
    b.corePID = pid
    if !started.IsZero() { b.coreStarted = started }
    b.lastActive = time.Now()
    b.mu.Unlock()
}

func (b *broker) getCoreState() (uint32, time.Time) {
    b.mu.Lock(); defer b.mu.Unlock(); return b.corePID, b.coreStarted
}

func (b *broker) startCoreUnlocked() error {
    cmd := exec.Command(b.core)
    cmd.Dir = b.dir
    if err := cmd.Start(); err != nil { return err }
    parentPID := uint32(cmd.Process.Pid)
    _ = cmd.Process.Release()
    started := time.Now()
    b.setCoreState(parentPID, started)
    go func() {
        if owner, ok := waitRecoverAnyCoreWindow(15 * time.Second); ok { b.setCoreState(owner, time.Time{}) }
    }()
    return nil
}

func (b *broker) adoptOrStartCore() error {
    b.coreMu.Lock(); defer b.coreMu.Unlock()
    if len(processIDsByName(coreName)) > 0 {
        if owner, ok := waitRecoverAnyCoreWindow(5 * time.Second); ok {
            b.setCoreState(owner, time.Now().Add(-30*time.Second)); return nil
        }
        killAllCoreProcesses()
    }
    return b.startCoreUnlocked()
}

func (b *broker) ensureHealthyCore() error {
    b.coreMu.Lock(); defer b.coreMu.Unlock()
    if len(processIDsByName(coreName)) > 0 {
        if owner, ok := recoverAnyCoreWindow(); ok { b.setCoreState(owner, time.Time{}); return nil }
        _, started := b.getCoreState()
        waitFor := 2500 * time.Millisecond
        if !started.IsZero() {
            age := time.Since(started)
            if age < 15*time.Second {
                waitFor = 15*time.Second - age
                if waitFor < 2500*time.Millisecond { waitFor = 2500 * time.Millisecond }
            }
        }
        if owner, ok := waitRecoverAnyCoreWindow(waitFor); ok { b.setCoreState(owner, time.Time{}); return nil }
        killAllCoreProcesses()
        b.setCoreState(0, time.Time{})
    }
    return b.startCoreUnlocked()
}

func (b *broker) queuePath(path string) {
    path = strings.TrimSpace(path)
    if path == "" { return }
    b.mu.Lock()
    b.lastActive = time.Now()
    if len(b.subscribers) == 0 {
        for _, existing := range b.pending { if strings.EqualFold(existing, path) { b.mu.Unlock(); return } }
        b.pending = append(b.pending, path)
        b.mu.Unlock(); return
    }
    chans := make([]chan string, 0, len(b.subscribers))
    for ch := range b.subscribers { chans = append(chans, ch) }
    b.mu.Unlock()
    for _, ch := range chans { select { case ch <- path: default: } }
}

func (b *broker) addSubscriber(ch chan string) []string {
    b.mu.Lock(); defer b.mu.Unlock()
    b.subscribers[ch] = struct{}{}
    pending := append([]string(nil), b.pending...)
    b.pending = nil
    b.lastActive = time.Now()
    return pending
}

func (b *broker) removeSubscriber(ch chan string) { b.mu.Lock(); delete(b.subscribers, ch); b.mu.Unlock() }

func setCORS(w http.ResponseWriter) {
    w.Header().Set("Access-Control-Allow-Origin", "*")
    w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
    w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
}

func (b *broker) handleOpen(w http.ResponseWriter, r *http.Request) {
    setCORS(w)
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }
    var req openRequest
    if err := json.NewDecoder(io.LimitReader(r.Body, 1<<20)).Decode(&req); err != nil { http.Error(w, "invalid request", http.StatusBadRequest); return }
    paths := normalizePaths(req.Paths)
    if err := b.ensureHealthyCore(); err != nil { http.Error(w, err.Error(), http.StatusInternalServerError); return }
    for _, p := range paths { b.queuePath(p) }
    w.Header().Set("Content-Type", "application/json")
    _ = json.NewEncoder(w).Encode(map[string]any{"ok": true, "count": len(paths)})
}

func (b *broker) handleActivate(w http.ResponseWriter, r *http.Request) {
    setCORS(w)
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }
    if err := b.ensureHealthyCore(); err != nil { http.Error(w, err.Error(), http.StatusInternalServerError); return }
    w.Header().Set("Content-Type", "application/json")
    _, _ = w.Write([]byte(`{"ok":true}`))
}

func (b *broker) handleAck(w http.ResponseWriter, r *http.Request) {
    setCORS(w)
    if r.Method == http.MethodOptions { w.WriteHeader(http.StatusNoContent); return }
    if r.Method != http.MethodPost { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }
    var req ackRequest
    if err := json.NewDecoder(io.LimitReader(r.Body, 1<<20)).Decode(&req); err != nil { http.Error(w, "invalid request", http.StatusBadRequest); return }
    b.mu.Lock()
    b.ackCount++
    b.lastAck = strings.TrimSpace(req.Path)
    b.lastActive = time.Now()
    b.mu.Unlock()
    w.Header().Set("Content-Type", "application/json")
    _, _ = w.Write([]byte(`{"ok":true}`))
}

func writeEvent(w io.Writer, path string) {
    data, _ := json.Marshal(map[string]string{"path": path})
    _, _ = fmt.Fprintf(w, "data: %s\n\n", data)
}

func (b *broker) handleEvents(w http.ResponseWriter, r *http.Request) {
    setCORS(w)
    if r.Method != http.MethodGet { http.Error(w, "method not allowed", http.StatusMethodNotAllowed); return }
    flusher, ok := w.(http.Flusher)
    if !ok { http.Error(w, "stream unsupported", http.StatusInternalServerError); return }
    w.Header().Set("Content-Type", "text/event-stream")
    w.Header().Set("Cache-Control", "no-cache")
    w.Header().Set("Connection", "keep-alive")
    ch := make(chan string, 32)
    pending := b.addSubscriber(ch)
    defer b.removeSubscriber(ch)
    _, _ = fmt.Fprint(w, ": CSM Visualizador XML broker\n\n")
    for _, p := range pending { writeEvent(w, p) }
    flusher.Flush()
    ticker := time.NewTicker(12 * time.Second)
    defer ticker.Stop()
    for {
        select {
        case <-r.Context().Done(): return
        case p := <-ch: writeEvent(w, p); flusher.Flush()
        case <-ticker.C: _, _ = fmt.Fprint(w, ": ping\n\n"); flusher.Flush()
        }
    }
}

func (b *broker) handleHealth(w http.ResponseWriter, r *http.Request) {
    setCORS(w)
    processes := len(processIDsByName(coreName))
    b.mu.Lock()
    info := map[string]any{
        "ok": true,
        "core_pid": b.corePID,
        "core_processes": processes,
        "subscribers": len(b.subscribers),
        "pending": len(b.pending),
        "ack_count": b.ackCount,
        "last_ack": b.lastAck,
    }
    b.mu.Unlock()
    w.Header().Set("Content-Type", "application/json")
    _ = json.NewEncoder(w).Encode(info)
}

func (b *broker) supervise() {
    ticker := time.NewTicker(1 * time.Second)
    defer ticker.Stop()
    var noCoreSince time.Time
    for range ticker.C {
        if len(processIDsByName(coreName)) > 0 { noCoreSince = time.Time{}; continue }
        if noCoreSince.IsZero() { noCoreSince = time.Now(); continue }
        if time.Since(noCoreSince) > 4*time.Second { os.Exit(0) }
    }
}

func main() {
    core, dir, err := corePath()
    if err != nil {
        messageBox("Não encontrei os arquivos internos do CSM Visualizador XML. Reinstale o software pelo instalador oficial.", "CSM Visualizador XML")
        return
    }
    if len(os.Args) > 1 && os.Args[1] == "--csm-launcher-selftest" { return }
    paths := normalizePaths(os.Args[1:])
    if postExisting(paths) { return }

    ln, err := net.Listen("tcp", brokerAddress)
    if err != nil {
        time.Sleep(250 * time.Millisecond)
        if postExisting(paths) { return }
        messageBox("O CSM Visualizador XML já está iniciando, mas ainda não respondeu. Tente novamente em alguns segundos.", "CSM Visualizador XML")
        return
    }

    b := newBroker(core, dir)
    mux := http.NewServeMux()
    mux.HandleFunc("/open", b.handleOpen)
    mux.HandleFunc("/activate", b.handleActivate)
    mux.HandleFunc("/ack", b.handleAck)
    mux.HandleFunc("/events", b.handleEvents)
    mux.HandleFunc("/health", b.handleHealth)
    server := &http.Server{Handler: mux, ReadHeaderTimeout: 2 * time.Second}
    go func() { _ = server.Serve(ln) }()
    go b.supervise()

    if err := b.adoptOrStartCore(); err != nil {
        _ = server.Close()
        messageBox("Não foi possível iniciar o CSM Visualizador XML.\n\n"+err.Error(), "CSM Visualizador XML")
        return
    }
    for _, p := range paths { b.queuePath(p) }
    if owner, ok := waitRecoverAnyCoreWindow(15 * time.Second); ok { b.setCoreState(owner, time.Time{}) }

    // O broker permanece invisível enquanto o Core estiver aberto e recebe os próximos XMLs.
    select {}
}
