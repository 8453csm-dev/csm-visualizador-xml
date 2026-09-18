from pathlib import Path

p=Path('installer-v2/launcher/csm_fiscal_core.cs')
s=p.read_text(encoding='utf-8')
MARK='CSM_REPOSITORY_API_3140'
if MARK in s:
    print('Repositório CSM NF-e 3.14.0 já aplicado')
    raise SystemExit(0)
if 'CSM_FISCAL_ISSUER_3131' not in s:
    raise SystemExit('Aplique o Fiscal Core 3.13.1 antes')

# Desde 3.14.0 os dados persistentes ficam fora da pasta de instalação, para sobreviver às atualizações.
old_cert='''        return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CSM Visualizador XML", "certificados");'''
new_cert='''        return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CSM", "VisualizadorXML", "certificados");'''
if old_cert not in s: raise SystemExit('CertConfigDir 3.13 não localizado')
s=s.replace(old_cert,new_cert,1)

old='''            if (cmd == "cert") return CertificateCommand(args.Skip(1).ToArray());
            if (cmd == "consult") return Consult(args.Skip(1).ToArray());'''
new='''            if (cmd == "cert") return CertificateCommand(args.Skip(1).ToArray());
            if (cmd == "sync") return SyncRepository(args.Skip(1).ToArray());
            if (cmd == "repo") return RepositoryCommand(args.Skip(1).ToArray());
            if (cmd == "consult") return Consult(args.Skip(1).ToArray());'''
if old not in s: raise SystemExit('Dispatch do Fiscal Core não localizado')
s=s.replace(old,new,1)

anchor='''    private static string IntegrationPath()
    {'''
if anchor not in s: raise SystemExit('IntegrationPath não localizado')

