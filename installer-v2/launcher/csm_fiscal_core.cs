using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;
using System.Xml.Linq;

internal sealed class CertRecord
{
    public string Cnpj = "";
    public string Empresa = "";
    public string Path = "";
    public string Expiry = "";
    public string Status = "";
    public string CredentialTarget = "";
    public string PasswordDpapiB64 = "";
}

internal sealed class ProtocolResult
{
    public bool Ok;
    public string CStat = "";
    public string Message = "";
    public string Status = "INDEFINIDA";
    public string Protocol = "";
    public string ReceivedAt = "";
    public string Raw = "";
}

internal sealed class DistributionResult
{
    public bool Ok;
    public string CStat = "";
    public string Message = "";
    public bool Cancelled;
    public bool Denied;
    public bool SummaryOnly;
    public string FullXml = "";
    public readonly List<string> Schemas = new List<string>();
    public string Raw = "";
}

internal static class Program
{
    private const string Version = "1.0.0";
    private const string DistributionUrl = "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx";
    private const string NFeNs = "http://www.portalfiscal.inf.br/nfe";
    private const string ConsultWsNs = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4";
    private const string DistributionWsNs = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe";
    private static readonly JavaScriptSerializer Json = new JavaScriptSerializer();

    [STAThread]
    private static int Main(string[] args)
    {
        Console.OutputEncoding = new UTF8Encoding(false);
        ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
        try
        {
            if (args.Length == 0) return WriteError("Comando ausente.", 2);
            string cmd = (args[0] ?? "").Trim().ToLowerInvariant();
            if (cmd == "selftest") return SelfTest();
            if (cmd == "list") return ListCertificates();
            if (cmd == "consult") return Consult(args.Skip(1).ToArray());
            return WriteError("Comando desconhecido.", 2);
        }
        catch (Exception ex)
        {
            return WriteError("Falha no CSM Fiscal Core: " + ex.Message, 99);
        }
    }

    private static int SelfTest()
    {
        string key = "35260822636383000121550010000034651119682428";
        if (!IsValidKey(key)) return WriteError("Self-test: chave válida rejeitada.", 90);
        if (GetProtocolUrl("35").IndexOf("fazenda.sp.gov.br", StringComparison.OrdinalIgnoreCase) < 0) return WriteError("Self-test: endpoint SP incorreto.", 91);
        if (GetProtocolUrl("11").IndexOf("svrs", StringComparison.OrdinalIgnoreCase) < 0) return WriteError("Self-test: roteamento SVRS incorreto.", 92);
        if (GetProtocolUrl("21").IndexOf("sefazvirtual", StringComparison.OrdinalIgnoreCase) < 0) return WriteError("Self-test: roteamento SVAN incorreto.", 93);
        string body = BuildDistributionPayload(key, "12345678000199");
        if (body.IndexOf("consChNFe", StringComparison.Ordinal) < 0 || body.IndexOf(key, StringComparison.Ordinal) < 0) return WriteError("Self-test: XML de distribuição incorreto.", 94);
        WriteJson(new Dictionary<string, object> { { "ok", true }, { "version", Version }, { "native", true }, { "browser", false } });
        return 0;
    }

    private static int ListCertificates()
    {
        List<CertRecord> certs = LoadCertificateRecords();
        List<Dictionary<string, object>> publicList = new List<Dictionary<string, object>>();
        foreach (CertRecord c in certs)
        {
            publicList.Add(new Dictionary<string, object>
            {
                { "cnpj", c.Cnpj },
                { "empresa", c.Empresa },
                { "expiry", c.Expiry },
                { "status", c.Status },
                { "available", File.Exists(c.Path) }
            });
        }
        WriteJson(new Dictionary<string, object>
        {
            { "ok", true },
            { "source", IntegrationPath() },
            { "certificates", publicList }
        });
        return 0;
    }

