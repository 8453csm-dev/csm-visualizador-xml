# Benchmark — 4.0.0-alpha.1

Ambiente de desenvolvimento Linux, SSD local, 8 workers, 1.000 XMLs NF-e sintéticos com 1 item cada.

| Cenário | Resultado |
|---|---:|
| Primeira indexação | 0,546 s |
| Segunda abertura (100% cache) | 0,023 s |
| XMLs importados na primeira carga | 1.000 |
| XMLs reutilizados do cache na segunda | 1.000 |
| Falhas | 0 |

O benchmark não representa garantia de tempo no Windows nem em XMLs reais maiores. Ele valida a arquitetura incremental: após a primeira indexação, arquivos inalterados não são reprocessados.
