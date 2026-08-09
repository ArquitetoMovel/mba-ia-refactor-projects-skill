# Agent Instructions

## Scope

These instructions apply to the whole `ecommerce-api-legacy` project.

## Current Architecture (MVC)

- Node.js/Express API organized as Model-View-Controller with a services layer.
- `src/server.js` is the process entry: creates the app and listens on `PORT` (default `3000`).
- `src/app.js` is the composition root: Express JSON middleware, DB open + schema/seed, route registration.
- `src/models/` owns SQL access (users, courses, enrollments, payments, audit logs, report queries).
- `src/services/` owns business rules (checkout transaction, payment decision, password hashing, report aggregation, user cascade delete).
- `src/controllers/` translate HTTP requests into service calls.
- `src/views/httpResponses.js` formats status/body responses (legacy text errors + JSON success).
- `src/routes/index.js` registers URL paths.
- `src/config/settings.js` reads environment variables (no hard-coded production secrets).
- `src/db/database.js` provides Promise helpers, transactions, schema and seeds.
- `api.http` contains manually executable request examples.

## Data and API

- Default SQLite path is `:memory:`; data disappears when the process stops.
- Tables are `users`, `courses`, `enrollments`, `payments`, and `audit_logs`.
- `POST /api/checkout` expects the legacy fields `usr`, `eml`, `pwd`, `c_id`, and `card`.
- `GET /api/admin/financial-report` returns course revenue and students.
- `DELETE /api/users/:id` removes the user and related payments/enrollments in a transaction.
- Card prefix `4` is a fake payment approval; never use real payment data.
- Never log credentials, passwords, card numbers, or payment keys.

## Run and Verify

```bash
npm ci
npm start
```

The API is available at `http://localhost:3000`. Use `api.http` or `curl` for
smoke checks. Stop it with `Ctrl+C`.

## Working Rules

- Preserve the legacy request/response contract unless a change explicitly includes documentation and client updates.
- Keep Model (SQL), View (response shaping), Controller (HTTP), and Service (domain) responsibilities separate.
- Use parameterized SQL, explicit error handling (`AppError`), and transactions for multi-table changes.
- Never add, copy, or log credentials, passwords, card numbers, or payment keys.
- Prefer environment variables via `src/config/settings.js` over hard-coded secrets.
- Update `README.md` and `api.http` when startup behavior or endpoint contracts change.
- Prefer small, focused changes and verify startup plus the affected endpoint after edits.
