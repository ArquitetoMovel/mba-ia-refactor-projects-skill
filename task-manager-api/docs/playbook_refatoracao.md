# Playbook de Refatoração Arquitetural — task-manager-api

**Onda 2 — Hardening do MVC aplicável** (re-auditoria pós-primeira-refatoração)
**Data:** 2026-08-29 · **Skill:** `refactor-arch` · **Stack:** Python 3.14 · Flask 3 · Flask-SQLAlchemy 3 · Marshmallow 3 · itsdangerous

---

## 1. Sumário Executivo

A primeira onda de refatoração converteu as *fat routes* em camadas MVC (Model/View/Controller/Schema).
A re-auditoria (Fases 1–2 desta onda) provou em runtime que **estrutura ≠ comportamento**: o esqueleto
MVC estava correto, mas 12 achados residuais transformavam a arquitetura em decoração — o token de
autenticação era emitido e nunca validado, a `SECRET_KEY` tinha default forjável, commits não tinham
rollback, leituras carregavam tabelas inteiras e schemas de resposta eram código morto.

Esta onda fechou todos os 12 achados com **8 padrões de transformação** replicáveis.

### Tabela de resultados

| # | Padrão | Anti-pattern (severidade) | Camadas | Status |
|---|--------|---------------------------|---------|--------|
| P1 | Guard de autenticação obrigatório no edge | Fake Authentication / Broken Access Control (**CRITICAL**) | View + Middleware | ✅ |
| P2 | Segredo com fail-fast em produção | Hardcoded/Weak Secret (**CRITICAL**) | Config + App Factory | ✅ |
| P3 | Contexto transacional ACID em toda escrita | Missing Transaction Boundaries (**HIGH**) | Controller + Middleware + DB | ✅ |
| P4 | Agregação SQL única contra N+1 / full-table load | N+1 Query Problem (**HIGH**) | Controller + Model | ✅ |
| P5 | Integridade referencial coordenada no delete | Orphan Records (**HIGH**) | Controller | ✅ |
| P6 | Contrato de query string via Schema | Poor Error Handling — 500 em input inválido (**MEDIUM**) | View + Schema | ✅ |
| P7 | Schema de resposta como contrato de saída + envelope de paginação | Dead Code / Unbounded Lists (**MEDIUM**) | View + Schema | ✅ |
| P8 | Fonte única de regra, ORM moderno e dependências declaradas | Shotgun Surgery / Deprecated API / Magic Numbers / Phantom Deps (**MEDIUM/LOW**) | Model + Utils + Config | ✅ |

### Evidências capturadas antes da refatoração (test_client)

```text
GET    /users              sem token -> 200   (PII exposta)
DELETE /users/1            sem token -> 200   (destruição aberta)
GET    /reports/summary    sem token -> 200   (métricas expostas)
Token forjado c/ SECRET_KEY default ('change-me-in-production') -> aceito
GET    /tasks/search?priority=abc -> 500      (ValueError não tratado)
LegacyAPIWarning: Query.get() -> emitida em runtime
```

---

## 2. Arquitetura MVC-Alvo desta onda

```text
                       ┌──────────────────────────────────────────────────┐
 Request ──HTTP─────▶  │  VIEW (views/*_views.py — blueprints finos)      │
                       │  ├─ P1: @token_required / @role_required         │
                       │  ├─ P6: Schema().load(request.args) → 400/✅      │
                       │  └─ P7: ResponseSchema.dump() + envelope         │
                       └───────────────┬──────────────────────────────────┘
                                       │ payload validado / User da sessão (g)
                       ┌───────────────▼──────────────────────────────────┐
                       │  CONTROLLER (controllers/*_controller.py)        │
                       │  ├─ autorização de domínio (user_authz.py)       │
                       │  ├─ P3: com database.transaction(): add/delete   │
                       │  ├─ P4: status_counts() / agregações GROUP BY    │
                       │  └─ P5: nullify + delete na mesma transação      │
                       └───────┬──────────────────────────┬───────────────┘
                               │ ORM moderno (P8)         │ efeitos colaterais
                       ┌───────▼──────────────┐  ┌────────▼───────────────┐
                       │  MODEL (models/)     │  │  SERVICE (services/)   │
                       │  to_dict, is_overdue │  │  NotificationService   │
                       │  ← utils/time.py (P8)│  └────────────────────────┘
                       └──────────────────────┘
        Transversais:  middlewares/auth.py (P1) · middlewares/error_handler.py (P3: rollback)
                       config/settings.py (P2: WEAK_SECRETS/constantes) · app.py (P2: fail-fast)
                       database.py (P3: transaction()) · requirements.txt (P8: deps explícitas)
```

