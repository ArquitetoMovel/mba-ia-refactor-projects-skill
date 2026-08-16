# Playbook de Refatoração Arquitetural: Padrões de Transformação MVC

- **Projeto:** `ecommerce-api-legacy`
- **Análise do Commit:** `7269daff95273bc4cbd6900443f76511a052921a`
- **Mensagem do Commit:** `ecomerce-api-legacy refactored and fix the findings`
- **Escopo da Refatoração:** 35 arquivos alterados (+748 / -354 linhas). Migração de monólito centrado em God Class (`AppManager.js` e `utils.js`) para arquitetura em camadas **MVC (Model-View-Controller)** com camada de Serviços de Domínio, infraestrutura transacional assíncrona (Promise-based), configuração 12-Factor e saneamento de segurança (CWE-532, CWE-327).

---

## Sumário Executivo dos 8 Padrões de Transformação

| # | Padrão de Transformação | Anti-Pattern / Code Smell Mitigado | Severidade | Camadas Afetadas |
|---|---|---|---|---|
| 1 | Decomposição de Monolito/God Object em Camadas MVC + Services | God Object / Fat Controller / Lack of Separation of Concerns | CRITICAL | routes/, controllers/, services/, models/, views/ |
| 2 | Externalização e Centralização de Configurações (12-Factor) | Hardcoded Secrets / Configuration Drift | CRITICAL | config/settings.js, .env.example |
| 3 | Proteção de Dados Sensíveis e Remoção de Logs Inseguros | Sensitive Data Exposure in Logs (CWE-532) / PII Leakage | CRITICAL | services/checkoutService.js, paymentGateway.js |
| 4 | Criptografia Forte de Senhas com Salt e Key Derivation | Insecure / Custom Pseudo-Cryptography (CWE-327/916) | CRITICAL | services/passwordService.js |
| 5 | Delimitação de Transações em Operações Multi-Tabela | Missing Transaction Boundaries / Non-Atomic Writes | HIGH | db/database.js, services/checkoutService.js |
| 6 | Otimização de Performance e Eliminação de Queries N+1 via JOIN | N+1 Query Problem & Fragile Asynchronous Coordination | HIGH | models/reportModel.js, services/reportService.js |
| 7 | Exclusão em Cascata Transacional e Integridade Referencial | Orphan Records / Missing Cascade Deletion | HIGH / MEDIUM | services/userService.js, models/ |
| 8 | Eliminação de Callback Hell, Padronização de Erros e Boot | Callback Hell, Silent Failures & Boot Race Condition | MEDIUM / HIGH | db/database.js, services/errors.js, views/, server.js |

---

## Diagrama da Arquitetura Alvo (MVC + Services)

```
                            ARQUITETURA ALVO (MVC + SERVICES)
   
     [ HTTP Client ] 
           |
           v
    +--------------+       Delega Request         +----------------------+
    | Routes/Index | ---------------------------> |     Controllers      |
    +--------------+                              +----------+-----------+
                                                             | Orquestra Caso de Uso
                                                             v
    +--------------+       Formata Resposta       +----------------------+
    |    Views     | <--------------------------- |       Services       |
    | (Formatters) |     (Success / AppError)     | (Regras / Gateway)   |
    +--------------+                              +----------+-----------+
                                                             | Consulta / Transação
                                                             v
    +--------------+       Param SQL / Async      +----------------------+
    |   Database   | <--------------------------- |        Models        |
    | (SQLite/Tx)  |                              |    (Persistência)    |
    +--------------+                              +----------------------+
```

---

## Detalhamento dos 8 Padrões de Transformação

---

### Padrão 1: Decomposição de Monolito/God Object em Camadas MVC + Services

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** God Object / Fat Controller / Lack of Separation of Concerns (Severidade: CRITICAL).
- **Problema:** A classe `AppManager.js` concentrava todo o ciclo de vida da aplicação: conexão SQLite, DDL de tabelas, seeds, rotas Express, parsing/validação de requisições, lógica de pagamento, persistência SQL, geração de relatórios e manipulação de cache em memória.

#### 2. Estratégia de Transformação
- **View (`src/views/httpResponses.js`):** Formatação de respostas HTTP padronizadas (sucesso JSON e erros texto/JSON conforme contrato legado).
- **Routes (`src/routes/index.js`):** Registro de rotas HTTP mapeadas para funções controladoras.
- **Controller (`src/controllers/*`):** Extração de parâmetros da requisição e delegação para a camada de serviço.
- **Service (`src/services/*`):** Concentração das regras de negócio puras, validações de domínio e integrações externas.
- **Model (`src/models/*`):** Módulos com queries SQL parametrizadas isoladas por entidade (`userModel.js`, `courseModel.js`, `paymentModel.js`, `enrollmentModel.js`, `auditLogModel.js`, `reportModel.js`).

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/AppManager.js — God Object misturando HTTP, SQL e regras no checkout
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
            // ... mais 50 linhas de callbacks aninhados com inserts diretos ...
        });
    });
});
```

```javascript
// [DEPOIS] src/controllers/checkoutController.js — Controller enxuto
const { checkout } = require('../services/checkoutService');
const { sendCheckoutSuccess, sendError } = require('../views/httpResponses');

