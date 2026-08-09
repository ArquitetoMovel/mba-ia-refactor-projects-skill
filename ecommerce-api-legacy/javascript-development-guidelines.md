# JavaScript Development Guidelines

## Project Stack

This guideline was generated from the existing `ecommerce-api-legacy` repository.
No library parameters were supplied in the command invocation.

**Detected application dependencies**:
- **Node.js runtime**: Node 24 LTS is the recommended baseline; Node 26.7.0 is the current line researched for native APIs - JavaScript runtime - https://nodejs.org/api/
- **Express**: manifest range `^4.18.2`, lockfile `4.22.1`; latest stable researched `5.2.1` - HTTP middleware framework - https://expressjs.com/
- **sqlite3**: manifest range `^5.1.6`, lockfile `5.1.7`; latest stable researched `6.0.1` - asynchronous SQLite bindings - https://github.com/TryGhost/node-sqlite3
- **Database approach**: raw SQL through the SQLite driver; no ORM is present.
- **AI framework**: none detected.

**Auto-populated essential tools**:
- **npm**: `12.0.1` - package manager and task runner - https://docs.npmjs.com/
- **node:test**: built into Node.js - unit and integration test runner - https://nodejs.org/api/test.html
- **ESLint**: `10.8.1` - static analysis and correctness linting - https://eslint.org/
- **Prettier**: `3.9.6` - opinionated source formatter - https://prettier.io/
- **Console logging**: Node.js `console` and `node:console` - standard output logging - https://nodejs.org/api/console.html
- **HTTP client**: built-in `fetch` in supported Node.js versions - https://nodejs.org/api/globals.html#fetch
- **Async model**: ECMAScript Promises and `async`/`await` - https://tc39.es/ecma262/

> The application libraries are listed for context. Source examples in this document
> use JavaScript and Node.js built-ins only. Express and `sqlite3` remain integration
> choices, not reasons to couple domain logic to framework APIs.

## 1. Core Principles

### 1.1 Philosophy and Style

- Prefer small modules with one reason to change.
- Make data flow visible at module boundaries.
- Use `const` by default and make mutation local and intentional.
- Validate untrusted input before business logic.
- Keep HTTP, persistence, and business rules separate.
- Make asynchronous operations explicit with `async`/`await`.
- Use a formatter and linter in CI, not only in an editor.
- Keep error context while hiding internal details from clients.
- Treat the lockfile as part of the application source.
- Measure performance before changing an algorithm.

### 1.2 Clarity Over Brevity

Names should describe the business operation, not the implementation detail.
`findActiveCourse` communicates more than `getData`. A short function is not
automatically clear if it hides side effects or returns inconsistent shapes.

Prefer a predictable transformation:

```js
function toPublicUser(user) {
    return {
        id: user.id,
        name: user.name,
        email: user.email
    };
}
```

Avoid dense expressions that mix validation, I/O, mutation, and formatting.
One level of indirection is useful when it names a domain decision. More layers
are justified only when they isolate a change or make a test faster and clearer.

### 1.3 Automated Consistency

Use Prettier for layout and ESLint for correctness. Keep formatting decisions
in versioned files so that local editors, CI, and code review use the same rules.
Prettier is intentionally opinionated; do not turn every preference into a
project-specific option.

```json
{
    "singleQuote": true,
    "trailingComma": "all",
    "printWidth": 100
}
```

The formatter does not replace review. It cannot decide whether a payment
should be retried, whether a secret is exposed, or whether a transaction is
atomic.

## 2. Project Initialization

### 2.1 Creating a Project

Use an explicit Node.js version and initialize the package manifest:

```bash
node --version
npm --version
npm init -y
npm install express sqlite3
npm install --save-dev eslint prettier
npm pkg set engines.node=">=24.0.0"
```

Keep application dependencies in `dependencies` and development-only tools in
`devDependencies`. The manifest should expose short, repeatable tasks:

```json
{
    "name": "ecommerce-api",
    "private": true,
    "type": "commonjs",
    "engines": {
        "node": ">=24.0.0"
    },
    "scripts": {
        "start": "node src/server.js",
        "test": "node --test",
        "lint": "eslint .",
        "format": "prettier --write .",
        "format:check": "prettier --check ."
    }
}
```

Use `npm ci` in reproducible environments. It installs exactly what the
lockfile describes and fails when the manifest and lockfile disagree.

### 2.2 Dependency Management

```bash
npm install
npm ci
npm install package-name
npm install --save-dev tool-name
npm update
npm outdated
npm audit
npm audit fix
```

Review major upgrades separately from routine patch updates. Record runtime
requirements in `engines`, avoid unbounded version ranges, and update the
lockfile in the same change as `package.json`.

### 2.3 Configuration at Startup

Read environment variables once at the composition boundary. Normalize and
validate them before constructing clients or opening the server:

```js
function requiredEnv(name, environment = process.env) {
    const value = environment[name];

    if (!value) {
        throw new Error(`Missing required environment variable: ${name}`);
    }

    return value;
}

const settings = Object.freeze({
    port: Number(process.env.PORT ?? 3000),
    paymentGatewayKey: requiredEnv('PAYMENT_GATEWAY_KEY')
});
```

