# AGENTS.md — code-smells-project

Instructions for AI coding agents working in this repository.

This project is an **intentionally flawed** Flask e-commerce API used as input for the `refactor-arch` challenge. Prefer fixing architecture and security issues over extending the broken patterns.

Authoritative style/security reference: [`python-development-guidelines.md`](./python-development-guidelines.md).  
Human runbook: [`README.md`](./README.md).

---

## 1. Mission

| Goal | Detail |
|------|--------|
| Domain | E-commerce API: produtos, usuários, pedidos, relatório de vendas |
| Challenge | Detect smells / antipatterns and refactor toward maintainable MVC (or layered) architecture |
| Success | Safer SQL, clear layers, no secrets in responses, testable services, same business behavior unless fixing a bug |

When refactoring, **preserve API paths and JSON shapes** unless the task explicitly asks to change the contract.

---

## 2. Stack (as-is)

| Layer | Choice | Notes |
|-------|--------|-------|
| Language | Python 3 | Local env may be 3.12–3.14 |
| Web | Flask `3.1.1` | WSGI; routes via `add_url_rule` + a few `@app.route` |
| CORS | flask-cors `5.0.1` | Enabled globally in `app.py` |
| DB | SQLite file `loja.db` | Created/seeded on first `get_db()` |
| Persistence | `sqlite3` stdlib | Raw SQL, **no ORM** |
| Tests | None in repo yet | Prefer `pytest` when adding tests |
| Format/lint | Not wired yet | Prefer `ruff format` / `ruff check` per guidelines |

Dependencies are only what is in [`requirements.txt`](./requirements.txt):

```text
flask==3.1.1
flask-cors==5.0.1
```

---

## 3. How to run

```bash
cd code-smells-project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

- **Actual bind:** `http://localhost:5003` (`app.run(..., port=5003)` in `app.py`).
- **README says 5000** — treat `5003` as source of truth until README is fixed.
- Host: `0.0.0.0`, `debug=True`.
- First boot creates `loja.db` and seeds produtos + usuários.

Do not commit `.venv/`, `__pycache__/`, or local DB changes unless asked.

---

## 4. Repository map

```text
code-smells-project/
├── app.py              # Flask app, route registration, unsafe admin endpoints
├── controllers.py      # HTTP handlers (validation + some business side effects)
├── models.py           # Data access + business logic mixed (all domains)
├── database.py         # Global SQLite connection, schema, seed data
├── loja.db             # Runtime SQLite database (generated)
├── requirements.txt    # Runtime deps only
├── README.md           # Short human instructions
├── python-development-guidelines.md  # Full Python engineering standard
├── AGENTS.md           # This file
├── .claude/skills/     # Challenge skills (e.g. refactor-arch)
└── venv/               # Local virtualenv — ignore
```

There is **no** `src/`, `tests/`, service layer, DI container, migrations folder, or auth middleware today.

---

## 5. Architecture (current)

Monolith with four Python modules and broken layering:

```text
HTTP (app.py / controllers.py)
        │
        ▼
  "models" (models.py)   ← SQL + domain rules + reporting
        │
        ▼
  database.get_db()      ← process-wide global connection
        │
        ▼
     loja.db
```

### Module responsibilities (as-is)

| File | Intended role | Actual role |
|------|---------------|-------------|
| `app.py` | App factory / routing | Also runs admin SQL + DB wipe |
| `controllers.py` | Controllers | Validation, notifications via `print`, health exposes secrets, some direct SQL |
| `models.py` | Models / repository | God module for produtos, usuários, pedidos, relatórios |
| `database.py` | DB bootstrap | Global `db_connection` with `check_same_thread=False` |

### Target direction (when refactoring)

Align with guidelines §19.2 / challenge MVC:

1. **Routes / controllers** — parse HTTP, status codes, call services.
2. **Services** — business rules (stock, totals, status transitions).
3. **Repositories / DB** — parameterized SQL only.
4. **No SQL or secrets** in HTTP health/admin without auth.

Prefer small incremental commits when the user asks for commits; do not invent a large framework.

---

## 6. Data model

Tables created in `database.py`:

### `produtos`
`id`, `nome`, `descricao`, `preco`, `estoque`, `categoria`, `ativo`, `criado_em`

