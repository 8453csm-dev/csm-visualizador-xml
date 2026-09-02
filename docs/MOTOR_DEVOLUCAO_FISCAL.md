# Motor Fiscal de Devolução — CSM Visualizador XML

Versão inicial das regras: **1.0.0**  
Data-base: **02/09/2026**

## Objetivo

Criar, a partir da NF-e original carregada no Visualizador, um **modelo orientativo de devolução** para revisão do fiscal e envio ao cliente. O módulo **não transmite NF-e**, não assina documento fiscal e não altera o XML original.

O motor deve:

- sugerir devolução total ou parcial;
- calcular proporcionalidade por item;
- sugerir CFOP por finalidade, UF e ICMS-ST;
- tratar regime normal e Simples Nacional;
- manter CST/CSOSN editável;
- mostrar ICMS, ICMS-ST, IPI, PIS e COFINS por item;
- exibir `pDevol` e `vIPIDevol` como orientação quando houver IPI;
- exigir revisão fiscal para PIS/COFINS e situações não determinísticas;
- orientar o referenciamento por item via `DFeReferenciado`;
- permitir edição manual de qualquer valor sugerido;
- persistir rascunho localmente;
- gerar orientação HTML e layout para impressão / PDF.

## Regra estrutural

A devolução busca anular os efeitos da operação original. Em devolução parcial, os valores são proporcionais às quantidades efetivamente devolvidas.

## Referenciamento por item — NF-e 2026

A NT 2025.002 v1.40 prevê, para NF-e de devolução (`finNFe=4`), referenciamento no grupo `DFeReferenciado`, com implantação em produção em **01/09/2026**. Quando houver referenciamento em nível de item, o `nItem` do documento original deve ser informado.

```xml
<DFeReferenciado>
  <chaveAcesso>CHAVE-DA-NFE-ORIGINAL</chaveAcesso>
  <nItem>ITEM-ORIGINAL</nItem>
</DFeReferenciado>
```

## CFOP — devolução de compra (saída)

| Finalidade | Interna | Interestadual | Com ST interna | Com ST interestadual |
|---|---:|---:|---:|---:|
| Comercialização | 5.202 | 6.202 | 5.411 | 6.411 |
| Industrialização | 5.201 | 6.201 | 5.410 | 6.410 |
| Uso/consumo | 5.556 | 6.556 | 5.413 | 6.413 |
| Ativo imobilizado | 5.553 | 6.553 | 5.412 | 6.412 |
| Transferência p/ comercialização | 5.209 | 6.209 | — | — |
| Transferência p/ industrialização | 5.208 | 6.208 | — | — |

Combustíveis possuem família específica e são tratados separadamente pelo motor quando reconhecidos.

## ICMS

Para devolução total ou parcial, a referência é a mesma base de cálculo e a mesma alíquota da operação original, proporcionalmente quando parcial.

### Simples Nacional — São Paulo

Para devolução de compra por optante do Simples Nacional, a orientação paulista vigente é **CSOSN 900**, com base de cálculo e ICMS nos campos próprios da NF-e.

### ICMS-ST — contribuinte substituído em São Paulo

Quando aplicável:

- ICMS da operação própria do fornecedor: campos próprios;
- BC-ST e ICMS-ST: `infAdFisco`;
- ICMS-ST proporcional: também em `vOutro`, para composição do valor total da NF-e.

## IPI

Quando houver IPI na operação original, o motor calcula proporcionalmente e mostra como orientação:

- `pDevol`;
- `vIPIDevol`;
- grupo `impostoDevol`, conforme o leiaute e a situação do emitente.

## PIS/COFINS

O motor mostra valores proporcionais como **referência**, porém mantém CST PIS e CST COFINS em revisão manual por padrão. O tratamento depende do regime da pessoa jurídica, tributação do produto e forma de escrituração.

O Guia Prático da EFD-Contribuições diferencia devolução de compras e devolução de vendas; portanto o CSM não deve inventar automaticamente um CST universal.

## IBS/CBS

Quando a NF-e original possui campos RTC, o módulo emite alerta de revisão e exige preservação do vínculo por item. A primeira versão não força automaticamente CST/cClassTrib de IBS/CBS sem evidência suficiente no documento.

## Segurança fiscal

- XML original é somente leitura.
- O resultado é **modelo orientativo**, nunca XML autorizado.
- Campos automáticos são editáveis.
- Campos alterados manualmente são marcados no relatório.
- Quantidade devolvida maior que a original gera bloqueio/alerta.
- Operações classificadas como “outra” usam 5.949/6.949 apenas como referência provisória e exigem revisão.

## Fontes oficiais usadas na base inicial

- Portal Nacional NF-e — NT 2025.002 v1.40 / RTC: https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY=
- SEFAZ-SP — RC 33626/2026: https://legislacao.fazenda.sp.gov.br/Paginas/RC33626_2026.aspx
- SEFAZ-SP — RC 34023/2026: https://legislacao.fazenda.sp.gov.br/Paginas/RC34023_2026.aspx
- SEFAZ-SP — RC 33346/2026: https://legislacao.fazenda.sp.gov.br/Paginas/RC33346_2026.aspx
- Resolução CGSN 140/2018: https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=92278
- Receita Federal — Guia Prático EFD-Contribuições: https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/manuais/sped/manuais-efd-contribuicoes/

## Evolução prevista

1. Regras por UF versionadas.
2. Perfis salvos por empresa/CNPJ.
3. Tabela CFOP completa nacional e operações especiais.
4. Regras específicas por produto/NCM.
5. IBS/CBS completo por `CST` e `cClassTrib`.
6. Exportação PDF nativa pelo backend.
7. Integração futura com emissores/G5 sem transmissão automática pelo Visualizador.
