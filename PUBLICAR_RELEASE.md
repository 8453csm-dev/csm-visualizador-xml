# Publicar uma versão do CSM Visualizador XML

O repositório possui automação para atualizar o canal oficial após a publicação de uma Release.

## Para a versão 3.7.8

1. Abra **Releases** no repositório.
2. Clique em **Draft a new release**.
3. Crie a tag `v3.7.8`.
4. Título: `CSM Visualizador XML 3.7.8`.
5. Anexe exatamente este arquivo:
   `CSMVisualizadorXML-3.7.8-Instalador-Completo.exe`
6. Publique a Release.

Depois de publicada, o workflow `Publicar canal da release`:

- baixa o EXE da própria Release;
- calcula o SHA-256 real;
- atualiza `latest.json` com o link direto de download;
- atualiza `releases/3.7.8/SHA256SUMS.txt`;
- registra tudo automaticamente no repositório.

## SHA-256 esperado para 3.7.8

`d6086b661fb40d4c05ce76d38ecec836a8ff7d5c4c55a6df35c68ed03b484b74`

Se o checksum calculado pelo workflow for diferente, não distribua o arquivo até verificar a origem da divergência.
