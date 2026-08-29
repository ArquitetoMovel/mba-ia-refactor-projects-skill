# Playbook de Refatoração Arquitetural: Padrões de Transformação MVC

- **Projeto:** `ecommerce-api-legacy`
- **Baseline legado (ANTES):** commit `73a4dec` — `ecomerce-api-legacy inicialização da app` (`src/app.js`, `src/AppManager.js`, `src/utils.js`)
- **Commit da refatoração (DEPOIS):** `7269daf` — `ecomerce-api-legacy refactored and fix the findings` (35 arquivos alterados, +748 / -354 linhas)
- **Escopo da Refatoração:** Migração de monólito centrado em God Class (`AppManager.js` e `utils.js`) para arquitetura em camadas **MVC (Model-View-Controller)** com camada de Serviços de Domínio, infraestrutura transacional assíncrona (Promise-based), configuração 12-Factor e saneamento de segurança (CWE-532, CWE-327).
- **Rastreabilidade:** Cada diagnóstico referencia os findings de `docs/project_issues.txt` (arquivo + intervalo de linhas no código legado).

---

## Sumário Executivo dos 8 Padrões de Transformação

| # | Padrão de Transformação | Anti-Pattern / Code Smell Mitigado (catálogo) | Severidade | Camadas Afetadas |
|---|---|---|---|---|
| 1 | Decomposição de Monolito/God Object em Camadas MVC + Services | God Object / Fat Controller / Lack of Separation of Concerns (§1.1, §1.2) | CRITICAL | routes/, controllers/, services/, models/, views/ |
| 2 | Externalização e Centralização de Configurações (12-Factor) | Hardcoded Secrets (§2.1) | CRITICAL | config/settings.js, .env.example |
| 3 | Proteção de Dados Sensíveis e Gateway de Pagamento Isolado | Sensitive Data Exposure in Logs / CWE-532 (§2.3) | CRITICAL | services/checkoutService.js, services/paymentGateway.js |
| 4 | Criptografia Forte de Senhas com Salt e Key Derivation | Insecure / Broken Cryptography / CWE-327 (§2.2) | CRITICAL | services/passwordService.js |
| 5 | Delimitação de Transações em Operações Multi-Tabela (ACID) | Missing Transaction Boundaries (§3.3) | HIGH | db/database.js, services/checkoutService.js |
| 6 | Otimização de Performance e Eliminação de Queries N+1 via JOIN | N+1 Query Problem (§3.1) | HIGH | models/reportModel.js, services/reportService.js |
| 7 | Exclusão em Cascata Transacional e Integridade Referencial | Orphan Records / Missing Cascade Deletion (§3.4) | HIGH / MEDIUM | services/userService.js, models/ |
| 8 | Promisificação, Padronização de Erros, Fim do Estado Global e Boot Seguro | Callback Hell (§4.8), Silent Failures (§5.1), Mutable Global State (§1.5/§4.5), Boot Race (§1.6) | MEDIUM / HIGH | db/database.js, services/errors.js, views/, server.js |

---

## Diagrama da Arquitetura Alvo (MVC + Services)

```
                             ARQUITETURA ALVO (MVC + SERVICES)

     [ HTTP Client ]
            |
            v
     +--------------+       Delega Request         +----------------------+
     | Routes/Index | ---------------------------> |     Controllers      |
     | routes/      |                              | controllers/*        |
     +--------------+                              +----------+-----------+
                                                              | Orquestra Caso de Uso
                                                              v
     +--------------+       Formata Resposta       +----------------------+
     |    Views     | <--------------------------- |       Services       |
     | views/http   |     (Success / AppError)     | services/*           |
     | Responses.js |                              | (Regras / Gateway)   |
     +--------------+                              +----------+-----------+
                                                              | Consulta / Transação
                                                              v
     +--------------+       Param SQL / Async      +----------------------+
     |   Database   | <--------------------------- |        Models        |
     | db/database  |                              | models/*             |
     | (SQLite/Tx)  |                              |    (Persistência)    |
     +--------------+                              +----------------------+
            ^
            | Env (PORT, DB_PATH, PAYMENT_GATEWAY_KEY, PASSWORD_SALT)
     +--------------+
     |   Config     |
     | config/      |
     | settings.js  |
     +--------------+
```