    private static int Consult(string[] args)
    {
        string key = Arg(args, "--key");
        string requestedCnpj = NormalizeDocument(Arg(args, "--cnpj"));
        if (!IsValidKey(key)) return WriteError("Chave de acesso inválida. Informe os 44 dígitos com DV válido.", 10);

        List<CertRecord> records = LoadCertificateRecords();
        CertRecord selected = SelectCertificate(records, requestedCnpj, key);
        if (selected == null)
        {
            List<Dictionary<string, object>> choices = new List<Dictionary<string, object>>();
            foreach (CertRecord c in records)
                choices.Add(new Dictionary<string, object> { { "cnpj", c.Cnpj }, { "empresa", c.Empresa }, { "expiry", c.Expiry }, { "status", c.Status } });
            WriteJson(new Dictionary<string, object>
            {
                { "ok", false }, { "needs_certificate", true },
                { "message", records.Count == 0 ? "Nenhum certificado A1 foi encontrado na integração CSM Certificados Digitais." : "Selecione a empresa/certificado que deve consultar esta NF-e." },
                { "certificates", choices }
            });
            return 11;
        }

        X509Certificate2 cert;
        try { cert = LoadCertificate(selected); }
        catch (Exception ex) { return WriteError("Não foi possível abrir o certificado de " + SafeCompany(selected) + ": " + ex.Message, 12); }

        ProtocolResult protocol = new ProtocolResult();
        DistributionResult distribution = new DistributionResult();
        string protocolError = "";
        string distributionError = "";

        try { protocol = QueryProtocol(cert, key); }
        catch (Exception ex) { protocolError = ex.Message; }

        try { distribution = QueryDistribution(cert, key, selected.Cnpj); }
        catch (Exception ex) { distributionError = ex.Message; }

        string status = protocol.Ok ? protocol.Status : "INDEFINIDA";
        if (distribution.Cancelled) status = "CANCELADA";
        else if (distribution.Denied) status = "DENEGADA";
        else if (status == "INDEFINIDA" && !String.IsNullOrEmpty(distribution.FullXml)) status = "AUTORIZADA";
        else if (status == "INDEFINIDA" && distribution.Ok) status = "ENCONTRADA";

        string xmlPath = "";
        if (!String.IsNullOrEmpty(distribution.FullXml))
        {
            if (!XmlMatchesKey(distribution.FullXml, key))
                return WriteError("A Receita retornou um XML que não corresponde à chave consultada. O arquivo foi descartado por segurança.", 13);
            xmlPath = SaveXml(distribution.FullXml, key, status);
        }

        bool anyOk = protocol.Ok || distribution.Ok;
        string message = protocol.Ok ? protocol.Message : distribution.Message;
        if (String.IsNullOrWhiteSpace(message))
            message = anyOk ? "Consulta concluída." : JoinErrors(protocolError, distributionError);

        Dictionary<string, object> result = new Dictionary<string, object>
        {
            { "ok", anyOk },
            { "native", true },
            { "browser", false },
            { "source", "Web Services oficiais NF-e (SEFAZ / Ambiente Nacional)" },
            { "key", key },
            { "cnpj", selected.Cnpj },
            { "empresa", SafeCompany(selected) },
            { "status", status },
            { "cstat", protocol.CStat },
            { "message", message },
            { "protocol", protocol.Protocol },
            { "received_at", protocol.ReceivedAt },
            { "distribution_cstat", distribution.CStat },
            { "distribution_message", distribution.Message },
            { "xml_available", !String.IsNullOrEmpty(xmlPath) },
            { "xml_path", xmlPath },
            { "summary_only", distribution.SummaryOnly },
            { "requires_manifestation", distribution.SummaryOnly && String.IsNullOrEmpty(xmlPath) },
            { "schemas", distribution.Schemas.ToArray() },
            { "protocol_error", protocolError },
            { "distribution_error", distributionError }
        };
        WriteJson(result);
        return anyOk ? 0 : 14;
    }

    private static string SafeCompany(CertRecord c)
    {
        return String.IsNullOrWhiteSpace(c.Empresa) ? c.Cnpj : c.Empresa;
    }

    private static string JoinErrors(string a, string b)
    {
        if (!String.IsNullOrWhiteSpace(a) && !String.IsNullOrWhiteSpace(b)) return a + " | " + b;
        return !String.IsNullOrWhiteSpace(a) ? a : b;
    }

    private static string Arg(string[] args, string name)
    {
        for (int i = 0; i < args.Length - 1; i++)
            if (String.Equals(args[i], name, StringComparison.OrdinalIgnoreCase)) return args[i + 1] ?? "";
        return "";
    }

