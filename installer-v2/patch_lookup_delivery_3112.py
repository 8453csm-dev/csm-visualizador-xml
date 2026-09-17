from pathlib import Path

MARKER = 'CSM_LOOKUP_DELIVERY_3112'
path = Path('installer-v2/launcher/consulta_danfe_helper.cs')
text = path.read_text(encoding='utf-8')

if MARKER in text:
    print('Entrega XML 3.11.2 já aplicada')
    raise SystemExit(0)

# Imports necessários para validar XML e avisar o broker local.
text = text.replace('using System.Text;\n', 'using System.Text;\nusing System.Xml.Linq;\nusing System.Net;\n')

old_main = '''            Log("Consulta enviada; aguardando resultado e botão Baixar XML.");
            var deadline = DateTime.UtcNow.AddMinutes(6);
            var cookieTick = 0;
            while (DateTime.UtcNow < deadline)
            {
                win = FindLookupWindow();
                if (win == null) { Log("Janela de consulta foi fechada antes do download."); return 14; }
                if (HasMatchingXmlInDownloads(key)) { Log("XML correspondente já apareceu em Downloads; evitando clique duplicado."); return 0; }
                if ((cookieTick++ % 6) == 0) TryAcceptCookies(win);
                if (TryInvokeDownloadXml(win)) { Log("Baixar XML acionado automaticamente."); return 0; }
                DetectCaptcha(win);
                Thread.Sleep(500);
            }
            Log("Baixar XML não ficou disponível no prazo.");
            return 15;'''

new_main = '''            Log("Consulta enviada; aguardando resultado e XML real da NF-e.");
            var deadline = DateTime.UtcNow.AddMinutes(6);
            var cookieTick = 0;
            var downloadRequested = false;
            while (DateTime.UtcNow < deadline)
            {
                win = FindLookupWindow();
                if (win == null) { Log("Janela de consulta foi fechada antes do XML."); return 14; }

                var matching = FindMatchingXmlInDownloads(key);
                if (!String.IsNullOrEmpty(matching))
                {
                    var status = DetectDocumentStatus(win);
                    Log("XML válido localizado: " + matching + " | situação=" + status);
                    NotifyBrokerOpen(matching);
                    return 0;
                }

                CancelUnexpectedSpreadsheetSaveDialog();
                if ((cookieTick++ % 6) == 0) TryAcceptCookies(win);

                if (!downloadRequested && TryInvokeDownloadXmlStrict(win))
                {
                    downloadRequested = true;
                    Log("Download XML legítimo acionado; aguardando o arquivo XML.");
                }

                if (downloadRequested)
                    TryConfirmXmlSaveDialog(key);

                DetectCaptcha(win);
                Thread.Sleep(500);
            }
            Log("XML válido da NF-e não ficou disponível no prazo.");
            return 15;'''

if old_main not in text:
    raise RuntimeError('Fluxo antigo do helper não encontrado')
text = text.replace(old_main, new_main, 1)

old_download = '''    private static bool TryInvokeDownloadXml(AutomationElement win)
    {
        var ranked = new List<Tuple<AutomationElement, int>>();
        foreach (AutomationElement e in SafeDescendants(win))
        {
            var text = ElementText(e); if (String.IsNullOrEmpty(text)) continue;
            var score = 0;
            if (text.Contains("baixar xml")) score += 50;
            if (text.Contains("download xml")) score += 45;
            if (text.Contains("xml") && (text.Contains("baixar") || text.Contains("download"))) score += 25;
            if (text.Contains("pdf") || text.Contains("danfe")) score -= 15;
            if (score >= 25) ranked.Add(Tuple.Create(e, score));
        }
        foreach (var item in ranked.OrderByDescending(x => x.Item2))
            if (TryInvokeElementOrParent(item.Item1, "Baixar XML: " + SafeName(item.Item1))) return true;
        return false;
    }
'''

