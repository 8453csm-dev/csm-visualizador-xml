using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using System.Xml.Linq;

internal static class Program
{
    private const string CredentialTarget = "CSM_VisualizadorXML_MeuDanfe_ApiKey";
    private const string BaseUrl = "https://api.meudanfe.com.br/v2";
    private static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = 16 * 1024 * 1024 };

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct CREDENTIAL
    {
        public UInt32 Flags;
        public UInt32 Type;
        public IntPtr TargetName;
        public IntPtr Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public UInt32 CredentialBlobSize;
        public IntPtr CredentialBlob;
        public UInt32 Persist;
        public UInt32 AttributeCount;
        public IntPtr Attributes;
        public IntPtr TargetAlias;
        public IntPtr UserName;
    }

    [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredRead(string target, uint type, int reservedFlag, out IntPtr credentialPtr);

    [DllImport("advapi32.dll", EntryPoint = "CredWriteW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredWrite(ref CREDENTIAL credential, uint flags);

    [DllImport("advapi32.dll", EntryPoint = "CredDeleteW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredDelete(string target, uint type, uint flags);

    [DllImport("advapi32.dll")]
    private static extern void CredFree(IntPtr buffer);

    private static int Main(string[] args)
    {
        ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072; // TLS 1.2

        try
        {
            if (args.Length == 0) return Fail("comando ausente", 2);
            var cmd = (args[0] ?? "").Trim().ToLowerInvariant();

            if (cmd == "selftest") return SelfTest();
            if (cmd == "status") return Status();
            if (cmd == "set-key") return SetKey();
            if (cmd == "clear-key") return ClearKey();
            if (cmd == "consult") return Consult(args.Skip(1).ToArray());

            return Fail("comando desconhecido", 3);
        }
        catch (Exception ex)
        {
            return Fail(ex.Message, 99);
        }
    }

    private static int SelfTest()
    {
        const string key = "35260802562527000135550010000194421659945019";
        if (!ValidNFeKey(key)) return 71;

        var sample = "<?xml version=\"1.0\"?><nfeProc xmlns=\"http://www.portalfiscal.inf.br/nfe\"><NFe><infNFe Id=\"NFe" + key + "\"></infNFe></NFe><protNFe><infProt><chNFe>" + key + "</chNFe></infProt></protNFe></nfeProc>";
        if (!XmlMatchesKey(sample, key)) return 72;

        var j = new Dictionary<string, object>();
        j["data"] = sample;
        var body = Json.Serialize(j);
        if (ExtractXml(body) != sample) return 73;

        WriteJson(new Dictionary<string, object> { { "ok", true }, { "selftest", true } });
        return 0;
    }

    private static int Status()
    {
        var env = Environment.GetEnvironmentVariable("MEUDANFE_API_KEY");
        var saved = ReadCredential();
        WriteJson(new Dictionary<string, object>
        {
            { "ok", true },
            { "configured", !String.IsNullOrWhiteSpace(saved) || !String.IsNullOrWhiteSpace(env) },
            { "credential_manager", !String.IsNullOrWhiteSpace(saved) },
            { "environment", !String.IsNullOrWhiteSpace(env) },
            { "provider", "Meu Danfe API v2" }
        });
        return 0;
    }

    private static int SetKey()
    {
        var key = (Console.In.ReadToEnd() ?? "").Trim();
        if (key.Length < 8 || key.Length > 512) return Fail("Api-Key inválida", 20);
        WriteCredential(key);
        WriteJson(new Dictionary<string, object> { { "ok", true }, { "configured", true } });
        return 0;
    }

    private static int ClearKey()
    {
        try { CredDelete(CredentialTarget, 1, 0); } catch { }
        WriteJson(new Dictionary<string, object> { { "ok", true }, { "configured", false } });
        return 0;
    }

    private static int Consult(string[] args)
    {
        var key = Arg(args, "--key");
        key = DigitsOnly(key);
        if (!ValidNFeKey(key)) return Fail("Chave de acesso inválida.", 30);

        var apiKey = GetApiKey();
        if (String.IsNullOrWhiteSpace(apiKey))
            return Fail("Api-Key do Meu Danfe não configurada.", 31, "api_key_required");

        var root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CSM", "VisualizadorXML", "cache", "meudanfe");
        Directory.CreateDirectory(root);
        var target = Path.Combine(root, "NFe-" + key + ".xml");

        // Reaproveita cache validado sem consumir nova consulta.
        if (File.Exists(target))
        {
            try
            {
                var cached = File.ReadAllText(target, Encoding.UTF8);
                if (XmlMatchesKey(cached, key))
                {
                    WriteSuccess(key, target, true, "cache");
                    return 0;
                }
            }
            catch { }
        }

        var headers = new Dictionary<string, string> { { "Api-Key", apiKey }, { "Accept", "application/json" } };
        string getUrl = BaseUrl + "/fd/get/xml/" + key;
        string addUrl = BaseUrl + "/fd/add/" + key;

        var first = Request("GET", getUrl, headers);
        if (first.StatusCode == 200)
        {
            var xml = ExtractXml(first.Body);
            if (!String.IsNullOrEmpty(xml) && XmlMatchesKey(xml, key))
            {
                SaveXml(target, xml);
                WriteSuccess(key, target, false, "account");
                return 0;
            }
        }

        if (first.StatusCode == 401) return ProviderError("Api-Key não informada ou inválida.", 401, "invalid_api_key");
        if (first.StatusCode == 403) return ProviderError("Api-Key substituída ou sem permissão. Gere outra em API / Integração.", 403, "forbidden");
        if (first.StatusCode == 400) return ProviderError("O Meu Danfe informou que a chave de acesso é inválida.", 400, "invalid_key");

        bool ready = false;
        string lastMessage = "";
        for (int i = 0; i < 12; i++)
        {
            if (i > 0) Thread.Sleep(1200);
            var add = Request("PUT", addUrl, headers);
            if (add.StatusCode == 401) return ProviderError("Api-Key não informada ou inválida.", 401, "invalid_api_key");
            if (add.StatusCode == 402) return ProviderError("Saldo insuficiente na conta Meu Danfe.", 402, "insufficient_credit");
            if (add.StatusCode == 403) return ProviderError("Api-Key substituída ou sem permissão. Gere outra em API / Integração.", 403, "forbidden");
            if (add.StatusCode == 400) return ProviderError("O Meu Danfe informou que a chave de acesso é inválida.", 400, "invalid_key");
            if (add.StatusCode >= 500) return ProviderError("O Meu Danfe não respondeu corretamente. Tente novamente.", add.StatusCode, "provider_error");

            var parsed = ParseObject(add.Body);
            var status = GetString(parsed, "status").ToUpperInvariant();
            lastMessage = GetString(parsed, "statusMessage", "message");

            if (status == "NOT_FOUND") return ProviderError(String.IsNullOrEmpty(lastMessage) ? "NF-e não encontrada." : lastMessage, 404, "not_found");
            if (status == "ERROR") return ProviderError(String.IsNullOrEmpty(lastMessage) ? "Falha ao consultar a NF-e." : lastMessage, add.StatusCode, "provider_error");
            if (status == "OK") { ready = true; break; }
            // WAITING / SEARCHING: documentação pede intervalo >= 1 segundo.
        }

        var final = Request("GET", getUrl, headers);
        if (final.StatusCode == 200)
        {
            var xml = ExtractXml(final.Body);
            if (!String.IsNullOrEmpty(xml) && XmlMatchesKey(xml, key))
            {
                SaveXml(target, xml);
                WriteSuccess(key, target, false, ready ? "searched" : "account");
                return 0;
            }
        }

        if (final.StatusCode == 401) return ProviderError("Api-Key não informada ou inválida.", 401, "invalid_api_key");
        if (final.StatusCode == 402) return ProviderError("Saldo insuficiente na conta Meu Danfe.", 402, "insufficient_credit");
        if (final.StatusCode == 403) return ProviderError("Api-Key substituída ou sem permissão.", 403, "forbidden");

        return ProviderError("O XML ainda não ficou disponível após a consulta. Tente novamente em alguns segundos.", final.StatusCode, "timeout");
    }

    private static void WriteSuccess(string key, string path, bool cache, string source)
    {
        WriteJson(new Dictionary<string, object>
        {
            { "ok", true },
            { "key", key },
            { "xml_path", path },
            { "xml_available", true },
            { "cached", cache },
            { "source", source },
            { "provider", "Meu Danfe API v2" }
        });
    }

    private static int ProviderError(string message, int http, string code)
    {
        WriteJson(new Dictionary<string, object>
        {
            { "ok", false },
            { "error", message },
            { "code", code },
            { "http_status", http },
            { "provider", "Meu Danfe API v2" }
        });
        return 40;
    }

    private sealed class Response
    {
        public int StatusCode;
        public string Body = "";
    }

    private static Response Request(string method, string url, Dictionary<string, string> headers)
    {
        var req = (HttpWebRequest)WebRequest.Create(url);
        req.Method = method;
        req.Timeout = 25000;
        req.ReadWriteTimeout = 25000;
        req.UserAgent = "CSM-Visualizador-XML/3.16";
        req.AutomaticDecompression = DecompressionMethods.GZip | DecompressionMethods.Deflate;
        foreach (var kv in headers)
        {
            if (String.Equals(kv.Key, "Accept", StringComparison.OrdinalIgnoreCase)) req.Accept = kv.Value;
            else req.Headers[kv.Key] = kv.Value;
        }

        try
        {
            using (var resp = (HttpWebResponse)req.GetResponse())
            using (var sr = new StreamReader(resp.GetResponseStream(), Encoding.UTF8, true))
                return new Response { StatusCode = (int)resp.StatusCode, Body = sr.ReadToEnd() };
        }
        catch (WebException ex)
        {
            var resp = ex.Response as HttpWebResponse;
            string body = "";
            if (resp != null)
            {
                try { using (var sr = new StreamReader(resp.GetResponseStream(), Encoding.UTF8, true)) body = sr.ReadToEnd(); } catch { }
                return new Response { StatusCode = (int)resp.StatusCode, Body = body };
            }
            throw new Exception("Falha de conexão com o Meu Danfe: " + ex.Message);
        }
    }

    private static Dictionary<string, object> ParseObject(string body)
    {
        try { return Json.Deserialize<Dictionary<string, object>>(body ?? "") ?? new Dictionary<string, object>(); }
        catch { return new Dictionary<string, object>(); }
    }

    private static string ExtractXml(string body)
    {
        if (String.IsNullOrWhiteSpace(body)) return "";
        var trimmed = body.Trim();
        if (trimmed.StartsWith("<", StringComparison.Ordinal)) return trimmed;

        var obj = ParseObject(trimmed);
        object value;
        if (obj.TryGetValue("data", out value) && value != null)
        {
            var s = Convert.ToString(value, CultureInfo.InvariantCulture) ?? "";
            if (s.Contains("<")) return s;
        }
        if (obj.TryGetValue("xml", out value) && value != null)
        {
            var s = Convert.ToString(value, CultureInfo.InvariantCulture) ?? "";
            if (s.Contains("<")) return s;
        }
        return "";
    }

    private static void SaveXml(string path, string xml)
    {
        var doc = XDocument.Parse(xml, LoadOptions.PreserveWhitespace);
        var tmp = path + ".tmp";
        File.WriteAllText(tmp, doc.Declaration == null ? doc.ToString(SaveOptions.DisableFormatting) : doc.Declaration + Environment.NewLine + doc.ToString(SaveOptions.DisableFormatting), new UTF8Encoding(false));
        if (File.Exists(path)) File.Delete(path);
        File.Move(tmp, path);
    }

    private static bool XmlMatchesKey(string xml, string key)
    {
        if (String.IsNullOrWhiteSpace(xml) || String.IsNullOrWhiteSpace(key)) return false;
        try
        {
            var doc = XDocument.Parse(xml, LoadOptions.None);
            var root = doc.Root == null ? "" : doc.Root.Name.LocalName;
            if (root != "nfeProc" && root != "NFe" && root != "resNFe") return false;

            foreach (var a in doc.Descendants().Attributes())
                if (String.Equals(a.Name.LocalName, "Id", StringComparison.OrdinalIgnoreCase) &&
                    a.Value.IndexOf(key, StringComparison.OrdinalIgnoreCase) >= 0) return true;

            foreach (var e in doc.Descendants())
                if (String.Equals(e.Name.LocalName, "chNFe", StringComparison.OrdinalIgnoreCase) &&
                    String.Equals((e.Value ?? "").Trim(), key, StringComparison.OrdinalIgnoreCase)) return true;
        }
        catch { }
        return false;
    }

    private static string GetApiKey()
    {
        var saved = ReadCredential();
        if (!String.IsNullOrWhiteSpace(saved)) return saved.Trim();
        return (Environment.GetEnvironmentVariable("MEUDANFE_API_KEY") ?? "").Trim();
    }

    private static string ReadCredential()
    {
        IntPtr ptr;
        if (!CredRead(CredentialTarget, 1, 0, out ptr) || ptr == IntPtr.Zero) return "";
        try
        {
            var c = (CREDENTIAL)Marshal.PtrToStructure(ptr, typeof(CREDENTIAL));
            if (c.CredentialBlob == IntPtr.Zero || c.CredentialBlobSize == 0) return "";
            var bytes = new byte[c.CredentialBlobSize];
            Marshal.Copy(c.CredentialBlob, bytes, 0, bytes.Length);
            return Encoding.Unicode.GetString(bytes).TrimEnd('\0');
        }
        finally { CredFree(ptr); }
    }

    private static void WriteCredential(string secret)
    {
        var bytes = Encoding.Unicode.GetBytes(secret);
        IntPtr target = IntPtr.Zero, user = IntPtr.Zero, blob = IntPtr.Zero;
        try
        {
            target = Marshal.StringToCoTaskMemUni(CredentialTarget);
            user = Marshal.StringToCoTaskMemUni("CSM Visualizador XML");
            blob = Marshal.AllocCoTaskMem(bytes.Length);
            Marshal.Copy(bytes, 0, blob, bytes.Length);

            var cred = new CREDENTIAL
            {
                Flags = 0,
                Type = 1,
                TargetName = target,
                Comment = IntPtr.Zero,
                CredentialBlobSize = (uint)bytes.Length,
                CredentialBlob = blob,
                Persist = 2,
                AttributeCount = 0,
                Attributes = IntPtr.Zero,
                TargetAlias = IntPtr.Zero,
                UserName = user
            };
            if (!CredWrite(ref cred, 0))
                throw new Exception("Não foi possível salvar a Api-Key no Credential Manager do Windows.");
        }
        finally
        {
            if (target != IntPtr.Zero) Marshal.FreeCoTaskMem(target);
            if (user != IntPtr.Zero) Marshal.FreeCoTaskMem(user);
            if (blob != IntPtr.Zero) Marshal.FreeCoTaskMem(blob);
        }
    }

    private static string Arg(string[] args, string name)
    {
        for (int i = 0; i < args.Length - 1; i++)
            if (String.Equals(args[i], name, StringComparison.OrdinalIgnoreCase)) return args[i + 1] ?? "";
        return "";
    }

    private static string DigitsOnly(string value)
    {
        var sb = new StringBuilder();
        foreach (var c in value ?? "") if (c >= '0' && c <= '9') sb.Append(c);
        return sb.ToString();
    }

    private static bool ValidNFeKey(string key)
    {
        if (key == null || key.Length != 44 || key.Any(c => c < '0' || c > '9')) return false;
        int sum = 0, weight = 2;
        for (int i = 42; i >= 0; i--)
        {
            sum += (key[i] - '0') * weight;
            weight++;
            if (weight > 9) weight = 2;
        }
        int mod = sum % 11;
        int dv = 11 - mod;
        if (dv == 10 || dv == 11) dv = 0;
        return dv == (key[43] - '0');
    }

    private static string GetString(Dictionary<string, object> obj, params string[] keys)
    {
        foreach (var k in keys)
        {
            object v;
            if (obj != null && obj.TryGetValue(k, out v) && v != null) return Convert.ToString(v, CultureInfo.InvariantCulture) ?? "";
        }
        return "";
    }

    private static int Fail(string message, int exit, string code = "error")
    {
        WriteJson(new Dictionary<string, object> { { "ok", false }, { "error", message }, { "code", code } });
        return exit;
    }

    private static void WriteJson(Dictionary<string, object> obj)
    {
        Console.OutputEncoding = new UTF8Encoding(false);
        Console.WriteLine(Json.Serialize(obj));
    }
}