    private static ProtocolResult QueryProtocol(X509Certificate2 cert, string key)
    {
        string cuf = key.Substring(0, 2);
        string url = GetProtocolUrl(cuf);
        if (String.IsNullOrEmpty(url)) throw new Exception("Não há autorizador configurado para a UF " + cuf + ".");
        string payload = "<consSitNFe xmlns=\"" + NFeNs + "\" versao=\"4.00\"><tpAmb>1</tpAmb><xServ>CONSULTAR</xServ><chNFe>" + key + "</chNFe></consSitNFe>";
        string response = PostSoap(cert, url, ConsultWsNs, "nfeConsultaNF", ConsultWsNs + "/nfeConsultaNF", payload);
        XDocument doc = XDocument.Parse(response, LoadOptions.PreserveWhitespace);
        XElement ret = FirstLocal(doc, "retConsSitNFe");
        if (ret == null) throw new Exception("A SEFAZ respondeu sem retConsSitNFe.");
        ProtocolResult r = new ProtocolResult();
        r.Raw = response;
        r.CStat = ChildValue(ret, "cStat");
        r.Message = ChildValue(ret, "xMotivo");
        r.Protocol = DescValue(ret, "nProt");
        r.ReceivedAt = DescValue(ret, "dhRecbto");
        r.Status = StatusFromProtocol(r.CStat, r.Message);
        r.Ok = !String.IsNullOrEmpty(r.CStat) && r.CStat != "108" && r.CStat != "109";
        return r;
    }

    private static DistributionResult QueryDistribution(X509Certificate2 cert, string key, string cnpj)
    {
        string cleanCnpj = NormalizeDocument(cnpj);
        if (cleanCnpj.Length != 14) throw new Exception("CNPJ do certificado/empresa inválido para NFeDistribuicaoDFe.");
        string payload = BuildDistributionPayload(key, cleanCnpj);
        string response = PostSoap(cert, DistributionUrl, DistributionWsNs, "nfeDistDFeInteresse", DistributionWsNs + "/nfeDistDFeInteresse", payload);
        XDocument doc = XDocument.Parse(response, LoadOptions.PreserveWhitespace);
        XElement ret = FirstLocal(doc, "retDistDFeInt");
        if (ret == null) throw new Exception("O Ambiente Nacional respondeu sem retDistDFeInt.");
        DistributionResult r = new DistributionResult();
        r.Raw = response;
        r.CStat = ChildValue(ret, "cStat");
        r.Message = ChildValue(ret, "xMotivo");
        r.Ok = r.CStat == "138" || r.CStat == "137";

        foreach (XElement z in ret.Descendants().Where(x => x.Name.LocalName == "docZip"))
        {
            string schema = (string)z.Attribute("schema") ?? "";
            if (!String.IsNullOrWhiteSpace(schema)) r.Schemas.Add(schema);
            string inner;
            try { inner = UnzipBase64(z.Value); }
            catch { continue; }
            if (String.IsNullOrWhiteSpace(inner)) continue;
            string lowSchema = schema.ToLowerInvariant();
            string lowXml = inner.ToLowerInvariant();
            if (lowSchema.Contains("procnfe") || lowXml.Contains("<nfeproc") || lowXml.Contains("<nfe ") || lowXml.Contains("<nfe>"))
            {
                if (XmlMatchesKey(inner, key)) r.FullXml = inner;
            }
            else if (lowSchema.Contains("resnfe") || lowXml.Contains("<resnfe"))
            {
                r.SummaryOnly = true;
                try
                {
                    XDocument sx = XDocument.Parse(inner);
                    string sit = DescValue(sx.Root, "cSitNFe");
                    if (sit == "3") r.Denied = true;
                }
                catch { }
            }
            if (lowSchema.Contains("evento") || lowXml.Contains("<proceventonfe") || lowXml.Contains("<resevento"))
            {
                try
                {
                    XDocument ex = XDocument.Parse(inner);
                    string eventKey = DescValue(ex.Root, "chNFe");
                    string tpEvento = DescValue(ex.Root, "tpEvento");
                    string desc = DescValue(ex.Root, "descEvento");
                    if ((String.IsNullOrEmpty(eventKey) || eventKey == key) && (tpEvento == "110111" || (desc ?? "").IndexOf("cancel", StringComparison.OrdinalIgnoreCase) >= 0)) r.Cancelled = true;
                }
                catch { }
            }
        }
        return r;
    }

