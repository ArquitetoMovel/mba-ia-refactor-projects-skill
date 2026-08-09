# AGENTS.md

Guidance for AI coding agents working on **task-manager-api**.

## Stack

- Python 3 + Flask 3 + Flask-SQLAlchemy + Marshmallow + flask-cors + python-dotenv
- SQLite by default (`DATABASE_URL`)

## Architecture (MVC)

Respect the layer boundaries:

| Layer | Path | Do |
|-------|------|----|
| Model | `models/` | Persistence, domain methods (`to_dict`, `is_overdue`, password hashing) |
| View | `views/` | HTTP only: parse request, call schema + controller, return `jsonify` |
| Controller | `controllers/` | Business rules, DB transactions, call services |
| Schema | `schemas/` | Input validation / response shapes (Marshmallow) |
| Config | `config/settings.py` | Env-based settings only |
| Services | `services/` | Side effects (email, etc.) |
| Middleware | `middlewares/` | Cross-cutting errors |

Do **not** put business logic or SQLAlchemy queries in views. Do **not** hardcode secrets.

## Conventions

- App factory: `create_app()` in `app.py`
- Raise `AppError(message, status_code)` for domain/HTTP errors
- Passwords: Werkzeug `generate_password_hash` / `check_password_hash` — never return password fields
- Auth tokens: `AuthController` + `itsdangerous` signed tokens
- Prefer `datetime.now(timezone.utc)` over `datetime.utcnow()`
- Eager-load relations (`joinedload`) when listing tasks with user/category names

## Running

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # if needed
python seed.py
python app.py
```

Smoke-test with Flask `test_client` or HTTP against `http://localhost:5000`.

## Docs

Analysis and refactor reports live under `docs/` (`project_analysis.txt`, `project_issues.txt`, `project_refactored.txt`, `summary.md`).