Do not import configuration into every domain module. Pass only the values a
module needs. This makes tests deterministic and prevents secret sprawl.

## 3. Project Structure

### 3.1 Recommended Layout

The current repository puts bootstrap, persistence, routes, and utilities in
one manager class. A maintainable target separates those responsibilities:

```text
ecommerce-api/
├── src/
│   ├── server.js              # process lifecycle and port binding
│   ├── app.js                # application composition without listen()
│   ├── config/
│   │   └── settings.js       # validated environment configuration
│   ├── domain/
│   │   ├── errors.js         # business error types
│   │   └── checkout.js       # pure checkout decisions
│   ├── application/
│   │   └── checkout-service.js
│   ├── infrastructure/
│   │   └── sqlite/
│   │       ├── connection.js
│   │       └── migrations/
│   ├── interfaces/
│   │   ├── http/
│   │   └── repositories/
│   └── observability/
│       └── logger.js
├── test/
│   ├── unit/
│   └── integration/
├── package.json
├── package-lock.json
└── README.md
```

### 3.2 Dependency Direction

- `domain` depends on language primitives only.
- `application` depends on domain contracts and receives infrastructure ports.
- `infrastructure` implements persistence, HTTP clients, and process adapters.
- `interfaces` translates external requests into application inputs.
- `server.js` composes concrete implementations.

The domain must not import Express, SQLite, environment variables, or `console`.
The application layer should not know whether a repository uses callbacks,
Promises, a file, or a database.

### 3.3 Module Boundaries

Prefer one public responsibility per file. Export a small surface:

```js
// domain/price.js
function calculateTotal(unitPrice, quantity) {
    if (!Number.isFinite(unitPrice) || unitPrice < 0) {
        throw new RangeError('unitPrice must be a non-negative number');
    }
    if (!Number.isInteger(quantity) || quantity < 1) {
        throw new RangeError('quantity must be a positive integer');
    }
    return unitPrice * quantity;
}

module.exports = { calculateTotal };
```

Avoid circular imports. If two modules require each other, extract the shared
value into a third module or move composition to the bootstrap layer.

## 4. Container Development

### 4.1 Container Philosophy

Use a pinned official Node.js image when the team needs a repeatable runtime.
The example uses the current Node 26.7.0 Alpine image researched for this
guideline. Adopt the next approved patch deliberately instead of using `latest`.
Development images should be simple and must not use multi-stage builds.

### 4.2 Development Dockerfile

The `sqlite3` dependency can require native build tools when a matching binary
is unavailable, so install the build toolchain in the development image:

```dockerfile
FROM node:26.7.0-alpine3.22

WORKDIR /app

RUN apk add --no-cache python3 make g++

COPY package*.json ./
RUN npm ci

COPY . .

ENV NODE_ENV=development
EXPOSE 3000
CMD ["npm", "start"]
```

### 4.3 Docker Compose

Use a named volume for `node_modules`; otherwise a bind mount can hide the
dependencies installed during image creation:

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: development
      PORT: 3000
      PAYMENT_GATEWAY_KEY: local-only-key
    volumes:
      - .:/app
      - node_modules:/app/node_modules
    init: true

volumes:
  node_modules:
```

### 4.4 Ignore Files and Commands

```text
node_modules
npm-debug.log*
.git
.gitignore
.env
.env.*
coverage
*.sqlite
*.sqlite-journal
```

```bash
docker compose build
docker compose up
docker compose logs -f api
docker compose exec api npm test
docker compose exec api sh
docker compose down
```

Never put production credentials in Compose files. Use a secret store or an
orchestrator-provided environment. Keep the container process in the
foreground so the runtime can receive termination signals.

## 5. Naming Conventions

### 5.1 Identifiers

- Use `camelCase` for variables, functions, and object properties.
- Use `PascalCase` for classes and custom error constructors.
- Use `UPPER_SNAKE_CASE` only for immutable process-wide constants.
- Use singular nouns for entities and plural nouns for collections.
- Use verbs for commands: `createEnrollment`, `closeDatabase`.
- Use predicates for booleans: `isActive`, `hasPaid`, `canRetry`.
- Prefer full words over unexplained abbreviations.

```js
const MAX_RETRY_ATTEMPTS = 3;

class PaymentDeclinedError extends Error {}

function canRetryPayment(payment) {
    return payment.status === 'TEMPORARY_FAILURE';
}
```

### 5.2 Files and Routes

Use lowercase kebab-case for new files:

```text
checkout-service.js
payment-repository.js
request-id-middleware.js
```

Keep route paths resource-oriented and stable:

```text
POST   /api/checkouts
GET    /api/admin/financial-report
DELETE /api/users/:id
```

Do not encode internal abbreviations such as `usr`, `eml`, or `c_id` in new
contracts. If legacy clients require them, translate them at the boundary and
use descriptive names internally.

### 5.3 Constants and Environment Names

Environment variables use uppercase names with underscores:

```text
NODE_ENV=production
PORT=3000
DATABASE_PATH=/var/lib/app/data.sqlite
PAYMENT_GATEWAY_KEY=provided-by-secret-store
```

Keep user-facing labels, database columns, and JavaScript identifiers separate
when their conventions differ. A mapper is safer than leaking storage names
through every layer.

## 6. Functions and Methods

### 6.1 Signatures and Contracts

JavaScript does not have native return-type annotations. Use clear parameter
names, runtime validation, and JSDoc when a public function needs a documented
contract. A function should either return a complete value or throw a defined
error; it should not silently return `undefined` for invalid input.

```js
/**
 * @param {unknown} input
 * @returns {{email: string, courseId: number}}
 * @throws {TypeError|RangeError}
 */