---

## Detalhamento dos 8 Padrões de Transformação

---

### Padrão 1: Decomposição de Monolito/God Object em Camadas MVC + Services

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** God Object / Fat Controller / Lack of Separation of Concerns (Severidade: **CRITICAL** — catálogo §1.1, §1.2).
- **Problema:** A classe `AppManager` concentrava conexão SQLite, DDL/seed (`initDb`), rotas Express, parsing/validação HTTP, regra de pagamento, persistência SQL, relatório financeiro e deleção de usuário — tudo sem nenhuma camada de apresentação ou domínio isolada.
- **Localização no legado (findings `[CRITICAL] God Object`, `[HIGH] Lack of MVC`, `[HIGH] Business logic in route handlers`):**
  - `src/AppManager.js:4-139` (classe inteira; `initDb` 10-23, `setupRoutes` 25-138)
  - `src/AppManager.js:28-78` (checkout com regra de negócio dentro da rota)
  - `src/utils.js:1-25` (config, cache e criptografia misturados em utilitário global)
  - `src/app.js:1-14` (bootstrap acoplado ao AppManager)

#### 2. Estratégia de Transformação
- **Routes (`src/routes/index.js:5-9`):** apenas registro de URLs → controladores.
- **Controller (`src/controllers/*`):** extração de parâmetros da requisição, try/catch mínimo, delegação da resposta à View. Não conhece SQL.
- **Service (`src/services/*`):** regras de negócio puras (checkout, relatório, deleção em cascata), orquestração de transações. Não conhece `req`/`res`.
- **Model (`src/models/*`):** queries SQL parametrizadas isoladas por entidade (`userModel`, `courseModel`, `enrollmentModel`, `paymentModel`, `auditLogModel`, `reportModel`).
- **View (`src/views/httpResponses.js`):** formatação padronizada de respostas HTTP preservando o contrato legado (textos 400/404/500, JSON de sucesso).

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/AppManager.js:28-41 — God Object misturando HTTP, SQL e regras no checkout
app.post('/api/checkout', (req, res) => {
    let u = req.body.usr;
    let e = req.body.eml;
    let p = req.body.pwd;
    let cid = req.body.c_id;
    let cc = req.body.card;

    if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");

    this.db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [cid], (err, course) => {
        if (err || !course) return res.status(404).send("Curso não encontrado");

        this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
            if (err) return res.status(500).send("Erro DB");
            // ... linhas 43-77: mais 4 níveis de callbacks com inserts, pagamento e auditoria ...
        });
    });
});
```

```javascript
// [DEPOIS] src/routes/index.js:5-9 — Rotas apenas mapeiam URL → Controller
function registerRoutes(app, db) {
    app.post('/api/checkout', createCheckoutController(db));
    app.get('/api/admin/financial-report', createReportController(db));
    app.delete('/api/users/:id', createUserController(db));
}
```

```javascript
// [DEPOIS] src/controllers/checkoutController.js:4-13 — Controller enxuto (sem SQL, sem regra)
function createCheckoutController(db) {
    return async function checkout(req, res) {
        try {
            const result = await checkoutService.checkout(db, req.body || {});
            return sendCheckoutSuccess(res, result.enrollmentId);
        } catch (error) {
            return sendError(res, error);
        }
    };
}
```

```javascript
// [DEPOIS] src/services/checkoutService.js:11-74 — Regra de domínio isolada e transacional
async function checkout(db, input) {
    const name = input.usr;
    const email = input.eml;
    const password = input.pwd;
    const courseId = input.c_id;
    const card = input.card;

    if (!name || !email || !courseId || !card) {
        throw new AppError('Bad Request', 400);
    }

    const course = await courseModel.findActiveCourseById(db, courseId);
    if (!course) {
        throw new AppError('Curso não encontrado', 404);
    }

    const status = decidePaymentStatus(card);
    if (status === 'DENIED') {
        throw new AppError('Pagamento recusado', 400);
    }

    try {
        return await withTransaction(db, async () => {
            let user = await userModel.findUserIdByEmail(db, email);
            let userId;

            if (!user) {
                const passwordHash = hashPassword(password || '123456');
                const created = await userModel.createUser(db, {
                    name,
                    email,
                    passwordHash,
                });
                userId = created.lastID;
            } else {
                userId = user.id;
            }

            const enrollment = await enrollmentModel.createEnrollment(db, {
                userId,
                courseId,
            });
            const enrollmentId = enrollment.lastID;

            await paymentModel.createPayment(db, {
                enrollmentId,
                amount: course.price,
                status,
            });

            await auditLogModel.createAuditLog(
                db,
                `Checkout curso ${courseId} por ${userId}`,
            );

            return { enrollmentId, courseTitle: course.title };
        });
    } catch (error) {
        if (error instanceof AppError) {
            throw error;
        }
        throw new AppError('Erro DB', 500);
    }
}
```

```javascript
// [DEPOIS] src/models/enrollmentModel.js:3-8 — Model com SQL parametrizado isolado
function createEnrollment(db, { userId, courseId }) {
    return run(db, 'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [
        userId,
        courseId,
    ]);
}
```

> O contrato legado é preservado: campos `usr/eml/pwd/c_id/card` na borda (`checkoutService.js:12-16`) e resposta `{ msg: "Sucesso", enrollment_id }` via `sendCheckoutSuccess` (`views/httpResponses.js:11-13`).

---

### Padrão 2: Externalização e Centralização de Configurações e Segredos (12-Factor Config)

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Hardcoded Secrets (Severidade: **CRITICAL** — catálogo §2.1).
- **Problema:** Credenciais de banco, chave **live** de gateway de pagamento (`pk_live_...`) e usuário SMTP embutidos estaticamente em `utils.js`, com porta fixa sem suporte a ambiente.
- **Localização no legado (finding `[CRITICAL] Hard-coded secrets`):** `src/utils.js:1-7` (objeto `config`).

#### 2. Estratégia de Transformação
- Criação de `src/config/settings.js` como único ponto de leitura de configuração, consumindo `process.env` via helper `readEnv` com fallbacks seguros de desenvolvimento.
- Template versionado `.env.example` (`PORT`, `DB_PATH`, `PAYMENT_GATEWAY_KEY`, `PASSWORD_SALT`) e remoção integral dos segredos estáticos.

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/utils.js:1-7 — Segredos e credenciais hardcoded
const config = {
    dbUser: "admin_master",
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    smtpUser: "no-reply@fullcycle.com.br",
    port: 3000
};
```