---

## 3. Os 8 Padrões de Transformação

### P1 — Guard de autenticação obrigatório no edge
**Diagnóstico:** *Fake Authentication / Broken Access Control* (**CRITICAL**, catálogo §2.4).
`AuthController.verify_token()` (controllers/auth_controller.py:18-25) não era referenciado por ninguém;
nenhum blueprint exigia credencial. Matriz de roles (`user`/`manager`/`admin`) persistida mas inerte.

**Estratégia:** criar um middleware de autorização decorativo (camada View/middleware) que resolve o
usuário da sessão para `flask.g` e delega regras de propriedade ao Controller (que conhece domínio, não HTTP).

**Antes** (`controllers/auth_controller.py` — verificador órfão; `views/user_views.py` — rota aberta):
```python
class AuthController:
    @classmethod
    def verify_token(cls, token):        # nunca chamado por nenhuma rota
        ...
        return payload.get('user_id')

@user_bp.route('/users', methods=['GET'])
def get_users():                          # qualquer cliente lista PII
    return jsonify(UserController.list_users()), 200

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):                 # destruição sem credencial alguma
    return jsonify(UserController.delete_user(user_id)), 200
```

**Depois** (`middlewares/auth.py` novo + views protegidas):
```python
def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = AuthController.verify_token(_extract_bearer_token())
        user = db.session.get(User, user_id)
        if not user or not user.active:
            raise AppError('Sessao invalida ou encerrada', 401)
        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @token_required
        def wrapper(*args, **kwargs):
            if g.current_user.role not in roles:
                raise AppError('Permissao insuficiente', 403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
```
```python
@user_bp.route('/users', methods=['GET'])
@role_required(Settings.ROLE_ADMIN)
def get_users():
    ...

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@role_required(Settings.ROLE_ADMIN)
def delete_user(user_id):
    ...

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(user_id):                 # regra self-or-admin vive no controller
    payload = UserUpdateSchema().load(request.get_json() or {})
    data = UserController.update_user(user_id, payload, g.current_user)
    return jsonify(user_schema.dump(data)), 200
```
`controllers/user_authz.py` concentra a regra de negócio de acesso:
```python
def ensure_can_modify(user_id, actor, changing_role=False):
    if changing_role and not actor.is_admin():
        raise AppError('Apenas administradores podem alterar roles', 403)
    if actor.id != user_id and not actor.is_admin():
        raise AppError('Acesso negado: edite apenas o seu próprio cadastro', 403)
```
**Regra replicável:** o edge (View) *autentica* (quem é?), o Controller *autoriza casos de uso*
(pode este recurso?). Nenhum decorator de rota existe sem guard, exceto a whitelist pública
(`GET /`, `GET /health`, `POST /login`, `POST /users`).

---

### P2 — Segredo com fail-fast em produção
**Diagnóstico:** *Hardcoded/Weak Secret* (**CRITICAL**, catálogo §2.1). O fallback
`SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')` permitia forjar tokens com a chave
pública do repositório — comprovado: `URLSafeTimedSerializer('change-me-in-production', salt=...)`
desserializava `{'user_id': 1}` forjado.

**Estratégia:** Config sem default de segredo; a Composition Root decide o comportamento por ambiente —
recusa total em produção, chave efêmera em memória com warning explícito apenas em DEBUG/TESTS.

**Antes** (`config/settings.py:8` + `controllers/auth_controller.py:11`):
```python
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')   # default público
...
return URLSafeTimedSerializer(Settings.SECRET_KEY, salt='task-manager-auth')
```

