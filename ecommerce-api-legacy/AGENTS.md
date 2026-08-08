# Agent Instructions

## Scope

These instructions apply to the whole `ecommerce-api-legacy` project.

## Current Architecture

- This is a deliberately legacy, monolithic Node.js/Express API.
- `src/app.js` is the bootstrap: it creates Express, enables JSON parsing, creates `AppManager`, initializes the database, registers routes, and listens on port `3000`.
- `src/AppManager.js` currently owns the SQLite connection, schema/seeds, route handlers, checkout workflow, financial report, and user deletion.
- `initDb()` uses `sqlite3` callbacks; `app.listen()` is not explicitly gated on seed completion.
- `src/utils.js` contains hard-coded configuration, a process-local cache, logging, and the intentionally insecure password helper.
- `api.http` contains manually executable request examples.
- `javascript-development-guidelines.md` contains the language and runtime guidance generated for this repository.

## Data and API

- SQLite uses `:memory:`; all data disappears when the process stops.
- Tables are `users`, `courses`, `enrollments`, `payments`, and `audit_logs`.
- `POST /api/checkout` expects the legacy fields `usr`, `eml`, `pwd`, `c_id`, and `card`.
- `GET /api/admin/financial-report` returns course revenue and students.
- `DELETE /api/users/:id` deletes only the user row; it does not clean related records.
- The card prefix is only a fake payment decision (`4` means paid); never use real payment data.

## Run and Verify

```bash
npm ci
npm start
```

The API is available at `http://localhost:3000`. Use `api.http` or `curl` for
smoke checks. Stop it with `Ctrl+C`. There is currently no automated test or
lint script in `package.json`.

## Working Rules

- Preserve the legacy request contract unless a change explicitly includes documentation and client updates.
- Keep bootstrap, HTTP, domain, and persistence responsibilities separate in new code; avoid adding more responsibilities to `AppManager`.
- Use parameterized SQL, explicit error handling, and transactions for multi-table changes.
- Never add, copy, or log credentials, passwords, card numbers, or payment keys.
- Do not treat the current hard-coded configuration or `badCrypto` helper as production-safe.
- Update `README.md` and `api.http` when startup behavior or endpoint contracts change.
- Prefer small, focused changes and verify startup plus the affected endpoint after edits.