Valid categorias used in controllers:  
`informatica`, `moveis`, `vestuario`, `geral`, `eletronicos`, `livros`

### `usuarios`
`id`, `nome`, `email`, `senha`, `tipo`, `criado_em`

Seed users (plaintext passwords — do not treat as production-safe):

| Email | Password | Tipo |
|-------|----------|------|
| `admin@loja.com` | `admin123` | `admin` |
| `joao@email.com` | `123456` | `cliente` |
| `maria@email.com` | `senha123` | `cliente` |

### `pedidos`
`id`, `usuario_id`, `status`, `total`, `criado_em`

Status values: `pendente`, `aprovado`, `enviado`, `entregue`, `cancelado`

### `itens_pedido`
`id`, `pedido_id`, `produto_id`, `quantidade`, `preco_unitario`

No foreign keys enforced in schema today (`PRAGMA foreign_keys` not enabled on connect).

---

## 7. HTTP API surface

Base URL: `http://localhost:5003`

### Public / store

| Method | Path | Handler |
|--------|------|---------|
| GET | `/` | `app.index` — welcome + endpoint map |
| GET | `/health` | `controllers.health_check` |
| GET | `/produtos` | `listar_produtos` |
| GET | `/produtos/busca?q=&categoria=&preco_min=&preco_max=` | `buscar_produtos` |
| GET | `/produtos/<id>` | `buscar_produto` |
| POST | `/produtos` | `criar_produto` |
| PUT | `/produtos/<id>` | `atualizar_produto` |
| DELETE | `/produtos/<id>` | `deletar_produto` |
| GET | `/usuarios` | `listar_usuarios` |
| GET | `/usuarios/<id>` | `buscar_usuario` |
| POST | `/usuarios` | `criar_usuario` |
| POST | `/login` | `login` body: `{email, senha}` |
| POST | `/pedidos` | `criar_pedido` body: `{usuario_id, itens:[{produto_id, quantidade}]}` |
| GET | `/pedidos` | `listar_todos_pedidos` |
| GET | `/pedidos/usuario/<usuario_id>` | `listar_pedidos_usuario` |
| PUT | `/pedidos/<pedido_id>/status` | `atualizar_status_pedido` body: `{status}` |
| GET | `/relatorios/vendas` | `relatorio_vendas` |

### Dangerous admin (no auth)

| Method | Path | Behavior |
|--------|------|----------|
| POST | `/admin/reset-db` | Deletes all rows in all tables |
| POST | `/admin/query` | Executes arbitrary SQL from `{ "sql": "..." }` |

Typical JSON envelope:

```json
{ "dados": ..., "sucesso": true }
```

Errors often: `{ "erro": "..." }` with 4xx/5xx.

---

## 8. Known issues (agents must not ignore)

These are intentional training smells. When editing code, **fix or do not worsen** them.

### Critical

1. **SQL injection** — `models.py` builds SQL with string concatenation (`"WHERE id = " + str(id)`, name/email in quotes, etc.). Always switch to `?` placeholders.
2. **`/admin/query`** — arbitrary SQL execution without authentication.
3. **Secrets exposure** — hardcoded `SECRET_KEY` in `app.py`; `/health` returns `secret_key`, `debug`, `db_path`, and claims `"ambiente": "producao"`.
4. **Plaintext passwords** — stored and sometimes returned in list/get usuário payloads (`senha` field).

### High

5. **God modules** — `models.py` / `controllers.py` own every domain.
6. **Business logic in controllers** — long validation blocks; fake email/SMS/push via `print`.
7. **Global DB connection** — `database.db_connection` + `check_same_thread=False`.
8. **`/admin/reset-db`** — unauthenticated destructive operation.
9. **Duplication** — product validation create vs update; product/user dict mapping; pedido list N+1 duplicated between `get_pedidos_usuario` and `get_todos_pedidos`.

### Medium / low

10. **N+1 queries** on pedido + itens + produto nome.
11. **Logging via `print`** instead of `logging`.
12. **Magic discount thresholds** in `relatorio_vendas`.
13. **No tests**, no type hints, no env-based config.

Severity rubric used by the challenge skill: `.claude/skills/refactor-arch/references/issues_severity.md`.

---

## 9. Coding standards for agents

