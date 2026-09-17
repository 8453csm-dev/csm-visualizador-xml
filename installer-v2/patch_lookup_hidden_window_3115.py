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

# Detecta a nova janela com baixa latência para que, na prática, ela não fique
# visível como uma segunda tela. Depois mantemos o AutomationElement salvo.
old_wait_loop='''        while (DateTime.UtcNow < until) { var w = FindLookupWindow(); if (w != null) return w; Thread.Sleep(250); }'''
new_wait_loop='''        while (DateTime.UtcNow < until) { var w = FindLookupWindow(); if (w != null) return w; Thread.Sleep(35); }'''
if old_wait_loop not in s: raise RuntimeError('Polling de WaitForLookupWindow não encontrado')
s=s.replace(old_wait_loop,new_wait_loop,1)

old_wait='''            var win = WaitForLookupWindow(TimeSpan.FromSeconds(45));\n            if (win == null) { Log("Janela Consulta DANFE não encontrada."); return 11; }'''
new_wait='''            var win = WaitForLookupWindow(TimeSpan.FromSeconds(45));\n            if (win == null) { Log("Janela Consulta DANFE não encontrada."); return 11; }\n            _managedLookupWindow = win;\n            HideLookupWindow(win);'''
if old_wait not in s: raise RuntimeError('Abertura da janela de consulta não encontrada')
s=s.replace(old_wait,new_wait,1)

# ValuePattern funciona sem mostrar a janela. Somente se for necessário o
# fallback por teclado, revelamos por instantes e ocultamos novamente.
old_key_fallback='''            try { c.Item1.SetFocus(); Thread.Sleep(80); SendKeys.SendWait("^a"); SendKeys.SendWait(key); Thread.Sleep(100); Log("Chave preenchida via foco/teclado como fallback."); return true; }\n            catch { }'''
new_key_fallback='''            try\n            {\n                RevealLookupWindow(win);\n                c.Item1.SetFocus(); Thread.Sleep(80); SendKeys.SendWait("^a"); SendKeys.SendWait(key); Thread.Sleep(100);\n                Log("Chave preenchida via foco/teclado como fallback temporariamente visível."); return true;\n            }\n            catch { }\n            finally { HideLookupWindow(win); }'''
if old_key_fallback not in s: raise RuntimeError('Fallback de teclado da chave não encontrado')
s=s.replace(old_key_fallback,new_key_fallback,1)

# Primeiro tenta acionar a busca com UI Automation enquanto oculto. Só revela
# se o site não expuser InvokePattern e precisar do fallback manual do Windows.
search_anchor='''            if (!TryInvokeSearch(win)) { Log("Botão de consulta não foi localizado via UI Automation."); return 13; }\n'''
search_new='''            if (!TryInvokeSearch(win))\n            {\n                RevealLookupWindow(win);\n                var retried = TryInvokeSearch(win);\n                HideLookupWindow(win);\n                if (!retried) { Log("Botão de consulta não foi localizado via UI Automation."); return 13; }\n            }\n            HideLookupWindow(win);\n'''
if search_anchor not in s: raise RuntimeError('Acionamento da consulta não encontrado')
s=s.replace(search_anchor,search_new,1)

# Depois de ocultar, não procure a janela novamente pela árvore raiz.
old_loop='''                win = FindLookupWindow();\n                if (win == null) { Log("Janela de consulta foi fechada antes do XML."); return 14; }'''
new_loop='''                win = _managedLookupWindow;\n                if (!IsLookupWindowAlive(win)) { Log("Janela de consulta foi encerrada antes do XML."); return 14; }'''
if old_loop not in s:
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
        s=s.replace(needle,needle+'\n        HideLookupWindow(dlg);',1)

# Feche a janela externa em qualquer saída normal/erro. Se apareceu CAPTCHA,
# ela permanece disponível ao usuário para a intervenção necessária.
old_catch='''        catch (Exception ex) { Log("Erro não tratado: " + ex.GetType().Name + " - " + ex.Message); return 99; }\n    }'''
new_catch='''        catch (Exception ex) { Log("Erro não tratado: " + ex.GetType().Name + " - " + ex.Message); return 99; }\n        finally\n        {\n            if (!_captchaLogged)\n            {\n                CloseLookupWindow(_managedLookupWindow);\n                Log("Janela externa do provedor encerrada automaticamente.");\n            }\n        }\n    }'''
if old_catch not in s: raise RuntimeError('Final do Main não encontrado')
s=s.replace(old_catch,new_catch,1)

for tok in (MARKER,'Thread.Sleep(35)','HideLookupWindow(win)','SW_HIDE','IsLookupWindowAlive','CloseLookupWindow(_managedLookupWindow)','janela exibida somente para intervenção manual'):
    if tok not in s: raise SystemExit('Patch hidden 3.11.5 incompleto: '+tok)
p.write_text(s,encoding='utf-8',newline='\n')
print('3.11.5: provedor é ocultado assim que a janela nasce; só aparece se houver fallback manual/CAPTCHA e fecha ao terminar.')
