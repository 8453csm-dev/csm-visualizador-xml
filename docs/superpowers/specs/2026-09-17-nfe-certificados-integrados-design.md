# CSM Visualizador XML — Consulta NF-e e Certificados Integrados

## Objetivo

Transformar a consulta por chave em um fluxo fiscal nativo e completo dentro do CSM Visualizador XML, sem navegador, sem scraping e sem dependência do Consulta DANFE no caminho principal.

O usuário deve conseguir:

1. colar uma chave de acesso e consultar a situação oficial da NF-e;
2. visualizar a NF-e completa quando o CSM puder obter o XML com um certificado autorizado;
3. salvar o XML para importação no G5;
4. gerar/salvar o DANFE em PDF a partir do XML obtido;
5. cadastrar uma ou mais pastas de certificados A1 e ver empresa, CNPJ, validade, vencimento e situação;
6. usar automaticamente o certificado compatível com a empresa envolvida na NF-e;
7. selecionar manualmente um certificado e informar a senha quando o CSM não conseguir resolver automaticamente;
8. registrar Ciência da Operação somente mediante confirmação explícita do usuário quando isso for necessário para obter o XML completo.

## Princípios do produto

- **Consulta oficial primeiro.** `NfeConsultaProtocolo` e `NFeDistribuicaoDFe` são o caminho principal.
- **Sem navegador no fluxo principal.** Localizadores web permanecem apenas como recurso legado em Mais ferramentas.
- **Nenhuma senha em texto puro.** Senhas validadas são migradas para Windows Credential Manager/DPAPI e nunca expostas ao frontend ou logs.
- **CNPJ real manda.** O vínculo certificado ↔ empresa é pelo CNPJ contido no A1, nunca apenas pelo nome do arquivo.
- **Visualizar não significa exportar.** XML obtido para visualização pode ficar no cache privado do CSM. Arquivo permanente só é criado quando o usuário pede Salvar XML/Exportar.
- **Eventos fiscais exigem consentimento.** Ciência da Operação nunca será transmitida silenciosamente.

## Arquitetura

### 1. Frontend do Visualizador

A tela `Consultar NF-e` passa a ter dois modos implícitos:

- **Consulta simples por chave:** sempre disponível. Exibe situação oficial, protocolo e mensagem da SEFAZ.
- **Consulta completa:** ativada automaticamente quando existe certificado compatível ou manualmente após o usuário selecionar um A1.

O frontend não lê PFX, não recebe senha e não fala diretamente com a SEFAZ. Ele conversa apenas com a API local do launcher/Fiscal Core.

### 2. Broker local do launcher

O launcher mantém a API local protegida em `127.0.0.1` e expõe endpoints internos para:

- listar certificados conhecidos;
- cadastrar/remover pastas monitoradas;
- reescanear certificados;
- validar um certificado manual e salvar a credencial protegida;
- consultar NF-e;
- registrar Ciência da Operação;
- salvar/exportar XML;
- gerar/salvar DANFE PDF.

Nenhuma origem web externa pode acionar esses endpoints.

### 3. CSM Fiscal Core

O `CSM Fiscal Core.exe` concentra toda a lógica fiscal e de certificado:

- validação de chave de acesso;
- roteamento por autorizadora;
- `NfeConsultaProtocolo` 4.00;
- `NFeDistribuicaoDFe` por `consChNFe`;
- leitura de `procNFe`, `resNFe` e eventos;
- identificação de autorizada/cancelada/denegada/não localizada;
- emissão de evento de Ciência da Operação quando explicitamente solicitado;
- nova consulta à distribuição após a manifestação;
- gravação segura de XML no cache;
- validação de que o XML devolvido corresponde exatamente à chave consultada.

### 4. Gerenciador de certificados integrado

O Visualizador passa a possuir uma área própria `Certificados Digitais`, usando o mesmo modelo de integração já adotado pelo ecossistema CSM.

O usuário pode adicionar uma ou mais pastas locais, de rede ou UNC. O scanner procura arquivos `.pfx` e `.p12` recursivamente.

Para cada certificado, o CSM tenta identificar:

- razão social / nome amigável;
- CNPJ extraído do certificado;
- caminho do arquivo;
- data inicial;
- vencimento;
- dias restantes;
- situação: Válido, Vence em breve, Vencido, Senha necessária, Arquivo indisponível;
- thumbprint;
- origem da credencial protegida.

