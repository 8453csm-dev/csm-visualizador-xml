# CSM Visualizador XML 4.0 — desenvolvimento

Base isolada da próxima geração do CSM Visualizador XML.

Objetivo: preservar a responsividade e os recursos da linha 3.7.x, incorporando nativamente a aba XML validada, cache SQLite, importação paralela com progresso real e operações pesadas fora da thread da interface.

## Estado

`4.0.0-alpha.1`

Implementado no núcleo alpha:

- parsing defensivo de XML fiscal;
- indexação incremental em SQLite/WAL;
- importação paralela com progresso real e cancelamento;
- pesquisa local por documento e item;
- geração de PDF único com progresso e escrita atômica;
- componente da aba XML baseado na interface v8 homologada.

A versão 3.7.8 continua sendo o canal estável até a homologação completa do 4.0.