    private static string BuildDistributionPayload(string key, string cnpj)
    {
        return "<distDFeInt xmlns=\"" + NFeNs + "\" versao=\"1.01\"><tpAmb>1</tpAmb><CNPJ>" + Escape(cnpj) + "</CNPJ><consChNFe><chNFe>" + Escape(key) + "</chNFe></consChNFe></distDFeInt>";
    }

    private static string PostSoap(X509Certificate2 cert, string url, string wsNamespace, string operation, string action, string payload)
    {
        string body12 = "<?xml version=\"1.0\" encoding=\"utf-8\"?><soap12:Envelope xmlns:soap12=\"http://www.w3.org/2003/05/soap-envelope\"><soap12:Body><" + operation + " xmlns=\"" + wsNamespace + "\"><nfeDadosMsg>" + payload + "</nfeDadosMsg></" + operation + "></soap12:Body></soap12:Envelope>";
        try { return SendSoap(cert, url, action, body12, true); }
        catch (Exception first)
        {
            string body11 = "<?xml version=\"1.0\" encoding=\"utf-8\"?><soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\"><soap:Body><" + operation + " xmlns=\"" + wsNamespace + "\"><nfeDadosMsg>" + payload + "</nfeDadosMsg></" + operation + "></soap:Body></soap:Envelope>";
            try { return SendSoap(cert, url, action, body11, false); }
            catch (Exception second) { throw new Exception("Falha no Web Service oficial: " + first.Message + " | fallback SOAP 1.1: " + second.Message); }
        }
    }

    private static string SendSoap(X509Certificate2 cert, string url, string action, string envelope, bool soap12)
    {
        HttpWebRequest req = (HttpWebRequest)WebRequest.Create(url);
        req.Method = "POST";
        req.Timeout = 30000;
        req.ReadWriteTimeout = 30000;
        req.KeepAlive = false;
        req.ClientCertificates.Add(cert);
        req.Accept = "application/soap+xml, text/xml, */*";
        if (soap12)
            req.ContentType = "application/soap+xml; charset=utf-8; action=\"" + action + "\"";
        else
        {
            req.ContentType = "text/xml; charset=utf-8";
            req.Headers["SOAPAction"] = "\"" + action + "\"";
        }
        byte[] bytes = new UTF8Encoding(false).GetBytes(envelope);
        req.ContentLength = bytes.Length;
        using (Stream s = req.GetRequestStream()) s.Write(bytes, 0, bytes.Length);
        try
        {
            using (HttpWebResponse resp = (HttpWebResponse)req.GetResponse())
            using (StreamReader sr = new StreamReader(resp.GetResponseStream(), Encoding.UTF8, true)) return sr.ReadToEnd();
        }
        catch (WebException ex)
        {
            string detail = "";
            try
            {
                if (ex.Response != null)
                    using (StreamReader sr = new StreamReader(ex.Response.GetResponseStream(), Encoding.UTF8, true)) detail = sr.ReadToEnd();
            }
            catch { }
            detail = StripXml(detail);
            if (detail.Length > 260) detail = detail.Substring(0, 260);
            throw new Exception(ex.Message + (String.IsNullOrWhiteSpace(detail) ? "" : " - " + detail));
        }
    }

    private static string GetProtocolUrl(string cuf)
    {
        switch (cuf)
        {
            case "13": return "https://nfe.sefaz.am.gov.br/services2/services/NfeConsulta4";
            case "21": return "https://www.sefazvirtual.fazenda.gov.br/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx";
            case "26": return "https://nfe.sefaz.pe.gov.br/nfe-service/services/NFeConsultaProtocolo4";
            case "29": return "https://nfe.sefaz.ba.gov.br/webservices/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx";
            case "31": return "https://nfe.fazenda.mg.gov.br/nfe2/services/NFeConsultaProtocolo4";
            case "35": return "https://nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx";
            case "41": return "https://nfe.sefa.pr.gov.br/nfe/NFeConsultaProtocolo4";
            case "43": return "https://nfe.sefazrs.rs.gov.br/ws/NfeConsulta/NfeConsulta4.asmx";
            case "50": return "https://nfe.sefaz.ms.gov.br/ws/NFeConsultaProtocolo4";
            case "51": return "https://nfe.sefaz.mt.gov.br/nfews/v2/services/NfeConsulta4";
            case "52": return "https://nfe.sefaz.go.gov.br/nfe/services/NFeConsultaProtocolo4";
            case "11": case "12": case "14": case "15": case "16": case "17":
            case "22": case "23": case "24": case "25": case "27": case "28":
            case "32": case "33": case "42": case "53":
                return "https://nfe.svrs.rs.gov.br/ws/NfeConsulta/NfeConsulta4.asmx";
            default: return "";
        }
    }

