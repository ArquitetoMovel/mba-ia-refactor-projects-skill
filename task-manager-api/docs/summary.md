# Refactor Architecture — Summary

Project: **task-manager-api**  
Date: 2026-08-09  
Process: `refactor-arch` (Phases 1 → 3)

---

## Phase 1 — Stack & architecture (before)

| Item | Finding |
|------|---------|
| Language | Python 3 |
| Framework | Flask 3.0 + Flask-SQLAlchemy |
| DB | SQLite (`tasks.db`) — `users`, `tasks`, `categories` |
| Domain | Task Manager API |
| Structure | Partial folders (`models/`, `routes/`, `services/`, `utils/`) |
| Architecture gap | **Not MVC** — routes owned validation, business rules, DB access, and JSON serialization |

Full report: [`project_analysis.txt`](./project_analysis.txt)

---

## Phase 2 — Findings (by severity)

### Critical
1. **Hardcoded secrets** — `SECRET_KEY` in `app.py`; SMTP user/password in `notification_service.py`
2. **Insecure passwords** — MD5 hashing; hash returned in `User.to_dict()` API responses
3. **Fake auth** — login returned `fake-jwt-token-{id}` with no verification
4. **God / fat routes** — HTTP + domain + persistence mixed in `routes/*`

### High
5. Incomplete MVC / no real controller layer  
6. Duplicated overdue / status / email validation (shotgun surgery)  
7. N+1 queries on `GET /tasks`  
8. In-memory notification list; service unused  

### Medium
9. Long methods in routes/reports  
10. Category CRUD misplaced under report routes  
11. Dead code + unused deps (`marshmallow` unused, `requests`, bare imports)  
12. Poor error handling (`bare except`, `print`)  

### Low
13. Deprecated `datetime.utcnow()`  
14. Inconsistent naming / verbose booleans  
15. Weak password policy (min 4 chars)  

Full report: [`project_issues.txt`](./project_issues.txt)

---

## Phase 3 — What changed

### MVC target structure

- **Model** → `models/` (entities + domain helpers)
- **View** → `views/` (thin Flask blueprints)
- **Controller** → `controllers/` (use-cases / transactions)
- Supporting: `schemas/` (Marshmallow), `config/`, `middlewares/`, `services/`

### Fixes applied

| Issue | Resolution |
|-------|------------|
| Secrets | `config/settings.py` + `.env` / `.env.example` |
| Password security | Werkzeug hashes; never serialized |
| Auth token | Signed token via `itsdangerous` (`AuthController`) |
| Fat routes | Replaced `routes/` with `views/` + `controllers/` |
| Validation | Marshmallow schemas |
| Overdue logic | Single `Task.is_overdue()` |
| N+1 | `joinedload(Task.user/category)` |
| Categories | Dedicated `category_views` / `CategoryController` |
| Notifications | Env-gated SMTP; called on task assign |
| Errors | `AppError` + centralized handlers + logging |
| Docs | `README.md`, `AGENTS.md`, this summary |

Full report: [`project_refactored.txt`](./project_refactored.txt)

---

## Validation

- App boots via `create_app()`
- `seed.py` loads sample data (passwords ≥ 8 chars)
- Smoke tests: health, users, login (token + no password leak), tasks (relations/overdue), stats, categories, reports, create task, validation errors

---

## How to run

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
python app.py
```