function parseCheckoutInput(input) {
    if (!input || typeof input !== 'object') {
        throw new TypeError('checkout input must be an object');
    }

    const email = String(input.email ?? '').trim();
    const courseId = Number(input.courseId);

    if (!email.includes('@')) {
        throw new TypeError('email is invalid');
    }
    if (!Number.isInteger(courseId) || courseId < 1) {
        throw new RangeError('courseId must be a positive integer');
    }

    return { email, courseId };
}
```

### 6.2 Good and Bad Return Patterns

Good code makes failure explicit and preserves context:

```js
function findCourse(courses, id) {
    const course = courses.find((candidate) => candidate.id === id);

    if (!course) {
        throw new Error(`Course ${id} was not found`);
    }

    return course;
}
```

Bad code swallows the failure and forces callers to guess what happened:

```js
function findCourseBad(courses, id) {
    try {
        return courses.find((candidate) => candidate.id === id);
    } catch {
        return null;
    }
}
```

The bad version does not distinguish “not found” from a broken collection and
does not add an operation or identifier to the failure. Do not catch an error
unless the function can recover, translate, or add useful context.

### 6.3 Function Design

- Keep functions focused on one decision or one side effect.
- Prefer three or fewer parameters; use an options object for related inputs.
- Avoid hidden writes to module-level state.
- Make mutation visible in names such as `update`, `append`, or `remove`.
- Return stable object shapes.
- Keep I/O at the edge and make core calculations pure.
- Use `Promise.all` only when operations are independent.
- Do not mix callback-style APIs and Promise-style APIs in the same function.

```js
async function completeCheckout({ userRepository, paymentGateway, input }) {
    const user = await userRepository.findOrCreate(input.user);
    const payment = await paymentGateway.charge({
        customerId: user.id,
        amount: input.amount
    });

    return { userId: user.id, paymentId: payment.id };
}
```

The caller supplies dependencies explicitly, so the function can be tested with
small fakes and does not depend on a global manager instance.

## 7. Error Handling

### 7.1 Error Model

Use `Error` instances, preserve the original cause, and give domain failures
stable names or codes. Do not throw strings, objects without a stack, or
database messages directly to an HTTP client.

```js
class ApplicationError extends Error {
    constructor(message, { code, status = 500, cause } = {}) {
        super(message, { cause });
        this.name = 'ApplicationError';
        this.code = code ?? 'INTERNAL_ERROR';
        this.status = status;
    }
}

