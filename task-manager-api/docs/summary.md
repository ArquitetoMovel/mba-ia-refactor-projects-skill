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

## Wave 2 — Re-audit & hardening (2026-08-29)

The re-audit of the already-MVC codebase (Phases 1–2 refreshed in
[`project_analysis.txt`](./project_analysis.txt) and
[`project_issues.txt`](./project_issues.txt)) found **12 residual
findings** — structural MVC existed, but enforcement did not.

### Findings fixed (Phase 3 — Wave 2)

| # | Severity | Issue | Resolution |
|---|----------|-------|------------|
| 1 | Critical | Auth token issued but **never verified** — all endpoints open | `middlewares/auth.py` with `token_required` / `role_required` wired on every protected blueprint; access matrix documented in README |
| 2 | Critical | Weak fallback `SECRET_KEY` → forgeable tokens | `app.py::_configure_secret` fails fast in production; ephemeral key + warning only in DEBUG/TESTS; signing uses `current_app.secret_key` |
| 3 | High | Bare commits, no rollback | `database.transaction()` context manager on all writes; rollback in `IntegrityError`/500 handlers |
| 4 | High | N+1 / full-table loads | Single `GROUP BY`/`OUTER JOIN` queries in `list_users`, `list_categories`, `TaskController.stats`, `ReportController.summary`/`user_report` |
| 5 | High | `delete_category` orphaned `tasks.category_id` | Coordinated `UPDATE … SET NULL` + `DELETE` in one transaction |
| 6 | Medium | `?priority=abc` → unhandled 500 | `TaskSearchSchema` + `PaginationSchema` validate query args → 400 |
| 7 | Medium | Dead code (unused ResponseSchemas, no-op `pre_load`, unused validators/helpers) | Removed or wired (ResponseSchemas now serialize views via `.dump()`) |
| 8 | Medium | `itsdangerous`/`SQLAlchemy` not declared | Pinned in `requirements.txt` |
| 9 | Medium | `utcnow()` ×3, overdue-fix ×2, status counts ×2, manual dict | `utils/time.py` (single source), `TaskController.status_counts()` reused, `Task.to_dict` reuse |
| 10 | Medium | Unbounded lists | Pagination envelope `{items, page, per_page, total, pages}` on `/tasks`, `/users`, `/tasks/search` |
| 11 | Low | Legacy `Query.get()` (SQLAlchemy 2.0) | All 11 call-sites → `db.session.get()`; validated with `warnings=error` |
| 12 | Low | Magic numbers | `Settings` constants (`DEFAULT_STATUS/ROLE/COLOR/PRIORITY`, `NON_OVERDUE_STATUSES`, `HIGH_PRIORITY_MAX`, page limits) |

### Wave 2 validation

- `seed.py` + full `test_client` suite: 50+ assertions — auth matrix (401/403),
  validation (400), pagination envelope, cascade-nullify, transactional
  delete-user, aggregate consistency with `Task.is_overdue()`, forged-token
  rejection, production fail-fast on weak secret — **all passing, zero
  deprecation warnings**.

Full report: [`project_refactored.txt`](./project_refactored.txt)

---

## How to run

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set a strong SECRET_KEY for production
python seed.py
python app.py
```
