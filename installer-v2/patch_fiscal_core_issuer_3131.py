from pathlib import Path

p=Path('installer-v2/launcher/csm_fiscal_core.cs')
s=p.read_text(encoding='utf-8')
MARK='CSM_FISCAL_ISSUER_3131'
if MARK in s:
    print('Tratamento de NF-e própria 3.13.1 já aplicado')
    raise SystemExit(0)
if 'CSM_MANIFESTACAO_3130' not in s:
    raise SystemExit('Aplique os patches fiscais 3.13.0 antes')

old='''        ProtocolResult protocol = new ProtocolResult();
        DistributionResult distribution = new DistributionResult();
        string protocolError = "";
        string distributionError = "";

        try { protocol = QueryProtocol(cert, key); }
        catch (Exception ex) { protocolError = ex.Message; }

        try { distribution = QueryDistribution(cert, key, selected.Cnpj); }
        catch (Exception ex) { distributionError = ex.Message; }
'''
new='''        string issuerCnpj = key.Substring(6, 14);
        bool selectedIsIssuer = String.Equals(selected.Cnpj, issuerCnpj, StringComparison.OrdinalIgnoreCase);
        ProtocolResult protocol = new ProtocolResult();
        DistributionResult distribution = new DistributionResult();
        string protocolError = "";
        string distributionError = "";

        try { protocol = QueryProtocol(cert, key); }
        catch (Exception ex) { protocolError = ex.Message; }

        // consChNFe não redistribui o XML ao próprio emitente (regra H17 / cStat 641).
        // Evita uma chamada inútil e deixa o frontend procurar o XML original em fontes locais.
        if (selectedIsIssuer)
        {
            distribution.CStat = "641";
            distribution.Message = "NF-e emitida pela própria empresa. O Ambiente Nacional não redistribui o XML ao emitente na consulta por chave.";
            distribution.Ok = false;
        }
        else
        {
            try { distribution = QueryDistribution(cert, key, selected.Cnpj); }
            catch (Exception ex) { distributionError = ex.Message; }
        }
'''
if old not in s: raise SystemExit('Bloco protocolo/distribuição não localizado')
s=s.replace(old,new,1)

old='''            { "empresa", SafeCompany(selected) },
            { "status", status },'''
new='''            { "empresa", SafeCompany(selected) },
            { "issuer_cnpj", issuerCnpj },
            { "issuer_document", selectedIsIssuer },
            { "distribution_restricted", selectedIsIssuer && String.IsNullOrEmpty(xmlPath) },
            { "xml_unavailable_reason", selectedIsIssuer && String.IsNullOrEmpty(xmlPath) ? "issuer" : "" },
            { "status", status },'''
if old not in s: raise SystemExit('Resultado fiscal não localizado')
s=s.replace(old,new,1)

s=s.rstrip()+"\n// "+MARK+" — detecta emitente e expõe motivo 641 sem fingir que o XML foi baixado.\n"
for tok in (MARK,'issuer_document','distribution_restricted','xml_unavailable_reason','"641"'):
    if tok not in s: raise SystemExit('Patch fiscal 3.13.1 incompleto: '+tok)
p.write_text(s,encoding='utf-8',newline='\n')
print('3.13.1: NF-e própria detectada; consChNFe não tenta redistribuição ao emitente.')
