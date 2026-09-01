using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Automation;
using System.Windows.Forms;

internal static class Program
{
    private static string _logPath = "";
    private static DateTime _startedAt;
    private static bool _captchaLogged;

    [STAThread]
    private static int Main(string[] args)
    {
        try
        {
            var key = args.Length > 0 ? NormalizeKey(args[0]) : "";
            if (key.Length != 44) return 10;

            var logDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CSM Visualizador XML", "logs");
            Directory.CreateDirectory(logDir);
            _logPath = Path.Combine(logDir, "consulta-danfe-automacao.log");
            _startedAt = DateTime.UtcNow;
            Log("CSM_LOOKUP_HELPER_V3 iniciado para chave " + key.Substring(0, 4) + "..." + key.Substring(40, 4));

            var win = WaitForLookupWindow(TimeSpan.FromSeconds(45));
            if (win == null)
            {
                Log("Janela Consulta DANFE não encontrada.");
                return 11;
            }

            TryAcceptCookies(win);
            Thread.Sleep(350);

            if (!TrySetKey(win, key))
            {
                Log("Não foi possível preencher a chave pela árvore de acessibilidade.");
                return 12;
            }

            TryAcceptCookies(win);
            Thread.Sleep(220);

            if (!TryInvokeSearch(win))
            {
                Log("Botão de consulta não foi localizado via UI Automation.");
                return 13;
            }

            Log("Consulta enviada; aguardando resultado e botão Baixar XML.");
            var deadline = DateTime.UtcNow.AddMinutes(6);
            var cookieTick = 0;
            while (DateTime.UtcNow < deadline)
            {
                win = FindLookupWindow();
                if (win == null)
                {
                    Log("Janela de consulta foi fechada antes do download.");
                    return 14;
                }

                if (HasMatchingXmlInDownloads(key))
                {
                    Log("XML correspondente já apareceu em Downloads; evitando clique duplicado.");
                    return 0;
                }

                if ((cookieTick++ % 6) == 0) TryAcceptCookies(win);

                if (TryInvokeDownloadXml(win))
                {
                    Log("Baixar XML acionado automaticamente.");
                    return 0;
                }

                DetectCaptcha(win);
                Thread.Sleep(500);
            }

            Log("Baixar XML não ficou disponível no prazo.");
            return 15;
        }
        catch (Exception ex)
        {
            Log("Erro não tratado: " + ex.GetType().Name + " - " + ex.Message);
            return 99;
        }
    }

    private static string NormalizeKey(string value)
    {
        var sb = new StringBuilder();
        foreach (var ch in (value ?? "").ToUpperInvariant())
            if ((ch >= '0' && ch <= '9') || (ch >= 'A' && ch <= 'Z')) sb.Append(ch);
        return sb.ToString();
    }

    private static string NormalizeText(string value)
    {
        if (String.IsNullOrWhiteSpace(value)) return "";
        var form = value.Normalize(NormalizationForm.FormD);
        var sb = new StringBuilder();
        foreach (var ch in form)
        {
            if (CharUnicodeInfo.GetUnicodeCategory(ch) != UnicodeCategory.NonSpacingMark)
                sb.Append(Char.ToLowerInvariant(ch));
        }
        return sb.ToString().Normalize(NormalizationForm.FormC);
    }

    private static void Log(string text)
    {
        try
        {
            if (!String.IsNullOrEmpty(_logPath))
                File.AppendAllText(_logPath, DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff") + " " + text + Environment.NewLine, Encoding.UTF8);
        }
        catch { }
    }

    private static AutomationElement WaitForLookupWindow(TimeSpan timeout)
    {
        var until = DateTime.UtcNow.Add(timeout);
        while (DateTime.UtcNow < until)
        {
            var w = FindLookupWindow();
            if (w != null) return w;
            Thread.Sleep(250);
        }
        return null;
    }

    private static AutomationElement FindLookupWindow()
    {
        try
        {
            var cond = new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window);
            var wins = AutomationElement.RootElement.FindAll(TreeScope.Children, cond);
            foreach (AutomationElement w in wins)
            {
                string name;
                try { name = NormalizeText(w.Current.Name); } catch { continue; }
                if (name.Contains("consulta automatica") || name.Contains("consulta danfe") || (name.Contains("csm") && name.Contains("consulta") && name.Contains("xml")))
                    return w;
            }
        }
        catch { }
        return null;
    }