```javascript
// [DEPOIS] src/config/settings.js:1-16 — 12-Factor App centralizado
function readEnv(name, fallback) {
    const value = process.env[name];
    if (value === undefined || value === '') {
        return fallback;
    }
    return value;
}

const settings = {
    port: Number(readEnv('PORT', '3000')),
    dbPath: readEnv('DB_PATH', ':memory:'),
    paymentGatewayKey: readEnv('PAYMENT_GATEWAY_KEY', 'local-dev-only'),
    passwordSalt: readEnv('PASSWORD_SALT', 'local-dev-salt'),
};

module.exports = { settings };
```

```dotenv
# [DEPOIS] .env.example — template versionado (sem segredos reais)
PORT=3000
DB_PATH=:memory:
PAYMENT_GATEWAY_KEY=local-dev-only
PASSWORD_SALT=local-dev-salt
```

---

### Padrão 3: Proteção de Dados Sensíveis e Remoção de Logs Inseguros (CWE-532)

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Sensitive Data Exposure & Unsafe Logging (Severidade: **CRITICAL** — catálogo §2.3, CWE-532).
- **Problema:** O fluxo de checkout imprimia o número completo do cartão (PAN) e a chave do gateway no `console.log`, violando PCI-DSS e LGPD/GDPR; o `globalCache` ainda guardava dados da última compra em memória.
- **Localização no legado (finding `[CRITICAL] Sensitive data exposure in logs`):** `src/AppManager.js:45` (console.log com `cc` e `config.paymentGatewayKey`); escrita em cache via `logAndCache` (`src/AppManager.js:59`, função em `src/utils.js:12-15`).