async function loadCourse(repository, courseId) {
    try {
        const course = await repository.findById(courseId);

        if (!course) {
            throw new ApplicationError('Course was not found', {
                code: 'COURSE_NOT_FOUND',
                status: 404
            });
        }

        return course;
    } catch (cause) {
        if (cause instanceof ApplicationError) {
            throw cause;
        }
        throw new ApplicationError('Could not load course', {
            code: 'COURSE_LOOKUP_FAILED',
            status: 503,
            cause
        });
    }
}
```

### 7.2 Good and Bad Propagation

Good code adds operation context once and lets the boundary map the error:

```js
async function createEnrollment(repository, input) {
    try {
        return await repository.insertEnrollment(input);
    } catch (cause) {
        throw new ApplicationError('Enrollment creation failed', {
            code: 'ENROLLMENT_CREATE_FAILED',
            status: 503,
            cause
        });
    }
}
```

Bad code discards the cause and reports a misleading success:

```js
async function createEnrollmentBad(repository, input) {
    try {
        await repository.insertEnrollment(input);
        return { ok: true };
    } catch {
        console.log('error');
        return { ok: true };
    }
}
```

### 7.3 Boundary Rules

- Validate input errors at the request boundary.
- Translate infrastructure errors in the application or adapter layer.
- Log unexpected failures once at the process or HTTP boundary.
- Return a stable public error shape with a correlation identifier.
- Never include SQL, stack traces, card numbers, passwords, or secret values.
- Preserve `cause` for logs and diagnostics.
- Handle rejected Promises; no asynchronous work may become unobserved.
- On shutdown, reject new work and finish accepted work where possible.

An Express error middleware is an adapter concern. It should inspect
`ApplicationError.status`, emit a safe response, and delegate unknown failures
to the framework’s final handler after logging them.

## 8. Concurrency and Parallelism

### 8.1 Node.js Concurrency Model

Node.js runs JavaScript on an event loop and delegates many I/O operations to
the runtime. `async`/`await` makes Promise control flow readable; it does not
make CPU-heavy work non-blocking. Keep synchronous file, crypto, parsing, and
large array operations out of request handlers.

Run independent I/O concurrently and await the combined result:

```js
async function buildReport({ courseRepository, paymentRepository }) {
    const [courses, payments] = await Promise.all([
        courseRepository.listActive(),
        paymentRepository.listPaid()
    ]);

    return joinReport(courses, payments);
}
```

Do not create a Promise and forget to await or return it. Every asynchronous
operation must have an owner responsible for success, failure, and cleanup.

### 8.2 Timeouts and Cancellation

Use `AbortController` for operations with a finite business deadline:

```js
async function fetchExchangeRate(url, timeoutMs = 2_000) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) {
            throw new Error(`Exchange service returned ${response.status}`);
        }
        return await response.json();
    } finally {
        clearTimeout(timer);
    }
}
```

Propagate cancellation instead of retrying an operation after the caller has
gone away. Use bounded concurrency for collections; `Promise.all(items.map())`
can overwhelm a database or remote service.

### 8.3 Common Pitfalls

- Do not use `Array.prototype.forEach` with an async callback.
- Do not run blocking CPU work in an HTTP callback.
- Do not share mutable module-level objects between requests.
- Do not race two writes that must be ordered.
- Do not retry non-idempotent payment operations without an idempotency key.
- Close timers, streams, sockets, and database handles during shutdown.

## 9. Interfaces and Abstractions

### 9.1 Small Contracts

JavaScript has no enforced interface keyword in the language. Modules,
functions, classes, and documented object shapes provide equivalent boundaries.
Define the smallest capability a consumer needs:

```js
function createCheckoutService({ userStore, paymentGateway }) {
    return {
        async execute(input) {
            const user = await userStore.findOrCreate(input.user);
            const payment = await paymentGateway.charge({
                customerId: user.id,
                amount: input.amount
            });
            return { userId: user.id, paymentId: payment.id };
        }
    };
}
```

The service depends on `findOrCreate` and `charge`, not on a concrete database
class or an HTTP client package. Tests can provide objects with the same
capabilities without loading the application.

### 9.2 Composition Over Inheritance

Use classes when identity, lifecycle, or invariants make them useful. Prefer
factory functions and object composition for stateless operations. Avoid a
base manager class that accumulates unrelated repositories, routes, caches,
configuration, and lifecycle methods.

### 9.3 Abstraction Rules

- Introduce an abstraction at a change boundary.
- Keep ports free of HTTP and SQL vocabulary when possible.
- Make optional capabilities explicit.
- Do not create an interface for a single trivial function without a reason.
- Test the contract at the boundary, then test important implementations.
- Keep adapters replaceable, but do not hide meaningful transaction semantics.

## 10. Unit Tests

### 10.1 Structure

Use the built-in `node:test` runner and strict assertions. A test names the
observable behavior, arranges inputs, acts once, and asserts the result:

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const { calculateTotal } = require('../../src/domain/price');

test('calculates the total for a positive quantity', () => {
    assert.equal(calculateTotal(12.5, 4), 50);
});

test('rejects a non-positive quantity', () => {
    assert.throws(
        () => calculateTotal(12.5, 0),
        { name: 'RangeError' }
    );
});
```

Keep unit tests independent of network, clock, environment, and real
databases. Give each test its own state and use descriptive test names.

### 10.2 Table-Driven Tests

Represent related cases as data to make coverage visible:

```js
const cases = [
    { unitPrice: 10, quantity: 1, expected: 10 },
    { unitPrice: 10, quantity: 3, expected: 30 },
    { unitPrice: 0, quantity: 5, expected: 0 }
];

for (const { unitPrice, quantity, expected } of cases) {
    test(`total for ${quantity} item(s)`, () => {
        assert.equal(calculateTotal(unitPrice, quantity), expected);
    });
}
```

Test invalid inputs separately so failures identify the contract being broken.
Avoid asserting private variables, call order, or exact log formatting unless
those are part of the public behavior.

### 10.3 Commands and Coverage

```bash
node --test
node --test test/unit/price.test.js
node --test --test-name-pattern="positive quantity"
node --test --test-reporter=spec
node --test --experimental-test-coverage
npm test
```

Run fast unit tests on every change. Run integration tests against an isolated
database and external-service fake in CI. Treat flaky tests as defects rather
than increasing arbitrary sleep durations.

## 11. Mocks and Testability

### 11.1 Test Doubles

Prefer a manual fake when it communicates the contract more clearly than a
mocking library. A fake should implement only the behavior the test needs:

```js
function createPaymentGatewayFake() {
    const charges = [];
    return {
        charges,
        async charge(request) {
            charges.push(request);
            return { id: `payment-${charges.length}`, status: 'PAID' };
        }
    };
}
```

Use the native `node:test` mock helpers for a focused call assertion:

```js
const { mock } = require('node:test');

test('sends the calculated amount', async () => {
    const gateway = { charge: async () => ({ id: 'p-1' }) };
    const charge = mock.method(gateway, 'charge');

    await gateway.charge({ amount: 25 });
    assert.equal(charge.mock.calls.length, 1);
    assert.deepEqual(charge.mock.calls[0].arguments[0], { amount: 25 });
});
```

### 11.2 Mock Rules

- Mock at the boundary, not the function under test.
- Restore mocks automatically through the test context where available.
- Never mock the language’s arithmetic or Promise implementation.
- Do not assert implementation details that prevent safe refactoring.
- Use contract tests when multiple adapters implement the same capability.

## 12. Integration Tests

### 12.1 Real Boundaries

