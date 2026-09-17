from pathlib import Path

MARKER='CSM_POSTINSTALL_LAUNCHER_3112'
p=Path('installer-v2/launcher/main.go')
s=p.read_text(encoding='utf-8')
if MARKER in s:
    print('Launcher pós-instalação 3.11.2 já aplicado')
    raise SystemExit(0)

old='''func killAllCoreProcesses() {\n    cmd := exec.Command("taskkill.exe", "/F", "/IM", coreName)'''
new='''func killAllCoreProcesses() {\n    // CSM_POSTINSTALL_LAUNCHER_3112: /T encerra também o WebView2 filho do Core antigo.\n    cmd := exec.Command("taskkill.exe", "/F", "/T", "/IM", coreName)'''
if old not in s:
    raise RuntimeError('killAllCoreProcesses esperado não encontrado')
s=s.replace(old,new,1)

old_main='''    if len(os.Args) > 1 && os.Args[1] == "--csm-launcher-selftest" { return }\n    paths := normalizePaths(os.Args[1:])\n    if postExisting(paths) { return }\n\n    ln, err := net.Listen("tcp", brokerAddress)\n    if err != nil {\n        time.Sleep(250 * time.Millisecond)\n        if postExisting(paths) { return }\n        messageBox("O CSM Visualizador XML já está iniciando, mas ainda não respondeu. Tente novamente em alguns segundos.", "CSM Visualizador XML")\n        return\n    }'''
new_main='''    if len(os.Args) > 1 && os.Args[1] == "--csm-launcher-selftest" { return }\n\n    freshPostInstall := false\n    for _, a := range os.Args[1:] {\n        if strings.EqualFold(strings.TrimSpace(a), "--post-install-fresh") { freshPostInstall = true; break }\n    }\n    paths := normalizePaths(os.Args[1:])\n\n    if freshPostInstall {\n        // O instalador ainda está terminando quando o checkbox final inicia o launcher.\n        // Dá tempo para os processos antigos fecharem, mata o Core + WebView filhos e NÃO\n        // reutiliza um broker de versão anterior.\n        time.Sleep(2500 * time.Millisecond)\n        killAllCoreProcesses()\n    } else if postExisting(paths) {\n        return\n    }\n\n    var ln net.Listener\n    if freshPostInstall {\n        deadline := time.Now().Add(6 * time.Second)\n        for {\n            ln, err = net.Listen("tcp", brokerAddress)\n            if err == nil || time.Now().After(deadline) { break }\n            time.Sleep(250 * time.Millisecond)\n        }\n    } else {\n        ln, err = net.Listen("tcp", brokerAddress)\n    }\n    if err != nil {\n        time.Sleep(250 * time.Millisecond)\n        if !freshPostInstall && postExisting(paths) { return }\n        messageBox("O CSM Visualizador XML já está iniciando, mas ainda não respondeu. Tente novamente em alguns segundos.", "CSM Visualizador XML")\n        return\n    }'''
if old_main not in s:
    raise RuntimeError('Bloco main esperado não encontrado para modo pós-instalação')
s=s.replace(old_main,new_main,1)

p.write_text(s,encoding='utf-8',newline='\n')
print('Launcher 3.11.2: primeira abertura não reutiliza Core/broker/WebView antigo.')