#### 2. Estratégia de Transformação
- Eliminação completa de impressões de dados confidenciais (PAN, chaves) no fluxo de pagamento.
- Encapsulamento da decisão de pagamento em módulo puro e isolado (`paymentGateway.js`), sem I/O e sem logging.
- O `paymentGatewayKey` só existe em `settings.js` (env), nunca é referenciado em logs.

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/AppManager.js:43-48 — Exposição de cartão e credenciais em stdout
let processPaymentAndEnroll = (userId) => {

    console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
    let status = cc.startsWith("4") ? "PAID" : "DENIED";

    if (status === "DENIED") return res.status(400).send("Pagamento recusado");
```

```javascript
// [ANTES] src/AppManager.js:59 — Escrita de dado de compra em cache global
logAndCache(`last_checkout_${userId}`, course.title);
```

```javascript
// [DEPOIS] src/services/paymentGateway.js:1-6 — Decisão pura, sem log e sem vazamento
function decidePaymentStatus(cardNumber) {
    const card = String(cardNumber);
    return card.startsWith('4') ? 'PAID' : 'DENIED';
}

module.exports = { decidePaymentStatus };
```

```javascript
// [DEPOIS] src/services/checkoutService.js:27-30 — Gateway chamado sem imprimir o cartão
const status = decidePaymentStatus(card);
if (status === 'DENIED') {
    throw new AppError('Pagamento recusado', 400);
}
```

---

### Padrão 4: Criptografia Forte de Senhas com Salt e Key Derivation

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Insecure / Broken Cryptography (Severidade: **CRITICAL** — catálogo §2.2, CWE-327/CWE-916).
- **Problema:** `badCrypto(pwd)` era pseudo-criptografia caseira: loop de 10.000 iterações concatenando substrings de Base64, produzindo sempre o mesmo byte repetido, truncado a 10 caracteres, sem salt real — trivial de colidir e reverter.
- **Localização no legado (finding `[HIGH] Insecure password helper`):** `src/utils.js:17-23` (definição), uso em `src/AppManager.js:68` (`badCrypto(p || "123456")`).

#### 2. Estratégia de Transformação
- Criação de `src/services/passwordService.js` com a derivação de chave nativa `crypto.scryptSync` (32 bytes, saída hex) e salt configurável via `settings.passwordSalt` (env `PASSWORD_SALT`).

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/utils.js:17-23 — Pseudo-criptografia artesanal insegura
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

```javascript
// [ANTES] src/AppManager.js:68 — Uso do pseudo-hash no cadastro do checkout
let hash = badCrypto(p || "123456");
```

```javascript
// [DEPOIS] src/services/passwordService.js:1-10 — Scrypt com salt via configuração 12-Factor
const crypto = require('crypto');
const { settings } = require('../config/settings');

function hashPassword(password) {
    return crypto
        .scryptSync(String(password), settings.passwordSalt, 32)
        .toString('hex');
}

module.exports = { hashPassword };
```

```javascript
// [DEPOIS] src/services/checkoutService.js:37-44 — Hash forte no cadastro, dentro da transação
if (!user) {
    const passwordHash = hashPassword(password || '123456');
    const created = await userModel.createUser(db, {
        name,
        email,
        passwordHash,
    });
    userId = created.lastID;
}
```

---

### Padrão 5: Delimitação de Transações em Operações Multi-Tabela (Atomicidade ACID)

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Missing Transaction Boundaries / Non-Atomic Multi-Table Writes (Severidade: **HIGH** — catálogo §3.3).
- **Problema:** Matrícula, pagamento e auditoria eram gravados em três `db.run` encadeados por callbacks, sem `BEGIN/COMMIT`. Uma falha na etapa de pagamento deixava a matrícula gravada — usuário matriculado sem pagamento registrado.
- **Localização no legado (finding `[HIGH] No transactional boundary on checkout`):** `src/AppManager.js:50-63` (inserts aninhados em `processPaymentAndEnroll`).

#### 2. Estratégia de Transformação
- **Infrastructure (`src/db/database.js:44-58`):** helper `withTransaction(db, work)` com `BEGIN`, `COMMIT` e `ROLLBACK` automático (preservando o erro original mesmo se o rollback falhar).
- **Service (`src/services/checkoutService.js:33-67`):** os três writes dependentes (usuário → matrícula → pagamento → auditoria) executam dentro de uma única transação.

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/AppManager.js:50-63 — Inserções sequenciais sem transação (parciais possíveis)
this.db.run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [userId, cid], function(err) {
    if (err) return res.status(500).send("Erro Matrícula");
    let enrId = this.lastID;

    self.db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enrId, course.price, status], function(err) {
        if (err) return res.status(500).send("Erro Pagamento"); // MATRÍCULA JÁ FICOU GRAVADA!

        self.db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [`Checkout curso ${cid} por ${userId}`], (err) => {

            logAndCache(`last_checkout_${userId}`, course.title);
            res.status(200).json({ msg: "Sucesso", enrollment_id: enrId });
        });
    });
});
```

```javascript
// [DEPOIS] src/db/database.js:44-58 — Helper de transação ACID com rollback automático
async function withTransaction(db, work) {
    await run(db, 'BEGIN');
    try {
        const result = await work();
        await run(db, 'COMMIT');
        return result;
    } catch (error) {
        try {
            await run(db, 'ROLLBACK');
        } catch (rollbackError) {
            error.rollbackError = rollbackError;
        }
        throw error;
    }
}
```

```javascript
// [DEPOIS] src/services/checkoutService.js:33-67 — Escrita multi-tabela atômica
return await withTransaction(db, async () => {
    let user = await userModel.findUserIdByEmail(db, email);
    // ... cria usuário se necessário (34-47) ...

    const enrollment = await enrollmentModel.createEnrollment(db, {
        userId,
        courseId,
    });
    const enrollmentId = enrollment.lastID;

    await paymentModel.createPayment(db, {
        enrollmentId,
        amount: course.price,
        status,
    });

    await auditLogModel.createAuditLog(
        db,
        `Checkout curso ${courseId} por ${userId}`,
    );

    return { enrollmentId, courseTitle: course.title };
});
```

---

### Padrão 6: Otimização de Performance e Eliminação de Queries N+1 via JOIN

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** N+1 Query Problem & Fragile Asynchronous Coordination (Severidade: **HIGH** — catálogo §3.1).
- **Problema:** O relatório financeiro buscava os cursos e, em loops aninhados, disparava 1 query de `enrollments` por curso e 2 queries (`users` + `payments`) por matrícula — total de `1 + N + 2N` round-trips — montando a resposta com contadores manuais (`coursesPending--`, `enrPending--`) sujeitos a condições de corrida, respostas truncadas e callbacks sem verificação de `err`.
- **Localização no legado (finding `[MEDIUM] N+1 queries in financial report`):** `src/AppManager.js:80-129` (handler), queries aninhadas em `89-127` (enrollments `92`, user `104`, payment `106`).

#### 2. Estratégia de Transformação
- **Model (`src/models/reportModel.js:3-18`):** uma única query com `LEFT JOIN` unindo `courses`, `enrollments`, `users` e `payments`, ordenada deterministicamente.
- **Service (`src/services/reportService.js:4-33`):** agregação síncrona e determinística em memória via `Map`, sem contadores de concorrência; cursos sem matrícula aparecem com receita 0 (efeito do `LEFT JOIN` com `student/paid` nulos).

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/AppManager.js:80-127 (resumo fiel) — N+1 com coordenação assíncrona frágil
app.get('/api/admin/financial-report', (req, res) => {
    let report = [];

    this.db.all("SELECT * FROM courses", [], (err, courses) => {
        let coursesPending = courses.length;
        courses.forEach(c => {
            let courseData = { course: c.title, revenue: 0, students: [] };

            this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
                let enrPending = enrollments.length;

                enrollments.forEach(enr => {
                    this.db.get("SELECT name, email FROM users WHERE id = ?", [enr.user_id], (err, user) => {
                        this.db.get("SELECT amount, status FROM payments WHERE enrollment_id = ?", [enr.id], (err, payment) => {
                            // ... linhas 108-122: acumula receita e decrementa coursesPending/enrPending ...
                            if (enrPending === 0) { report.push(courseData); coursesPending--;
                                if (coursesPending === 0) res.json(report); }
                        });
                    });
                });
            });
        });
    });
});
```

```javascript
// [DEPOIS] src/models/reportModel.js:3-18 — Query única otimizada com LEFT JOIN
function listFinancialReportRows(db) {
    return all(
        db,
        `SELECT
            c.id AS course_id,
            c.title AS course,
            u.name AS student,
            p.amount AS paid,
            p.status AS payment_status
         FROM courses c
         LEFT JOIN enrollments e ON e.course_id = c.id
         LEFT JOIN users u ON u.id = e.user_id
         LEFT JOIN payments p ON p.enrollment_id = e.id
         ORDER BY c.id, e.id`,
    );
}
```

```javascript
// [DEPOIS] src/services/reportService.js:4-42 — Agregação determinística em memória
function buildFinancialReport(rows) {
    const byCourse = new Map();

    for (const row of rows) {
        if (!byCourse.has(row.course_id)) {
            byCourse.set(row.course_id, {
                course: row.course,
                revenue: 0,
                students: [],
            });
        }

        const courseData = byCourse.get(row.course_id);

        if (row.student == null && row.paid == null) {
            continue;
        }

        if (row.payment_status === 'PAID') {
            courseData.revenue += row.paid || 0;
        }

        courseData.students.push({
            student: row.student || 'Unknown',
            paid: row.paid || 0,
        });
    }

    return Array.from(byCourse.values());
}