    private static string ElementText(AutomationElement e)
    {
        try
        {
            return NormalizeText((e.Current.Name ?? "") + " " + (e.Current.HelpText ?? "") + " " + (e.Current.AutomationId ?? "") + " " + (e.Current.ClassName ?? ""));
        }
        catch { return ""; }
    }

    private static bool TrySetKey(AutomationElement win, string key)
    {
        AutomationElementCollection edits;
        try
        {
            edits = win.FindAll(TreeScope.Descendants, new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Edit));
        }
        catch { return false; }

        var candidates = new List<Tuple<AutomationElement, int>>();
        foreach (AutomationElement e in edits)
        {
            var text = ElementText(e);
            var score = 0;
            if (text.Contains("chave")) score += 12;
            if (text.Contains("44")) score += 9;
            if (text.Contains("acesso")) score += 5;
            candidates.Add(Tuple.Create(e, score));
        }

        foreach (var c in candidates.OrderByDescending(x => x.Item2))
        {
            object pattern;
            try
            {
                if (c.Item1.TryGetCurrentPattern(ValuePattern.Pattern, out pattern))
                {
                    var vp = (ValuePattern)pattern;
                    vp.SetValue(key);
                    Thread.Sleep(120);
                    if (NormalizeKey(vp.Current.Value) == key)
                    {
                        Log("Chave preenchida via ValuePattern, sem clique por coordenada.");
                        return true;
                    }
                }
            }
            catch { }

            try
            {
                c.Item1.SetFocus();
                Thread.Sleep(80);
                SendKeys.SendWait("^a");
                SendKeys.SendWait(key);
                Thread.Sleep(100);
                Log("Chave preenchida via foco/teclado como fallback.");
                return true;
            }
            catch { }
        }
        return false;
    }

    private static bool TryAcceptCookies(AutomationElement win)
    {
        var all = SafeDescendants(win);
        foreach (AutomationElement e in all)
        {
            var text = ElementText(e);
            if (String.IsNullOrEmpty(text)) continue;
            var cookieCandidate = text.Contains("aceitar todos") || text.Contains("aceitar cookies") || text == "aceitar" || text.Contains("permitir todos") || text.Contains("concordar") || text.Contains("consentir");
            if (!cookieCandidate) continue;
            if (TryInvokeElement(e, "cookies: " + SafeName(e)))
            {
                Log("Aviso de cookies aceito automaticamente.");
                Thread.Sleep(250);
                return true;
            }
        }
        return false;
    }

    private static bool TryInvokeSearch(AutomationElement win)
    {
        var all = SafeDescendants(win);
        var ranked = new List<Tuple<AutomationElement, int>>();
        foreach (AutomationElement e in all)
        {
            var text = ElementText(e);
            if (String.IsNullOrEmpty(text)) continue;
            var score = 0;
            if (text.Contains("imprimir danfe")) score += 30;
            if (text.Contains("consultar")) score += 20;
            if (text.Contains("buscar")) score += 18;
            if (score > 0) ranked.Add(Tuple.Create(e, score));
        }
        foreach (var item in ranked.OrderByDescending(x => x.Item2))
        {
            if (TryInvokeElement(item.Item1, "consulta: " + SafeName(item.Item1)))
            {
                Log("Consulta acionada via UI Automation.");
                return true;
            }
        }
        return false;
    }

    private static bool TryInvokeDownloadXml(AutomationElement win)
    {
        var all = SafeDescendants(win);
        var ranked = new List<Tuple<AutomationElement, int>>();
        foreach (AutomationElement e in all)
        {
            var text = ElementText(e);
            if (String.IsNullOrEmpty(text)) continue;
            var score = 0;
            if (text.Contains("baixar xml")) score += 50;
            if (text.Contains("download xml")) score += 45;
            if (text.Contains("xml") && (text.Contains("baixar") || text.Contains("download"))) score += 25;
            if (text.Contains("pdf") || text.Contains("danfe")) score -= 15;
            if (score >= 25) ranked.Add(Tuple.Create(e, score));
        }

        foreach (var item in ranked.OrderByDescending(x => x.Item2))
        {
            if (TryInvokeElementOrParent(item.Item1, "Baixar XML: " + SafeName(item.Item1))) return true;
        }
        return false;
    }

    private static AutomationElementCollection SafeDescendants(AutomationElement win)
    {
        try { return win.FindAll(TreeScope.Descendants, Condition.TrueCondition); }
        catch { return AutomationElement.RootElement.FindAll(TreeScope.Children, new PropertyCondition(AutomationElement.NameProperty, "__CSM_NO_MATCH__")); }
    }

    private static bool TryInvokeElementOrParent(AutomationElement e, string label)
    {
        var current = e;
        for (var i = 0; i < 4 && current != null; i++)
        {
            if (TryInvokeElement(current, label + (i == 0 ? "" : " (parent " + i + ")"))) return true;
            try { current = TreeWalker.ControlViewWalker.GetParent(current); } catch { current = null; }
        }
        return false;
    }

    private static bool TryInvokeElement(AutomationElement e, string label)
    {
        object pattern;
        try
        {
            if (e.TryGetCurrentPattern(InvokePattern.Pattern, out pattern))
            {
                ((InvokePattern)pattern).Invoke();
                Log("Ação via InvokePattern: " + label);
                return true;
            }
        }
        catch { }

        try
        {
            if (e.TryGetCurrentPattern(LegacyIAccessiblePattern.Pattern, out pattern))
            {
                ((LegacyIAccessiblePattern)pattern).DoDefaultAction();
                Log("Ação via LegacyIAccessiblePattern: " + label);
                return true;
            }
        }
        catch { }

        try
        {
            e.SetFocus();
            Thread.Sleep(60);
            SendKeys.SendWait("{ENTER}");
            Log("Ação via foco/ENTER: " + label);
            return true;
        }
        catch { }
        return false;
    }

    private static string SafeName(AutomationElement e)
    {
        try { return e.Current.Name ?? ""; } catch { return ""; }
    }

    private static void DetectCaptcha(AutomationElement win)
    {
        if (_captchaLogged) return;
        foreach (AutomationElement e in SafeDescendants(win))
        {
            var text = ElementText(e);
            if (text.Contains("captcha") || text.Contains("recaptcha"))
            {
                _captchaLogged = true;
                Log("CAPTCHA detectado; aguardando intervenção manual sem tentar contorná-lo.");
                return;
            }
        }
    }

    private static bool HasMatchingXmlInDownloads(string key)
    {
        try
        {
            var downloads = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads");
            if (!Directory.Exists(downloads)) return false;
            foreach (var path in Directory.GetFiles(downloads, "*.xml", SearchOption.TopDirectoryOnly))
            {
                var fi = new FileInfo(path);
                if (fi.LastWriteTimeUtc < _startedAt.AddSeconds(-5) || fi.Length <= 0 || fi.Length > 25L * 1024L * 1024L) continue;
                try
                {
                    var text = File.ReadAllText(path);
                    if (text.IndexOf(key, StringComparison.OrdinalIgnoreCase) >= 0) return true;
                }
                catch { }
            }
        }
        catch { }
        return false;
    }
}