block=r'''
    // CSM_REPOSITORY_API_3140 — base local indexada por chave + distNSU oficial.
    private static string RepositoryRoot()
    {
        return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CSM", "VisualizadorXML", "repository");
    }
    private static string RepositoryNFeDir() { return Path.Combine(RepositoryRoot(), "nfe"); }
    private static string RepositorySummaryDir() { return Path.Combine(RepositoryRoot(), "summary"); }
    private static string RepositoryStateDir() { return Path.Combine(RepositoryRoot(), "state"); }
    private static string RepositoryXmlPath(string key) { return Path.Combine(RepositoryNFeDir(), key + ".xml"); }
    private static string RepositorySummaryPath(string key) { return Path.Combine(RepositorySummaryDir(), key + ".json"); }
    private static string RepositoryStatePath(string cnpj) { return Path.Combine(RepositoryStateDir(), cnpj + ".json"); }

    private static string ExtractNFeKey(string xml)
    {
        if (String.IsNullOrWhiteSpace(xml)) return "";
        Match m = Regex.Match(xml, @"\bId\s*=\s*[""']NFe(\d{44})[""']", RegexOptions.IgnoreCase);
        if (m.Success && IsValidKey(m.Groups[1].Value)) return m.Groups[1].Value;
        m = Regex.Match(xml, @"<chNFe>\s*(\d{44})\s*</chNFe>", RegexOptions.IgnoreCase);
        if (m.Success && IsValidKey(m.Groups[1].Value)) return m.Groups[1].Value;
        return "";
    }

    private static void SaveRepositoryXml(string xml, string actorCnpj, string nsu, string schema)
    {
        string key = ExtractNFeKey(xml);
        if (String.IsNullOrEmpty(key)) return;
        Directory.CreateDirectory(RepositoryNFeDir());
        File.WriteAllText(RepositoryXmlPath(key), xml, new UTF8Encoding(false));
        Directory.CreateDirectory(RepositorySummaryDir());
        Dictionary<string,object> meta = new Dictionary<string,object>
        {
            {"key",key},{"actor_cnpj",actorCnpj},{"nsu",nsu},{"schema",schema},
            {"xml_available",true},{"updated_utc",DateTime.UtcNow.ToString("o",CultureInfo.InvariantCulture)}
        };
        File.WriteAllText(RepositorySummaryPath(key), Json.Serialize(meta), new UTF8Encoding(false));
    }

    private static void SaveRepositorySummary(string xml, string actorCnpj, string nsu, string schema)
    {
        string key = ExtractNFeKey(xml);
        if (String.IsNullOrEmpty(key)) return;
        Directory.CreateDirectory(RepositorySummaryDir());
        Dictionary<string,object> meta = new Dictionary<string,object>
        {
            {"key",key},{"actor_cnpj",actorCnpj},{"nsu",nsu},{"schema",schema},
            {"xml_available",File.Exists(RepositoryXmlPath(key))},{"summary_only",true},
            {"updated_utc",DateTime.UtcNow.ToString("o",CultureInfo.InvariantCulture)}
        };
        File.WriteAllText(RepositorySummaryPath(key), Json.Serialize(meta), new UTF8Encoding(false));
    }

    private static Dictionary<string,object> LoadJsonDictionary(string path)
    {
        if (!File.Exists(path)) return new Dictionary<string,object>();
        try
        {
            object root=Json.DeserializeObject(File.ReadAllText(path,Encoding.UTF8));
            Dictionary<string,object> d=root as Dictionary<string,object>;
            return d ?? new Dictionary<string,object>();
        }
        catch { return new Dictionary<string,object>(); }
    }

    private static string DictString(Dictionary<string,object> d, string name, string fallback)
    {
        object v;
        return d != null && d.TryGetValue(name,out v) && v != null ? Convert.ToString(v,CultureInfo.InvariantCulture) ?? fallback : fallback;
    }

    private static DateTime DictUtc(Dictionary<string,object> d, string name)
    {
        string value=DictString(d,name,"");
        DateTime dt;
        if (DateTime.TryParse(value,CultureInfo.InvariantCulture,DateTimeStyles.RoundtripKind,out dt)) return dt.ToUniversalTime();
        return DateTime.MinValue;
    }

    private static string PadNSU(string value)
    {
        string digits=new string((value ?? "").Where(Char.IsDigit).ToArray());
        if (digits.Length>15) digits=digits.Substring(digits.Length-15);
        return digits.PadLeft(15,'0');
    }

    private static void SaveRepositoryState(string cnpj, string ultNsu, string maxNsu, DateTime nextAllowedUtc, string cstat, string message)
    {
        Directory.CreateDirectory(RepositoryStateDir());
        Dictionary<string,object> d=new Dictionary<string,object>
        {
            {"cnpj",cnpj},{"ult_nsu",PadNSU(ultNsu)},{"max_nsu",PadNSU(maxNsu)},
            {"next_allowed_utc",nextAllowedUtc==DateTime.MinValue ? "" : nextAllowedUtc.ToUniversalTime().ToString("o",CultureInfo.InvariantCulture)},
            {"last_cstat",cstat ?? ""},{"last_message",message ?? ""},
            {"updated_utc",DateTime.UtcNow.ToString("o",CultureInfo.InvariantCulture)}
        };
        File.WriteAllText(RepositoryStatePath(cnpj),Json.Serialize(d),new UTF8Encoding(false));
    }

    private static string BuildDistNSUPayload(string cnpj, string ultNsu)
    {
        // cUFAutor é opcional no schema distDFeInt; omitir evita inferir UF incorreta.
        return "<distDFeInt xmlns=\"" + NFeNs + "\" versao=\"1.01\"><tpAmb>1</tpAmb><CNPJ>" + Escape(cnpj) + "</CNPJ><distNSU><ultNSU>" + Escape(PadNSU(ultNsu)) + "</ultNSU></distNSU></distDFeInt>";
    }

    private static Dictionary<string,object> SyncRepositoryBatch(X509Certificate2 cert, string cnpj, string ultNsu)
    {
        string payload=BuildDistNSUPayload(cnpj,ultNsu);
        string response=PostSoap(cert,DistributionUrl,DistributionWsNs,"nfeDistDFeInteresse",DistributionWsNs + "/nfeDistDFeInteresse",payload);
        XDocument doc=XDocument.Parse(response,LoadOptions.PreserveWhitespace);
        XElement ret=FirstLocal(doc,"retDistDFeInt");
        if (ret==null) throw new Exception("O Ambiente Nacional respondeu sem retDistDFeInt.");
        string cstat=ChildValue(ret,"cStat"), message=ChildValue(ret,"xMotivo");
        string retUlt=ChildValue(ret,"ultNSU"), max=ChildValue(ret,"maxNSU");
        if (String.IsNullOrWhiteSpace(retUlt)) retUlt=ultNsu;
        if (String.IsNullOrWhiteSpace(max)) max=retUlt;
        int full=0, summaries=0, eventsCount=0;
        foreach (XElement z in ret.Descendants().Where(x=>x.Name.LocalName=="docZip"))
        {
            string schema=(string)z.Attribute("schema") ?? "";
            string nsu=(string)z.Attribute("NSU") ?? "";
            string inner="";
            try { inner=UnzipBase64(z.Value); } catch { continue; }
            if (String.IsNullOrWhiteSpace(inner)) continue;
            string lowSchema=schema.ToLowerInvariant(), lowXml=inner.ToLowerInvariant();
            if (lowSchema.Contains("procnfe") || lowXml.Contains("<nfeproc") || lowXml.Contains("<nfe "))
            {
                SaveRepositoryXml(inner,cnpj,nsu,schema); full++;
            }
            else if (lowSchema.Contains("resnfe") || lowXml.Contains("<resnfe"))
            {
                SaveRepositorySummary(inner,cnpj,nsu,schema); summaries++;
            }
            else if (lowSchema.Contains("evento") || lowXml.Contains("<proceventonfe") || lowXml.Contains("<resevento"))
            {
                eventsCount++;
            }
        }
        return new Dictionary<string,object>
        {
            {"cstat",cstat},{"message",message},{"ult_nsu",PadNSU(retUlt)},{"max_nsu",PadNSU(max)},
            {"full_xml",full},{"summaries",summaries},{"events",eventsCount}
        };
    }

    private static int SyncRepository(string[] args)
    {
        string requested=NormalizeDocument(Arg(args,"--cnpj"));
        if (requested.Length!=14) return WriteError("Informe o CNPJ de 14 dígitos para sincronizar a Base CSM.",40);
        int maxBatches=3; int parsed;
        if (Int32.TryParse(Arg(args,"--batches"),out parsed)) maxBatches=Math.Max(1,Math.Min(10,parsed));
        List<CertRecord> records=LoadAllCertificateRecords();
        CertRecord selected=records.Where(c=>String.Equals(c.Cnpj,requested,StringComparison.OrdinalIgnoreCase) && File.Exists(c.Path) && !IsClearlyExpired(c)).OrderByDescending(c=>ParseDate(c.Expiry)).FirstOrDefault();
        if (selected==null) return WriteError("Certificado A1 não encontrado para o CNPJ informado.",41);
        Dictionary<string,object> state=LoadJsonDictionary(RepositoryStatePath(requested));
        DateTime next=DictUtc(state,"next_allowed_utc");
        string ult=PadNSU(DictString(state,"ult_nsu","0"));
        if (next!=DateTime.MinValue && DateTime.UtcNow<next)
        {
            WriteJson(new Dictionary<string,object>{{"ok",true},{"skipped",true},{"reason","cooldown"},{"cnpj",requested},{"ult_nsu",ult},{"next_allowed_utc",next.ToString("o",CultureInfo.InvariantCulture)}});
            return 0;
        }
        X509Certificate2 cert;
        try { cert=LoadCertificate(selected); } catch(Exception ex) { return WriteError("Não foi possível abrir o A1 para sincronização: "+ex.Message,42); }
        int totalFull=0,totalSummaries=0,totalEvents=0,batches=0; string cstat="",message="",max=ult;
        try
        {
            for (int i=0;i<maxBatches;i++)
            {
                Dictionary<string,object> r=SyncRepositoryBatch(cert,requested,ult);
                batches++;
                cstat=DictString(r,"cstat",""); message=DictString(r,"message","");
                string newUlt=PadNSU(DictString(r,"ult_nsu",ult)); max=PadNSU(DictString(r,"max_nsu",newUlt));
                totalFull+=Convert.ToInt32(r["full_xml"],CultureInfo.InvariantCulture);
                totalSummaries+=Convert.ToInt32(r["summaries"],CultureInfo.InvariantCulture);
                totalEvents+=Convert.ToInt32(r["events"],CultureInfo.InvariantCulture);
                ult=newUlt;
                DateTime cooldown=DateTime.MinValue;
                if (cstat=="137" || cstat=="656" || String.Equals(ult,max,StringComparison.Ordinal)) cooldown=DateTime.UtcNow.AddHours(1);
                SaveRepositoryState(requested,ult,max,cooldown,cstat,message);
                if (cstat=="656" || cstat=="137" || String.Equals(ult,max,StringComparison.Ordinal)) break;
                if (cstat!="138") break;
            }
        }
        catch(Exception ex)
        {
            SaveRepositoryState(requested,ult,max,DateTime.MinValue,cstat,message);
            return WriteError("Falha ao sincronizar Base CSM: "+ex.Message,43);
        }
        finally { try { cert.Reset(); } catch { } }
        WriteJson(new Dictionary<string,object>
        {
            {"ok",true},{"cnpj",requested},{"batches",batches},{"full_xml",totalFull},{"summaries",totalSummaries},{"events",totalEvents},
            {"ult_nsu",ult},{"max_nsu",max},{"cstat",cstat},{"message",message},{"repository",RepositoryRoot()}
        });
        return 0;
    }

    private static int RepositoryCommand(string[] args)
    {
        string op=args.Length>0 ? (args[0] ?? "").Trim().ToLowerInvariant() : "";
        if (op=="get")
        {
            string key=Arg(args,"--key");
            if (!IsValidKey(key)) return WriteError("Chave inválida.",44);
            string xmlPath=RepositoryXmlPath(key);
            Dictionary<string,object> meta=LoadJsonDictionary(RepositorySummaryPath(key));
            if (File.Exists(xmlPath))
            {
                WriteJson(new Dictionary<string,object>
                {
                    {"ok",true},{"found",true},{"xml_available",true},{"key",key},{"xml_path",xmlPath},
                    {"actor_cnpj",DictString(meta,"actor_cnpj","")},{"source","Base CSM"}
                });
                return 0;
            }
            if (meta.Count>0)
            {
                WriteJson(new Dictionary<string,object>
                {
                    {"ok",true},{"found",true},{"xml_available",false},{"summary_only",true},{"requires_manifestation",true},
                    {"key",key},{"actor_cnpj",DictString(meta,"actor_cnpj","")},{"source","Base CSM"}
                });
                return 0;
            }
            WriteJson(new Dictionary<string,object>{{"ok",true},{"found",false},{"xml_available",false},{"key",key},{"source","Base CSM"}});
            return 0;
        }
        if (op=="stats")
        {
            int xml=Directory.Exists(RepositoryNFeDir()) ? Directory.GetFiles(RepositoryNFeDir(),"*.xml").Length : 0;
            int summaries=Directory.Exists(RepositorySummaryDir()) ? Directory.GetFiles(RepositorySummaryDir(),"*.json").Length : 0;
            WriteJson(new Dictionary<string,object>{{"ok",true},{"xml_count",xml},{"index_count",summaries},{"repository",RepositoryRoot()}});
            return 0;
        }
        return WriteError("Operação de repositório desconhecida.",45);
    }

'''
s=s.replace(anchor,block+anchor,1)
s=s.rstrip()+"\n// "+MARK+" — Base CSM por chave + sincronização distNSU respeitando cooldown.\n"
for tok in (MARK,'BuildDistNSUPayload','<distNSU>','RepositoryCommand','SyncRepository','next_allowed_utc','repository'):
    if tok not in s: raise SystemExit('Fiscal Core 3.14.0 incompleto: '+tok)
p.write_text(s,encoding='utf-8',newline='\n')
print('3.14.0: Base CSM NF-e + distNSU oficial adicionados ao Fiscal Core.')