async function getFinancialReport(db) {
    try {
        const rows = await reportModel.listFinancialReportRows(db);
        return buildFinancialReport(rows);
    } catch (error) {
        throw new AppError('Erro DB', 500);
    }
}
```

> **Ganho:** de `1 + N + 2N` consultas assíncronas para **1** consulta; a resposta do relatório torna-se determinística (validado: `GET /api/admin/financial-report` retorna os dados do seed com revenue/students corretos).

---

### Padrão 7: Exclusão em Cascata Transacional e Integridade Referencial

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Orphan Records / Missing Cascade Deletion (Severidade: **HIGH/MEDIUM** — catálogo §3.4).
- **Problema:** `DELETE /api/users/:id` removia apenas a linha em `users`, deixando `enrollments` e `payments` órfãos apontando para `user_id` inexistente — o próprio texto da resposta admitia a sujeira ("...ficaram sujos no banco") e ignorava `err`, sempre retornando sucesso.
- **Localização no legado (findings `[MEDIUM] Orphan data on user delete`, `[MEDIUM] Missing/inconsistent error handling`):** `src/AppManager.js:131-137` (handler), `133-136` (err ignorado).

#### 2. Estratégia de Transformação
- **Service (`src/services/userService.js:7-23`):** deleção ordenada `payments → enrollments → users` dentro de `withTransaction`; verificação de existência via `changes === 0` → `AppError 404`; falha de banco → `AppError 500`.
- **Models:** `paymentModel.deletePaymentsByUserId` com subquery por matrícula do usuário; `enrollmentModel.deleteEnrollmentsByUserId`; `userModel.deleteUserById` retornando `{ changes }`.

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/AppManager.js:131-137 — Deleção parcial, erro ignorado, sucesso garantido
app.delete('/api/users/:id', (req, res) => {
    let id = req.params.id;
    this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {

        res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
    });
});
```