Integration tests exercise multiple modules and a real protocol. Keep the
server factory separate from the port-binding process so tests can select an
ephemeral port:

```js
const http = require('node:http');
const test = require('node:test');
const assert = require('node:assert/strict');

function createServer() {
    return http.createServer((request, response) => {
        response.writeHead(200, { 'content-type': 'application/json' });
        response.end(JSON.stringify({ status: 'ok' }));
    });
}

test('health endpoint returns JSON', async (t) => {
    const server = createServer().listen(0);
    t.after(() => server.close());
    const { port } = server.address();
    const response = await fetch(`http://127.0.0.1:${port}`);

    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), { status: 'ok' });
});
```

### 12.2 Isolation

Use a temporary database file or an in-memory database for each test suite.
Apply migrations before tests and close all handles after tests. Do not share
the process-wide application singleton between test cases.

```bash
node --test test/integration
node --test test/integration/checkout.test.js
NODE_ENV=test node --test
```

Assert response status, public body, persistence effects, and rollback
behavior. Do not assert private framework internals.

## 13. Load and Stress Tests

### 13.1 Goals

Define the workload before measuring: request rate, payload size, concurrency,
duration, success criteria, and database state. Track latency percentiles,
throughput, error rate, event-loop delay, and resource use.

### 13.2 Native Probe

For a small repeatable probe, use the built-in `fetch` API:

```js
async function runProbe(url, count = 100) {
    const started = performance.now();
    const results = await Promise.all(
        Array.from({ length: count }, () => fetch(url))
    );
    const failures = results.filter((response) => !response.ok).length;
    return {
        count,
        failures,
        elapsedMs: performance.now() - started
    };
}
```

This probe intentionally has no ramp-up or concurrency limit. Use an established
load tool such as `autocannon` for realistic traffic, and never point a stress
test at production without an approved test plan.

```bash
npx autocannon --connections 10 --duration 30 http://localhost:3000/health
node scripts/probe.js
```

## 14. Profiling and Diagnostics

### 14.1 CPU, Memory, and Event Loop

Profile representative workloads, not an idle process:

```bash
node --inspect src/server.js
node --cpu-prof src/server.js
node --heap-prof src/server.js
node --trace-gc src/server.js
node --trace-warnings src/server.js
```

Use the Inspector for breakpoints and heap snapshots. Delete generated profile
artifacts from the workspace after analysis if they contain request data.

### 14.2 Runtime Metrics

```js
const { monitorEventLoopDelay } = require('node:perf_hooks');

const delay = monitorEventLoopDelay({ resolution: 20 });
delay.enable();

setInterval(() => {
    console.log(JSON.stringify({
        event: 'runtime_sample',
        meanMs: Number(delay.mean) / 1e6,
        maxMs: Number(delay.max) / 1e6
    }));
}, 10_000).unref();
```

Record a baseline before optimizing. A lower CPU time with worse latency or
higher memory is not an improvement.

## 15. Benchmarks

### 15.1 Measurement

Benchmark pure functions with stable inputs and enough iterations to reduce
noise. Warm up code before comparing alternatives and report environment,
runtime version, and input size.

```js
const { performance } = require('node:perf_hooks');

function benchmark(name, fn, iterations = 100_000) {
    for (let index = 0; index < 10_000; index += 1) fn();
    const started = performance.now();
    for (let index = 0; index < iterations; index += 1) fn();
    const elapsed = performance.now() - started;
    console.log(JSON.stringify({
        name,
        iterations,
        elapsedMs: elapsed,
        operationsPerSecond: iterations / (elapsed / 1000)
    }));
}
```

### 15.2 Benchmark Rules

- Never benchmark a single run.
- Do not include logging or network calls in a microbenchmark.
- Avoid allocations that the real workload does not perform.
- Compare one variable at a time.
- Keep a correctness assertion beside each candidate.
- Re-run on the target Node.js version and hardware class.

```bash
node scripts/benchmark-price.js
node --cpu-prof scripts/benchmark-price.js
```

## 16. Optimization

### 16.1 Measure First

Start with a user-visible symptom and a baseline. Identify whether the limit is
CPU, memory, event-loop delay, database latency, network latency, or contention.
Record the workload and keep the benchmark beside the change.

- Prefer a better query plan over a JavaScript micro-optimization.
- Avoid repeated serialization and parsing across layers.
- Select only the columns and rows required by a use case.
- Bound caches by size and lifetime.
- Stream large results instead of building unbounded arrays.
- Keep synchronous work out of request paths.

### 16.2 Data and Allocation

Use a `Map` for repeated keyed lookup and reuse immutable configuration:

```js
function indexCourses(courses) {
    return new Map(courses.map((course) => [course.id, course]));
}