    private static string StatusFromProtocol(string cstat, string message)
    {
        string m = (message ?? "").ToLowerInvariant();
        if (m.Contains("cancel")) return "CANCELADA";
        if (m.Contains("deneg")) return "DENEGADA";
        if (cstat == "100") return "AUTORIZADA";
        if (cstat == "101" || cstat == "151" || cstat == "155") return "CANCELADA";
        if (cstat == "110" || cstat == "301" || cstat == "302") return "DENEGADA";
        if (cstat == "217") return "NÃO LOCALIZADA";
        return "INDEFINIDA";
    }

    private static string SaveXml(string xml, string key, string status)
    {
        string dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CSM Visualizador XML", "cache", "nfe");
        Directory.CreateDirectory(dir);
        string number = key.Substring(25, 9).TrimStart('0');
        if (number == "") number = "0";
        string safeStatus = Regex.Replace((status ?? "ENCONTRADA").ToUpperInvariant(), "[^A-ZÁÀÂÃÉÊÍÓÔÕÚÇ ]", "");
        string file = "NF-e " + number + " - " + safeStatus + " - " + key + ".xml";
        string path = Path.Combine(dir, file);
        File.WriteAllText(path, xml, new UTF8Encoding(false));
        return path;
    }

    private static string UnzipBase64(string value)
    {
        byte[] zipped = Convert.FromBase64String(value ?? "");
        using (MemoryStream input = new MemoryStream(zipped))
        using (GZipStream gz = new GZipStream(input, CompressionMode.Decompress))
        using (StreamReader sr = new StreamReader(gz, Encoding.UTF8, true)) return sr.ReadToEnd();
    }

    private static bool XmlMatchesKey(string xml, string key)
    {
        if (String.IsNullOrWhiteSpace(xml)) return false;
        if (xml.IndexOf("NFe" + key, StringComparison.OrdinalIgnoreCase) >= 0) return true;
        if (xml.IndexOf("<chNFe>" + key + "</chNFe>", StringComparison.OrdinalIgnoreCase) >= 0) return true;
        try
        {
            XDocument d = XDocument.Parse(xml);
            foreach (XElement x in d.Descendants())
            {
                XAttribute id = x.Attribute("Id");
                if (id != null && String.Equals((id.Value ?? "").Replace("NFe", ""), key, StringComparison.OrdinalIgnoreCase)) return true;
                if (x.Name.LocalName == "chNFe" && String.Equals((x.Value ?? "").Trim(), key, StringComparison.Ordinal)) return true;
            }
        }
        catch { }
        return false;
    }

    private static bool IsValidKey(string key)
    {
        if (!Regex.IsMatch(key ?? "", "^[0-9]{44}$")) return false;
        int sum = 0, weight = 2;
        for (int i = 42; i >= 0; i--)
        {
            sum += (key[i] - '0') * weight;
            weight++;
            if (weight > 9) weight = 2;
        }
        int dv = 11 - (sum % 11);
        if (dv == 10 || dv == 11) dv = 0;
        return dv == (key[43] - '0');
    }

    private static string IntegrationPath()
    {
        return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CSM_Certificados_Digitais", "integracao", "certificados.json");
    }

    private static List<CertRecord> LoadCertificateRecords()
    {
        string path = IntegrationPath();
        List<CertRecord> list = new List<CertRecord>();
        if (!File.Exists(path)) return list;
        object root;
        try { root = Json.DeserializeObject(File.ReadAllText(path, Encoding.UTF8)); }
        catch { return list; }
        CollectCertificateRecords(root, list);
        Dictionary<string, CertRecord> unique = new Dictionary<string, CertRecord>(StringComparer.OrdinalIgnoreCase);
        foreach (CertRecord c in list)
        {
            if (String.IsNullOrWhiteSpace(c.Path) || String.IsNullOrWhiteSpace(c.Cnpj)) continue;
            string k = c.Cnpj + "|" + c.Path;
            if (!unique.ContainsKey(k)) unique[k] = c;
        }
        return unique.Values.OrderBy(x => x.Empresa).ThenBy(x => x.Cnpj).ToList();
    }