```javascript
// [DEPOIS] src/services/userService.js:7-23 — Cascata transacional consistente
async function deleteUser(db, userId) {
    try {
        await withTransaction(db, async () => {
            await paymentModel.deletePaymentsByUserId(db, userId);
            await enrollmentModel.deleteEnrollmentsByUserId(db, userId);
            const result = await userModel.deleteUserById(db, userId);
            if (result.changes === 0) {
                throw new AppError('Usuário não encontrado', 404);
            }
        });
    } catch (error) {
        if (error instanceof AppError) {
            throw error;
        }
        throw new AppError('Erro DB', 500);
    }
}
```

```javascript
// [DEPOIS] src/models/paymentModel.js:11-20 — Remoção dependente via subquery parametrizada
function deletePaymentsByUserId(db, userId) {
    return run(
        db,
        `DELETE FROM payments
         WHERE enrollment_id IN (
           SELECT id FROM enrollments WHERE user_id = ?
         )`,
        [userId],
    );
}
```

```javascript
// [DEPOIS] src/controllers/userController.js:4-13 — Controller delega e trata 404/500 pela View
function createUserController(db) {
    return async function deleteUser(req, res) {
        try {
            await userService.deleteUser(db, req.params.id);
            return sendText(res, 200, 'Usuário deletado.');
        } catch (error) {
            return sendError(res, error);
        }
    };
}
```

