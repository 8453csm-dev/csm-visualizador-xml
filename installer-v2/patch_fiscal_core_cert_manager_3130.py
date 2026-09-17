from pathlib import Path

p=Path('installer-v2/launcher/csm_fiscal_core.cs')
s=p.read_text(encoding='utf-8')
MARK='CSM_CERT_MANAGER_3130'
if MARK in s:
    print('Gerenciador de certificados 3.13.0 já aplicado')
    raise SystemExit(0)

old='''    public string PasswordDpapiB64 = "";\n}'''
new='''    public string PasswordDpapiB64 = "";\n    public string NotBefore = "";\n    public int DaysRemaining;\n    public string Thumbprint = "";\n    public string Issuer = "";\n}'''
if old not in s: raise SystemExit('CertRecord não localizado')
s=s.replace(old,new,1)

old='''            if (cmd == "selftest") return SelfTest();\n            if (cmd == "list") return ListCertificates();\n            if (cmd == "consult") return Consult(args.Skip(1).ToArray());'''
new='''            if (cmd == "selftest") return SelfTest();\n            if (cmd == "list") return ListCertificates();\n            if (cmd == "folders") return CertificateFolders(args.Skip(1).ToArray());\n            if (cmd == "scan") return ScanCertificateFolders();\n            if (cmd == "cert") return CertificateCommand(args.Skip(1).ToArray());\n            if (cmd == "consult") return Consult(args.Skip(1).ToArray());'''
if old not in s: raise SystemExit('Main dispatch não localizado')
s=s.replace(old,new,1)

old='''        List<CertRecord> certs = LoadCertificateRecords();\n        List<Dictionary<string, object>> publicList = new List<Dictionary<string, object>>();\n        foreach (CertRecord c in certs)\n        {\n            publicList.Add(new Dictionary<string, object>\n            {\n                { "cnpj", c.Cnpj },\n                { "empresa", c.Empresa },\n                { "expiry", c.Expiry },\n                { "status", c.Status },\n                { "available", File.Exists(c.Path) }\n            });\n        }'''
new='''        List<CertRecord> certs = LoadAllCertificateRecords();\n        List<Dictionary<string, object>> publicList = new List<Dictionary<string, object>>();\n        foreach (CertRecord c in certs) publicList.Add(PublicCertificate(c));'''
if old not in s: raise SystemExit('ListCertificates antigo não localizado')
s=s.replace(old,new,1)
s=s.replace('''        List<CertRecord> records = LoadCertificateRecords();''','''        List<CertRecord> records = LoadAllCertificateRecords();''',1)

anchor='''    private static string IntegrationPath()\n    {'''
if anchor not in s: raise SystemExit('IntegrationPath não encontrado')