**Depois** (`config/settings.py`, `app.py`, `controllers/auth_controller.py`):
```python
WEAK_SECRETS = frozenset({'', 'change-me-in-production', 'dev-secret-key-change-in-prod'})
SECRET_KEY = os.getenv('SECRET_KEY')          # sem default

def _configure_secret(app):
    secret = app.config.get('SECRET_KEY')
    if secret and secret not in Settings.WEAK_SECRETS:
        return
    if Settings.DEBUG or app.config.get('TESTING'):
        app.config['SECRET_KEY'] = secrets.token_urlsafe(48)
        logger.warning('SECRET_KEY ausente ou fraca; usando chave efemera ...')
        return
    raise RuntimeError('SECRET_KEY forte e obrigatoria em producao. ...')

# AuthController assina com o segredo DO APP (não o import estático):
return URLSafeTimedSerializer(current_app.secret_key, salt=Settings.AUTH_TOKEN_SALT)
```
**Regra replicável:** segredo nunca tem default utilizável; ambientes que precisam de conveniência
(DEBUG) ganham *efemeridade* + *warning*, jamais reuso de valor conhecido; o consumer do segredo lê
`current_app`, nunca o módulo de settings.

---

### P3 — Contexto transacional ACID em toda escrita
**Diagnóstico:** *Missing Transaction Boundaries* (**HIGH**, catálogo §3.3). Todo fluxo usava
`db.session.commit()` avulso; um `IntegrityError` deixava a sessão suja e o handler global respondia
409 sem `rollback()`, contaminando as próximas requisições do worker.

**Estratégia:** um context-manager no infra (`database.py`) como única porta de escrita; handlers
globais de erro completam a última linha de defesa com rollback.

**Antes** (`controllers/user_controller.py`):
```python
db.session.add(user)
db.session.commit()          # sem proteção; exceção -> sessão suja
return user.to_dict(), 201

with ... nada ...
Task.query.filter_by(user_id=user_id).delete()
db.session.delete(user)
db.session.commit()          # 2 operações multi-tabela sem limite atômico declarado
```
```python
@app.errorhandler(IntegrityError)
def handle_integrity_error(error):
    logger.exception('Integrity error')          # rollback ausente
    return jsonify({'error': 'Conflito de dados'}), 409
```

**Depois** (`database.py` + controllers + `middlewares/error_handler.py`):
```python
@contextmanager
def transaction():
    """Commit on success; rollback on any exception (domain AppError or DB error)."""
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
```
```python
with transaction():
    db.session.add(user)
# ...
with transaction():
    Task.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
```
```python
@app.errorhandler(IntegrityError)
def handle_integrity_error(error):
    db.session.rollback()            # última linha de defesa
    logger.exception('Integrity error')
    return jsonify({'error': 'Conflito de dados'}), 409
```
**Regra replicável:** `commit()` cru é proibido por convenção (AGENTS.md); a transação é o bloco
`with` do caso de uso — regras de negócio que lançam `AppError` dentro do bloco participam do rollback.

---

### P4 — Agregação SQL única contra N+1 e full-table loads
**Diagnóstico:** *N+1 Query Problem* (**HIGH**, catálogo §3.1). Quatro focos: `list_users`
(`len(self.tasks)` por linha), `list_categories` (COUNT por linha), `ReportController.summary`
(tabela tasks inteira + uma query de tasks por usuário no loop), `TaskController.stats`
(`Task.query.all()` só para contar atrasadas).

**Estratégia:** mover contagem/filtragem para o banco (`GROUP BY`, `OUTER JOIN`, `case`, predicado
SQL de atraso derivado da mesma regra do modelo) e deixar o Python apenas com projeção da resposta.

**Antes** (`controllers/user_controller.py:9-11`, `models/user.py:32-33`):
```python
users = User.query.all()
return [user.to_dict(include_task_count=True) for user in users]
# to_dict: data['task_count'] = len(self.tasks)  -> lazy-load 1+N
```
```python
# controllers/category_controller.py — um COUNT por categoria
return [category.to_dict(task_count=Task.query.filter_by(category_id=category.id).count())
        for category in categories]
```
```python
# controllers/report_controller.py — tasks inteiro + loop de queries
for task in Task.query.all():
    if task.is_overdue(): ...
for user in User.query.all():
    user_tasks = Task.query.filter_by(user_id=user.id).all()
    completed = sum(1 for task in user_tasks if task.status == 'done')
```
```python
# controllers/task_controller.py
overdue_count = sum(1 for task in Task.query.all() if task.is_overdue())
```

