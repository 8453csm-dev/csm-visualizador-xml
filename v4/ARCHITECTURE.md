# CSM Visualizador XML 4.0 — Arquitetura

## Objetivo

Evoluir a linha 3.7.x sem perder sua responsividade. O 4.0 separa interface, indexação, geração de documentos e integrações externas para impedir operações pesadas na thread da UI.

## Regras de preservação

- O XML fiscal original nunca é alterado.
- A linha 3.7.8 continua sendo o canal estável até a homologação do 4.0.
- Recursos atuais (NF-e, NFC-e, CT-e, MDF-e, NFS-e, eventos, Localizador Fiscal, devoluções, Dossiê Fiscal, PDFs e relacionamentos) devem ser migrados sem regressão.
- CAPTCHA permanece manual; o software não resolve nem contorna validação humana.

## Componentes

### Biblioteca SQLite

`library.sqlite3`, journal mode WAL. Arquivos inalterados não são relidos; quando um XML muda, ele é reprocessado e o SHA-256 é atualizado.

### Importador assíncrono

- descoberta da pasta uma vez;
- comparação com cache;
- parsing em pool de workers;
- escrita transacional no SQLite;
- progresso real `processados / total`;
- cancelamento cooperativo;
- interface continua utilizável.

### Aba XML nativa

A implementação visual aprovada na v8 passa a ser componente do frontend, não hotfix: syntax highlighting, destaque fiscal, busca, anterior/próximo, contador, sincronização imediata e copiar XML, ocultando o XML cru antes do primeiro repaint.

### PDF único

A união continua com `pypdf`, fora da thread da UI, com progresso por arquivo. O PDF final é gravado via `.part` e promovido somente após conclusão.

### Pesquisa global

Consulta SQLite por chave, número, CNPJ, razão social, produto, NCM e CFOP sem reabrir XMLs.

## Próximas etapas

1. Integrar o shell WebView2/pywebview da linha 3.7.x ao novo núcleo.
2. Migrar Localizador Fiscal e captura de downloads sem regressão.
3. Adicionar painel de operações em background.
4. Adicionar dashboard fiscal e auditorias determinísticas.
5. Empacotar `4.0.0-beta.1` com PyInstaller e instalador transacional.
6. Homologar em máquina real antes de alterar `latest.json`.
