using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Automation;
using System.Windows.Forms;

internal static class CsmPublicNfeViewer
{
    private static string _statusPath = "";
    private static string _logPath = "";
    private static string _key = "";
    private static IntPtr _portalHwnd = IntPtr.Zero;

    [DllImport("user32.dll")] private static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] private static extern bool IsWindow(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    private const int SW_RESTORE = 9;
    private const uint WM_CLOSE = 0x0010;

    [STAThread]
    private static int Main(string[] args)
    {
        if (args.Length == 1 && String.Equals(args[0], "--selftest", StringComparison.OrdinalIgnoreCase))
            return SelfTest();

        if (args.Length < 1) return 10;
        _key = DigitsOnly(args[0]);
        var root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CSM", "VisualizadorXML", "public-nfe");
        var jobId = DateTime.UtcNow.Ticks.ToString(CultureInfo.InvariantCulture);
        _statusPath = args.Length >= 2 && !String.IsNullOrWhiteSpace(args[1]) ? args[1] : Path.Combine(root, "jobs", jobId + ".json");
        var pdfPath = args.Length >= 3 && !String.IsNullOrWhiteSpace(args[2]) ? args[2] : Path.Combine(root, "cache", "Consulta Pública NF-e " + _key + ".pdf");
        if (_key.Length != 44) return 11;

        try
        {
            Directory.CreateDirectory(root);
            Directory.CreateDirectory(Path.GetDirectoryName(_statusPath));
            Directory.CreateDirectory(Path.GetDirectoryName(pdfPath));
            _logPath = Path.Combine(root, "consulta-publica.log");

            WriteStatus("starting", "Abrindo a consulta pública oficial da NF-e.", "", false);
            var browser = FindBrowser();
            if (String.IsNullOrWhiteSpace(browser))
            {
                WriteStatus("error", "Microsoft Edge ou Google Chrome não foi encontrado neste computador.", "", false);
                return 12;
            }

            var profile = Path.Combine(root, "browser-profile");
            Directory.CreateDirectory(profile);
            var url = "https://www.nfe.fazenda.gov.br/portal/consultaRecaptcha.aspx?tipoConsulta=completa&nfe=" + _key;

            Process p = StartPortal(browser, profile, url);
            var win = WaitForPortalWindow(TimeSpan.FromSeconds(45));
            if (win == null)
            {
                WriteStatus("error", "A janela oficial da consulta NF-e não abriu.", "", false);
                TryKill(p);
                return 13;
            }

            _portalHwnd = LookupHwnd(win);
            FocusWindow(_portalHwnd);
            TrySetKey(win, _key);
            WriteStatus("validation", "Se a Receita solicitar hCaptcha, faça a validação na janela oficial. O CSM continuará automaticamente depois.", "", false);

            var deadline = DateTime.UtcNow.AddMinutes(10);
            while (DateTime.UtcNow < deadline)
            {
                if (_portalHwnd != IntPtr.Zero && !IsWindow(_portalHwnd))
                {
                    WriteStatus("error", "A janela da Receita foi fechada antes da conclusão da consulta.", "", false);
                    return 14;
                }

                win = FindPortalWindow() ?? win;
                string pageText = SnapshotText(win, 220000);
                if (LooksLikePublicResult(pageText, _key))
                {
                    WriteStatus("result_found", "NF-e localizada. Preparando a visualização dentro do CSM.", "", false);
                    break;
                }

                string err = DetectPortalError(pageText);
                if (!String.IsNullOrEmpty(err))
                {
                    WriteStatus("error", err, "", false);
                    return 15;
                }

                if (LooksLikeCaptcha(pageText))
                    WriteStatus("validation", "Valide o hCaptcha na janela oficial da Receita. Depois disso o CSM continua sozinho.", "", false);

                Thread.Sleep(700);
            }

            win = FindPortalWindow() ?? win;
            if (!LooksLikePublicResult(SnapshotText(win, 220000), _key))
            {
                WriteStatus("error", "A consulta pública não foi concluída no prazo.", "", false);
                return 16;
            }

            var htmlPath = Path.Combine(Path.GetDirectoryName(pdfPath), "consulta-" + _key + ".html");
            TryDelete(htmlPath);
            WriteStatus("capturing", "Capturando a Consulta Completa da NF-e.", "", false);

            if (!SaveCurrentPage(win, htmlPath))
            {
                WriteStatus("error", "A NF-e foi localizada, mas o CSM não conseguiu capturar a página de consulta.", "", false);
                return 17;
            }

            ClosePortalWindow();
            Thread.Sleep(700);

            WriteStatus("rendering", "Gerando a visualização fiscal no CSM.", "", false);
            TryDelete(pdfPath);
            if (!RenderHtmlToPdf(browser, htmlPath, pdfPath))
            {
                WriteStatus("error", "A consulta foi capturada, mas não foi possível gerar a visualização em PDF.", "", false);
                return 18;
            }

            WriteStatus("done", "NF-e consultada e aberta no Visualizador.", pdfPath, true);
            NotifyBrokerOpen(pdfPath);
            CleanupSavedPage(htmlPath);
            return 0;
        }
        catch (Exception ex)
        {
            Log("Erro: " + ex.GetType().Name + " - " + ex.Message);
            WriteStatus("error", "Falha na consulta pública: " + ex.Message, "", false);
            return 99;
        }
        finally
        {
            if (_portalHwnd != IntPtr.Zero && IsWindow(_portalHwnd)) ClosePortalWindow();
        }
    }

    private static int SelfTest()
    {
        try
        {
            const string key = "35260802562527000135550010000194421659945019";
            if (DigitsOnly("35 2608-02562527000135 55 001 000019442 1659945019") != key) return 71;
            var sample = "Público em Geral Nota Fiscal Eletrônica Consulta Completa da NF-e Consulta da NF-e Dados Gerais Chave de Acesso " +
                         key + " Emitente Destinatário Produtos e Serviços Totais Transporte Cobrança Informações Adicionais";
            if (!LooksLikePublicResult(sample, key)) return 72;
            if (!LooksLikeCaptcha("Widget contendo caixa de seleção para desafio de segurança hCaptcha")) return 73;
            if (LooksLikePublicResult("Consultar NF-e Chave de Acesso hCaptcha", key)) return 74;
            return 0;
        }
        catch { return 79; }
    }

    private static Process StartPortal(string browser, string profile, string url)
    {
        var psi = new ProcessStartInfo();
        psi.FileName = browser;
        psi.Arguments = "--app="" + url + "" --user-data-dir="" + profile + "" --no-first-run --no-default-browser-check --window-size=1080,860";
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;
        var p = Process.Start(psi);
        Log("Portal oficial iniciado.");
        return p;
    }

    private static string FindBrowser()
    {
        var pf = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
        var pfx86 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);
        var local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var candidates = new[]
        {
            Path.Combine(pfx86, "Microsoft", "Edge", "Application", "msedge.exe"),
            Path.Combine(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
            Path.Combine(local, "Microsoft", "Edge", "Application", "msedge.exe"),
            Path.Combine(pf, "Google", "Chrome", "Application", "chrome.exe"),
            Path.Combine(pfx86, "Google", "Chrome", "Application", "chrome.exe"),
            Path.Combine(local, "Google", "Chrome", "Application", "chrome.exe")
        };
        return candidates.FirstOrDefault(File.Exists) ?? "";
    }

    private static AutomationElement WaitForPortalWindow(TimeSpan timeout)
    {
        var until = DateTime.UtcNow.Add(timeout);
        while (DateTime.UtcNow < until)
        {
            var w = FindPortalWindow();
            if (w != null) return w;
            Thread.Sleep(120);
        }
        return null;
    }

    private static AutomationElement FindPortalWindow()
    {
        try
        {
            var wins = AutomationElement.RootElement.FindAll(TreeScope.Children, new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window));
            foreach (AutomationElement w in wins)
            {
                var name = NormalizeText(SafeName(w));
                if (name.Contains("nota fiscal eletrônica") || name.Contains("nota fiscal eletronica") ||
                    name.Contains("consultar nf-e") || name.Contains("consulta da nf-e") ||
                    name.Contains("portal da nota fiscal"))
                    return w;
            }
        }
        catch { }
        return null;
    }

    private static IntPtr LookupHwnd(AutomationElement win)
    {
        if (win == null) return IntPtr.Zero;
        try { return new IntPtr(win.Current.NativeWindowHandle); } catch { return IntPtr.Zero; }
    }

    private static void FocusWindow(IntPtr hwnd)
    {
        if (hwnd == IntPtr.Zero) return;
        try { ShowWindow(hwnd, SW_RESTORE); SetForegroundWindow(hwnd); } catch { }
    }

    private static bool TrySetKey(AutomationElement win, string key)
    {
        try
        {
            var edits = win.FindAll(TreeScope.Descendants, new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Edit));
            var ranked = new List<Tuple<AutomationElement, int>>();
            foreach (AutomationElement e in edits)
            {
                string t = NormalizeText(ElementText(e));
                int score = 0;
                if (t.Contains("chave")) score += 20;
                if (t.Contains("acesso")) score += 10;
                if (t.Contains("44")) score += 5;
                ranked.Add(Tuple.Create(e, score));
            }
            foreach (var item in ranked.OrderByDescending(x => x.Item2))
            {
                object p;
                if (item.Item1.TryGetCurrentPattern(ValuePattern.Pattern, out p))
                {
                    var vp = (ValuePattern)p;
                    if (DigitsOnly(vp.Current.Value) == key) return true;
                    vp.SetValue(key);
                    return true;
                }
            }
        }
        catch { }
        return false;
    }

    private static string SnapshotText(AutomationElement win, int maxChars)
    {
        if (win == null) return "";
        var sb = new StringBuilder();
        try
        {
            var all = win.FindAll(TreeScope.Descendants, Condition.TrueCondition);
            foreach (AutomationElement e in all)
            {
                string name = SafeName(e);
                if (String.IsNullOrWhiteSpace(name)) continue;
                if (sb.Length + name.Length + 2 > maxChars) break;
                sb.Append(name).Append(' ');
            }
        }
        catch { }
        return sb.ToString();
    }

    private static bool LooksLikePublicResult(string text, string key)
    {
        string n = NormalizeText(text);
        int sections = 0;
        if (n.Contains("consulta da nf-e") || n.Contains("consulta completa da nf-e")) sections += 3;
        if (n.Contains("dados gerais")) sections++;
        if (n.Contains("emitente")) sections++;
        if (n.Contains("destinatario")) sections++;
        if (n.Contains("produtos") && n.Contains("servicos")) sections++;
        if (n.Contains("totais")) sections++;
        string digits = DigitsOnly(text);
        bool keySeen = digits.Contains(key);
        return sections >= 6 && (keySeen || n.Contains("chave de acesso"));
    }

    private static bool LooksLikeCaptcha(string text)
    {
        string n = NormalizeText(text);
        return n.Contains("hcaptcha") || n.Contains("desafio de seguranca") || n.Contains("sou humano") || n.Contains("i am human");
    }

    private static string DetectPortalError(string text)
    {
        string n = NormalizeText(text);
        if (n.Contains("nf-e inexistente") || n.Contains("nfe inexistente")) return "NF-e inexistente na consulta pública.";
        if (n.Contains("chave de acesso invalida")) return "A Receita informou que a chave de acesso é inválida.";
        if (n.Contains("nota fiscal nao encontrada") || n.Contains("nf-e nao encontrada")) return "NF-e não encontrada na consulta pública.";
        return "";
    }

    private static bool SaveCurrentPage(AutomationElement win, string htmlPath)
    {
        var hwnd = LookupHwnd(win);
        FocusWindow(hwnd);
        Thread.Sleep(250);
        try { SendKeys.SendWait("^s"); } catch { return false; }

        var dlg = WaitForWindowNames(new[] { "salvar como", "save as" }, TimeSpan.FromSeconds(15));
        if (dlg == null) return false;
        if (!SetFileName(dlg, htmlPath)) return false;
        if (!InvokeButton(dlg, new[] { "salvar", "save" })) return false;

        var replace = WaitForWindowNames(new[] { "confirmar salvar como", "confirm save as", "substituir" }, TimeSpan.FromSeconds(2));
        if (replace != null) InvokeButton(replace, new[] { "sim", "yes", "substituir", "replace" });

        var until = DateTime.UtcNow.AddSeconds(30);
        while (DateTime.UtcNow < until)
        {
            try
            {
                var fi = new FileInfo(htmlPath);
                if (fi.Exists && fi.Length > 500) return true;
            }
            catch { }
            Thread.Sleep(250);
        }
        return false;
    }

    private static AutomationElement WaitForWindowNames(string[] names, TimeSpan timeout)
    {
        var until = DateTime.UtcNow.Add(timeout);
        while (DateTime.UtcNow < until)
        {
            try
            {
                var wins = AutomationElement.RootElement.FindAll(TreeScope.Children, new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window));
                foreach (AutomationElement w in wins)
                {
                    var n = NormalizeText(SafeName(w));
                    if (names.Any(x => n.Contains(NormalizeText(x)))) return w;
                }
            }
            catch { }
            Thread.Sleep(120);
        }
        return null;
    }

    private static bool SetFileName(AutomationElement dlg, string path)
    {
        try
        {
            var edits = dlg.FindAll(TreeScope.Descendants, new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Edit));
            var ranked = new List<Tuple<AutomationElement, int>>();
            foreach (AutomationElement e in edits)
            {
                var t = NormalizeText(ElementText(e));
                int score = 0;
                if (t.Contains("nome")) score += 15;
                if (t.Contains("file name")) score += 15;
                if (t.Contains("arquivo")) score += 5;
                ranked.Add(Tuple.Create(e, score));
            }
            foreach (var item in ranked.OrderByDescending(x => x.Item2))
            {
                object p;
                if (item.Item1.TryGetCurrentPattern(ValuePattern.Pattern, out p))
                {
                    ((ValuePattern)p).SetValue(path);
                    return true;
                }
            }
        }
        catch { }
        return false;
    }

    private static bool InvokeButton(AutomationElement root, string[] labels)
    {
        try
        {
            var buttons = root.FindAll(TreeScope.Descendants, new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button));
            foreach (AutomationElement b in buttons)
            {
                var n = NormalizeText(SafeName(b));
                if (!labels.Any(x => n == NormalizeText(x) || n.Contains(NormalizeText(x)))) continue;
                object p;
                if (b.TryGetCurrentPattern(InvokePattern.Pattern, out p))
                {
                    ((InvokePattern)p).Invoke();
                    return true;
                }
                try { b.SetFocus(); SendKeys.SendWait("{ENTER}"); return true; } catch { }
            }
        }
        catch { }
        return false;
    }

    private static bool RenderHtmlToPdf(string browser, string htmlPath, string pdfPath)
    {
        try
        {
            var uri = new Uri(htmlPath).AbsoluteUri;
            var tempProfile = Path.Combine(Path.GetDirectoryName(pdfPath), "headless-profile-" + DateTime.UtcNow.Ticks.ToString(CultureInfo.InvariantCulture));
            Directory.CreateDirectory(tempProfile);
            var psi = new ProcessStartInfo();
            psi.FileName = browser;
            psi.Arguments = "--headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf-no-header --user-data-dir="" + tempProfile +
                            "" --print-to-pdf="" + pdfPath + "" "" + uri + """;
            psi.UseShellExecute = false;
            psi.CreateNoWindow = true;
            var p = Process.Start(psi);
            if (p == null) return false;
            if (!p.WaitForExit(60000)) { try { p.Kill(); } catch { } }
            var until = DateTime.UtcNow.AddSeconds(10);
            while (DateTime.UtcNow < until)
            {
                if (File.Exists(pdfPath) && new FileInfo(pdfPath).Length > 1000) { TryDeleteDirectory(tempProfile); return true; }
                Thread.Sleep(200);
            }
            TryDeleteDirectory(tempProfile);
        }
        catch (Exception ex) { Log("Render PDF: " + ex.Message); }
        return false;
    }

    private static void NotifyBrokerOpen(string path)
    {
        try
        {
            var body = "{\"paths\":[\"" + JsonEscape(path) + "\"]}";
            using (var wc = new WebClient())
            {
                wc.Headers[HttpRequestHeader.ContentType] = "application/json";
                wc.UploadString("http://127.0.0.1:47878/open", "POST", body);
            }
            Log("Consulta pública enviada ao Visualizador.");
        }
        catch (Exception ex) { Log("Falha ao avisar o broker: " + ex.Message); }
    }

    private static void ClosePortalWindow()
    {
        if (_portalHwnd == IntPtr.Zero) return;
        try { if (IsWindow(_portalHwnd)) PostMessage(_portalHwnd, WM_CLOSE, IntPtr.Zero, IntPtr.Zero); } catch { }
        _portalHwnd = IntPtr.Zero;
    }

    private static void CleanupSavedPage(string htmlPath)
    {
        TryDelete(htmlPath);
        var dir = Path.GetDirectoryName(htmlPath);
        var name = Path.GetFileNameWithoutExtension(htmlPath);
        TryDeleteDirectory(Path.Combine(dir, name + "_arquivos"));
        TryDeleteDirectory(Path.Combine(dir, name + "_files"));
    }

    private static void TryKill(Process p)
    {
        try { if (p != null && !p.HasExited) p.Kill(); } catch { }
    }

    private static void TryDelete(string path)
    {
        try { if (File.Exists(path)) File.Delete(path); } catch { }
    }

    private static void TryDeleteDirectory(string path)
    {
        try { if (Directory.Exists(path)) Directory.Delete(path, true); } catch { }
    }

    private static string ElementText(AutomationElement e)
    {
        try { return (e.Current.Name ?? "") + " " + (e.Current.HelpText ?? "") + " " + (e.Current.AutomationId ?? ""); }
        catch { return ""; }
    }

    private static string SafeName(AutomationElement e)
    {
        try { return e.Current.Name ?? ""; } catch { return ""; }
    }

    private static string DigitsOnly(string v)
    {
        var sb = new StringBuilder();
        foreach (char c in v ?? "") if (c >= '0' && c <= '9') sb.Append(c);
        return sb.ToString();
    }

    private static string NormalizeText(string value)
    {
        if (String.IsNullOrWhiteSpace(value)) return "";
        var form = value.Normalize(NormalizationForm.FormD);
        var sb = new StringBuilder();
        foreach (char ch in form)
            if (CharUnicodeInfo.GetUnicodeCategory(ch) != UnicodeCategory.NonSpacingMark) sb.Append(Char.ToLowerInvariant(ch));
        return sb.ToString().Normalize(NormalizationForm.FormC);
    }

    private static void WriteStatus(string state, string message, string pdfPath, bool ok)
    {
        try
        {
            var dir = Path.GetDirectoryName(_statusPath);
            if (!String.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);
            var json = "{" +
                       "\"ok\":" + (ok ? "true" : "false") + "," +
                       "\"state\":\"" + JsonEscape(state) + "\"," +
                       "\"message\":\"" + JsonEscape(message) + "\"," +
                       "\"pdf_path\":\"" + JsonEscape(pdfPath) + "\"," +
                       "\"key\":\"" + JsonEscape(_key) + "\"," +
                       "\"updated_utc\":\"" + DateTime.UtcNow.ToString("o", CultureInfo.InvariantCulture) + "\"" +
                       "}";
            var tmp = _statusPath + ".tmp";
            File.WriteAllText(tmp, json, new UTF8Encoding(false));
            if (File.Exists(_statusPath)) File.Delete(_statusPath);
            File.Move(tmp, _statusPath);
        }
        catch { }
    }

    private static string JsonEscape(string v)
    {
        return (v ?? "").Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", "\\r").Replace("\n", "\\n");
    }

    private static void Log(string text)
    {
        try
        {
            if (String.IsNullOrWhiteSpace(_logPath)) return;
            File.AppendAllText(_logPath, DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff") + " " + text + Environment.NewLine, Encoding.UTF8);
        }
        catch { }
    }
}