    private static void CollectCertificateRecords(object node, List<CertRecord> list)
    {
        Dictionary<string, object> d = node as Dictionary<string, object>;
        if (d != null)
        {
            string path = GetString(d, "path", "caminho", "arquivo");
            string cnpj = NormalizeDocument(GetString(d, "cnpj", "documento"));
            if (!String.IsNullOrWhiteSpace(path) && !String.IsNullOrWhiteSpace(cnpj))
            {
                CertRecord c = new CertRecord();
                c.Path = path;
                c.Cnpj = cnpj;
                c.Empresa = GetString(d, "empresa", "razao_social", "razao", "nome");
                c.Expiry = GetString(d, "expiry", "validade", "expires", "not_after");
                c.Status = GetString(d, "status", "situacao");
                c.CredentialTarget = GetString(d, "credential_target", "credentialTarget", "cred_target");
                c.PasswordDpapiB64 = GetString(d, "password_dpapi_b64", "passwordDpapiB64");
                list.Add(c);
            }
            foreach (object v in d.Values) CollectCertificateRecords(v, list);
            return;
        }
        IEnumerable enumerable = node as IEnumerable;
        if (enumerable != null && !(node is string))
            foreach (object item in enumerable) CollectCertificateRecords(item, list);
    }

    private static string GetString(Dictionary<string, object> d, params string[] names)
    {
        foreach (KeyValuePair<string, object> kv in d)
            foreach (string n in names)
                if (String.Equals(kv.Key, n, StringComparison.OrdinalIgnoreCase) && kv.Value != null) return Convert.ToString(kv.Value, CultureInfo.InvariantCulture) ?? "";
        return "";
    }

    private static CertRecord SelectCertificate(List<CertRecord> records, string requestedCnpj, string key)
    {
        IEnumerable<CertRecord> active = records.Where(c => File.Exists(c.Path) && !IsClearlyExpired(c));
        if (!String.IsNullOrEmpty(requestedCnpj))
        {
            CertRecord exact = active.FirstOrDefault(c => String.Equals(c.Cnpj, requestedCnpj, StringComparison.OrdinalIgnoreCase));
            if (exact != null) return exact;
            string root = requestedCnpj.Length >= 8 ? requestedCnpj.Substring(0, 8) : requestedCnpj;
            CertRecord byRoot = active.Where(c => c.Cnpj.Length >= 8 && c.Cnpj.Substring(0, 8) == root).OrderByDescending(c => ParseDate(c.Expiry)).FirstOrDefault();
            if (byRoot != null) return byRoot;
            return null;
        }
        string issuer = key.Substring(6, 14);
        CertRecord issuerCert = active.Where(c => c.Cnpj == issuer).OrderByDescending(c => ParseDate(c.Expiry)).FirstOrDefault();
        if (issuerCert != null) return issuerCert;
        List<CertRecord> all = active.ToList();
        return all.Count == 1 ? all[0] : null;
    }

    private static bool IsClearlyExpired(CertRecord c)
    {
        DateTime dt = ParseDate(c.Expiry);
        if (dt != DateTime.MinValue && dt.Date < DateTime.Today) return true;
        string s = (c.Status ?? "").ToLowerInvariant();
        return s.Contains("vencid") || s.Contains("expir");
    }

    private static DateTime ParseDate(string value)
    {
        DateTime dt;
        return DateTime.TryParse(value, CultureInfo.CurrentCulture, DateTimeStyles.AssumeLocal, out dt) || DateTime.TryParse(value, CultureInfo.InvariantCulture, DateTimeStyles.AssumeLocal, out dt) ? dt : DateTime.MinValue;
    }

