# ecommerce-api-legacy

API de LMS com fluxo de checkout, desenvolvida em Node.js e Express, completamente refatorada para o padrão arquitetural **MVC (Model-View-Controller)** com camada de **Serviços de Domínio**, persistência relacional transacional e configuração orientada a **12-Factor App**.

> Aviso: O fluxo de pagamento e os dados são fictícios e destinados para fins de estudo e benchmark arquitetural. Nunca utilize cartões reais ou credenciais de produção.

---

## Visão Geral

- **Runtime:** Node.js (v18+)
- **Framework Web:** Express 4
- **Banco de Dados:** SQLite (`:memory:` por padrão ou persistido via arquivo) via `sqlite3`
- **Módulos:** CommonJS (`require` / `module.exports`)
- **Arquitetura:** MVC + Services Layer + Database Helpers Transacionais
- **Porta:** `3000` (configurável via variável de ambiente `PORT`)
- **Criptografia:** `crypto.scryptSync` nativo com salt configurável
- **Transacionalidade:** Garantias ACID com rollback automático em operações multi-tabela

---

## Estrutura do Projeto

```text
ecommerce-api-legacy/
├── src/
│   ├── server.js                 # Ponto de entrada do processo (Async Bootstrap & Listen)
│   ├── app.js                    # Composition Root (Express & Registro de Rotas)
│   ├── config/
│   │   └── settings.js           # Configuração centralizada via variáveis de ambiente
│   ├── db/
│   │   └── database.js           # SQLite async helpers, transações (withTransaction), schema e seeds
│   ├── models/                   # Camada Model: persistência e queries SQL parametrizadas
│   │   ├── auditLogModel.js
│   │   ├── courseModel.js
│   │   ├── enrollmentModel.js
│   │   ├── paymentModel.js
│   │   ├── reportModel.js
│   │   └── userModel.js
│   ├── services/                 # Camada de Domínio: regras de negócio e integrações
│   │   ├── checkoutService.js
│   │   ├── errors.js             # Classe de erro de aplicação (AppError)
│   │   ├── passwordService.js    # Hashing seguro com scrypt + salt
│   │   ├── paymentGateway.js     # Gateway de pagamento isolado
│   │   ├── reportService.js      # Agregação pura de relatórios financeiros
│   │   └── userService.js        # Exclusão transacional em cascata
│   ├── controllers/              # Camada Controller: orquestração HTTP e delegação
│   │   ├── checkoutController.js
│   │   ├── reportController.js
│   │   └── userController.js
│   ├── views/
│   │   └── httpResponses.js      # Camada View: formatação padronizada de respostas HTTP
│   └── routes/
│       └── index.js              # Mapeamento e registro de rotas
├── docs/                         # Documentação e relatórios da refatoração
│   ├── playbook_refatoracao.md   # Playbook com os 8 padrões de transformação (Antes/Depois)
│   ├── project_analysis.txt      # Relatório Fase 1 (Stack & Arquitetura)
│   ├── project_issues.txt        # Relatório Fase 2 (Detecção de Code Smells & Anti-patterns)
│   └── project_refactored.txt    # Relatório Fase 3 (Resultado da Refatoração)
├── .cursor/skills/refactor-arch/ # Skill de automação arquitetural
│   ├── SKILL.md                  # Workflow das 4 fases da refatoração
│   ├── references/
│   │   ├── anti_patterns_catalog.md
│   │   └── issues_severity.md
│   └── templates/
├── api.http                      # Exemplos executáveis de requisições HTTP
├── .env.example                  # Modelo de variáveis de ambiente
├── package.json
├── AGENTS.md                     # Instruções e regras para agentes de IA
└── README.md
```

---

## Ciclo de Vida e Fluxo de Inicialização

A aplicação implementa o padrão **Composition Root** com bootstrap assíncrono para prevenir condições de corrida (*Boot Race Condition*):

1. [`src/server.js`](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/ecommerce-api-legacy/src/server.js) invoca `createApp()` de forma assíncrona.
2. [`src/app.js`](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/ecommerce-api-legacy/src/app.js) inicializa a instância do Express e abre a conexão do banco via `openDatabase()`.
3. Executa `await initSchemaAndSeed(db)` em [`src/db/database.js`](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/ecommerce-api-legacy/src/db/database.js), garantindo a criação de DDLs e carga inicial de dados antes do tráfego HTTP.
4. Registra as rotas da aplicação via `registerRoutes(app, db)`.
5. O servidor passa a escutar na porta configurada (`PORT`), garantindo disponibilidade imediata sem falhas de inicialização.

---

## Modelo de Dados (Tabelas SQLite)

| Tabela | Campos Principais | Responsabilidade |
|---|---|---|
| `users` | `id`, `name`, `email`, `pass` | Cadastro de usuários e credenciais com hash seguro |
| `courses` | `id`, `title`, `price`, `active` | Cursos disponíveis, precificação e status ativo |
| `enrollments` | `id`, `user_id`, `course_id` | Relação de matrícula de usuários em cursos |
| `payments` | `id`, `enrollment_id`, `amount`, `status` | Histórico financeiro e status de pagamento (`PAID`, `DENIED`) |
| `audit_logs` | `id`, `action`, `created_at` | Trilha de auditoria textual de operações de checkout |