## Regra de senha pelo nome do arquivo

O padrão legado `EMPRESA - SENHA.pfx` será aceito como facilitador.

Exemplo:

`FRAMEL - 1234.pfx`

Fluxo:

1. o scanner extrai `1234` como **senha candidata**;
2. tenta abrir o PFX localmente;
3. se abrir, lê o CNPJ real e demais metadados;
4. salva a senha em Windows Credential Manager ou DPAPI;
5. nunca grava a senha em JSON, banco, log ou frontend;
6. o índice passa a referenciar apenas `credential_target`/material protegido;
7. futuras consultas deixam de depender do nome do arquivo.

Se a senha candidata falhar, o arquivo fica com status `Senha necessária` e o usuário pode informar a senha manualmente.

## Seleção automática de certificado

A escolha segue esta prioridade:

1. certificado já associado ao CNPJ solicitado pelo usuário;
2. certificado cujo CNPJ corresponde ao ator necessário para a Distribuição DF-e;
3. certificado válido da mesma raiz de CNPJ, quando a regra fiscal permitir;
4. seleção manual pelo usuário.

Nunca será feito brute force com todos os certificados contra a SEFAZ.

## Fluxo de consulta por chave

### Etapa A — consulta oficial da situação

Ao clicar em `Consultar`:

1. validar a chave e DV;
2. consultar `NfeConsultaProtocolo`;
3. exibir situação, mensagem, protocolo e data de recebimento quando disponíveis.

Esse passo não exige que o usuário exporte ou salve qualquer arquivo.

### Etapa B — tentativa de obter o XML completo

Se houver certificado compatível:

1. chamar `NFeDistribuicaoDFe/consChNFe`;
2. se retornar `procNFe`, validar a chave e gravar no cache privado;
3. abrir automaticamente no parser existente do CSM;
4. liberar as ações `Visualizar NF-e`, `Salvar XML` e `DANFE PDF`.

Se não houver certificado compatível, exibir:

`Para visualizar a NF-e completa, selecione o certificado da empresa relacionada ao documento.`

com ações `Selecionar certificado` e `Informar senha`.

### Etapa C — somente resumo disponível

Se a Distribuição DF-e retornar apenas `resNFe`:

- mostrar que a NF-e foi localizada e autorizada;
- não fingir que o XML completo existe;
- exibir `Obter XML completo`.

Ao clicar, mostrar confirmação explícita:

> Para obter o XML completo será registrada **Ciência da Operação** em nome de `<empresa>` / `<CNPJ>`. Esta ação será transmitida à SEFAZ.

Ações:

- `Registrar Ciência e obter XML`
- `Agora não`

Após a confirmação:

1. transmitir evento `210210`;
2. validar resposta da SEFAZ;
3. consultar novamente a Distribuição DF-e;
4. ao receber o XML completo, validar chave, armazenar em cache e abrir no CSM.

Se a SEFAZ ainda não disponibilizar o XML, mostrar o retorno oficial sem repetir o evento automaticamente.

## Visualização, XML e DANFE

### Visualizar NF-e

A visualização completa usa o XML no cache interno do CSM e o mesmo pipeline de parser/abas já existente. Não cria arquivo em Downloads.

### Salvar XML

`Salvar XML` copia o XML validado do cache para o caminho escolhido pelo usuário. O XML deve permanecer exatamente como recebido da SEFAZ, sem alteração de conteúdo fiscal.

O objetivo principal é permitir uso posterior em sistemas como o G5.

### DANFE PDF

Quando houver XML completo, o CSM gera o DANFE/PDF localmente a partir do XML. Não é necessário baixar PDF de terceiros.

O PDF deve ser tratado como representação gráfica do documento, sem modificar o XML fiscal.

## Interface de Certificados Digitais

A tela terá:

- lista de pastas monitoradas;
- `Adicionar pasta`;
- `Remover pasta`;
- `Procurar certificados agora`;
- cards/lista de certificados ordenados alfabeticamente por empresa;
- filtros `Todos`, `Válidos`, `Vencendo`, `Vencidos`, `Senha necessária`;
- ações por certificado: `Testar`, `Informar senha`, `Abrir local`, `Remover credencial salva`.

Cada certificado exibirá:

- Empresa;
- CNPJ;
- tipo A1;
- emissor;
- início da validade;
- vencimento;
- dias restantes;
- status;
- caminho de origem.

Senhas nunca serão exibidas.