    private static X509Certificate2 LoadCertificate(CertRecord rec)
    {
        if (!File.Exists(rec.Path)) throw new Exception("arquivo A1 não encontrado.");
        string password = ReadCredential(rec.CredentialTarget);
        if (String.IsNullOrEmpty(password)) password = UnprotectSecret(rec.PasswordDpapiB64);
        X509Certificate2 cert;
        try { cert = new X509Certificate2(rec.Path, password ?? "", X509KeyStorageFlags.UserKeySet | X509KeyStorageFlags.PersistKeySet); }
        catch (CryptographicException)
        {
            if (String.IsNullOrEmpty(password)) throw new Exception("senha do certificado não disponível no Credential Manager/DPAPI.");
            throw;
        }
        if (!cert.HasPrivateKey) throw new Exception("certificado sem chave privada.");
        if (cert.NotAfter < DateTime.Now) throw new Exception("certificado vencido em " + cert.NotAfter.ToString("dd/MM/yyyy") + ".");
        return cert;
    }

    private static string NormalizeDocument(string value)
    {
        if (String.IsNullOrWhiteSpace(value)) return "";
        StringBuilder sb = new StringBuilder();
        foreach (char ch in value.ToUpperInvariant()) if (Char.IsLetterOrDigit(ch)) sb.Append(ch);
        return sb.ToString();
    }

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
    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern void CredFree(IntPtr credentialPtr);

    private static string ReadCredential(string target)
    {
        if (String.IsNullOrWhiteSpace(target)) return "";
        IntPtr ptr;
        if (!CredRead(target, 1, 0, out ptr) || ptr == IntPtr.Zero) return "";
        try
        {
            CREDENTIAL c = (CREDENTIAL)Marshal.PtrToStructure(ptr, typeof(CREDENTIAL));
            if (c.CredentialBlob == IntPtr.Zero || c.CredentialBlobSize == 0) return "";
            byte[] blob = new byte[c.CredentialBlobSize];
            Marshal.Copy(c.CredentialBlob, blob, 0, blob.Length);
            string unicode = Encoding.Unicode.GetString(blob).TrimEnd('\0');
            if (LooksLikeSecret(unicode)) return unicode;
            string utf8 = Encoding.UTF8.GetString(blob).TrimEnd('\0');
            return LooksLikeSecret(utf8) ? utf8 : "";
        }
        finally { CredFree(ptr); }
    }

    private static string UnprotectSecret(string b64)
    {
        if (String.IsNullOrWhiteSpace(b64)) return "";
        try
        {
            byte[] encrypted = Convert.FromBase64String(b64);
            byte[] plain = ProtectedData.Unprotect(encrypted, null, DataProtectionScope.CurrentUser);
            string utf8 = Encoding.UTF8.GetString(plain).TrimEnd('\0');
            if (LooksLikeSecret(utf8)) return utf8;
            string unicode = Encoding.Unicode.GetString(plain).TrimEnd('\0');
            return LooksLikeSecret(unicode) ? unicode : "";
        }
        catch { return ""; }
    }

    private static bool LooksLikeSecret(string s)
    {
        if (String.IsNullOrEmpty(s) || s.IndexOf('\0') >= 0) return false;
        int printable = s.Count(ch => !Char.IsControl(ch));
        return printable >= Math.Max(1, s.Length - 1);
    }

    private static XElement FirstLocal(XContainer c, string name)
    {
        return c.Descendants().FirstOrDefault(x => x.Name.LocalName == name);
    }

    private static string ChildValue(XElement e, string name)
    {
        XElement x = e.Elements().FirstOrDefault(v => v.Name.LocalName == name);
        return x == null ? "" : (x.Value ?? "").Trim();
    }

    private static string DescValue(XElement e, string name)
    {
        if (e == null) return "";
        XElement x = e.Descendants().FirstOrDefault(v => v.Name.LocalName == name);
        return x == null ? "" : (x.Value ?? "").Trim();
    }

    private static string Escape(string s)
    {
        return (s ?? "").Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;").Replace("\"", "&quot;").Replace("'", "&apos;");
    }

    private static string StripXml(string s)
    {
        if (String.IsNullOrWhiteSpace(s)) return "";
        return Regex.Replace(s, "<[^>]+>", " ").Replace("\r", " ").Replace("\n", " ").Trim();
    }

    private static int WriteError(string message, int code)
    {
        WriteJson(new Dictionary<string, object> { { "ok", false }, { "message", message }, { "code", code }, { "native", true }, { "browser", false } });
        return code;
    }

    private static void WriteJson(object value)
    {
        Console.Write(Json.Serialize(value));
    }
}