Follow [`python-development-guidelines.md`](./python-development-guidelines.md). Non-negotiable subset:

### Do

- Use **parameterized** SQL only: `cursor.execute("... WHERE id = ?", (id,))`.
- Prefer **early returns**, small functions, typed signatures where you touch code.
- Use `logging.getLogger(__name__)`; never log passwords or secrets.
- Load secrets from environment (`os.environ`), not literals.
- Separate HTTP / domain / persistence when refactoring.
- Close connections with context managers when introducing new DB access patterns.
- Add `pytest` tests for behavior you change (unit for rules, integration for SQL with `tmp_path`).

### Do not

- Concatenate user input into SQL.
- Return `senha` or `SECRET_KEY` in API responses.
- Add new unauthenticated admin/debug endpoints.
- Expand the god modules without extracting responsibilities.
- Introduce heavy frameworks (Django, full ORMs) unless the user explicitly asks.
- Rewrite the whole app in one shot when a focused fix was requested.
- Commit `.env`, credentials, or `loja.db` with production-like secrets.

### Good vs bad (SQL)

```python
# BAD (current pattern in models.py)
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))

# GOOD
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```

### Good vs bad (layers)

```python
# BAD — controller talks to DB and embeds rules + side effects
def criar_pedido():
    db = get_db()
    # validate, insert, decrement stock, print("ENVIANDO EMAIL...")

# GOOD — thin controller
def criar_pedido():
    body = request.get_json() or {}
    result = order_service.create(body["usuario_id"], body["itens"])
    return jsonify({"dados": result, "sucesso": True}), 201
```

---

## 10. Refactor playbook

When asked to improve architecture, prefer this order:

1. **Safety first** — parameterized queries; remove or protect `/admin/query` and `/admin/reset-db`; strip secrets from `/health`; stop returning passwords.
2. **Extract repositories** — one module/package per aggregate (`produtos`, `usuarios`, `pedidos`) with shared row mappers.
3. **Extract services** — stock checks, order totals, status transitions, discount rules.
4. **Thin controllers** — validate input shapes; map domain errors to HTTP.
5. **DB lifecycle** — drop process-global connection; per-request or pooled pattern safe for Flask; enable `foreign_keys`.
6. **Observability** — replace `print` with structured logging.
7. **Tests** — cover order creation, stock errors, login, and SQL injection regressions.

Keep Portuguese field names (`nome`, `preco`, `estoque`, …) unless migrating the API contract on purpose.

---

## 11. Working agreements

| Topic | Rule |
|-------|------|
| Language in code | Portuguese identifiers and user-facing messages (existing style) |
| Language in agent docs / guidelines | English OK |
| Commits | Only when the user asks; follow repo commit style |
| Scope | Change only files required by the task |
| Skills | `refactor-arch` under `.claude/skills/` (symlinked as `.cursor`) for smell detection / refactor workflow |
| Guidelines | Treat `python-development-guidelines.md` as the engineering contract for new code |

### Commands agents should know

```bash
python -m pip install -r requirements.txt
python app.py
# after tooling is added:
ruff format .
ruff check .
pytest -q
pip-audit
```

### Manual smoke checks

```bash
curl -s http://127.0.0.1:5003/health
curl -s http://127.0.0.1:5003/produtos
curl -s -X POST http://127.0.0.1:5003/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","senha":"123456"}'
```

---

## 12. What “done” looks like

A solid agent contribution typically:

- [ ] Does not introduce new SQL concatenation or plaintext-secret leakage
- [ ] Matches existing JSON field names unless contract change was requested
- [ ] Moves logic toward services/repositories instead of growing `models.py`
- [ ] Adds or updates tests for changed behavior
- [ ] Updates README only when run/port/setup actually changed
- [ ] Leaves the tree runnable with `pip install -r requirements.txt && python app.py`

---

## 13. Quick file index for navigation

| Need | Start here |
|------|------------|
| Register routes | `app.py` |
| HTTP handlers | `controllers.py` |
| SQL / domain queries | `models.py` |
| Schema + seed | `database.py` |
| Engineering rules | `python-development-guidelines.md` |
| Challenge skill | `.claude/skills/refactor-arch/SKILL.md` |

---

*Last aligned with the four-module Flask layout, Flask 3.1.1, and `python-development-guidelines.md`.*
