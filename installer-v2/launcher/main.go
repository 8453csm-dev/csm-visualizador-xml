//go:build windows

package main

import (
    "os"
    "os/exec"
    "path/filepath"
    "strings"
    "syscall"
    "time"
    "unsafe"
)

const (
    th32csSnapProcess = 0x00000002
    swShow            = 5
    swRestore         = 9
    swpShowWindow     = 0x0040
    smXVirtualScreen  = 76
    smYVirtualScreen  = 77
    smCXVirtualScreen = 78
    smCYVirtualScreen = 79
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
    procIsIconic                 = user32.NewProc("IsIconic")
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

type rect struct {
    Left, Top, Right, Bottom int32
}

type windowCandidate struct {
    hwnd    uintptr
    title   string
    visible bool
    iconic  bool
    rect    rect
}

func utf16ToString(v []uint16) string {
    n := 0
    for n < len(v) && v[n] != 0 {
        n++
    }
    return syscall.UTF16ToString(v[:n])
}

func processIDsByName(name string) []uint32 {
    snap, _, _ := procCreateToolhelp32Snapshot.Call(th32csSnapProcess, 0)
    if snap == ^uintptr(0) || snap == 0 {
        return nil
    }
    defer syscall.CloseHandle(syscall.Handle(snap))

    var pe processEntry32
    pe.Size = uint32(unsafe.Sizeof(pe))
    var result []uint32
    ok, _, _ := procProcess32FirstW.Call(snap, uintptr(unsafe.Pointer(&pe)))
    for ok != 0 {
        if strings.EqualFold(utf16ToString(pe.ExeFile[:]), name) {
            result = append(result, pe.ProcessID)
        }
        ok, _, _ = procProcess32NextW.Call(snap, uintptr(unsafe.Pointer(&pe)))
    }
    return result
}

func windowTitle(hwnd uintptr) string {
    n, _, _ := procGetWindowTextLengthW.Call(hwnd)
    if n == 0 {
        return ""
    }
    buf := make([]uint16, n+1)
    procGetWindowTextW.Call(hwnd, uintptr(unsafe.Pointer(&buf[0])), uintptr(len(buf)))
    return syscall.UTF16ToString(buf)
}

func windowsForPID(pid uint32) []windowCandidate {
    var out []windowCandidate
    cb := syscall.NewCallback(func(hwnd uintptr, lparam uintptr) uintptr {
        var winPID uint32
        procGetWindowThreadProcessId.Call(hwnd, uintptr(unsafe.Pointer(&winPID)))
        if winPID != pid {
            return 1
        }
        title := strings.TrimSpace(windowTitle(hwnd))
        if title == "" {
            return 1
        }
        var r rect
        procGetWindowRect.Call(hwnd, uintptr(unsafe.Pointer(&r)))
        vis, _, _ := procIsWindowVisible.Call(hwnd)
        ico, _, _ := procIsIconic.Call(hwnd)
        out = append(out, windowCandidate{hwnd: hwnd, title: title, visible: vis != 0, iconic: ico != 0, rect: r})
        return 1
    })
    procEnumWindows.Call(cb, 0)
    return out
}

func primaryWindow(pid uint32) (windowCandidate, bool) {
    wins := windowsForPID(pid)
    if len(wins) == 0 {
        return windowCandidate{}, false
    }
    for _, w := range wins {
        if strings.Contains(strings.ToLower(w.title), "csm visualizador xml") {
            return w, true
        }
    }
    for _, w := range wins {
        if w.visible {
            return w, true
        }
    }
    return wins[0], true
}

func isOffScreen(r rect) bool {
    x, _, _ := procGetSystemMetrics.Call(smXVirtualScreen)
    y, _, _ := procGetSystemMetrics.Call(smYVirtualScreen)
    w, _, _ := procGetSystemMetrics.Call(smCXVirtualScreen)
    h, _, _ := procGetSystemMetrics.Call(smCYVirtualScreen)
    vx, vy := int32(x), int32(y)
    vw, vh := int32(w), int32(h)
    if vw <= 0 || vh <= 0 {
        return false
    }
    return r.Right <= vx || r.Left >= vx+vw || r.Bottom <= vy || r.Top >= vy+vh
}

func recoverWindow(pid uint32) bool {
    w, ok := primaryWindow(pid)
    if !ok {
        return false
    }
    width := w.rect.Right - w.rect.Left
    height := w.rect.Bottom - w.rect.Top
    if width < 300 {
        width = 1280
    }
    if height < 200 {
        height = 820
    }

    procShowWindowAsync.Call(w.hwnd, swRestore)
    procShowWindow.Call(w.hwnd, swShow)

    if isOffScreen(w.rect) || w.rect.Left < -30000 || w.rect.Top < -30000 {
        x, _, _ := procGetSystemMetrics.Call(smXVirtualScreen)
        y, _, _ := procGetSystemMetrics.Call(smYVirtualScreen)
        nx, ny := int32(x)+80, int32(y)+80
        procSetWindowPos.Call(w.hwnd, 0, uintptr(nx), uintptr(ny), uintptr(width), uintptr(height), swpShowWindow)
    } else {
        procSetWindowPos.Call(w.hwnd, 0, 0, 0, 0, 0, swpShowWindow|0x0001|0x0002)
    }

    procBringWindowToTop.Call(w.hwnd)
    procSetForegroundWindow.Call(w.hwnd)
    return true
}

func killPID(pid uint32) {
    p, err := os.FindProcess(int(pid))
    if err == nil {
        _ = p.Kill()
    }
}

func messageBox(text, title string) {
    t, _ := syscall.UTF16PtrFromString(text)
    c, _ := syscall.UTF16PtrFromString(title)
    procMessageBoxW.Call(0, uintptr(unsafe.Pointer(t)), uintptr(unsafe.Pointer(c)), 0x10)
}

func corePath() (string, string, error) {
    exe, err := os.Executable()
    if err != nil {
        return "", "", err
    }
    dir := filepath.Dir(exe)
    core := filepath.Join(dir, "CSM Visualizador XML Core.exe")
    if _, err := os.Stat(core); err != nil {
        return "", dir, err
    }
    return core, dir, nil
}

func waitAndRecover(pid uint32, timeout time.Duration) bool {
    deadline := time.Now().Add(timeout)
    for time.Now().Before(deadline) {
        if recoverWindow(pid) {
            return true
        }
        time.Sleep(80 * time.Millisecond)
    }
    return false
}

func main() {
    core, dir, err := corePath()
    if err != nil {
        messageBox("Não encontrei os arquivos internos do CSM Visualizador XML. Reinstale o software pelo instalador oficial.", "CSM Visualizador XML")
        return
    }

    if len(os.Args) > 1 && os.Args[1] == "--csm-launcher-selftest" {
        return
    }

    args := os.Args[1:]
    existing := processIDsByName("CSM Visualizador XML Core.exe")

    if len(args) == 0 {
        for _, pid := range existing {
            if recoverWindow(pid) {
                return
            }
        }
        if len(existing) > 0 {
            time.Sleep(700 * time.Millisecond)
            for _, pid := range existing {
                if !recoverWindow(pid) {
                    killPID(pid)
                } else {
                    return
                }
            }
            time.Sleep(250 * time.Millisecond)
        }
    } else {
        for _, pid := range existing {
            if !recoverWindow(pid) {
                killPID(pid)
            }
        }
    }

    cmd := exec.Command(core, args...)
    cmd.Dir = dir
    if err := cmd.Start(); err != nil {
        messageBox("Não foi possível iniciar o CSM Visualizador XML.\n\n"+err.Error(), "CSM Visualizador XML")
        return
    }

    if waitAndRecover(uint32(cmd.Process.Pid), 12*time.Second) {
        return
    }

    for _, pid := range processIDsByName("CSM Visualizador XML Core.exe") {
        if recoverWindow(pid) {
            return
        }
    }

    messageBox("O CSM Visualizador XML iniciou, mas a janela não ficou disponível. O launcher tentou restaurá-la automaticamente. Se isso se repetir, reinstale esta correção.", "CSM Visualizador XML")
}
