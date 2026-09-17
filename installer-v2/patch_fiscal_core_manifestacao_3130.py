from pathlib import Path

p=Path('installer-v2/launcher/csm_fiscal_core.cs')
s=p.read_text(encoding='utf-8')
MARK='CSM_MANIFESTACAO_3130'
if MARK in s:
    print('Manifestação 3.13.0 já aplicada')
    raise SystemExit(0)
if 'CSM_CERT_MANAGER_3130' not in s:
    raise SystemExit('Aplique o gerenciador de certificados 3.13.0 antes')

# XMLDSig clássico exigido pela NF-e.
if 'using System.Security.Cryptography.Xml;' not in s:
    s=s.replace('using System.Security.Cryptography.X509Certificates;\n','using System.Security.Cryptography.X509Certificates;\nusing System.Security.Cryptography.Xml;\n',1)
if 'using System.Xml;\n' not in s:
    s=s.replace('using System.Web.Script.Serialization;\n','using System.Web.Script.Serialization;\nusing System.Xml;\n',1)

old='''internal sealed class DistributionResult\n{'''
new='''internal sealed class EventResult\n{\n    public bool Ok;\n    public bool Registered;\n    public bool Duplicate;\n    public string CStat = "";\n    public string Message = "";\n    public string Protocol = "";\n    public string Raw = "";\n}\n\ninternal sealed class DistributionResult\n{'''
if old not in s: raise SystemExit('DistributionResult não encontrado')
s=s.replace(old,new,1)

old='''    private const string DistributionUrl = "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx";\n    private const string NFeNs = "http://www.portalfiscal.inf.br/nfe";'''
new='''    private const string DistributionUrl = "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx";\n    private const string EventUrl = "https://www.nfe.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx";\n    private const string NFeNs = "http://www.portalfiscal.inf.br/nfe";'''
if old not in s: raise SystemExit('constantes principais não localizadas')
s=s.replace(old,new,1)
old='''    private const string DistributionWsNs = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe";'''
new='''    private const string DistributionWsNs = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe";\n    private const string EventWsNs = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4";'''
s=s.replace(old,new,1)

old='''            if (cmd == "cert") return CertificateCommand(args.Skip(1).ToArray());\n            if (cmd == "consult") return Consult(args.Skip(1).ToArray());'''
new='''            if (cmd == "cert") return CertificateCommand(args.Skip(1).ToArray());\n            if (cmd == "manifest") return Manifest(args.Skip(1).ToArray());\n            if (cmd == "consult") return Consult(args.Skip(1).ToArray());'''
if old not in s: raise SystemExit('dispatch para manifest não localizado')
s=s.replace(old,new,1)