---

### Padrão 8: Eliminação de Callback Hell, Padronização de Erros, Estado Global e Boot Assíncrono Seguro

#### 1. Diagnóstico e Contexto
- **Anti-Patterns:** Callback Hell / Pyramid of Doom (§4.8, **MEDIUM**), Poor Error Handling / Silent Failures (§5.1, **MEDIUM**), Mutable Global State & Dead Code (§1.5/§4.5, **HIGH/LOW**), Asynchronous Boot Race Condition (§1.6, **HIGH**).
- **Problema:** Pirâmides de callbacks até 5 níveis no checkout e no relatório suprimindo erros (`err` ignorado); estado global mutável (`globalCache`, `totalRevenue` exportado e nunca atualizado); e `app.listen()` disparado imediatamente após `initDb()` assíncrono — as primeiras requisições podiam falhar com `no such table`.
- **Localização no legado (findings `[MEDIUM] Long Method/Callback Hell`, `[MEDIUM] Missing/inconsistent error handling`, `[HIGH] Global mutable state`, `[LOW] Dead/unused state`, `[MEDIUM] Race on boot`):**
  - `src/AppManager.js:28-78` e `80-129` (callback hell)
  - `src/AppManager.js:57`, `104-106`, `133-136` (erros ignorados)
  - `src/utils.js:9-15` (`globalCache`/`totalRevenue`/`logAndCache`), `10` e `25` (dead state exportado)
  - `src/app.js:9-12` + `src/AppManager.js:10-23` (boot race)

#### 2. Estratégia de Transformação
- **DB (`src/db/database.js:8-42`):** promisificação de `run/get/all` — `async/await` linear substitui a pirâmide.
- **Erros (`src/services/errors.js:1-7`):** classe `AppError` com `statusCode` semântico (400/404/500).
- **View (`src/views/httpResponses.js:15-20`):** tradução centralizada de `AppError` → resposta HTTP, preservando os textos legados.
- **Composition Root (`src/app.js:8-17`, `src/server.js:4-15`):** `createApp()` faz `await initSchemaAndSeed(db)` **antes** de registrar rotas; `server.js` só chama `app.listen()` após a promise resolver.
- **Estado global removido:** `globalCache`, `totalRevenue` e `logAndCache` deixaram de existir; nenhum módulo exporta variável mutável compartilhada.

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/app.js:8-13 — Boot com race condition (initDb assíncrono não esperado)
const manager = new AppManager();
manager.initDb(); // ASSÍNCRONO VIA CALLBACKS — NÃO ESPERADO!
manager.setupRoutes(app);

app.listen(config.port, () => {
    console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
});
```

```javascript
// [ANTES] src/utils.js:9-15 — Estado global mutável e utilitário de cache
let globalCache = {};
let totalRevenue = 0;