async function handleCheckout(req, res, db) {
    try {
        const result = await checkout(db, req.body);
        return sendCheckoutSuccess(res, result.enrollmentId);
    } catch (error) {
        return sendError(res, error);
    }
}

module.exports = { handleCheckout };
```

```javascript
// [DEPOIS] src/services/checkoutService.js — Regra de domínio isolada
const { AppError } = require('./errors');
const { hashPassword } = require('./passwordService');
const { decidePaymentStatus } = require('./paymentGateway');
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const { withTransaction } = require('../db/database');

async function checkout(db, input) {
    const { usr: name, eml: email, pwd: password, c_id: courseId, card } = input;
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

    return await withTransaction(db, async () => {
        let user = await userModel.findUserIdByEmail(db, email);
        let userId = user ? user.id : (await userModel.createUser(db, {
            name, email, passwordHash: hashPassword(password || '123456')
        })).lastID;

        const enrollment = await enrollmentModel.createEnrollment(db, { userId, courseId });
        await paymentModel.createPayment(db, { enrollmentId: enrollment.lastID, amount: course.price, status });
        await auditLogModel.createAuditLog(db, `Checkout curso ${courseId} por ${userId}`);

        return { enrollmentId: enrollment.lastID, courseTitle: course.title };
    });
}

module.exports = { checkout };
```

---

### Padrão 2: Externalização e Centralização de Configurações e Segredos (12-Factor Config)

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Hardcoded Secrets & Configuration Drift (Severidade: CRITICAL).
- **Problema:** Credenciais de banco de dados, chaves ativas de gateway de pagamento (`pk_live_...`) e credenciais de SMTP embutidas estaticamente em `utils.js`.

#### 2. Estratégia de Transformação
- Criação de `src/config/settings.js` consumindo variáveis de ambiente (`process.env`) com fallbacks seguros para ambiente de desenvolvimento.
- Criação de template versionado `.env.example` e remoção de segredos estáticos do repositório.

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/utils.js — Segredos e credenciais hardcoded
const config = {
    dbUser: "admin_master",
    dbPass: "senha_super_secreta_prod_123", 
    paymentGatewayKey: "pk_live_1234567890abcdef",
    smtpUser: "no-reply@fullcycle.com.br",
    port: 3000
};
```

```javascript
// [DEPOIS] src/config/settings.js — 12-Factor App centralizado
const settings = {
    port: Number(process.env.PORT || 3000),
    sqlitePath: process.env.SQLITE_PATH || ':memory:',
    passwordSalt: process.env.PASSWORD_SALT || 'dev_salt_change_in_production',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'pk_test_local',
};

module.exports = { settings };
```

---

### Padrão 3: Proteção de Dados Sensíveis e Remoção de Logs Inseguros (CWE-532)

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Sensitive Data Exposure in Logs (Severidade: CRITICAL).
- **Problema:** O método de checkout imprimia o número completo do cartão de crédito do cliente e a chave de API do gateway no `console.log`, violando normas PCI-DSS e legislações de privacidade (LGPD/GDPR).

#### 2. Estratégia de Transformação
- Eliminação completa de impressões de dados confidenciais (PAN, senhas, tokens e chaves privadas) no fluxo de processamento de pagamentos.
- Encapsulamento da lógica de decisão de pagamento em módulo isolado (`paymentGateway.js`).

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/AppManager.js — Exposição de cartão e credenciais em stdout
let processPaymentAndEnroll = (userId) => {
    console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
    let status = cc.startsWith("4") ? "PAID" : "DENIED";
    // ...
};
```

```javascript
// [DEPOIS] src/services/paymentGateway.js — Processamento seguro sem vazamento de logs
function decidePaymentStatus(cardNumber) {
    const card = String(cardNumber || '');
    return card.startsWith('4') ? 'PAID' : 'DENIED';
}