function sumPaid(enrollments, coursesById) {
    let total = 0;
    for (const enrollment of enrollments) {
        const course = coursesById.get(enrollment.courseId);
        if (course && enrollment.status === 'PAID') total += course.price;
    }
    return total;
}
```

Do not add a cache until its invalidation, ownership, memory bound, and
consistency behavior are documented. A process-local cache is not a substitute
for a durable source of truth.

### 16.3 Optimization Review

Every optimization should state the measured before and after result, the
trade-off, and the rollback path. Re-run correctness tests, load tests, and
profiling after changing concurrency, caching, query shape, or serialization.

## 17. Security

### 17.1 Essential Practices

- Never commit passwords, API keys, card data, or private certificates.
- Load secrets from a secret manager or protected environment.
- Validate type, size, range, and format at every external boundary.
- Use parameterized SQL; never concatenate user input into SQL.
- Enforce authentication and authorization independently.
- Use HTTPS and a correctly configured reverse proxy.
- Set `NODE_ENV=production` in production deployments.
- Limit request body size and apply rate limits to expensive operations.
- Keep Node.js and dependencies patched.
- Run as a non-root container user when the deployment permits it.

Bad:

```js
const config = {
    password: 'hardcoded-credential-value',
    paymentKey: 'pk_live_example_only'
};
```

Good:

```js
function loadSecrets(environment = process.env) {
    const paymentKey = environment.PAYMENT_GATEWAY_KEY;
    if (!paymentKey || paymentKey.startsWith('pk_live_')) {
        throw new Error('Payment credentials must come from a secret store');
    }
    return Object.freeze({ paymentKey });
}
```

The example deliberately rejects the production-shaped key in local startup.
Use separate test credentials and make accidental production calls impossible.

### 17.2 Boundary Defense

Treat request bodies, query strings, headers, uploaded files, database rows,
and third-party responses as untrusted data. Allow-list fields, normalize
values, reject unknown sensitive fields, and avoid reflecting raw input in
HTML or logs. Redact before serializing errors.

```js
function redact(value) {
    return JSON.stringify(value, (key, current) => {
        if (['password', 'pass', 'card', 'authorization'].includes(key)) {
            return '[REDACTED]';
        }
        return current;
    });
}
```

### 17.3 Security Checks

```bash
npm audit
npm outdated
npm ci
git diff --check
node --check src/server.js
```

Review dependency install scripts, lockfile changes, permissions, proxy
configuration, and secret access during code review. Security failures should
fail closed and produce an actionable audit event without leaking the secret.

## 18. Code Patterns

### 18.1 Early Return

Reduce nesting by rejecting invalid state at the start:

```js
function approveEnrollment(enrollment) {
    if (!enrollment) throw new Error('Enrollment is required');
    if (enrollment.status !== 'PENDING') {
        throw new Error('Only pending enrollments can be approved');
    }
    if (enrollment.amount <= 0) {
        throw new Error('Enrollment amount must be positive');
    }
    return { ...enrollment, status: 'APPROVED' };
}
```

### 18.2 Separate Logic from I/O

Pure decisions are easy to test; adapters perform effects:

```js
function decidePaymentStatus(cardNumber) {
    return cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
}

async function processPayment({ gateway, auditLog, cardNumber, amount }) {
    const status = decidePaymentStatus(cardNumber);
    const payment = await gateway.record({ amount, status });
    await auditLog.append({ paymentId: payment.id, status });
    return payment;
}
```

Never log the card number. The pure function can be tested with a table, while
the process function can be tested with a fake gateway and audit logger.

### 18.3 DRY and Scope

Remove duplication when the duplicated behavior has the same reason to change.
Do not extract two similar lines into an abstraction that has different
business rules. Declare variables at the smallest useful scope and prefer
immutable values:

```js
function formatRevenue(amount, currency = 'BRL') {
    const formatter = new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency
    });
    return formatter.format(amount);
}
```

## 19. Dependency Management

### 19.1 Principles

- Prefer the Node.js standard library for small, stable capabilities.
- Add a dependency when it removes substantial risk or maintenance cost.
- Verify maintenance activity, license, security history, and transitive size.
- Pin the runtime and commit `package-lock.json`.
- Keep production and development dependencies in the correct sections.
- Avoid packages that duplicate built-in `fetch`, test, crypto, or URL APIs.
- Review native modules for supported Node.js and platform binaries.
- Remove unused packages rather than keeping them “just in case”.

### 19.2 Commands

```bash
npm ls --depth=0
npm explain package-name
npm uninstall package-name
npm prune
npm dedupe
npm ci --ignore-scripts
npm audit --omit=dev
npm pkg get dependencies
```

Use `npm ci --ignore-scripts` for a restricted inspection environment, but
verify native modules separately because disabling install scripts can prevent
their required build step. Use normal `npm ci` in the approved build pipeline.

### 19.3 Upgrade Policy

Read release notes before a major upgrade. Upgrade one infrastructure boundary
at a time, run unit and integration tests, exercise startup and shutdown, and
check native module compatibility. Do not mix a framework migration with an
unrelated domain refactor.

## 20. Comments and Documentation

### 20.1 Comments Explain Why

Code should explain what it does. A comment should record a non-obvious
constraint, business decision, compatibility reason, or safety invariant:

```js
// Keep the timeout below the gateway SLA so the checkout can return a
// deterministic failure before the client-side request expires.
const PAYMENT_TIMEOUT_MS = 2_000;
```

Delete comments that restate the next line or describe a temporary state.
Comments are part of the maintenance surface and must change with the code.

### 20.2 Public API Documentation

Use JSDoc for public module functions, input shape, return shape, and thrown
errors. Keep examples executable or covered by tests:

```js
/**
 * Creates one enrollment after payment confirmation.
 *
 * @param {{userId: number, courseId: number, amount: number}} input
 * @returns {Promise<{enrollmentId: number}>}
 * @throws {ApplicationError} when payment or persistence fails
 */
