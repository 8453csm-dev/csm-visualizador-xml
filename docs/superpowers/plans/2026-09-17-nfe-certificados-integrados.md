# NF-e e Certificados Integrados Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o CSM Visualizador XML 3.13.0 com consulta oficial por chave, gerenciamento local de A1, obtenção/visualização/exportação de XML e Ciência da Operação explícita quando necessária.

**Architecture:** O frontend fala apenas com o broker local do launcher. O broker chama o `CSM Fiscal Core.exe`, que concentra certificado, Credential Manager/DPAPI, Web Services NF-e e cache. O XML completo validado é sempre aberto pelo pipeline de abas já existente; o frontend nunca recebe senha de PFX.

**Tech Stack:** Windows, Go launcher/broker, C# .NET Framework Fiscal Core, HTML/CSS/JavaScript do Visualizador, GitHub Actions, Inno Setup.

**Spec:** `docs/superpowers/specs/2026-09-17-nfe-certificados-integrados-design.md`

## Global Constraints

- Base funcional: `release/3.12.1` / CSM Visualizador XML 3.12.1.
- Versão desta entrega: `3.13.0`.
- Consulta principal não pode abrir navegador nem provedor externo.
- Senha de PFX nunca é devolvida ao frontend nem escrita em logs/JSON de configuração.
- CNPJ fiscal vem do certificado, não do nome do arquivo.
- Ciência da Operação (`210210`) exige confirmação explícita antes da transmissão.
- XML exportado deve permanecer byte-a-byte equivalente ao XML oficial salvo no cache do Fiscal Core.
- Não alterar os motores fiscais existentes nem associação `.xml`/abas/fullscreen.

---

### Task 1: Registro local de pastas e scanner de certificados A1

**Files:**
- Modify: `installer-v2/launcher/csm_fiscal_core.cs`
- Create: `installer-v2/test_cert_manager_3130.py`

**Interfaces:**
- Produces CLI commands: `folders list`, `folders add --path <dir>`, `folders remove --path <dir>`, `scan`, `cert validate --path <pfx> --password-stdin`.
- Produces JSON certificate fields: `cnpj`, `empresa`, `path`, `expiry`, `not_before`, `days_remaining`, `status`, `thumbprint`, `credential_target`, `issuer`.

- [ ] **Step 1: Write failing tests**

Create tests that compile the Fiscal Core and verify that a temporary certificate directory can be added/listed/removed; that `.pfx/.p12` discovery is recursive; that a filename `FRAMEL - 1234.pfx` yields only a password *candidate* internally and never emits `1234` in JSON/log output; and that invalid/unopenable files return `Senha necessária`/`Arquivo inválido` rather than crashing.

- [ ] **Step 2: Run tests to verify RED**

Run: `python installer-v2/test_cert_manager_3130.py`
Expected: FAIL because the new CLI commands and folder registry do not exist.

- [ ] **Step 3: Implement minimal certificate registry/scanner**

Store monitored-folder metadata under `%LOCALAPPDATA%\CSM Visualizador XML\certificados\folders.json`. Reuse existing external integration JSON when present, merge by thumbprint/path, scan recursively, inspect PFX only in the Fiscal Core, and return sanitized metadata.

- [ ] **Step 4: Verify GREEN**

Run: `python installer-v2/test_cert_manager_3130.py`
Expected: PASS with no candidate password present in stdout/config/log fixtures.

- [ ] **Step 5: Commit**

Commit message: `feat: add integrated A1 certificate registry`

---

### Task 2: Credenciais protegidas e seleção manual

**Files:**
- Modify: `installer-v2/launcher/csm_fiscal_core.cs`
- Modify: `installer-v2/test_cert_manager_3130.py`

**Interfaces:**
- Consumes: certificate records from Task 1.
- Produces: `cert validate` that stores credentials under deterministic target `CSM.VisualizadorXML.A1.<thumbprint>` using Credential Manager with DPAPI fallback.

- [ ] **Step 1: Add failing tests**

Test that a valid password can be supplied through redirected stdin, that stdout never contains it, that the stored record contains only `credential_target`/protected data, and that a wrong password returns `Senha inválida` without overwriting an existing valid credential.

- [ ] **Step 2: Verify RED**

Run: `python installer-v2/test_cert_manager_3130.py`
Expected: new credential tests FAIL.

- [ ] **Step 3: Implement protected credential persistence**