anchor='''    private static string SafeCompany(CertRecord c)\n    {'''
if anchor not in s: raise SystemExit('SafeCompany não localizado')
block=r'''
    private static int Manifest(string[] args)
    {
        string key = Arg(args, "--key");
        string requestedCnpj = NormalizeDocument(Arg(args, "--cnpj"));
        string eventType = Arg(args, "--event");
        if (!IsValidKey(key)) return WriteError("Chave de acesso inválida.", 40);
        if (eventType != "210210") return WriteError("Somente Ciência da Operação (210210) é permitida neste fluxo.", 41);

        List<CertRecord> records = LoadAllCertificateRecords();
        CertRecord selected = SelectCertificate(records, requestedCnpj, key);
        if (selected == null)
        {
            WriteJson(new Dictionary<string, object>{{"ok",false},{"needs_certificate",true},{"message","Selecione o certificado A1 do destinatário antes de registrar a Ciência."}});
            return 42;
        }

        X509Certificate2 cert;
        try { cert = LoadCertificate(selected); }
        catch (Exception ex) { return WriteError("Não foi possível abrir o certificado de " + SafeCompany(selected) + ": " + ex.Message, 43); }

        ProtocolResult current;
        try { current = QueryProtocol(cert, key); }
        catch (Exception ex) { return WriteError("Não foi possível confirmar a situação da NF-e antes da Ciência: " + ex.Message, 44); }
        if (current.Status == "CANCELADA" || current.Status == "DENEGADA" || current.Status == "NÃO LOCALIZADA")
            return WriteError("Ciência não transmitida: NF-e " + current.Status + ".", 45);

        EventResult ev;
        try { ev = SendCiencia(cert, key, selected.Cnpj); }
        catch (Exception ex) { return WriteError("Falha ao registrar Ciência da Operação: " + ex.Message, 46); }

        bool accepted = ev.Registered || ev.Duplicate;
        DistributionResult distribution = new DistributionResult();
        string distributionError = "";
        if (accepted)
        {
            try { distribution = QueryDistribution(cert, key, selected.Cnpj); }
            catch (Exception ex) { distributionError = ex.Message; }
        }

        string xmlPath = "";
        if (!String.IsNullOrWhiteSpace(distribution.FullXml))
        {
            if (!XmlMatchesKey(distribution.FullXml, key)) return WriteError("XML retornado após a Ciência não corresponde à chave consultada.", 47);
            xmlPath = SaveXml(distribution.FullXml, key, "AUTORIZADA");
        }

        string message = ev.Message;
        if (accepted && !String.IsNullOrWhiteSpace(xmlPath)) message = "Ciência registrada. XML completo obtido e validado.";
        else if (accepted && distribution.SummaryOnly) message = "Ciência registrada. A Receita ainda retornou somente o resumo; consulte novamente mais tarde.";
        else if (accepted && !String.IsNullOrWhiteSpace(distribution.Message)) message = ev.Message + " • " + distribution.Message;

        WriteJson(new Dictionary<string, object>
        {
            {"ok", accepted}, {"native",true}, {"browser",false}, {"key",key}, {"cnpj",selected.Cnpj}, {"empresa",SafeCompany(selected)},
            {"event","210210"}, {"event_registered",accepted}, {"event_duplicate",ev.Duplicate}, {"event_cstat",ev.CStat}, {"event_protocol",ev.Protocol},
            {"distribution_retried",accepted}, {"distribution_cstat",distribution.CStat}, {"distribution_message",distribution.Message},
            {"summary_only",distribution.SummaryOnly}, {"xml_available",!String.IsNullOrWhiteSpace(xmlPath)}, {"xml_path",xmlPath},
            {"message",message}, {"distribution_error",distributionError}
        });
        return accepted ? 0 : 48;
    }

    private static EventResult SendCiencia(X509Certificate2 cert, string key, string cnpj)
    {
        string payload = BuildSignedCienciaPayload(cert, key, NormalizeDocument(cnpj));
        string response = PostEventSoap(cert, payload);
        XDocument doc = XDocument.Parse(response, LoadOptions.PreserveWhitespace);
        XElement ret = FirstLocal(doc, "retEnvEvento");
        if (ret == null) throw new Exception("Ambiente Nacional respondeu sem retEnvEvento.");
        XElement inner = ret.Descendants().FirstOrDefault(x => x.Name.LocalName == "retEvento");
        XElement inf = inner == null ? null : inner.Descendants().FirstOrDefault(x => x.Name.LocalName == "infEvento");
        EventResult r = new EventResult();
        r.Raw = response;
        r.CStat = inf != null ? ChildValue(inf, "cStat") : ChildValue(ret, "cStat");
        r.Message = inf != null ? ChildValue(inf, "xMotivo") : ChildValue(ret, "xMotivo");
        r.Protocol = inf != null ? ChildValue(inf, "nProt") : "";
        r.Registered = r.CStat == "135" || r.CStat == "136";
        r.Duplicate = r.CStat == "573";
        r.Ok = r.Registered || r.Duplicate;
        return r;
    }

    private static string BuildSignedCienciaPayload(X509Certificate2 cert, string key, string cnpj)
    {
        if (cnpj.Length != 14) throw new Exception("CNPJ do destinatário inválido para a Ciência da Operação.");
        string eventId = "ID210210" + key + "01";
        string lote = DateTime.UtcNow.ToString("yyyyMMddHHmmss", CultureInfo.InvariantCulture);
        string dh = DateTimeOffset.Now.ToString("yyyy-MM-dd'T'HH:mm:sszzz", CultureInfo.InvariantCulture);
        string xml = "<envEvento xmlns=\"" + NFeNs + "\" versao=\"1.00\"><idLote>" + lote + "</idLote><evento versao=\"1.00\"><infEvento Id=\"" + eventId + "\"><cOrgao>" + key.Substring(0,2) + "</cOrgao><tpAmb>1</tpAmb><CNPJ>" + Escape(cnpj) + "</CNPJ><chNFe>" + Escape(key) + "</chNFe><dhEvento>" + dh + "</dhEvento><tpEvento>210210</tpEvento><nSeqEvento>1</nSeqEvento><verEvento>1.00</verEvento><detEvento versao=\"1.00\"><descEvento>Ciencia da Operacao</descEvento></detEvento></infEvento></evento></envEvento>";
        XmlDocument doc = new XmlDocument();
        doc.PreserveWhitespace = true;
        doc.LoadXml(xml);
        XmlElement inf = doc.GetElementsByTagName("infEvento", NFeNs).OfType<XmlElement>().FirstOrDefault();
        XmlElement evento = doc.GetElementsByTagName("evento", NFeNs).OfType<XmlElement>().FirstOrDefault();
        if (inf == null || evento == null) throw new Exception("Não foi possível montar o XML de Ciência da Operação.");
        RSA rsa = cert.PrivateKey as RSA;
        if (rsa == null) throw new Exception("Certificado A1 não possui chave privada RSA compatível.");
        SignedXml signedXml = new SignedXml(doc);
        signedXml.SigningKey = rsa;
        signedXml.SignedInfo.CanonicalizationMethod = SignedXml.XmlDsigCanonicalizationUrl;
        signedXml.SignedInfo.SignatureMethod = SignedXml.XmlDsigRSASHA1Url;
        Reference reference = new Reference();
        reference.Uri = "#" + eventId;
        reference.DigestMethod = SignedXml.XmlDsigSHA1Url;
        reference.AddTransform(new XmlDsigEnvelopedSignatureTransform());
        reference.AddTransform(new XmlDsigC14NTransform());
        signedXml.AddReference(reference);
        KeyInfo keyInfo = new KeyInfo();
        keyInfo.AddClause(new KeyInfoX509Data(cert));
        signedXml.KeyInfo = keyInfo;
        signedXml.ComputeSignature();
        XmlElement signature = signedXml.GetXml();
        evento.AppendChild(doc.ImportNode(signature, true));
        return doc.OuterXml;
    }

    private static string PostEventSoap(X509Certificate2 cert, string payload)
    {
        string action = EventWsNs + "/nfeRecepcaoEvento";
        string body12 = "<?xml version=\"1.0\" encoding=\"utf-8\"?><soap12:Envelope xmlns:soap12=\"http://www.w3.org/2003/05/soap-envelope\"><soap12:Body><nfeDadosMsg xmlns=\"" + EventWsNs + "\">" + payload + "</nfeDadosMsg></soap12:Body></soap12:Envelope>";
        try { return SendSoap(cert, EventUrl, action, body12, true); }
        catch (Exception first)
        {
            string body11 = "<?xml version=\"1.0\" encoding=\"utf-8\"?><soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\"><soap:Body><nfeDadosMsg xmlns=\"" + EventWsNs + "\">" + payload + "</nfeDadosMsg></soap:Body></soap:Envelope>";
            try { return SendSoap(cert, EventUrl, action, body11, false); }
            catch (Exception second) { throw new Exception("Falha no Web Service de Eventos: " + first.Message + " | fallback SOAP 1.1: " + second.Message); }
        }
    }

'''
s=s.replace(anchor,block+anchor,1)

# Self-test sem transmissão: garante estrutura estática e endpoint central.
old='''        WriteJson(new Dictionary<string, object> { { "ok", true }, { "version", Version }, { "native", true }, { "browser", false } });'''
new='''        if (EventUrl.IndexOf("NFeRecepcaoEvento4", StringComparison.Ordinal) < 0 || EventWsNs.IndexOf("NFeRecepcaoEvento4", StringComparison.Ordinal) < 0) return WriteError("Self-test: endpoint de eventos incorreto.", 98);\n        WriteJson(new Dictionary<string, object> { { "ok", true }, { "version", Version }, { "native", true }, { "browser", false }, { "manifestacao", "210210" } });'''
if old not in s: raise SystemExit('SelfTest final não localizado')
s=s.replace(old,new,1)

s=s.rstrip()+"\n// "+MARK+" — Ciência da Operação 210210 explícita, XMLDSig e retry único da distribuição.\n"
p.write_text(s,encoding='utf-8',newline='\n')
print('3.13.0: Ciência da Operação 210210 integrada ao Fiscal Core.')