async function createEnrollment(input) {
    return enrollmentService.create(input);
}
```

Document status codes, error bodies, idempotency behavior, authentication,
timeouts, and side effects for each HTTP endpoint.

### 20.3 Repository Documentation

The README should answer:

- What the service does and which runtime version it needs.
- How to install, run, test, lint, format, and inspect it.
- Which environment variables are required and how to provide them safely.
- How the database is initialized and migrated.
- Which endpoints exist and show safe sample requests.
- How graceful shutdown and health checks work.
- How to report a security issue without publishing a secret.

Keep architecture diagrams small and update them when module boundaries change.

## 21. Database

### 21.1 Approach

Choose the smallest persistence abstraction that protects the use case:

- Raw SQL is explicit and appropriate for a small SQLite service.
- A query builder can reduce repetitive SQL while preserving query visibility.
- An ORM can help with entity mapping, but may hide joins and transaction scope.

The current application uses raw SQL through `sqlite3`. The native
`node:sqlite` examples below show the same safety principles without adding a
third-party library. `DatabaseSync` is synchronous; use it only when the
runtime and workload have been evaluated. If the existing asynchronous driver
remains, preserve the same parameter, transaction, and cleanup rules.

### 21.2 Connection and Driver

Enable constraints and a sensible wait policy when opening a file database:

```js
const { DatabaseSync } = require('node:sqlite');

function openDatabase(path) {
    const database = new DatabaseSync(path, {
        enableForeignKeyConstraints: true,
        timeout: 5_000
    });
    database.exec('PRAGMA journal_mode = WAL;');
    return database;
}

const database = openDatabase(process.env.DATABASE_PATH ?? 'data.sqlite');
try {
    database.exec('SELECT 1');
} finally {
    database.close();
}
```

SQLite does not provide a Node-style connection pool in this native API. Treat
the connection as an owned process resource, bound its lifetime, and document
the concurrency model. For an asynchronous driver, configure its pool size
and busy timeout explicitly rather than relying on defaults.

### 21.3 Queries and Transactions

Use placeholders for every external value and close the database at shutdown:

Good:

```js
const database = openDatabase('data.sqlite');
const findCourse = database.prepare(
    'SELECT id, title, price FROM courses WHERE id = ? AND active = 1'
);
const course = findCourse.get(2);

const insertEnrollment = database.prepare(
    'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)'
);
const result = insertEnrollment.run(7, course.id);

database.exec('BEGIN IMMEDIATE');
try {
    database.prepare(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)'
    ).run(result.lastInsertRowid, course.price, 'PAID');
    database.exec('COMMIT');
} catch (error) {
    database.exec('ROLLBACK');
    throw error;
}
```

Bad:

```js
const sql = `SELECT * FROM users WHERE email = '${request.body.email}'`;
database.prepare(sql).all();
```

The bad form permits SQL injection and makes query plans harder to reuse.
Parameterized statements also make the boundary between SQL and data explicit.

### 21.4 Schema and Migration Rules

- Define primary keys, `NOT NULL`, `UNIQUE`, and foreign keys deliberately.
- Enable `PRAGMA foreign_keys = ON` for every connection.
- Add indexes for measured access paths, not every column.
- Use transactions for a business operation that changes multiple tables.
- Store migrations as ordered, immutable files.
- Make migrations observable and fail startup when schema state is invalid.
- Back up before destructive migrations and test rollback procedures.
- Keep monetary values in integer minor units or a precisely defined decimal.

## 22. Logs and Observability

### 22.1 Levels and Destinations

Use `DEBUG` for local diagnostics, `INFO` for lifecycle and business events,
`WARN` for recoverable anomalies, and `ERROR` for failed operations. Keep logs
on stdout/stderr so the runtime or orchestrator can collect them. Do not write
application logs to an unbounded local file in a container.

Configure the minimum level once:

```js
const { Console } = require('node:console');

const logger = new Console({
    stdout: process.stdout,
    stderr: process.stderr
});

const levels = { DEBUG: 10, INFO: 20, WARN: 30, ERROR: 40 };
const minimum = levels[process.env.LOG_LEVEL ?? 'INFO'] ?? levels.INFO;

function write(level, event, fields = {}) {
    if (levels[level] < minimum) return;
    const entry = {
        timestamp: new Date().toISOString(),
        level,
        service: 'ecommerce-api',
        event,
        ...fields
    };
    const output = JSON.stringify(entry);
    if (level === 'ERROR' || level === 'WARN') logger.error(output);
    else logger.log(output);
}
```

### 22.2 Structured Context

Carry a request identifier through asynchronous work with
`AsyncLocalStorage`. Do not put customer secrets or payment credentials in
the context:

Good:

```js
const { AsyncLocalStorage } = require('node:async_hooks');
const requestContext = new AsyncLocalStorage();

function withRequestContext(requestId, callback) {
    return requestContext.run({ requestId }, callback);
}