module.exports = { decidePaymentStatus };
```

---

### Padrão 4: Criptografia Forte de Senhas com Salt e Key Derivation

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Insecure / Broken Pseudo-Cryptography (Severidade: CRITICAL).
- **Problema:** A função `badCrypto(pwd)` realizava um loop artesanal de 10.000 iterações concatenando pedaços de Base64, gerando um pseudo-hash frágil, sem salt e vulnerável a colisões triviais.

#### 2. Estratégia de Transformação
- Criação de `src/services/passwordService.js` utilizando a função nativa `crypto.scryptSync` com derivação de chave de 32 bytes e salt configurável via `settings.passwordSalt`.

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/utils.js — Pseudo-criptografia artesanal insegura
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

```javascript
// [DEPOIS] src/services/passwordService.js — Algoritmo seguro Scrypt com Salt
const crypto = require('crypto');
const { settings } = require('../config/settings');

function hashPassword(password) {
    return crypto
        .scryptSync(String(password), settings.passwordSalt, 32)
        .toString('hex');
}

module.exports = { hashPassword };
```

---

### Padrão 5: Delimitação de Transações em Operações Multi-Tabela (Atomicidade ACID)

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Missing Transaction Boundaries / Non-Atomic Multi-Table Operations (Severidade: HIGH).
- **Problema:** A criação de matrículas, pagamentos e logs de auditoria ocorria em chamadas assíncronas avulsas sem bloco transacional. Uma falha de rede ou SQL na etapa de pagamento deixava o usuário matriculado gratuitamente.

#### 2. Estratégia de Transformação
- Criação do helper `withTransaction(db, callback)` em `src/db/database.js` executando `BEGIN TRANSACTION`, `COMMIT` e `ROLLBACK` automático no caso de qualquer exceção lançada.

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/AppManager.js — Inserções sequenciais sem transação
this.db.run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [userId, cid], function(err) {
    if (err) return res.status(500).send("Erro Matrícula");
    let enrId = this.lastID;

    self.db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enrId, course.price, status], function(err) {
        if (err) return res.status(500).send("Erro Pagamento"); // MATRÍCULA JÁ FICOU GRAVADA!

        self.db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [...]);
    });
});
```

```javascript
// [DEPOIS] src/db/database.js — Helper de Transação ACID com Rollback Automático
async function withTransaction(db, callback) {
    await dbRun(db, 'BEGIN TRANSACTION');
    try {
        const result = await callback();
        await dbRun(db, 'COMMIT');
        return result;
    } catch (error) {
        try {
            await dbRun(db, 'ROLLBACK');
        } catch (_) {
            // Ignora erro secundário de rollback se a conexão já falhou
        }
        throw error;
    }
}
```

---

### Padrão 6: Otimização de Performance e Eliminação de Queries N+1 via JOIN

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** N+1 Query Problem & Fragile Asynchronous Coordination (Severidade: HIGH).
- **Problema:** A rota de relatório financeiro buscava todos os cursos e, dentro de loops aninhados assíncronos, disparava queries individuais para `enrollments`, `users` e `payments`, utilizando contadores manuais (`coursesPending--`, `enrPending--`) vulneráveis a travamentos e condições de corrida.

#### 2. Estratégia de Transformação
- **Model (`src/models/reportModel.js`):** Executa uma única query SQL com `LEFT JOIN` unindo `courses`, `enrollments`, `payments` e `users`.
- **Service (`src/services/reportService.js`):** Agrega os registros em memória através de um `Map`, calculando receita total e listando estudantes matriculados de forma determinística e síncrona.

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/AppManager.js — Queries N+1 aninhadas e contadores manuais
app.get('/api/admin/financial-report', (req, res) => {
    this.db.all("SELECT * FROM courses", [], (err, courses) => {
        let coursesPending = courses.length;
        courses.forEach(c => {
            this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
                let enrPending = enrollments.length;
                enrollments.forEach(enr => {
                    this.db.get("SELECT name FROM users WHERE id = ?", [enr.user_id], (err, user) => {
                        this.db.get("SELECT amount, status FROM payments WHERE enrollment_id = ?", [enr.id], (err, payment) => {
                            // ... controle de concorrência com coursesPending e enrPending ...
                        });
                    });
                });
            });
        });
    });
});
```

```javascript
// [DEPOIS] src/models/reportModel.js — Query única otimizada com JOIN
const { dbAll } = require('../db/database');

function listFinancialReportRows(db) {
    const query = `
        SELECT 
            courses.id AS course_id,
            courses.title AS course,
            payments.amount AS paid,
            payments.status AS payment_status,
            users.name AS student
        FROM courses
        LEFT JOIN enrollments ON enrollments.course_id = courses.id
        LEFT JOIN payments ON payments.enrollment_id = enrollments.id
        LEFT JOIN users ON users.id = enrollments.user_id
        ORDER BY courses.id ASC
    `;
    return dbAll(db, query, []);
}