new_download = '''    // CSM_LOOKUP_DELIVERY_3112
    private static bool IsDirectActionControl(AutomationElement e)
    {
        try
        {
            var ct = e.Current.ControlType;
            return ct == ControlType.Button || ct == ControlType.Hyperlink || ct == ControlType.MenuItem;
        }
        catch { return false; }
    }

    private static bool IsSpreadsheetText(string text)
    {
        text = NormalizeText(text);
        return text.Contains("excel") || text.Contains("xlsx") || text.Contains("xls") || text.Contains("csv") || text.Contains("planilha") || text.Contains("exportar");
    }

    private static bool TryInvokeDownloadXmlStrict(AutomationElement win)
    {
        var ranked = new List<Tuple<AutomationElement, int>>();
        foreach (AutomationElement e in SafeDescendants(win))
        {
            if (!IsDirectActionControl(e)) continue;
            var text = ElementText(e); if (String.IsNullOrEmpty(text)) continue;
            if (IsSpreadsheetText(text) || text.Contains("pdf") || text.Contains("danfe")) continue;
            var score = 0;
            if (text.Contains("baixar xml")) score += 100;
            if (text.Contains("download xml")) score += 95;
            if (text.Contains("xml") && (text.Contains("baixar") || text.Contains("download"))) score += 60;
            if (text.Trim() == "xml") score += 30;
            if (score >= 60) ranked.Add(Tuple.Create(e, score));
        }
        foreach (var item in ranked.OrderByDescending(x => x.Item2))
        {
            if (TryInvokeElement(item.Item1, "Baixar XML estrito: " + SafeName(item.Item1))) return true;
        }
        return false;
    }

    private static AutomationElement FindTopWindowByName(params string[] names)
    {
        try
        {
            var wins = AutomationElement.RootElement.FindAll(TreeScope.Children, new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window));
            foreach (AutomationElement w in wins)
            {
                var n = NormalizeText(SafeName(w));
                foreach (var name in names) if (n.Contains(NormalizeText(name))) return w;
            }
        }
        catch { }
        return null;
    }

    private static void CancelUnexpectedSpreadsheetSaveDialog()
    {
        var dlg = FindTopWindowByName("salvar como", "save as");
        if (dlg == null) return;
        var all = SafeDescendants(dlg);
        var text = "";
        foreach (AutomationElement e in all) text += " " + ElementText(e);
        if (!IsSpreadsheetText(text)) return;
        foreach (AutomationElement e in all)
        {
            var t = ElementText(e);
            if (t.Contains("cancelar") || t == "cancel")
            {
                if (TryInvokeElement(e, "Cancelar exportação de planilha"))
                {
                    Log("Janela de Excel/CSV cancelada automaticamente; planilhas não fazem parte da consulta NF-e.");
                    Thread.Sleep(250);
                    return;
                }
            }
        }
        try { dlg.SetFocus(); SendKeys.SendWait("{ESC}"); Log("Janela de planilha fechada com ESC."); } catch { }
    }

    private static bool TryConfirmXmlSaveDialog(string key)
    {
        var dlg = FindTopWindowByName("salvar como", "save as");
        if (dlg == null) return false;
        var all = SafeDescendants(dlg);
        var joined = "";
        foreach (AutomationElement e in all) joined += " " + ElementText(e);
        if (IsSpreadsheetText(joined)) { CancelUnexpectedSpreadsheetSaveDialog(); return false; }

        AutomationElement edit = null;
        foreach (AutomationElement e in all)
        {
            try
            {
                if (e.Current.ControlType == ControlType.Edit)
                {
                    var t = ElementText(e);
                    if (t.Contains("nome") || t.Contains("arquivo") || t.Contains("file name")) { edit = e; break; }
                    if (edit == null) edit = e;
                }
            }
            catch { }
        }
        if (edit == null) return false;

        var downloads = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads");
        Directory.CreateDirectory(downloads);
        var target = Path.Combine(downloads, key + ".xml");
        try
        {
            object p;
            if (edit.TryGetCurrentPattern(ValuePattern.Pattern, out p)) ((ValuePattern)p).SetValue(target);
            else { edit.SetFocus(); SendKeys.SendWait("^a"); SendKeys.SendWait(target); }
            Thread.Sleep(120);
        }
        catch { return false; }

        foreach (AutomationElement e in all)
        {
            var t = ElementText(e);
            if ((t.Contains("salvar") || t == "save") && IsDirectActionControl(e))
            {
                if (TryInvokeElement(e, "Salvar XML em Downloads")) { Log("Salvar Como confirmado para XML: " + target); return true; }
            }
        }
        try { edit.SetFocus(); SendKeys.SendWait("{ENTER}"); Log("Salvar Como confirmado por ENTER para XML."); return true; } catch { return false; }
    }
'''