**Depois:**
```python
# list_users: 1 GROUP BY + paginação
counts = dict(db.session.query(Task.user_id, func.count(Task.id))
              .group_by(Task.user_id).all())
pagination = User.query.order_by(User.id).paginate(page=page, per_page=per_page, error_out=False)
return {'items': [u.to_dict(task_count=counts.get(u.id, 0)) for u in pagination.items], ...}

# list_categories: 1 OUTER JOIN
rows = (db.session.query(Category, func.count(Task.id))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id).order_by(Category.id).all())

# stats(): contagem por status em 1 GROUP BY; atrasadas por predicado SQL único
@staticmethod
def _overdue_filter():
    return (Task.due_date.isnot(None),
            Task.due_date < utcnow(),
            Task.status.notin_(Settings.NON_OVERDUE_STATUSES))

# user_productivity do relatório: 1 join agregado com case()
db.session.query(User.id, User.name, func.count(Task.id),
                 func.sum(case((Task.status == Settings.STATUS_DONE, 1), else_=0))) \
  .outerjoin(Task, Task.user_id == User.id).group_by(User.id, User.name)
```
O `Model.to_dict(task_count=None)` recebe a contagem de fora — a relação deixa de ser carregada
para contar. **Regra replicável:** contagem/filtro pertencem ao SQL; a entidade apenas formata o que
já foi agregado; o predicado SQL e o método de domínio compartilham as mesmas constantes (`Settings.NON_OVERDUE_STATUSES`),
validado por teste de consistência (stats == is_overdue).

---

### P5 — Integridade referencial coordenada no delete
**Diagnóstico:** *Orphan Records* (**HIGH**, catálogo §3.4). `delete_category` removia a linha pai e
deixava `tasks.category_id` apontando para categoria inexistente (SQLite não impõe FK por default) —
enquanto `delete_user` já tinha cuidado manual, provando a inconsistência.

**Estratégia:** exclusão coordenada na camada Controller dentro de UMA transação: desvincular
filhos (`SET NULL`) e então apagar o pai.

**Antes** (`controllers/category_controller.py:43-51`):
```python
category = Category.query.get(category_id)
if not category:
    raise AppError('Categoria não encontrada', 404)
db.session.delete(category)
db.session.commit()        # tasks permanecem com category_id órfão
```

**Depois:**
```python
with transaction():
    category = db.session.get(Category, category_id)
    if not category:
        raise AppError('Categoria não encontrada', 404)
    Task.query.filter_by(category_id=category_id).update(
        {Task.category_id: None}, synchronize_session=False
    )
    db.session.delete(category)
```
**Regra replicável:** onde o banco não garante cascade (SQLite/legado), o caso de uso garante —
toda destruição de pai declara explicitamente o destino dos filhos, no mesmo limite transacional (P3).

---

### P6 — Contrato de query string via Schema
**Diagnóstico:** *Poor Error Handling* (**MEDIUM**, catálogo §5.1). `search_tasks` recebia `request.args`
cru e fazia `int(priority)` / `int(user_id)`: um `?priority=abc` derramava `ValueError` → **500**.

**Estratégia:** a View valida TODOS os parâmetros (body e query) com Marshmallow antes do Controller;
o handler central de `ValidationError` converte em 400 padronizado.

**Antes** (`views/task_views.py:37-44` + `controllers/task_controller.py:107-121`):
```python
def search_tasks():
    return jsonify(TaskController.search_tasks(
        query=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),   # str cru
        user_id=request.args.get('user_id', ''),
    )), 200

q = q.filter(Task.priority == int(priority))          # ValueError -> 500
```

