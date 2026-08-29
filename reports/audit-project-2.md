# Architecture Audit Report — Project 2: ecommerce-api-legacy

**Stack:** JavaScript (Node.js 18+) + Express 4.18.2 + SQLite (`:memory:`)  
**Domain:** LMS API with Course Checkout Workflow (usuários, cursos, matrículas, pagamentos, auditoria)  
**Execution Phase:** Phase 2 (Code Smells & Architecture Issues Detection)  
**Skill:** `refactor-arch`

---

## 1. Summary of Findings

| Severity | Count | Primary Impact Areas |
|----------|-------|----------------------|
| **CRITICAL** | 3 | God Class (`AppManager`), Hardcoded Secrets in Source, Sensitive Card & Key Exposure in Logs |
| **HIGH** | 5 | Lack of MVC Separation, Business Logic in Route Handlers, Insecure Pseudo-Crypto (`badCrypto`), Non-Transactional Multi-Table Writes, Global Mutable State |
| **MEDIUM** | 5 | Callback Hell / Long Methods, N+1 Queries in Financial Report, Silently Ignored Errors, Orphan Data on Delete, Boot Race Condition |
| **LOW** | 2 | Cryptic / Abbreviated Request Field Naming, Dead / Unused Exported State |
| **TOTAL** | **15** | **Exceeds minimum threshold (≥ 5 findings)** |

---

## 2. Detailed Findings (Ordered by Severity)

### [CRITICAL] God Class (`AppManager.js`)
- **Location:**
  - `file: src/AppManager.js`; `line: 4-139`; `symbol: AppManager` (`initDb`: 10-23, `setupRoutes`: 25-138, `processPaymentAndEnroll`: 50-63)
- **Description:** Classe única concentrando conexão SQLite, criação de tabelas DDL, carga de seeds, roteamento HTTP do Express, lógica de checkout, decisão de pagamento, emissão de relatórios e exclusão de usuários.
- **Impact:** Dificuldade extrema de manutenção, impossibilidade de testes unitários isolados e acoplamento máximo de infraestrutura com lógica de negócio.
- **Recommendation:** Decompor a aplicação no padrão MVC com Controllers (`checkoutController`, `reportController`, `userController`), Models (`userModel`, `courseModel`, `enrollmentModel`, `paymentModel`, `auditLogModel`, `reportModel`) e Services de domínio.

### [CRITICAL] Hardcoded Secrets in Source Code
- **Location:**
  - `file: src/utils.js`; `line: 1-7`; `symbol: config`
- **Description:** Credenciais de banco, chave live de gateway de pagamento (`PAYMENT_GATEWAY_KEY = 'pk_live_supersecret_key_12345'`) e usuário SMTP versionados diretamente no código-fonte.
- **Impact:** Vazamento direto de credenciais em repositórios e comprometimento de contas de pagamento de terceiros.
- **Recommendation:** Centralizar todas as configurações em `src/config/settings.js` lendo de `process.env` com fallback seguro e arquivo `.env.example`.

### [CRITICAL] Sensitive Data Leaked in Console Logs
- **Location:**
  - `file: src/AppManager.js`; `line: 45-45`; `symbol: processPaymentAndEnroll`
- **Description:** Números completos de cartão de crédito (`cc`) e chaves secretas de gateway de pagamento impressos no console a cada requisição de checkout.
- **Impact:** Violação grave de compliance PCI-DSS e exposição de dados financeiros de clientes.
- **Recommendation:** Remover logs que contenham cartões ou credenciais; nunca logar payloads sensíveis.

### [HIGH] Lack of MVC Separation of Concerns
- **Location:**
  - `file: src/app.js`; `line: 1-14`; `symbol: bootstrap/listen`
  - `file: src/AppManager.js`; `line: 1-141`; `symbol: AppManager`
  - `file: src/utils.js`; `line: 1-25`; `symbol: config/cache/crypto helpers`
- **Description:** Inexistência de camadas distintas de Model, View (formatação de resposta JSON) e Controller; código monolítico em callbacks.
- **Recommendation:** Reestruturar em MVC com camada de apresentação View (`src/views/httpResponses.js`) e rotas desacopladas (`src/routes/index.js`).

### [HIGH] Business Logic Embedded in Express Route Handlers
- **Location:**
  - `file: src/AppManager.js`; `line: 28-78`; `symbol: POST /api/checkout`
- **Description:** Validação de cartão, criação de usuário, verificação de duplicidade, inserção de matrícula e registro de auditoria executados diretamente dentro do callback HTTP do Express.
- **Recommendation:** Extrair o caso de uso para `src/services/checkoutService.js` e gateway para `src/services/paymentGateway.js`.

### [HIGH] Insecure Pseudo-Cryptography (`badCrypto`)
- **Location:**
  - `file: src/utils.js`; `line: 17-23`; `symbol: badCrypto`
  - `file: src/AppManager.js`; `line: 68-68`; `symbol: badCrypto usage`
