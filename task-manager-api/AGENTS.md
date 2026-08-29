# AGENTS.md

Guidance for AI coding agents working on **task-manager-api**.

## Stack

- Python 3 + Flask 3 + Flask-SQLAlchemy 3 (SQLAlchemy 2) + Marshmallow + itsdangerous + flask-cors + python-dotenv
- SQLite by default (`DATABASE_URL`)
- All direct dependencies are declared in `requirements.txt` (no reliance on transitive installs)

## Architecture (MVC)

Respect the layer boundaries:

| Layer | Path | Do |
|-------|------|----|
| Model | `models/` | Persistence, domain methods (`to_dict`, `is_overdue`, password hashing) |
| View | `views/` | HTTP only: auth decorators, request parsing via schemas, call controller, `jsonify` |
| Controller | `controllers/` | Business rules, authorization rules, DB transactions, call services |
| Schema | `schemas/` | Input validation / query validation / response serialization (Marshmallow) |
| Config | `config/settings.py` | Env-based settings + domain constants (statuses, roles, limits, pagination) |
| Services | `services/` | Side effects (email, etc.) |
| Middleware | `middlewares/` | Cross-cutting errors (`AppError` handlers) and auth guards (`token_required`, `role_required`) |

Do **not** put business logic or SQLAlchemy queries in views. Do **not** hardcode secrets.

## Conventions

- App factory: `create_app()` in `app.py`; module-level `app = create_app()` composition root
- Secrets: `SECRET_KEY` must come from env; production fails fast on missing/weak key (DEBUG/TESTS get an ephemeral in-memory key with a warning)
- Raise `AppError(message, status_code)` for domain/HTTP errors; `IntegrityError`/`500` handlers `db.session.rollback()`
- All writes go through `database.transaction()` (commit on success, rollback on any exception) — never call `db.session.commit()` bare in controllers
- Passwords: Werkzeug `generate_password_hash` / `check_password_hash` — never return password fields
- Auth tokens: `AuthController` + `itsdangerous` signed tokens (`current_app.secret_key`); protect endpoints with `token_required` / `role_required` from `middlewares/auth.py`
- Access matrix: public = `GET /`, `GET /health`, `POST /login`, `POST /users`; admin = user listing/deletion; admin/manager = category writes and reports; everything else requires a valid token; self-or-admin ownership rules live in `controllers/user_authz.py`
- ORM: `db.session.get(Model, pk)` — do not use the legacy `Model.query.get()` (SQLAlchemy 2.0 warning)
- Time: `utils.time.utcnow()` / `as_utc()` only — prefer `datetime.now(timezone.utc)` over `datetime.utcnow()`
- Lists: return the pagination envelope `{items, page, per_page, total, pages}`; parse `page`/`per_page` with `PaginationSchema`
- Aggregations: single SQL `GROUP BY` queries (no full-table loads, no per-row COUNT/lazy-load loops)
- Constants: use `Settings.*` (statuses, roles, priority bounds, defaults) — no magic literals
- Eager-load relations (`joinedload`) when listing tasks with user/category names

## Running

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set a strong SECRET_KEY for production
python seed.py
python app.py
```

Smoke-test with Flask `test_client` or HTTP against `http://localhost:5000` (protected endpoints need `Authorization: Bearer <token>` from `POST /login`).

## Docs

Analysis and refactor reports live under `docs/` (`project_analysis.txt`, `project_issues.txt`, `project_refactored.txt`, `playbook_refatoracao.md`, `summary.md`).