**Depois** (`schemas/task_schema.py` + `schemas/common_schema.py` + view):
```python
class TaskSearchSchema(Schema):
    class Meta:
        unknown = EXCLUDE
    q = fields.Str(load_default='')
    status = fields.Str(load_default='', validate=validate.OneOf(SEARCH_STATUSES))
    priority = fields.Int(load_default=None, allow_none=True,
                          validate=validate.Range(min=Settings.MIN_PRIORITY, max=Settings.MAX_PRIORITY))
    user_id = fields.Int(load_default=None, allow_none=True)

class PaginationSchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=Settings.DEFAULT_PER_PAGE,
                          validate=validate.Range(min=1, max=Settings.MAX_PER_PAGE))
```
```python
@task_bp.route('/tasks/search', methods=['GET'])
@token_required
def search_tasks():
    filters = TaskSearchSchema().load(request.args)     # inválido -> ValidationError -> 400
    params = PaginationSchema().load(request.args)
    result = TaskController.search_tasks(query=filters['q'], ..., priority=filters['priority'])
```
O Controller agora recebe tipos coeridos e opcionais (`priority=None` significa "sem filtro") —
sem parsing defensivo dentro da camada de negócio.

---

### P7 — Schema de resposta como contrato de saída + envelope de paginação
**Diagnóstico:** *Dead Code* + *Unbounded Lists* (**MEDIUM**, catálogo §4.5). As classes
`UserResponseSchema`/`TaskResponseSchema`/`CategoryResponseSchema` eram instanciadas e exportadas
(`user_schema = UserResponseSchema()`) porém **jamais usadas** — a resposta era `to_dict()` cru,
e `GET /tasks`/`GET /users` devolviam a tabela inteira (dívida confessada no próprio seed:
*"Endpoints retornam todos os registros"*).

**Estratégia:** o Response Schema passa a ser o ponto de serialização efetivo na View (contrato
explícito do payload público) e as listes adotam envelope paginado estável.

**Antes** (`views/user_views.py` + `controllers/user_controller.py`):
```python
@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(UserController.list_users()), 200      # lista crua, schema morto
...
def get_user_tasks(user_id):                               # dicionario manual duplicando Task.to_dict
    return [{'id': task.id, 'title': task.title, 'description': task.description, ...}
            for task in tasks]
```

**Depois** (`views/user_views.py` + `controllers/user_controller.py`):
```python
@user_bp.route('/users', methods=['GET'])
@role_required(Settings.ROLE_ADMIN)
def get_users():
    params = PaginationSchema().load(request.args)
    result = UserController.list_users(page=params['page'], per_page=params['per_page'])
    result['items'] = users_schema.dump(result['items'])   # contrato de saída aplicado
    return jsonify(result), 200
# GET /users/<id>/tasks:
return jsonify(tasks_schema.dump(UserController.get_user_tasks(user_id, g.current_user))), 200

# get_user_tasks agora delega ao dono dos dados:
tasks = Task.query.filter_by(user_id=user_id).all()
return [task.to_dict() for task in tasks]
```
Envelope padronizado de lista:
```json
{ "items": [ ... ], "page": 1, "per_page": 20, "total": 42, "pages": 3 }
```
**Regra replicável:** duas fontes de verdade de serialização são uma a mais — ou o Model `to_dict`
alimenta o Schema de resposta na borda (como aqui), ou o Schema elimina o `to_dict`; código morto
de "contrato" é corrigido ligando-o, não deletando-o às cegas.

---

### P8 — Fonte única de regra, ORM moderno e dependências declaradas
**Diagnóstico (agregado):**
- *Shotgun Surgery/Duplicated Code* (**MEDIUM**, §4.1/§4.2): `utcnow()` definido 3× (models), o ajuste
  naive→UTC de `due_date` duplicado no Model e no relatório, contagens por status em 2 controllers.
- *Deprecated APIs* (**LOW**, §4.6): 11× `Model.query.get()` emitindo `LegacyAPIWarning` (SQLAlchemy 2.0).
- *Magic Numbers* (**LOW**, §4.7): `'pending'`, `3`, `'user'`, `'#000000'`, `priority <= 2` repetindo `Settings`.
- *Phantom/Undeclared Dependencies* (**MEDIUM**, §4.5): `itsdangerous` e `sqlalchemy` importados
  diretamente sem constar em `requirements.txt` (dependiam de transitividade do Flask).