- **Description:** Função customizada que faz truncamento de string Base64 e soma de caracteres, sem salt ou algoritmo de derivação seguro.
- **Impact:** Senhas reversíveis ou triviais de serem quebradas em milissegundos.
- **Recommendation:** Implementar hashing seguro usando o módulo nativo `crypto.scryptSync` com salt configurável por ambiente.

### [HIGH] Absence of Transactional Boundary in Checkout
- **Location:**
  - `file: src/AppManager.js`; `line: 50-63`; `symbol: processPaymentAndEnroll`
- **Description:** Inserções de matrícula, pagamento e log de auditoria são executadas de forma sequencial sem transação (`BEGIN TRANSACTION` / `COMMIT`).
- **Impact:** Se a inserção de pagamento ou log falhar, o aluno fica matriculado sem registro de cobrança, gerando inconsistência na base.
- **Recommendation:** Envolver operações dependentes em transação SQLite via helper `withTransaction(db, fn)` com rollback automático.

### [HIGH] Global Mutable State
- **Location:**
  - `file: src/utils.js`; `line: 9-15`; `symbol: globalCache/totalRevenue/logAndCache`
- **Description:** Objeto de cache global em memória e contador de receita acumulada compartilhados entre requisições.
- **Impact:** Vazamento de estado entre requisições concorrentes e perda de consistência em múltiplos nós.
- **Recommendation:** Eliminar variáveis mutáveis globais e calcular relatórios com queries agregadas.

### [MEDIUM] Callback Hell & Long Methods
- **Location:**
  - `file: src/AppManager.js`; `line: 28-78`; `symbol: POST /api/checkout`
  - `file: src/AppManager.js`; `line: 80-129`; `symbol: GET /api/admin/financial-report`
- **Description:** Callbacks SQLite aninhados em mais de 5 níveis de profundidade (*Pyramid of Doom*).
- **Recommendation:** Migrar para Promises e `async/await` com helpers `dbGet`, `dbAll`, `dbRun` em `src/db/database.js`.

### [MEDIUM] N+1 Queries in Financial Report
- **Location:**
  - `file: src/AppManager.js`; `line: 89-127`; `symbol: GET /api/admin/financial-report`
- **Description:** Carrega todos os cursos e, em loop, faz consultas separadas para cada matrícula, usuário e pagamento correspondente.
- **Recommendation:** Reescrever a agregação utilizando uma única query SQL com `LEFT JOIN` entre cursos, matrículas, pagamentos e usuários em `src/models/reportModel.js`.

### [MEDIUM] Missing / Inconsistent Error Handling
- **Location:**
  - `file: src/AppManager.js`; `line: 133-136`; `symbol: DELETE /api/users/:id`
  - `file: src/AppManager.js`; `line: 57-57`; `symbol: audit_logs callback`
  - `file: src/AppManager.js`; `line: 104-106`; `symbol: report callbacks`
- **Recommendation:** Utilizar classe customizada `AppError` e middleware de tratamento de erro com status codes semânticos.

### [MEDIUM] Orphan Records on User Deletion
- **Location:**
  - `file: src/AppManager.js`; `line: 131-137`; `symbol: DELETE /api/users/:id`
- **Description:** Deletar usuário remove apenas a linha de `users`, deixando matrículas e pagamentos órfãos e corrompendo relatórios.
- **Recommendation:** Implementar exclusão em cascata transacional em `src/services/userService.js` deletando pagamentos e matrículas antes do usuário.

### [MEDIUM] Boot Race Condition
- **Location:**
  - `file: src/app.js`; `line: 9-12`; `symbol: initDb/listen`
  - `file: src/AppManager.js`; `line: 10-23`; `symbol: initDb`
- **Description:** `app.listen()` era chamado de forma síncrona enquanto `initDb()` ainda criava tabelas e populava seeds de forma assíncrona.
- **Recommendation:** Isolar `src/server.js` com bootstrap assíncrono garantindo que o servidor só abra porta após o término do schema/seed.

### [LOW] Abbreviated Legacy Parameter Names
- **Location:**
  - `file: src/AppManager.js`; `line: 29-33`; `symbol: usr/eml/pwd/c_id/card mapping`
- **Description:** Nomes encurtados prejudicam a legibilidade do contrato.
- **Recommendation:** Manter compatibilidade com o contrato original no controller e documentar no `README.md` e `api.http`.

### [LOW] Dead / Unused Exported State
- **Location:**
  - `file: src/utils.js`; `line: 10-10`; `symbol: totalRevenue declaration`
  - `file: src/utils.js`; `line: 25-25`; `symbol: totalRevenue export`
  - `file: src/AppManager.js`; `line: 2-2`; `symbol: import`
- **Recommendation:** Remover variáveis e funções sem uso.