## Estados da tela Consultar NF-e

Estados mínimos:

- `Consultando situação na SEFAZ…`
- `AUTORIZADA`
- `CANCELADA`
- `DENEGADA`
- `NÃO LOCALIZADA`
- `XML completo disponível`
- `Somente resumo disponível`
- `Certificado necessário`
- `Senha necessária`
- `Registrando Ciência da Operação…`
- `Obtendo XML completo…`
- `XML aberto no Visualizador`

Mensagens técnicas de SOAP/TLS não aparecem como sucesso. Em modo normal o usuário recebe texto amigável; detalhe técnico vai para log sanitizado, sem senha, PFX ou conteúdo sensível.

## Cache

XML obtido para visualização fica em:

`%LOCALAPPDATA%\CSM Visualizador XML\cache\nfe\`

Regras:

- nome baseado em chave e situação;
- nenhuma duplicação desnecessária;
- antes de reutilizar, validar que o XML contém a mesma chave;
- `Salvar XML` sempre parte de um XML já validado;
- cache é implementação interna, não pasta de trabalho do usuário.

## Segurança

- Senha de PFX nunca vai para JavaScript.
- Senha nunca aparece em logs.
- `credential_target` e DPAPI são permitidos; texto puro não.
- Certificado só é carregado dentro do Fiscal Core.
- API local rejeita origens externas.
- XML recebido é validado pela chave antes de qualquer abertura/exportação.
- Ciência da Operação exige clique de confirmação explícito.
- Nenhuma manifestação conclusiva é feita automaticamente.

## Tratamento de erros

### Certificado

- arquivo removido: `Arquivo indisponível`;
- senha errada: `Senha inválida`;
- vencido: bloquear uso e mostrar vencimento;
- sem chave privada: bloquear uso;
- CNPJ não identificável: permitir cadastro manual apenas para rótulo, nunca para forjar o CNPJ fiscal.

### SEFAZ

- serviço indisponível: mostrar retorno amigável e manter opção de tentar novamente;
- consumo indevido: não repetir automaticamente; mostrar bloqueio temporário;
- XML não distribuído: mostrar resumo/manifestação quando aplicável;
- retorno de outra chave: descartar imediatamente;
- evento já registrado: tratar como estado idempotente e prosseguir para nova distribuição quando a resposta oficial permitir.

## Compatibilidade e legado

- O Visualizador local de XML/PDF continua intacto.
- O Localizador Fiscal web antigo permanece em `Mais ferramentas` durante a transição, sem participar do botão principal `Consultar NF-e`.
- O CSM Certificados Digitais externo pode continuar existindo; o Visualizador deve consumir o mesmo formato de integração quando disponível, mas passa também a conseguir cadastrar pastas diretamente.
- Não quebrar associação `.xml`, abertura em abas, fullscreen, importação de pasta, Motor Fiscal, DIFAL/ST, Devolução e Entender a Tributação.

## Critérios de aceite

A implementação só é considerada pronta quando:

1. chave válida consulta a situação sem navegador;
2. certificado compatível é selecionado automaticamente quando disponível;
3. pasta de certificados pode ser cadastrada e reescaneada;
4. arquivos `EMPRESA - SENHA.pfx` podem ser reconhecidos sem deixar a senha em texto puro após a validação;
5. certificados mostram CNPJ, validade, vencimento e status;
6. certificado ausente ou senha inválida leva a seleção/manual sem travar o fluxo;
7. `procNFe` recebido abre automaticamente no Visualizador;
8. `resNFe` gera a opção de Ciência da Operação, sempre com confirmação;
9. após Ciência válida, o CSM tenta novamente obter o XML;
10. `Salvar XML` entrega o XML oficial intacto para uso no G5;
11. `DANFE PDF` é gerado localmente a partir do XML completo;
12. nenhuma consulta principal abre navegador ou site externo;
13. todos os módulos fiscais e fluxos existentes passam nos testes de regressão;
14. instalação limpa contém o Fiscal Core, a interface de certificados e os novos endpoints locais.

## Fora de escopo desta entrega

- emissão de NF-e;
- importação direta automatizada no G5;
- armazenamento centralizado de certificados em nuvem;
- manifestação conclusiva automática (`Confirmação`, `Desconhecimento`, `Operação não Realizada`) sem ação específica do usuário;
- tentativa de obter XML de terceiros por scraping ou API não oficial.