**Antes:**
```python
# models/user.py:8-9 == models/task.py:6-7 == models/category.py:6-7
def utcnow():
    return datetime.now(timezone.utc)

# models/task.py:62-64 duplicado em report_controller.py:34-36
due = self.due_date
if due.tzinfo is None:
    due = due.replace(tzinfo=timezone.utc)

user = User.query.get(user_id)                 # LegacyAPIWarning

status=payload.get('status', 'pending'),       # literal repetido
priority=payload.get('priority', 3),           # Settings.DEFAULT_PRIORITY existe
high_priority = sum(1 for task in tasks if task.priority <= 2)   # 2 solto

# requirements.txt — sem itsdangerous/SQLAlchemy apesar de `from itsdangerous import ...`
```
Trecho morto simultâneo: `@pre_load def normalize_tags(self, data, **kwargs): return data`
e os validadores `Task.validate_status/validate_priority` nunca chamados (já cobertos pelos Schemas).

**Depois:**
```python
# utils/time.py — ÚNICA fonte
def utcnow(): return datetime.now(timezone.utc)
def as_utc(value): ...

# models/task.py — regra única do domínio, sem cópia do ajuste tz
def is_overdue(self):
    if not self.due_date or self.status in Settings.NON_OVERDUE_STATUSES:
        return False
    return as_utc(self.due_date) < utcnow()

# controllers: ORM moderno + predicado compartilhado + constantes
task = db.session.get(Task, task_id)
counts = {status: rows.get(status, 0) for status in Settings.VALID_STATUSES}  # status_counts() único
Task.query.filter(Task.user_id == user_id, Task.priority <= Settings.HIGH_PRIORITY_MAX).count()
```
```text
# requirements.txt
sqlalchemy==2.0.51
itsdangerous==2.2.0
```
Removidos: `validate_status`/`validate_priority` (Model), `format_date`/`is_valid_color` (helpers),
`notify_task_overdue` (service), `pre_load` no-op (schema).
**Regra replicável:** tempo/calendário, predicados de domínio e limites pertencem a um único módulo
importável; imports diretos de bibliotecas exigem declaração própria; validação vive em UMA camada
por tipo de fronteira (entrada → Schema; consistência → Model).

---

## 4. Guia de Execução Passo a Passo (replicável em qualquer API Flask/SQLAlchemy)

1. **Audite o enforcement, não só a estrutura** — rode a aplicação e prove cada política:
   `GET /recurso` sem token deveria ser 401; se for 200, o MVC é decorativo.
2. **Fixe segredos primeiro (P2)** — remova defaults; fail-fast em produção, efemeridade em DEBUG.
3. **Crie o guard de auth no edge (P1)** — `token_required`/`role_required` + whitelist pública mínima;
   regras de propriedade no Controller.
4. **Centralize transações (P3)** — `transaction()` como única porta de escrita + rollback nos
   handlers de erro global.
5. **Elimine N+1 (P4)** — substitua loops de contagem por `GROUP BY`/`OUTER JOIN`/`case`; mantenha
   paridade com o método de domínio via constantes compartilhadas.
6. **Coordinate deletes de pai (P5)** — NULL/cascade explícito dentro da transação.
7. **Valide a borda toda com Schema (P6)** — body **e** query string; erro de cliente nunca vaza 500.
8. **Ligue os contratos de saída (P7)** — ResponseSchemas no lugar de dicionários avulsos; adote
   envelope paginado.
9. **Faxina final (P8)** — fonte única de tempo/regra, `session.get()` contra legado, constantes,
   dependências explícitas, código morto removido.
10. **Valide com `warnings.simplefilter('error')`** — deprecation silenciosa vira falha de build, e
    rode suíte smoke cobrindo 401/403/400/409/200/201/404 por papel (user/manager/admin).

---

## 5. Validação Final

- Smoke suite completa (50+ asserções) **passando com warnings=error** — zero `LegacyAPIWarning`.
- `seed.py` populando 3 usuários / 4 categorias / 10 tasks; relatórios consistentes com `is_overdue`.
- Tokens forjados com segredo fraco rejeitados; produção recusa boot sem `SECRET_KEY` forte.
- `docs/project_refactored.txt` — inventário das mudanças por camada;
  `docs/project_issues.txt` — 12 findings com file:line da auditoria.