function logAndCache(key, data) {
    console.log(`[LOG] Salvando no cache: ${key}`);
    globalCache[key] = data;
}
```

```javascript
// [DEPOIS] src/db/database.js:8-18 — SQLite promisificado (base do async/await)
function run(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function onRun(err) {
            if (err) {
                reject(err);
                return;
            }
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}
```

```javascript
// [DEPOIS] src/services/errors.js:1-7 — Erro de aplicação com status HTTP semântico
class AppError extends Error {
    constructor(message, statusCode = 500) {
        super(message);
        this.name = 'AppError';
        this.statusCode = statusCode;
    }
}
```

```javascript
// [DEPOIS] src/views/httpResponses.js:3-20 — View centraliza a formatação da resposta
function sendText(res, statusCode, message) {
    return res.status(statusCode).send(message);
}

function sendJson(res, statusCode, payload) {
    return res.status(statusCode).json(payload);
}

function sendCheckoutSuccess(res, enrollmentId) {
    return sendJson(res, 200, { msg: 'Sucesso', enrollment_id: enrollmentId });
}

function sendError(res, error) {
    if (error instanceof AppError) {
        return sendText(res, error.statusCode, error.message);
    }
    return sendText(res, 500, 'Erro DB');
}
```

```javascript
// [DEPOIS] src/app.js:8-17 — Composition root aguarda schema/seed antes de expor rotas
async function createApp() {
    const app = express();
    app.use(express.json());

    const db = openDatabase();
    await initSchemaAndSeed(db);
    registerRoutes(app, db);

    return { app, db };
}
```

```javascript
// [DEPOIS] src/server.js:4-15 — Só escuta a porta quando o banco está pronto
async function start() {
    const { app } = await createApp();

    app.listen(settings.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${settings.port}...`);
    });
}

start().catch((error) => {
    console.error('Falha ao iniciar a aplicação:', error.message);
    process.exit(1);
});
```

---

## Guia Prático de Execução do Playbook (Passo a Passo)

1. **Centralizar Configuração (Padrão 2):** Extrair segredos/porta para `src/config/settings.js` com `readEnv` + `.env.example`; nunca versionar credenciais reais.
2. **Isolar Infraestrutura e Bootstrap (Padrões 5 e 8):** Promisificar o banco em `src/db/database.js` (`run/get/all` + `withTransaction`) e ordenar a inicialização: `createApp()` → `await initSchemaAndSeed` → `server.js` só então `app.listen()`.
3. **Implantar Camada de Erros e Respostas (Padrão 8):** Criar `AppError` (`services/errors.js`) e a View `views/httpResponses.js` mantendo o contrato legado de textos e JSON.
4. **Saneamento de Segurança e Criptografia (Padrões 3 e 4):** Remover todo log de PAN/chave (`AppManager.js:45`), isolar o gateway em `paymentGateway.js` e substituir `badCrypto` por `crypto.scryptSync` com salt via env.
5. **Estruturar Modelos de Persistência (Padrões 1 e 6):** Isolar SQL parametrizado por entidade em `src/models/*`; converter o N+1 do relatório em um único `LEFT JOIN` (`reportModel.js`).
6. **Implementar Serviços de Domínio e Transações (Padrões 1, 5 e 7):** Concentrar checkout (transacional), relatório (agregação em `Map`) e deleção em cascata (`payments → enrollments → users` + 404 por `changes`) em `src/services/*`.
7. **Montar Controladores e Roteamento (Padrão 1):** Factories de controller recebendo `db` (`create*Controller(db)`) registradas em `src/routes/index.js`; controllers não conhecem SQL.
8. **Validação de Fumaça e Regressão:** Subir `npm start` e exercitar `POST /api/checkout` (sucesso/cartão negado/campos faltantes), `GET /api/admin/financial-report` (seed íntegro) e `DELETE /api/users/:id` (cascade + 404), conferindo que o log do processo não contém dados sensíveis.
