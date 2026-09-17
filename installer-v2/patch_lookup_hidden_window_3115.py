from pathlib import Path

MARKER='CSM_LOOKUP_HIDDEN_WINDOW_3115'
p=Path('installer-v2/launcher/consulta_danfe_helper.cs')
s=p.read_text(encoding='utf-8')
if MARKER in s:
    print('Janela oculta 3.11.5 já aplicada')
    raise SystemExit(0)

if 'using System.Runtime.InteropServices;' not in s:
    s=s.replace('using System.Linq;\n','using System.Linq;\nusing System.Runtime.InteropServices;\n',1)

field_anchor='''    private static bool _captchaLogged;\n'''
field_new='''    private static bool _captchaLogged;\n    private static AutomationElement _managedLookupWindow;\n\n    // CSM_LOOKUP_HIDDEN_WINDOW_3115\n    [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);\n    [DllImport("user32.dll")] private static extern bool IsWindow(IntPtr hWnd);\n    [DllImport("user32.dll")] private static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);\n    private const int SW_HIDE = 0;\n    private const int SW_SHOWNOACTIVATE = 4;\n    private const uint WM_CLOSE = 0x0010;\n\n    private static IntPtr LookupHwnd(AutomationElement win)\n    {\n        if (win == null) return IntPtr.Zero;\n        try { return new IntPtr(win.Current.NativeWindowHandle); } catch { return IntPtr.Zero; }\n    }\n\n    private static bool IsLookupWindowAlive(AutomationElement win)\n    {\n        var hwnd = LookupHwnd(win);\n        return hwnd != IntPtr.Zero && IsWindow(hwnd);\n    }\n\n    private static void HideLookupWindow(AutomationElement win)\n    {\n        var hwnd = LookupHwnd(win);\n        if (hwnd == IntPtr.Zero) return;\n        try { ShowWindow(hwnd, SW_HIDE); Log("Janela externa do provedor ocultada; consulta continua em segundo plano."); } catch { }\n    }\n\n    private static void RevealLookupWindow(AutomationElement win)\n    {\n        var hwnd = LookupHwnd(win);\n        if (hwnd == IntPtr.Zero) return;\n        try { ShowWindow(hwnd, SW_SHOWNOACTIVATE); Log("Janela do provedor exibida porque é necessária intervenção manual."); } catch { }\n    }\n\n    private static void CloseLookupWindow(AutomationElement win)\n    {\n        var hwnd = LookupHwnd(win);\n        if (hwnd == IntPtr.Zero) return;\n        try { if (IsWindow(hwnd)) PostMessage(hwnd, WM_CLOSE, IntPtr.Zero, IntPtr.Zero); } catch { }\n    }\n'''
if field_anchor not in s: raise RuntimeError('Campo _captchaLogged não encontrado')
s=s.replace(field_anchor,field_new,1)

# Guarde a janela encontrada para continuar usando o mesmo AutomationElement
# mesmo depois de ocultá-la (janelas ocultas podem deixar de aparecer no RootElement).
old_wait='''            var win = WaitForLookupWindow(TimeSpan.FromSeconds(45));\n            if (win == null) { Log("Janela Consulta DANFE não encontrada."); return 11; }'''
new_wait='''            var win = WaitForLookupWindow(TimeSpan.FromSeconds(45));\n            if (win == null) { Log("Janela Consulta DANFE não encontrada."); return 11; }\n            _managedLookupWindow = win;'''
if old_wait not in s: raise RuntimeError('Abertura da janela de consulta não encontrada')
s=s.replace(old_wait,new_wait,1)

# Só ocultamos depois de preencher a chave e acionar a consulta, para manter
# os fallbacks de teclado disponíveis na etapa inicial.
search_anchor='''            if (!TryInvokeSearch(win)) { Log("Botão de consulta não foi localizado via UI Automation."); return 13; }\n'''
search_new='''            if (!TryInvokeSearch(win)) { Log("Botão de consulta não foi localizado via UI Automation."); return 13; }\n            HideLookupWindow(win);\n'''
if search_anchor not in s: raise RuntimeError('Acionamento da consulta não encontrado')
s=s.replace(search_anchor,search_new,1)

# Depois de ocultar, não procure a janela novamente pela árvore raiz.
old_loop='''                win = FindLookupWindow();\n                if (win == null) { Log("Janela de consulta foi fechada antes do XML."); return 14; }'''
new_loop='''                win = _managedLookupWindow;\n                if (!IsLookupWindowAlive(win)) { Log("Janela de consulta foi encerrada antes do XML."); return 14; }'''
if old_loop not in s:
    # compatibilidade caso algum patch anterior ainda use a mensagem antiga
    old_loop='''                win = FindLookupWindow();\n                if (win == null) { Log("Janela de consulta foi fechada antes do download."); return 14; }'''
if old_loop not in s: raise RuntimeError('Loop da consulta não encontrado')
s=s.replace(old_loop,new_loop,1)

# Se houver CAPTCHA, mostramos a janela somente nesse caso para permitir ação manual.
old_captcha='''            if (text.Contains("captcha") || text.Contains("recaptcha")) { _captchaLogged = true; Log("CAPTCHA detectado; aguardando intervenção manual sem tentar contorná-lo."); return; }'''
new_captcha='''            if (text.Contains("captcha") || text.Contains("recaptcha")) { _captchaLogged = true; RevealLookupWindow(win); Log("CAPTCHA detectado; janela exibida somente para intervenção manual."); return; }'''
if old_captcha not in s: raise RuntimeError('DetectCaptcha esperado não encontrado')
s=s.replace(old_captcha,new_captcha,1)

# Caso o site abra Salvar Como, esconda também esse diálogo antes de operar.
for needle in [
    'var dlg = FindTopWindowByName("salvar como", "save as");\n        if (dlg == null) return;',
    'var dlg = FindTopWindowByName("salvar como", "save as");\n        if (dlg == null) return false;'
]:
    if needle in s:
        repl=needle+'\n        HideLookupWindow(dlg);'
        s=s.replace(needle,repl,1)

# Feche a janela externa em qualquer saída normal/erro. Se apareceu CAPTCHA,
# ela permanece disponível ao usuário para a intervenção necessária.
old_catch='''        catch (Exception ex) { Log("Erro não tratado: " + ex.GetType().Name + " - " + ex.Message); return 99; }\n    }'''
new_catch='''        catch (Exception ex) { Log("Erro não tratado: " + ex.GetType().Name + " - " + ex.Message); return 99; }\n        finally\n        {\n            if (!_captchaLogged)\n            {\n                CloseLookupWindow(_managedLookupWindow);\n                Log("Janela externa do provedor encerrada automaticamente.");\n            }\n        }\n    }'''
if old_catch not in s: raise RuntimeError('Final do Main não encontrado')
s=s.replace(old_catch,new_catch,1)

for tok in (MARKER,'ShowWindow','SW_HIDE','IsLookupWindowAlive','HideLookupWindow(win)','CloseLookupWindow(_managedLookupWindow)','janela exibida somente para intervenção manual'):
    if tok not in s: raise SystemExit('Patch hidden 3.11.5 incompleto: '+tok)
p.write_text(s,encoding='utf-8',newline='\n')
print('3.11.5: site do provedor roda oculto; janela só aparece em CAPTCHA e fecha automaticamente ao terminar.')