Reuse the existing `CredReadW`/DPAPI logic from the CSM ecosystem. Filename candidate passwords may be tried locally during scan; successful candidates are persisted only through protected credential storage and are not copied to JSON.

- [ ] **Step 4: Verify GREEN**

Run: `python installer-v2/test_cert_manager_3130.py`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: protect A1 credentials and manual validation`

---

### Task 3: Broker endpoints for certificates and folders

**Files:**
- Modify: `installer-v2/launcher/main.go` via new patch `installer-v2/patch_launcher_cert_manager_3130.py`
- Create: `installer-v2/test_launcher_cert_manager_3130.py`

**Interfaces:**
- Produces local endpoints: `GET /fiscal/certificates`, `GET /fiscal/certificate-folders`, `POST /fiscal/certificate-folders/add`, `POST /fiscal/certificate-folders/remove`, `POST /fiscal/certificates/scan`, `POST /fiscal/certificate/validate`.
- All endpoints require the same localhost/origin protection as existing Fiscal Core routes.

- [ ] **Step 1: Write failing broker patch tests**

Test that patched Go source contains all routes, rejects external origins, limits request bodies, invokes only `CSM Fiscal Core.exe`, and never forwards password in query strings or command line arguments.

- [ ] **Step 2: Verify RED**

Run: `python installer-v2/test_launcher_cert_manager_3130.py`
Expected: FAIL because endpoints are absent.

- [ ] **Step 3: Implement broker routes**

Password validation endpoint sends the password to the child process through stdin. Folder paths and thumbprints use JSON bodies. Responses remain sanitized JSON.

- [ ] **Step 4: Verify GREEN + Go formatting/build**

Run: `python installer-v2/test_launcher_cert_manager_3130.py`
Then: `gofmt` and launcher self-test in CI.
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: expose protected certificate manager endpoints`

---

### Task 4: Manifestação Ciência da Operação e nova distribuição

**Files:**
- Modify: `installer-v2/launcher/csm_fiscal_core.cs`
- Create: `installer-v2/test_manifestacao_3130.py`

**Interfaces:**
- Produces command: `manifest --key <44> --cnpj <14> --event 210210`.
- Produces JSON: `ok`, `cstat`, `message`, `protocol`, `event_registered`, `distribution_retried`, `xml_path`, `xml_available`.

- [ ] **Step 1: Write failing payload/parser tests**

Assert event XML contains `tpEvento=210210`, `nSeqEvento=1`, `verEvento=1.00`, correct `chNFe`, CNPJ actor, and signed `infEvento`; assert no event request can be generated without explicit `--event 210210`.

- [ ] **Step 2: Verify RED**

Run: `python installer-v2/test_manifestacao_3130.py`
Expected: FAIL because event support is absent.

- [ ] **Step 3: Implement event service and retry flow**

Route the event to the correct NF-e event receiver, sign `infEvento` with the selected A1, parse idempotent/already-registered responses, and after accepted/idempotent Ciência perform exactly one new `NFeDistribuicaoDFe/consChNFe` attempt. Never emit a conclusive manifestation automatically.

- [ ] **Step 4: Verify GREEN**

Run: `python installer-v2/test_manifestacao_3130.py`
Expected: PASS for XML generation, signing structure and response parser fixtures.

- [ ] **Step 5: Commit**

Commit message: `feat: add explicit ciencia da operacao flow`

---

### Task 5: Exportação do XML oficial e DANFE pelo pipeline existente

**Files:**
- Modify: `installer-v2/launcher/main.go` via new patch `installer-v2/patch_launcher_nfe_exports_3130.py`
- Modify frontend via new patch `installer-v2/patch_nfe_exports_3130.py`
- Create: `installer-v2/test_nfe_exports_3130.js`

**Interfaces:**
- `Salvar XML` copies only a validated cached XML selected by key.
- `DANFE PDF` first opens/activates the cached XML in the normal Visualizador pipeline and invokes the existing PDF save flow; no third-party PDF download.

- [ ] **Step 1: Write failing frontend tests**

Test action visibility: XML actions hidden without `xml_available`; visible with XML; `Visualizar` opens cached XML; `Salvar XML` calls protected export route; `DANFE PDF` activates the document and uses existing PDF action.

- [ ] **Step 2: Verify RED**

Run: `node installer-v2/test_nfe_exports_3130.js`
Expected: FAIL because action panel is absent.

- [ ] **Step 3: Implement minimal actions**