---

## Variáveis de Ambiente

As configurações são gerenciadas em [`src/config/settings.js`](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/ecommerce-api-legacy/src/config/settings.js) e podem ser personalizadas via arquivo `.env`:

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `3000` | Porta do servidor HTTP |
| `SQLITE_PATH` | `:memory:` | Caminho do arquivo de banco SQLite (`:memory:` ou `./data.db`) |
| `PASSWORD_SALT` | `dev_salt_change_in_production` | Salt utilizado na derivação de chave Scrypt para senhas |
| `PAYMENT_GATEWAY_KEY` | `pk_test_local` | Chave de integração do gateway de pagamento (não logada) |

---

## Instalação e Execução

### Pré-requisitos
- Node.js 18+ instalado
- npm

### Passo a Passo

```bash
# 1. Acessar o diretório do projeto
cd ecommerce-api-legacy

# 2. Instalar dependências
npm ci

# 3. Configurar variáveis de ambiente (opcional)
cp .env.example .env

# 4. Iniciar o servidor
npm start
```

O servidor estará ativo em `http://localhost:3000`. Pressione `Ctrl+C` para encerrar.

---

## Endpoints da API

### 1. Checkout de Cursos
- **Rota:** `POST /api/checkout`
- **Headers:** `Content-Type: application/json`
- **Contrato de Entrada (Legado):**
  ```json
  {
    "usr": "Maria Silva",
    "eml": "maria@email.com",
    "pwd": "senhaSegura123",
    "c_id": 1,
    "card": "4111111111111111"
  }
  ```
- **Comportamento:**
  - Valida a presença de todos os campos obrigatórios (`400 Bad Request`).
  - Verifica se o curso existe e está ativo (`404 Curso não encontrado`).
  - Valida o pagamento: cartões iniciados em `4` são aprovados (`PAID`); demais são recusados (`400 Pagamento recusado`).
  - Executa a criação de usuário (se inexistente com senha hasheada em Scrypt), matrícula, pagamento e registro de auditoria dentro de uma **transação ACID atômica**.
- **Resposta de Sucesso (`200 OK`):**
  ```json
  {
    "msg": "Sucesso",
    "enrollment_id": 2
  }
  ```

---

### 2. Relatório Financeiro Administrativo
- **Rota:** `GET /api/admin/financial-report`
- **Comportamento:**
  - Realiza consulta otimizada única com `LEFT JOIN` agregando cursos, matrículas, pagamentos e alunos (sem N+1 queries).
- **Resposta de Sucesso (`200 OK`):**
  ```json
  [
    {
      "course": "Clean Architecture",
      "revenue": 997,
      "students": [
        {
          "student": "Leonan",
          "paid": 997
        }
      ]
    },
    {
      "course": "Docker",
      "revenue": 0,
      "students": []
    }
  ]
  ```

---

### 3. Exclusão de Usuário com Cascata Transacional
- **Rota:** `DELETE /api/users/:id`
- **Comportamento:**
  - Remove transacionalmente os pagamentos associados, as matrículas e o registro do usuário em `users`.
  - Retorna `404 Usuário não encontrado` se o ID informado não existir no banco.
- **Resposta de Sucesso (`200 OK`):**
  ```text
  Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
  ```

---

## Verificação e Testes Rápidos

Execução via `curl`:

```bash
# Relatório financeiro
curl -s http://localhost:3000/api/admin/financial-report

# Checkout com sucesso
curl -s -X POST http://localhost:3000/api/checkout \
  -H 'Content-Type: application/json' \
  -d '{
    "usr": "Aluno Teste",
    "eml": "aluno@teste.com",
    "pwd": "minhaSenha123",
    "c_id": 2,
    "card": "4111222233334444"
  }'

# Checkout com cartão recusado
curl -s -i -X POST http://localhost:3000/api/checkout \
  -H 'Content-Type: application/json' \
  -d '{
    "usr": "Aluno Recusado",
    "eml": "recusado@teste.com",
    "c_id": 2,
    "card": "5111222233334444"
  }'
```

---

## Documentação Arquitetural e Playbook

Para aprofundamento nos padrões arquiteturais adotados e histórico de refatoração:

- **Playbook de Refatoração:** [`docs/playbook_refatoracao.md`](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/ecommerce-api-legacy/docs/playbook_refatoracao.md) detalha os 8 padrões de transformação com exemplos completos de código antes e depois.
- **Catálogo de Anti-Patterns:** [`.cursor/skills/refactor-arch/references/anti_patterns_catalog.md`](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/ecommerce-api-legacy/.cursor/skills/refactor-arch/references/anti_patterns_catalog.md).
- **Classificação de Severidade:** [`.cursor/skills/refactor-arch/references/issues_severity.md`](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/ecommerce-api-legacy/.cursor/skills/refactor-arch/references/issues_severity.md).
- **Instruções para Agentes:** [`AGENTS.md`](file:///Users/alexandre/Developer/mba-ia-refactor-projects-skill/ecommerce-api-legacy/AGENTS.md).