function logRequestCompleted(route, status, durationMs) {
    const context = requestContext.getStore() ?? {};
    write('INFO', 'request_completed', {
        requestId: context.requestId ?? 'unknown',
        route,
        status,
        durationMs
    });
}
```

Bad logging records a complete request or card value:

```js
logger.log(JSON.stringify({ body: request.body, card: request.body.card }));
```

Log stable event names and bounded fields: request ID, route, status, duration,
resource ID, error code, and retry count. Redact before serializing and preserve
the original error as a non-public diagnostic field.

### 22.3 Metrics and Health

Measure request count, error count, latency percentiles, database failures,
queue depth, event-loop delay, and memory. Keep metric labels low-cardinality;
never use email, user ID, or arbitrary URL values as label names.

Expose separate endpoints or checks for:

- Liveness: the process is running.
- Readiness: required dependencies are reachable and migrations are applied.
- Metrics: operational measurements, protected when they reveal topology.

During shutdown, stop accepting traffic, mark readiness false, close the HTTP
server, finish or cancel in-flight operations, close the database, and exit.

## 23. Golden Rules

1. Make the simplest correct design the default.
2. Keep domain decisions independent from Express and SQLite.
3. Validate every external input and parameterize every query.
4. Use explicit errors with stable public codes and preserved causes.
5. Own every Promise, timer, stream, socket, and database handle.
6. Prefer pure functions for calculations and policy decisions.
7. Test behavior, boundaries, rollback, and failure paths.
8. Keep secrets out of source, logs, fixtures, and error responses.
9. Format and lint automatically; review semantics manually.
10. Measure CPU, memory, latency, and database plans before optimizing.
11. Pin the runtime and lock dependencies.
12. Make startup, health, readiness, and shutdown observable.

## 24. Pre-Commit Checklist

### Code

- [ ] Naming and module boundaries follow this guideline.
- [ ] Formatter was run and the diff is focused.
- [ ] Linter has no errors.
- [ ] No callback path can send two responses.
- [ ] No unhandled Promise or resource leak remains.
- [ ] Public errors do not expose internal details.

### Tests

- [ ] Unit tests cover success and failure behavior.
- [ ] Integration tests cover the changed boundary.
- [ ] Database transaction and foreign-key behavior was verified.
- [ ] Tests do not depend on shared mutable process state.
- [ ] Coverage or risk justification is recorded for critical paths.

### Security and Operations

- [ ] No secret, credential, card number, or personal data was committed.
- [ ] Inputs are validated and SQL is parameterized.
- [ ] Dependency and runtime versions are supported.
- [ ] `npm audit` was reviewed.
- [ ] Logs contain request context without sensitive payloads.
- [ ] Health, readiness, and shutdown behavior remain valid.

### Commands

```bash
npm ci
npm run format:check
npm run lint
npm test
node --test --experimental-test-coverage
npm audit
git diff --check
```

## 25. References

### Official Language and Runtime Documentation

- ECMAScript specification: https://tc39.es/ecma262/
- MDN JavaScript modules: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules
- MDN Promises: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises
- MDN error handling: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Control_flow_and_error_handling
- Node.js API index: https://nodejs.org/api/
- Node.js test runner: https://nodejs.org/api/test.html
- Node.js SQLite API: https://nodejs.org/api/sqlite.html
- Node.js asynchronous context: https://nodejs.org/api/async_context.html
- Node.js console API: https://nodejs.org/api/console.html
- Node.js performance hooks: https://nodejs.org/api/perf_hooks.html

### Tools and Frameworks

- npm `package.json`: https://docs.npmjs.com/cli/v11/configuring-npm/package-json/
- npm scripts: https://docs.npmjs.com/cli/v11/using-npm/scripts/
- Express error handling: https://expressjs.com/en/guide/error-handling.html
- Express middleware: https://expressjs.com/en/guide/using-middleware.html
- Express production security: https://expressjs.com/en/advanced/best-practice-security.html
- ESLint configuration: https://eslint.org/docs/latest/use/configure/
- ESLint rules: https://eslint.org/docs/latest/rules/
- Prettier configuration: https://prettier.io/docs/configuration
- Prettier option philosophy: https://prettier.io/docs/option-philosophy
- Official Node Docker images: https://hub.docker.com/_/node

### Database and Security Guidance

- SQLite transactions: https://www.sqlite.org/lang_transaction.html
- SQLite isolation and WAL: https://sqlite.org/isolation.html
- SQLite indexes: https://www.sqlite.org/lang_createindex.html
- SQLite pragmas and foreign keys: https://sqlite.org/pragma.html
- Express behind proxies: https://expressjs.com/en/guide/behind-proxies.html
- Node.js diagnostics and Inspector: https://nodejs.org/en/learn/diagnostics/live-debugging/using-inspector

### Industry and Production Examples

- Airbnb JavaScript Style Guide: https://github.com/airbnb/javascript
- Google JavaScript Style Guide: https://google.github.io/styleguide/jsguide.html
- Node.js production repository structure: https://github.com/nodejs/node
- Express framework repository: https://github.com/expressjs/express
- npm CLI repository structure: https://github.com/npm/cli
- sqlite3 Node bindings: https://github.com/TryGhost/node-sqlite3

Version metadata in the Project Stack was researched on 2026-08-08. Re-check
release pages before upgrading; the examples intentionally rely on standard
JavaScript and Node.js APIs rather than the detected application libraries.