Do not duplicate the existing renderer. Reuse `queuePath`/open-in-tab for visualização and the current Save PDF behavior for DANFE. For XML export, use native save/copy plumbing so the official cache file is copied intact.

- [ ] **Step 4: Verify GREEN**

Run: `node installer-v2/test_nfe_exports_3130.js`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: add XML and DANFE actions to NF-e lookup`

---

### Task 6: Tela Certificados Digitais e fallback manual no modal NF-e

**Files:**
- Create: `installer-v2/patch_certificates_ui_3130.py`
- Create: `installer-v2/test_certificates_ui_3130.js`
- Modify generated `app.js`/`refinement.css` through patching.

**Interfaces:**
- Adds `Certificados Digitais` under `Mais ferramentas`.
- Modal consulta consumes sanitized certificate list and states `Certificado necessário`, `Senha necessária`, `Somente resumo disponível`, `XML completo disponível`.

- [ ] **Step 1: Write failing JSDOM tests**

Test folder add/remove/rescan UI, alphabetical certificate cards, expiry/days/status display, filters, manual PFX selection/password prompt, and explicit Ciência confirmation. Assert password input value is never inserted into DOM history/localStorage/recent-query records.

- [ ] **Step 2: Verify RED**

Run: `node installer-v2/test_certificates_ui_3130.js`
Expected: FAIL because UI is absent.

- [ ] **Step 3: Implement UI patch**

Reuse current theme/classes. Keep `Consultar NF-e` compact. Certificate management lives in `Mais ferramentas`, while missing-certificate/password states offer contextual actions inside the lookup modal.

- [ ] **Step 4: Verify GREEN**

Run: `node installer-v2/test_certificates_ui_3130.js`
Expected: PASS in dark and light theme fixture states.

- [ ] **Step 5: Commit**

Commit message: `feat: add certificate management UI and lookup fallback`

---

### Task 7: Integração do fluxo completo de consulta

**Files:**
- Modify: `installer-v2/patch_native_fiscal_core_3120.py` through a new additive patch `installer-v2/patch_nfe_integrated_flow_3130.py`
- Create: `installer-v2/test_nfe_integrated_flow_3130.js`

**Interfaces:**
- Query result drives exactly one of: status-only, certificate-needed, password-needed, summary-only/manifest, XML-ready/opened.

- [ ] **Step 1: Write failing state-machine tests**

Fixture cases: authorized/no cert; authorized/cert+procNFe; authorized/resNFe; cancelled; wrong-key XML; service unavailable; consumption abuse; already-manifested event.

- [ ] **Step 2: Verify RED**

Run: `node installer-v2/test_nfe_integrated_flow_3130.js`
Expected: FAIL because 3.12.1 has only status/distribution basics.

- [ ] **Step 3: Implement state machine**

Auto-open only after validated `procNFe`. Never retry consumption-abuse automatically. For `resNFe`, expose Ciência CTA but transmit only after the separate confirm action.

- [ ] **Step 4: Verify GREEN**

Run: `node installer-v2/test_nfe_integrated_flow_3130.js`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: complete native NF-e lookup state machine`

---

### Task 8: Release 3.13.0, regressão e instalação limpa

**Files:**
- Create: `installer-v2/patch_release_identity_3130.py`
- Create: `installer-v2/prepare_release_3130.py`
- Create: `.github/workflows/build-3.13.0-final.yml`
- Update release docs/version metadata generated by patches.

**Interfaces:**
- Produces artifact `CSM Visualizador XML 3.13.0 - Instalador Completo.exe` and SHA-256.

- [ ] **Step 1: Add release verification before packaging**

Require tests from Tasks 1-7 plus existing folder-progress, DIFAL/ST, Devolução and Tributação suites. Require tokens proving browser flow is disabled for primary lookup.

- [ ] **Step 2: Build installer**

Compile Fiscal Core, launcher and Inno installer on `windows-latest`.
Expected: all compilation/self-tests succeed.

- [ ] **Step 3: Clean-install homologation**

Install to a temporary directory and assert: version 3.13.0; `CSM Fiscal Core.exe`; certificate routes; certificate UI; integrated lookup; no missing assets; launcher self-test passes.

- [ ] **Step 4: Regression verification**

Run all existing fiscal/UI tests and association/launcher self-tests. Expected: zero failures.

- [ ] **Step 5: Publish artifact**

Generate SHA-256 and upload final installer artifact.

- [ ] **Step 6: Commit**

Commit message: `release: build CSM Visualizador XML 3.13.0`