block=r'''
    // CSM_CERT_MANAGER_3130 — pastas locais + scanner A1 + credencial protegida.
    private static string CertConfigDir()
    {
        return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CSM Visualizador XML", "certificados");
    }

    private static string FolderConfigPath() { return Path.Combine(CertConfigDir(), "folders.json"); }
    private static string InternalIndexPath() { return Path.Combine(CertConfigDir(), "certificados.json"); }

    private static List<string> LoadCertificateFolders()
    {
        List<string> folders = new List<string>();
        string path = FolderConfigPath();
        if (!File.Exists(path)) return folders;
        try
        {
            object root = Json.DeserializeObject(File.ReadAllText(path, Encoding.UTF8));
            Dictionary<string, object> d = root as Dictionary<string, object>;
            if (d != null && d.ContainsKey("folders"))
            {
                IEnumerable e = d["folders"] as IEnumerable;
                if (e != null) foreach (object x in e)
                {
                    string value = Convert.ToString(x, CultureInfo.InvariantCulture) ?? "";
                    if (!String.IsNullOrWhiteSpace(value) && !folders.Any(v => String.Equals(v, value, StringComparison.OrdinalIgnoreCase))) folders.Add(value);
                }
            }
        }
        catch { }
        return folders.OrderBy(x => x, StringComparer.OrdinalIgnoreCase).ToList();
    }

    private static void SaveCertificateFolders(List<string> folders)
    {
        Directory.CreateDirectory(CertConfigDir());
        List<string> clean = folders.Where(x => !String.IsNullOrWhiteSpace(x)).Distinct(StringComparer.OrdinalIgnoreCase).OrderBy(x => x, StringComparer.OrdinalIgnoreCase).ToList();
        File.WriteAllText(FolderConfigPath(), Json.Serialize(new Dictionary<string, object>{{"folders", clean.ToArray()}}), new UTF8Encoding(false));
    }

    private static int CertificateFolders(string[] args)
    {
        string op = args.Length > 0 ? (args[0] ?? "").Trim().ToLowerInvariant() : "list";
        List<string> folders = LoadCertificateFolders();
        if (op == "add" || op == "remove")
        {
            string path = Arg(args, "--path");
            if (String.IsNullOrWhiteSpace(path)) return WriteError("Pasta de certificados não informada.", 30);
            try { path = Path.GetFullPath(path); } catch { }
            if (op == "add")
            {
                if (!Directory.Exists(path)) return WriteError("Pasta de certificados não encontrada.", 31);
                if (!folders.Any(x => String.Equals(x, path, StringComparison.OrdinalIgnoreCase))) folders.Add(path);
            }
            else folders.RemoveAll(x => String.Equals(x, path, StringComparison.OrdinalIgnoreCase));
            SaveCertificateFolders(folders);
            folders = LoadCertificateFolders();
        }
        else if (op != "list") return WriteError("Operação de pastas desconhecida.", 32);
        WriteJson(new Dictionary<string, object>{{"ok",true},{"folders",folders.ToArray()},{"native",true}});
        return 0;
    }

    private static int ScanCertificateFolders()
    {
        List<CertRecord> existing = LoadInternalCertificateRecords();
        Dictionary<string, CertRecord> byPath = new Dictionary<string, CertRecord>(StringComparer.OrdinalIgnoreCase);
        foreach (CertRecord c in existing) if (!String.IsNullOrWhiteSpace(c.Path)) byPath[c.Path] = c;
        List<CertRecord> scanned = new List<CertRecord>();
        foreach (string folder in LoadCertificateFolders())
        {
            if (!Directory.Exists(folder)) continue;
            IEnumerable<string> files;
            try { files = Directory.EnumerateFiles(folder, "*.*", SearchOption.AllDirectories).Where(f => String.Equals(Path.GetExtension(f), ".pfx", StringComparison.OrdinalIgnoreCase) || String.Equals(Path.GetExtension(f), ".p12", StringComparison.OrdinalIgnoreCase)).ToArray(); }
            catch { continue; }
            foreach (string file in files)
            {
                CertRecord prior = null;
                byPath.TryGetValue(file, out prior);
                scanned.Add(ScanOneCertificate(file, prior));
            }
        }
        SaveInternalCertificateRecords(scanned);
        WriteJson(new Dictionary<string, object>{{"ok",true},{"folders",LoadCertificateFolders().ToArray()},{"certificates",scanned.OrderBy(x=>x.Empresa).ThenBy(x=>x.Path).Select(PublicCertificate).ToArray()},{"native",true}});
        return 0;
    }

    private static CertRecord ScanOneCertificate(string path, CertRecord prior)
    {
        CertRecord rec = new CertRecord();
        rec.Path = path;
        rec.Empresa = FileLabel(path);
        string saved = prior == null ? "" : UnprotectSecret(prior.PasswordDpapiB64);
        string candidate = FilenamePasswordCandidate(path);
        List<string> tries = new List<string>();
        if (!String.IsNullOrEmpty(saved)) tries.Add(saved);
        if (!String.IsNullOrEmpty(candidate) && !tries.Contains(candidate)) tries.Add(candidate);
        if (!tries.Contains("")) tries.Add("");
        X509Certificate2 cert = null;
        string accepted = "";
        foreach (string pwd in tries)
        {
            try
            {
                cert = new X509Certificate2(path, pwd, X509KeyStorageFlags.UserKeySet);
                if (!cert.HasPrivateKey) { cert.Reset(); cert = null; continue; }
                accepted = pwd;
                break;
            }
            catch (CryptographicException) { }
            catch { }
        }
        if (cert == null)
        {
            rec.Status = "Senha necessária";
            if (prior != null)
            {
                rec.Cnpj = prior.Cnpj; rec.Expiry = prior.Expiry; rec.NotBefore = prior.NotBefore; rec.Thumbprint = prior.Thumbprint; rec.Issuer = prior.Issuer;
            }
            return rec;
        }
        try
        {
            FillCertificateMetadata(rec, cert);
            if (!String.IsNullOrEmpty(accepted)) rec.PasswordDpapiB64 = ProtectSecret(accepted);
            else if (prior != null) rec.PasswordDpapiB64 = prior.PasswordDpapiB64;
        }
        finally { cert.Reset(); }
        return rec;
    }

    private static string FileLabel(string path)
    {
        string n = Path.GetFileNameWithoutExtension(path) ?? "";
        int i = n.LastIndexOf(" - ", StringComparison.Ordinal);
        return (i > 0 ? n.Substring(0, i) : n).Trim();
    }

    private static string FilenamePasswordCandidate(string path)
    {
        string n = Path.GetFileNameWithoutExtension(path) ?? "";
        int i = n.LastIndexOf(" - ", StringComparison.Ordinal);
        if (i < 0 || i + 3 >= n.Length) return "";
        return n.Substring(i + 3).Trim();
    }

    private static void FillCertificateMetadata(CertRecord rec, X509Certificate2 cert)
    {
        rec.Cnpj = ExtractCertificateCnpj(cert);
        string simple = "";
        try { simple = cert.GetNameInfo(X509NameType.SimpleName, false); } catch { }
        if (!String.IsNullOrWhiteSpace(simple)) rec.Empresa = simple.Trim();
        rec.Expiry = cert.NotAfter.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
        rec.NotBefore = cert.NotBefore.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
        rec.DaysRemaining = (int)Math.Floor((cert.NotAfter.Date - DateTime.Today).TotalDays);
        rec.Thumbprint = (cert.Thumbprint ?? "").Replace(" ", "").ToUpperInvariant();
        rec.Issuer = cert.Issuer ?? "";
        if (!cert.HasPrivateKey) rec.Status = "Sem chave privada";
        else if (cert.NotAfter.Date < DateTime.Today) rec.Status = "Vencido";
        else if (rec.DaysRemaining <= 30) rec.Status = "Vencendo";
        else rec.Status = "Válido";
    }

    private static string ExtractCertificateCnpj(X509Certificate2 cert)
    {
        foreach (X509Extension ext in cert.Extensions)
        {
            if (ext.Oid == null || !String.Equals(ext.Oid.Value, "2.16.76.1.3.3", StringComparison.Ordinal)) continue;
            List<string> forms = new List<string>();
            try { forms.Add(ext.Format(false)); } catch { }
            try { forms.Add(Encoding.ASCII.GetString(ext.RawData ?? new byte[0])); } catch { }
            try { forms.Add(Encoding.UTF8.GetString(ext.RawData ?? new byte[0])); } catch { }
            try { forms.Add(Encoding.Unicode.GetString(ext.RawData ?? new byte[0])); } catch { }
            foreach (string form in forms)
            {
                Match m = Regex.Match(form ?? "", @"(?<!\d)(\d{14})(?!\d)");
                if (m.Success) return m.Groups[1].Value;
            }
            string digits = new string((ext.RawData ?? new byte[0]).Select(b => (char)b).Where(Char.IsDigit).ToArray());
            Match raw = Regex.Match(digits, @"\d{14}");
            if (raw.Success) return raw.Value;
        }
        Match subject = Regex.Match(cert.Subject ?? "", @"(?<!\d)(\d{14})(?!\d)");
        return subject.Success ? subject.Groups[1].Value : "";
    }

    private static string ProtectSecret(string secret)
    {
        if (String.IsNullOrEmpty(secret)) return "";
        byte[] plain = Encoding.UTF8.GetBytes(secret);
        byte[] enc = ProtectedData.Protect(plain, null, DataProtectionScope.CurrentUser);
        return Convert.ToBase64String(enc);
    }

    private static Dictionary<string, object> PublicCertificate(CertRecord c)
    {
        return new Dictionary<string, object>
        {
            {"cnpj", c.Cnpj ?? ""}, {"empresa", c.Empresa ?? ""}, {"path", c.Path ?? ""},
            {"expiry", c.Expiry ?? ""}, {"not_before", c.NotBefore ?? ""}, {"days_remaining", c.DaysRemaining},
            {"status", c.Status ?? ""}, {"thumbprint", c.Thumbprint ?? ""}, {"issuer", c.Issuer ?? ""},
            {"available", !String.IsNullOrWhiteSpace(c.Path) && File.Exists(c.Path)}, {"has_protected_credential", !String.IsNullOrWhiteSpace(c.PasswordDpapiB64) || !String.IsNullOrWhiteSpace(c.CredentialTarget)}
        };
    }

    private static List<CertRecord> LoadInternalCertificateRecords()
    {
        List<CertRecord> list = new List<CertRecord>();
        string path = InternalIndexPath();
        if (!File.Exists(path)) return list;
        object root;
        try { root = Json.DeserializeObject(File.ReadAllText(path, Encoding.UTF8)); } catch { return list; }
        IEnumerable arr = root as IEnumerable;
        if (arr == null || root is string) return list;
        foreach (object item in arr)
        {
            Dictionary<string, object> d = item as Dictionary<string, object>; if (d == null) continue;
            CertRecord c = new CertRecord();
            c.Path=GetString(d,"path"); c.Cnpj=NormalizeDocument(GetString(d,"cnpj")); c.Empresa=GetString(d,"empresa"); c.Expiry=GetString(d,"expiry"); c.NotBefore=GetString(d,"not_before");
            int days; Int32.TryParse(GetString(d,"days_remaining"), out days); c.DaysRemaining=days;
            c.Status=GetString(d,"status"); c.Thumbprint=GetString(d,"thumbprint"); c.Issuer=GetString(d,"issuer"); c.CredentialTarget=GetString(d,"credential_target"); c.PasswordDpapiB64=GetString(d,"password_dpapi_b64");
            if (!String.IsNullOrWhiteSpace(c.Path)) list.Add(c);
        }
        return list;
    }

    private static void SaveInternalCertificateRecords(List<CertRecord> list)
    {
        Directory.CreateDirectory(CertConfigDir());
        List<Dictionary<string, object>> rows = new List<Dictionary<string, object>>();
        foreach (CertRecord c in list)
        {
            rows.Add(new Dictionary<string, object>{{"cnpj",c.Cnpj},{"empresa",c.Empresa},{"path",c.Path},{"expiry",c.Expiry},{"not_before",c.NotBefore},{"days_remaining",c.DaysRemaining},{"status",c.Status},{"thumbprint",c.Thumbprint},{"issuer",c.Issuer},{"credential_target",c.CredentialTarget},{"password_dpapi_b64",c.PasswordDpapiB64}});
        }
        File.WriteAllText(InternalIndexPath(), Json.Serialize(rows), new UTF8Encoding(false));
    }

    private static List<CertRecord> LoadAllCertificateRecords()
    {
        List<CertRecord> all = new List<CertRecord>();
        all.AddRange(LoadCertificateRecords());
        all.AddRange(LoadInternalCertificateRecords());
        Dictionary<string, CertRecord> unique = new Dictionary<string, CertRecord>(StringComparer.OrdinalIgnoreCase);
        foreach (CertRecord c in all)
        {
            if (String.IsNullOrWhiteSpace(c.Path)) continue;
            string key = !String.IsNullOrWhiteSpace(c.Thumbprint) ? "T|"+c.Thumbprint : "P|"+c.Path;
            CertRecord prior;
            if (!unique.TryGetValue(key, out prior) || (!String.IsNullOrWhiteSpace(c.PasswordDpapiB64) && String.IsNullOrWhiteSpace(prior.PasswordDpapiB64))) unique[key]=c;
        }
        return unique.Values.OrderBy(x=>x.Empresa).ThenBy(x=>x.Cnpj).ToList();
    }

    private static int CertificateCommand(string[] args)
    {
        string op = args.Length > 0 ? (args[0] ?? "").Trim().ToLowerInvariant() : "";
        if (op != "validate") return WriteError("Operação de certificado desconhecida.", 33);
        string path = Arg(args,"--path");
        if (String.IsNullOrWhiteSpace(path) || !File.Exists(path)) return WriteError("Arquivo A1 não encontrado.", 34);
        string password = Console.In.ReadToEnd();
        if (password != null) password = password.TrimEnd('\r','\n');
        X509Certificate2 cert;
        try { cert = new X509Certificate2(path, password ?? "", X509KeyStorageFlags.UserKeySet); }
        catch (CryptographicException) { return WriteError("Senha inválida.", 35); }
        CertRecord rec = new CertRecord(); rec.Path=path; rec.Empresa=FileLabel(path);
        try
        {
            if (!cert.HasPrivateKey) return WriteError("Certificado sem chave privada.", 36);
            FillCertificateMetadata(rec, cert);
            rec.PasswordDpapiB64 = ProtectSecret(password ?? "");
        }
        finally { cert.Reset(); }
        List<CertRecord> rows=LoadInternalCertificateRecords(); rows.RemoveAll(x=>String.Equals(x.Path,path,StringComparison.OrdinalIgnoreCase)); rows.Add(rec); SaveInternalCertificateRecords(rows);
        WriteJson(new Dictionary<string, object>{{"ok",true},{"certificate",PublicCertificate(rec)},{"native",true}});
        return 0;
    }

'''
s=s.replace(anchor,block+anchor,1)

s=s.rstrip()+"\n// "+MARK+" — scanner A1 integrado, pastas monitoradas e DPAPI.\n"
p.write_text(s,encoding='utf-8',newline='\n')
print('3.13.0: gerenciador A1 integrado ao Fiscal Core.')