if old_download not in text:
    raise RuntimeError('Função antiga TryInvokeDownloadXml não encontrada')
text = text.replace(old_download, new_download, 1)

old_match = '''    private static bool HasMatchingXmlInDownloads(string key)
    {
        try
        {
            var downloads = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads");
            if (!Directory.Exists(downloads)) return false;
            foreach (var path in Directory.GetFiles(downloads, "*.xml", SearchOption.TopDirectoryOnly))
            {
                var fi = new FileInfo(path);
                if (fi.LastWriteTimeUtc < _startedAt.AddSeconds(-5) || fi.Length <= 0 || fi.Length > 25L * 1024L * 1024L) continue;
                try { var text = File.ReadAllText(path); if (text.IndexOf(key, StringComparison.OrdinalIgnoreCase) >= 0) return true; }
                catch { }
            }
        }
        catch { }
        return false;
    }
'''

new_match = '''    private static string FindMatchingXmlInDownloads(string key)
    {
        try
        {
            var downloads = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads");
            if (!Directory.Exists(downloads)) return "";
            foreach (var path in Directory.GetFiles(downloads, "*.xml", SearchOption.TopDirectoryOnly).OrderByDescending(File.GetLastWriteTimeUtc))
            {
                var fi = new FileInfo(path);
                if (fi.LastWriteTimeUtc < _startedAt.AddSeconds(-5) || fi.Length <= 20 || fi.Length > 25L * 1024L * 1024L) continue;
                if (ValidateXmlForKey(path, key)) return path;
            }
        }
        catch { }
        return "";
    }

    private static bool ValidateXmlForKey(string path, string key)
    {
        try
        {
            var doc = XDocument.Load(path, LoadOptions.None);
            if (doc.Root == null) return false;
            var rootName = doc.Root.Name.LocalName;
            if (rootName != "nfeProc" && rootName != "NFe" && rootName != "procEventoNFe" && rootName != "resNFe") return false;
            var id = doc.Descendants().Attributes("Id").Select(x => x.Value).FirstOrDefault(x => x.IndexOf(key, StringComparison.OrdinalIgnoreCase) >= 0);
            if (!String.IsNullOrEmpty(id)) return true;
            var ch = doc.Descendants().FirstOrDefault(x => x.Name.LocalName == "chNFe" && String.Equals((x.Value ?? "").Trim(), key, StringComparison.OrdinalIgnoreCase));
            return ch != null;
        }
        catch { return false; }
    }

    private static string DetectDocumentStatus(AutomationElement win)
    {
        try
        {
            var texts = SafeDescendants(win).Cast<AutomationElement>().Select(ElementText).Where(x => !String.IsNullOrEmpty(x)).ToArray();
            var joined = String.Join(" ", texts);
            if (joined.Contains("cancelada") || joined.Contains("cancelado") || joined.Contains("cancelamento homologado")) return "CANCELADA";
            if (joined.Contains("denegada") || joined.Contains("denegado")) return "DENEGADA";
            if (joined.Contains("autorizada") || joined.Contains("autorizado") || joined.Contains("uso autorizado")) return "AUTORIZADA";
        }
        catch { }
        return "ENCONTRADA";
    }

    private static void NotifyBrokerOpen(string path)
    {
        try
        {
            var body = "{\\\"paths\\\":[\\\"" + path.Replace("\\\\", "\\\\\\\\").Replace("\\\"", "\\\\\\\"") + "\\\"]}";
            using (var wc = new WebClient())
            {
                wc.Headers[HttpRequestHeader.ContentType] = "application/json";
                wc.UploadString("http://127.0.0.1:47878/open", "POST", body);
            }
            Log("XML enviado ao broker do CSM para abertura automática.");
        }
        catch (Exception ex) { Log("Falha ao avisar broker: " + ex.Message); }
    }
'''

if old_match not in text:
    raise RuntimeError('Função antiga HasMatchingXmlInDownloads não encontrada')
text = text.replace(old_match, new_match, 1)

path.write_text(text, encoding='utf-8', newline='\n')
print('Helper atualizado: somente XML válido, Excel cancelado e abertura automática via broker.')
