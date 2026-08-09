# ecommerce-api-legacy

API de LMS com fluxo de checkout, escrita em Node.js e Express, refatorada
para o padrão **MVC** (Model-View-Controller) com camada de serviços.

> Aviso: o fluxo de pagamento é fictício e serve apenas para estudo. Não use
> cartões reais nem trate as chaves de ambiente de desenvolvimento como
> produção.

## Visão geral

- Runtime: Node.js
- Framework HTTP: Express 4
- Banco: SQLite (`:memory:` por padrão) através de `sqlite3`
- Módulos: CommonJS (`require`/`module.exports`)
- Arquitetura: MVC + services
- Porta: `3000` (ou `PORT` via ambiente)
- Persistência: recriada e populada a cada inicialização quando `DB_PATH=:memory:`

## Estrutura do projeto

```text
ecommerce-api-legacy/
├── src/
│   ├── server.js                 # Entrada do processo (listen)
│   ├── app.js                    # Composition root (createApp)
│   ├── config/settings.js        # Configuração via variáveis de ambiente
│   ├── db/database.js            # SQLite helpers, schema e seeds
│   ├── models/                   # Model: acesso a dados
│   ├── services/                 # Regras de negócio / orquestração
│   ├── controllers/              # Controller: HTTP → services
│   ├── views/httpResponses.js    # View: formatação de respostas
│   └── routes/index.js           # Registro de rotas
├── docs/                         # Relatórios do refactor-arch
├── api.http
├── .env.example
├── package.json
├── AGENTS.md
└── README.md
```

### Fluxo de inicialização

`src/server.js` executa:

1. `createApp()` em `src/app.js`
2. Abre o banco e **aguarda** schema + seeds
3. Registra as rotas MVC
4. Escuta na porta configurada

### Modelo de dados

| Tabela | Responsabilidade |
| --- | --- |
| `users` | Usuários |
| `courses` | Cursos, preços e status ativo |
| `enrollments` | Relação entre usuários e cursos |
| `payments` | Pagamentos associados a matrículas |
| `audit_logs` | Registro textual de eventos de checkout |

## Como instalar e iniciar

```bash
cd ecommerce-api-legacy
npm ci
cp .env.example .env   # opcional
npm start
```

A API fica em `http://localhost:3000`. Encerrar com `Ctrl+C`.

Variáveis suportadas (ver `.env.example`):

| Variável | Padrão | Uso |
| --- | --- | --- |
| `PORT` | `3000` | Porta HTTP |
| `DB_PATH` | `:memory:` | Caminho do SQLite |
| `PAYMENT_GATEWAY_KEY` | `local-dev-only` | Chave fictícia (não logada) |
| `PASSWORD_SALT` | `local-dev-salt` | Salt para `scrypt` em novas senhas |

## Verificação rápida

```bash
curl http://localhost:3000/api/admin/financial-report

curl -X POST http://localhost:3000/api/checkout \
  -H 'Content-Type: application/json' \
  -d '{
    "usr": "Smoke Test",
    "eml": "smoke@example.com",
    "pwd": "test-only",
    "c_id": 2,
    "card": "4111111111111111"
  }'
```

Resultado esperado do checkout:

```json
{
  "msg": "Sucesso",
  "enrollment_id": 2
}
```

## Endpoints

### `POST /api/checkout`

Campos legados preservados: `usr`, `eml`, `pwd`, `c_id`, `card`.

- `400` se faltar campo obrigatório ou pagamento for recusado
- `404` se o curso não existir / estiver inativo
- `200` com `{ msg, enrollment_id }` em sucesso

O checkout roda em **transação** (matrícula + pagamento + audit log). Cartão
começando com `4` aprova; demais prefixos recusam. Dados de cartão e chaves
**não** são logados.

### `GET /api/admin/financial-report`

Retorna receita por curso e lista de alunos (consulta com JOINs, sem N+1).
Sem autenticação (cenário de estudo).

### `DELETE /api/users/:id`

Remove o usuário e, em transação, pagamentos e matrículas relacionados.
Responde `404` se o usuário não existir.

## Seeds iniciais

- Usuário `Leonan` / `leonan@fullcycle.com.br`
- Cursos `Clean Architecture` (997) e `Docker` (497)
- Matrícula + pagamento `PAID` no primeiro curso

## Documentação para agentes

Leia [`AGENTS.md`](./AGENTS.md) antes de modificar o código. Relatórios de
análise e refatoração estão em [`docs/`](./docs/).