module.exports = { listFinancialReportRows };
```

---

### Padrão 7: Exclusão em Cascata Transacional e Integridade Referencial

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Orphan Records / Missing Cascade Deletion (Severidade: HIGH / MEDIUM).
- **Problema:** A rota `DELETE /api/users/:id` apenas deletava a linha na tabela `users`, deixando linhas órfãs em `enrollments` e `payments`, quebrando a integridade relacional.

#### 2. Estratégia de Transformação
- Criação de `deleteUser` em `src/services/userService.js` executando a exclusão ordenada de pagamentos dependentes $\to$ matrículas $\to$ usuário dentro de uma transação, verificando se o usuário de fato existia (`changes > 0`) para retornar 404 em caso negativo.

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/AppManager.js — Deleção parcial gerando dados sujos e órfãos
app.delete('/api/users/:id', (req, res) => {
    let id = req.params.id;
    this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
        res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
    });
});
```

```javascript
// [DEPOIS] src/services/userService.js — Cascata transacional consistente
const { withTransaction } = require('../db/database');
const { AppError } = require('./errors');
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');

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
        if (error instanceof AppError) throw error;
        throw new AppError('Erro DB', 500);
    }
}

module.exports = { deleteUser };
```

---

### Padrão 8: Eliminação de Callback Hell, Padronização de Erros e Boot Assíncrono

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Callback Hell / Pyramid of Doom, Silent Failures & Asynchronous Boot Race Condition (Severidade: MEDIUM / HIGH).
- **Problema:** Pirâmides de callbacks aninhados dificultando a leitura, supressão de erros (ignorando `err`), e `app.listen()` disparado antes de `initDb()` concluir a criação das tabelas no SQLite.

#### 2. Estratégia de Transformação
- Promisificação dos métodos do SQLite (`dbRun`, `dbGet`, `dbAll`) permitindo o uso generalizado de `async/await`.
- Criação da classe `AppError` com códigos HTTP semânticos (400, 404, 500).
- Desacoplamento da inicialização: `src/server.js` orquestra a resolução assíncrona de `initSchemaAndSeed` antes de ligar a porta HTTP do servidor.

#### 3. Exemplos Antes e Depois

```javascript
// [ANTES] src/app.js — Boot com race condition e falta de sincronização
const manager = new AppManager();
manager.initDb(); // ASSÍNCRONO NÃO ESPERADO!
manager.setupRoutes(app);

app.listen(config.port, () => {
    console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
});
```

```javascript
// [DEPOIS] src/server.js — Composition Root assíncrono seguro
const { createApp } = require('./app');
const { settings } = require('./config/settings');

async function start() {
    const { app } = await createApp(); // Aguarda schema/seed antes de escutar

    app.listen(settings.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${settings.port}...`);
    });
}

start().catch((error) => {
    console.error('Falha ao iniciar a aplicação:', error.message);
    process.exit(1);
});
```

```javascript
// [DEPOIS] src/views/httpResponses.js — Tratamento unificado de erros
const { AppError } = require('../services/errors');

function sendError(res, error) {
    if (error instanceof AppError) {
        return res.status(error.statusCode).send(error.message);
    }
    return res.status(500).send('Erro DB');
}

module.exports = { sendError, ... };
```

---

## Guia Prático de Execução do Playbook (Passo a Passo)

1. **Centralizar Configuração (Padrão 2):** Extrair portas, salts e chaves para `src/config/settings.js` com suporte a `.env`.
2. **Isolar Infraestrutura e Bootstrap (Padrões 5 e 8):** Criar wrappers Promise para o banco (`dbRun`, `dbGet`, `dbAll`, `withTransaction`) e ordenar a inicialização em `server.js` aguardando schemas e seeds.
3. **Implantar Camada de Erros e Respostas (Padrão 8):** Criar a classe `AppError` e funções de resposta padronizadas em `src/views/httpResponses.js`.
4. **Saneamento de Segurança e Criptografia (Padrões 3 e 4):** Remover logs de dados sensíveis e substituir pseudo-criptografia por `crypto.scryptSync`.
5. **Estruturar Modelos de Persistência (Padrões 1 e 6):** Criar consultas SQL parametrizadas isoladas em `src/models/*`, convertendo queries N+1 em `JOIN` único.
6. **Implementar Serviços de Domínio e Transações (Padrões 1, 5 e 7):** Concentrar regras de checkout, relatórios e deleção em cascata dentro de `src/services/*`.
7. **Montar Controladores e Roteamento (Padrão 1):** Declarar rotas em `src/routes/index.js` delegando requisições aos controladores em `src/controllers/*`.
8. **Validação de Fumaça e Regressão:** Executar chamadas aos endpoints (`/api/checkout`, `/api/admin/financial-report`, `/api/users/:id`) garantindo compatibilidade total de contrato.
