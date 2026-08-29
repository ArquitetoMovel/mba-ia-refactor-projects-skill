# AGENTS.md — code-smells-project

Instructions for AI coding agents working in this repository.

This project is a Flask e-commerce API used for the `refactor-arch` challenge. It has been **refactored to MVC** with a service layer. Prefer extending the layered design over reintroducing god modules or string-built SQL.

Authoritative style/security reference: [`python-development-guidelines.md`](./python-development-guidelines.md).  
Human runbook: [`README.md`](./README.md).  
Skill reports: [`docs/`](./docs/).

---

## 1. Mission

| Goal | Detail |
|------|--------|
| Domain | E-commerce API: produtos, usuários, pedidos, relatório de vendas |
| Architecture | MVC + services (`src/`) |
| Success | Parameterized SQL, no secrets in responses, hashed passwords, signed auth, testable services |

Preserve API paths and JSON field names unless the task explicitly changes the contract.

---

## 2. Stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Language | Python 3.12+ | |
| Web | Flask `3.1.1` | App factory in `src/app.py` |
| CORS | flask-cors `5.0.1` | |
| DB | SQLite (`loja.db`) | Per-request connection via Flask `g` |
| Persistence | `sqlite3` + parameterized SQL | No ORM |
| Passwords | `werkzeug.security` | Hashed at rest |
| Authentication | `itsdangerous` | Signed, expiring Bearer tokens |
| Tests | pytest | `tests/unit`, `tests/integration` |

```text
flask==3.1.1
flask-cors==5.0.1
itsdangerous==2.2.0
```

Dev tools: `requirements-dev.txt` (`pytest`, `ruff`).

---

## 3. How to run

```bash
cd code-smells-project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Prefer `.venv` (uv default). If you see `VIRTUAL_ENV=venv does not match ... .venv`, deactivate the old env and activate `.venv`, or run via `uv run`.

- Default bind: `http://127.0.0.1:5003`
- Override with `HOST`, `PORT`, `SECRET_KEY`, `FLASK_DEBUG`, `DB_PATH`, `AMBIENTE`, `ADMIN_TOKEN`, `AUTH_TOKEN_MAX_AGE_SECONDS`, `CORS_ORIGINS` and seed password variables

```bash
pip install -r requirements-dev.txt
pytest -q
```

Do not commit `.venv/`, `venv/`, `__pycache__/`, or local DB changes unless asked.

---

## 4. Repository map

```text
code-smells-project/
├── app.py                 # Entrypoint
├── src/
│   ├── app.py             # create_app composition root
│   ├── config/settings.py
│   ├── domain/pedido.py   # order status policy
│   ├── db/database.py     # schema, seed, request-scoped connection
│   ├── schemas/payloads.py # input DTOs
│   ├── models/            # Model / persistence
│   ├── services/          # Business rules
│   ├── controllers/       # HTTP adapters
│   ├── views/routes.py    # Route registration
│   └── middlewares/       # Error handlers
├── tests/
├── docs/                  # refactor-arch phase reports
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── README.md
├── AGENTS.md
└── python-development-guidelines.md
```

---

## 5. Architecture

```text
View (routes)
    → Controller (HTTP + DTO boundary)
        → Schema (validated payloads)
            → Service (domain rules)
                → Model (parameterized SQL)
                    → get_db() per request
                        → loja.db
```

| Package | Role |
|---------|------|
| `src/views` | URLs → controller callables |
| `src/controllers` | Parse request, status codes, JSON envelope |
| `src/services` | Validation, stock, totals, auth, discounts, notifications |
| `src/domain` | Shared domain policies such as order statuses and transitions |
| `src/schemas` | Typed input DTOs and boundary validation |
| `src/models` | Repositories + row mappers (no password in public mappers) |
| `src/db` | Connection lifecycle, DDL, seed, password migration |
| `src/config` | Env-based settings |

---

## 6. Data model

Unchanged tables: `produtos`, `usuarios`, `pedidos`, `itens_pedido`.

- Categorias: `informatica`, `moveis`, `vestuario`, `geral`, `eletronicos`, `livros`
- Status pedido: `pendente`, `aprovado`, `enviado`, `entregue`, `cancelado`
- Seed users are optional and configured through `SEED_ADMIN_PASSWORD`,
  `SEED_JOAO_PASSWORD` and `SEED_MARIA_PASSWORD`; values are hashed before storage.
- Test-only seed credentials live in `tests/conftest.py`, not application code.

Foreign keys enabled (`PRAGMA foreign_keys = ON`).

---

## 7. HTTP API surface

Base URL: `http://127.0.0.1:5003`

Public paths unchanged: `/`, `/health`, `/produtos`, `/login` and registration at
`POST /usuarios`. Product reads remain public; sensitive operations require a
signed `Authorization: Bearer <token>` header.

| Admin | Behavior |
|-------|----------|
| `POST /admin/query` | **Removed** |
| `POST /admin/reset-db` | Requires `X-Admin-Token: $ADMIN_TOKEN` |

`/health` returns status, counts, versão, ambiente — **never** `secret_key`, passwords, or `db_path`.

---

## 8. Fixed issues (do not reintroduce)

1. SQL concatenation → use `?` placeholders only
2. Arbitrary SQL admin endpoint → removed
3. Secrets in `/health` / hardcoded production secret → env config with production validation
4. Plaintext passwords / `senha` in list/get → hashed + omitted from responses
5. Fake authentication / broken access control → signed expiring Bearer tokens and role checks
6. Predictable seed credentials → opt-in environment-configured seed users
7. God `models.py` / fat controllers → split by domain + services
8. Global `db_connection` → Flask `g` per request
9. N+1 on pedidos → JOIN load of itens
10. Non-atomic stock and mixed commits → service-owned transactions and conditional updates
11. `print` logging → `logging` module
12. Duplicated status policy / ad hoc payload checks → domain policy and DTOs

---

## 9. Coding standards

Follow [`python-development-guidelines.md`](./python-development-guidelines.md).

- Parameterized SQL only
- Thin controllers; rules in services
- Sensitive endpoints use `require_auth` / `require_roles`; never trust role data from a token
- `logging.getLogger(__name__)`; never log passwords
- Secrets from environment
- Add pytest coverage for behavior you change

---

## 10. Working agreements

| Topic | Rule |
|-------|------|
| Language in code | Portuguese identifiers / user-facing messages |
| Commits | Only when the user asks |
| Scope | Change only files required by the task |

### Smoke checks

```bash
curl -s http://127.0.0.1:5003/health
curl -s http://127.0.0.1:5003/produtos
curl -s -X POST http://127.0.0.1:5003/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"<seed-email>","senha":"<seed-password>"}'
```

---

*Aligned with MVC refactor (v2.0.0), Flask 3.1.1, and `python-development-guidelines.md`.*
