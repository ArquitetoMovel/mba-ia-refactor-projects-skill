# Playbook de Refatoração Arquitetural

Este playbook registra a transformação do `code-smells-project` de um módulo
Flask monolítico para MVC em camadas com Service Layer. Os exemplos **Antes**
foram extraídos do snapshot legado `6d1ce62`; os exemplos **Depois** foram
extraídos da árvore final e usam linhas 1-indexed.

## Sumário Executivo

| # | Padrão de transformação | Anti-pattern tratado | Severidade | Camadas afetadas | Estado |
|---|---|---|---|---|---|
| 1 | Decomposição do módulo monolítico em MVC | God Module / Lack of Separation of Concerns | CRITICAL/HIGH | views, controllers, services, models | Aplicado |
| 2 | Configuração segura orientada a ambiente | Hardcoded Secrets / Insecure CORS | CRITICAL/MEDIUM | config, db, app | Aplicado |
| 3 | Hash seguro e mapeamento sem senha | Insecure Cryptography / Sensitive Data Exposure | CRITICAL | db, services, models | Aplicado |
| 4 | Autenticação assinada e autorização por papel | Fake Authentication / Broken Access Control / SQL admin | CRITICAL | middleware, services, controllers, views | Aplicado |
| 5 | Unidade transacional e reserva atômica | Non-atomic Write / Tight Coupling / Silent Failure | HIGH/MEDIUM | services, models | Aplicado |
| 6 | Lifecycle da conexão e carga em lote | Global State / Connection Leakage / N+1 | HIGH | db, models | Aplicado |
| 7 | Políticas de domínio e DTOs | Shotgun Surgery / Long Method / Primitive Obsession | HIGH/MEDIUM | domain, schemas, services | Aplicado |
| 8 | Erros e logging centralizados | Poor Error Handling / Print Logging | MEDIUM | middleware, entrypoint | Aplicado |

## Arquitetura MVC Alvo

```text
HTTP client
    |
    v
View: src/views/routes.py
    |  registro de URLs
    v
Controller: src/controllers/
    |  request, auth, resposta HTTP
    v
Schema: src/schemas/payloads.py
    |  DTO e validação de entrada
    v
Service: src/services/
    |  caso de uso, regras e transação
    v
Model: src/models/
    |  SQL parametrizado e mappers
    v
Database: src/db/database.py
    |  conexão em Flask g e DDL
    v
SQLite: loja.db

Transversal: src/middlewares/auth.py + error_handler.py
Domínio: src/domain/pedido.py
Configuração: src/config/settings.py
```

## Padrões de Transformação

### 1. Decomposição do Módulo Monolítico em MVC

#### Diagnóstico e contexto

- **Anti-pattern:** God Module, God Routes e falta de separação de responsabilidades.
- **Severidade padrão:** CRITICAL para o módulo que acumulava todo o ciclo;
  HIGH para a violação de camadas.
- **Antes:** o entrypoint registrava as rotas e os handlers misturavam request,
  validação, Model e resposta (`6d1ce62/app.py:11-30`,
  `6d1ce62/controllers.py:24-62`).

#### Estratégia arquitetural

- View registra somente URL e método HTTP.
- Controller adapta request, chama o caso de uso e cria a resposta.
- Schema valida payloads sem conhecer o banco.
- Service concentra regras e transações.
- Model concentra SQL e mapeamento.

#### Antes e Depois

```python
# ANTES - 6d1ce62/app.py:11-16
app.add_url_rule("/produtos", "criar_produto", controllers.criar_produto,
                 methods=["POST"])

# ANTES - 6d1ce62/controllers.py:24-62
def criar_produto():
    dados = request.get_json()
    # validação, categorias, models.criar_produto e resposta no mesmo handler
```

```python
# DEPOIS - src/views/routes.py:40-45
app.add_url_rule(
    "/produtos",
    "criar_produto",
    produto_controller.criar_produto,
    methods=["POST"],
)

# DEPOIS - src/controllers/produto_controller.py:23-28
@require_roles("admin")
def criar_produto():
    produto_id = produto_service().criar(request.get_json(silent=True))
    return jsonify(
        {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}
    ), 201
```

### 2. Configuração Segura Orientada a Ambiente

#### Diagnóstico e contexto

- **Anti-pattern:** Hardcoded Secrets e política CORS global.
- **Severidade padrão:** CRITICAL para segredos; MEDIUM para CORS permissivo.
- **Antes:** `SECRET_KEY`, debug, bind e CORS eram definidos diretamente no
  app (`6d1ce62/app.py:6-9`). Credenciais também eram fixas no seed
  (`6d1ce62/database.py:75-83`).

#### Estratégia arquitetural

- `Settings` imutável é o único ponto de leitura de ambiente.
- Produção falha se `SECRET_KEY` não tiver pelo menos 32 caracteres.
- Desenvolvimento usa chave aleatória por processo, nunca um literal conhecido.
- Senhas de seed são opcionais e fornecidas por `SEED_*_PASSWORD`.
- CORS só é inicializado quando `CORS_ORIGINS` contém origens explícitas.

#### Antes e Depois

```python
# ANTES - 6d1ce62/app.py:6-9
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
CORS(app)
```

```python
# DEPOIS - src/config/settings.py:87-105
def load_settings() -> Settings:
    ambiente = os.environ.get("AMBIENTE", "desenvolvimento").strip().lower()
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    secret_key = os.environ.get("SECRET_KEY", "").strip()
    if ambiente in PRODUCTION_ENVIRONMENTS and len(secret_key) < 32:
        raise RuntimeError("SECRET_KEY deve ter pelo menos 32 caracteres em produção")
    if not secret_key:
        secret_key = secrets.token_urlsafe(32)

    return Settings(
        secret_key=secret_key,
        debug=debug,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5003")),
        db_path=os.environ.get("DB_PATH", "loja.db"),
        ambiente=ambiente,
        admin_token=os.environ.get("ADMIN_TOKEN", "").strip() or None,
        token_max_age_seconds=_load_positive_int("AUTH_TOKEN_MAX_AGE_SECONDS", "86400"),
        cors_origins=_load_cors_origins(),
        seed_users=_load_seed_users(),
    )

# DEPOIS - src/app.py:24-28
app = Flask(__name__)
app.config["SECRET_KEY"] = settings.secret_key
app.config["DEBUG"] = settings.debug
if settings.cors_origins:
    CORS(app, origins=list(settings.cors_origins))
```

### 3. Hash Seguro e Mapeamento sem Senha

#### Diagnóstico e contexto

- **Anti-pattern:** Insecure Cryptography e Sensitive Data Exposure.
- **Severidade padrão:** CRITICAL.
- **Antes:** seed persistia senha em texto e o mapper retornava `senha`
  (`6d1ce62/database.py:75-83`, `6d1ce62/models.py:79-86`).

#### Estratégia arquitetural

- Service/seed transforma a senha com `generate_password_hash`.
- Login usa `check_password_hash` somente no fluxo interno.
- Mapper público omite `senha`; o hash só é incluído na busca interna por email.

#### Antes e Depois

```python
# ANTES - 6d1ce62/database.py:75-83
usuarios = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
]
cursor.executemany(
    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
    usuarios,
)

# ANTES - 6d1ce62/models.py:79-86
"senha": row["senha"],
```

```python
# DEPOIS - src/db/database.py:111-119
user_count = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
if user_count == 0 and seed_users:
    hashed_users = [
        (name, email, generate_password_hash(password), role)
        for name, email, password, role in seed_users
    ]
    conn.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        hashed_users,
    )

# DEPOIS - src/models/mappers.py:22-32
def usuario_from_row(row: Row, *, include_senha: bool = False) -> dict[str, Any]:
    data = {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }
    if include_senha:
        data["senha"] = row["senha"]
    return data
```

### 4. Autenticação Assinada e Autorização por Papel

#### Diagnóstico e contexto

- **Anti-pattern:** Fake Authentication e Broken Access Control; endpoint de
  SQL administrativo arbitrário.
- **Severidade padrão:** CRITICAL.
- **Antes:** `/login` verificava credenciais sem criar sessão e as rotas não
  validavam identidade. `/admin/query` executava SQL recebido do cliente
  (`6d1ce62/controllers.py:237-255`, `6d1ce62/app.py:59-78`).

#### Estratégia arquitetural

- `AuthService` assina payload mínimo com `URLSafeTimedSerializer`.
- Middleware extrai Bearer, valida expiração e recarrega o usuário no banco.
- O papel é consultado no banco, não confiado no token.
- Decorators de controller aplicam `require_auth` ou `require_roles`.
- Endpoint arbitrário é removido; reset usa token administrativo de ambiente.

#### Antes e Depois

```python
# ANTES - 6d1ce62/app.py:59-78
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)

# ANTES - 6d1ce62/controllers.py:237-255
def login():
    usuario = models.login_usuario(email, senha)
    return jsonify({"dados": usuario, "sucesso": True}), 200
```

```python
# DEPOIS - src/services/auth_service.py:22-39
def criar_token(self, usuario_id: int) -> str:
    return self._serializer.dumps({"usuario_id": usuario_id})

def usuario_do_token(self, token: str) -> dict[str, object]:
    try:
        payload = self._serializer.loads(token, max_age=self._max_age_seconds)
    except BadData as exc:
        raise UnauthorizedError("Token inválido ou expirado") from exc
    if not isinstance(payload, dict):
        raise UnauthorizedError("Token inválido ou expirado")
    usuario_id = payload.get("usuario_id")
    if not isinstance(usuario_id, int) or isinstance(usuario_id, bool):
        raise UnauthorizedError("Token inválido ou expirado")
    usuario = self._model.buscar_por_id(usuario_id)
    if not usuario:
        raise UnauthorizedError("Usuário não encontrado")
    return usuario

# DEPOIS - src/controllers/usuario_controller.py:12-15
@require_roles("admin")
def listar_usuarios():
    usuarios = usuario_service().listar()
    return jsonify({"dados": usuarios, "sucesso": True}), 200

# DEPOIS - src/views/routes.py:111-117
app.add_url_rule(
    "/admin/reset-db", "reset_database", health_controller.reset_database,
    methods=["POST"],
)
```

### 5. Unidade Transacional e Reserva Atômica

#### Diagnóstico e contexto

- **Anti-pattern:** Non-atomic Write, Tight Coupling e Silent Failure.
- **Severidade padrão:** HIGH para consistência concorrente; MEDIUM para status
  inexistente reportado como sucesso.
- **Antes:** `criar_pedido` validava e decrementava em passos independentes,
  com possibilidade de itens duplicados e estoque negativo
  (`6d1ce62/models.py:133-169`). O update de status não verificava `rowcount`.

#### Estratégia arquitetural

- Service abre `BEGIN IMMEDIATE`, prepara todas as linhas e controla rollback.
- Model reserva com `UPDATE ... WHERE estoque >= ?` e retorna sucesso por
  `rowcount`.
- Quantidades do mesmo produto são agregadas antes da validação.
- Status consulta a existência, aplica a transição e repõe estoque ao cancelar.
- Models não confirmam automaticamente CRUD; o Service confirma o caso de uso.

#### Antes e Depois

```python
# ANTES - 6d1ce62/models.py:137-169
for item in itens:
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
cursor.execute("UPDATE produtos SET estoque = estoque - " + str(item["quantidade"]))
db.commit()
```

```python
# DEPOIS - src/services/pedido_service.py:35-49
try:
    self._model.iniciar_transacao()
    if not self._model.usuario_existe(payload.usuario_id):
        raise DomainError("Usuário não encontrado")
    linhas, total = self._preparar_linhas(payload)
    pedido_id = self._model.criar(payload.usuario_id, total)
    for produto_id, quantidade, preco in linhas:
        if not self._model.reservar_estoque(produto_id, quantidade):
            raise DomainError("Estoque insuficiente para o produto solicitado")
        self._model.adicionar_item(pedido_id, produto_id, quantidade, preco)
    self._model.commit()
except Exception:
    self._model.rollback()
    raise

# DEPOIS - src/models/pedido_model.py:77-83
cursor = self._db.execute(
    "UPDATE produtos SET estoque = estoque - ? "
    "WHERE id = ? AND estoque >= ?",
    (quantidade, produto_id, quantidade),
)
return cursor.rowcount == 1
```

### 6. Lifecycle da Conexão e Carga em Lote

#### Diagnóstico e contexto

- **Anti-pattern:** Global Mutable State, conexão sem escopo e N+1 Query.
- **Severidade padrão:** HIGH.
- **Antes:** uma conexão global usava `check_same_thread=False`
  (`6d1ce62/database.py:4-12`); cada pedido e item disparava queries adicionais
  (`6d1ce62/models.py:187-199`).

#### Estratégia arquitetural

- `get_db()` cria uma conexão por contexto Flask e `close_db()` fecha no teardown.
- Models recebem a conexão por injeção.
- Pedidos são carregados uma vez; itens e produtos são buscados em uma consulta
  com `LEFT JOIN` e associados em memória.

#### Antes e Depois

```python
# ANTES - 6d1ce62/database.py:4-12
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection

# ANTES - 6d1ce62/models.py:187-199
for row in rows:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

```python
# DEPOIS - src/db/database.py:21-34
def get_db() -> sqlite3.Connection:
    if "db" not in g:
        settings = get_settings()
        conn = sqlite3.connect(settings.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db

def close_db(_: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()

# DEPOIS - src/models/pedido_model.py:26-46
pedidos = {row["id"]: pedido_from_row(row) for row in rows}
placeholders = ",".join("?" * len(pedidos))
itens_sql = f"""
    SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
           p.nome AS produto_nome
    FROM itens_pedido i
    LEFT JOIN produtos p ON p.id = i.produto_id
    WHERE i.pedido_id IN ({placeholders})
    ORDER BY i.id
"""
item_rows = self._db.execute(itens_sql, tuple(pedidos.keys())).fetchall()
for item in item_rows:
    pedidos[item["pedido_id"]]["itens"].append(
        {
            "produto_id": item["produto_id"],
            "produto_nome": item["produto_nome"] or "Desconhecido",
            "quantidade": item["quantidade"],
            "preco_unitario": item["preco_unitario"],
        }
    )
```

### 7. Políticas de Domínio e DTOs

#### Diagnóstico e contexto

- **Anti-pattern:** Shotgun Surgery, regra duplicada, Long Method e Primitive
  Obsession.
- **Severidade padrão:** HIGH para política espalhada; MEDIUM para método longo
  e validações ad hoc.
- **Antes:** estados e validações apareciam em controllers, Models e Services;
  `criar_pedido` fazia parsing, cálculo, persistência e efeitos laterais no mesmo
  método (`6d1ce62/models.py:133-169`).

#### Estratégia arquitetural

- Enum e transições vivem em `src/domain/pedido.py`.
- DTOs imutáveis validam tipos, limites, email, status e filtros.
- Services recebem payloads já tipados e mantêm apenas regras do caso de uso.
- Relatório e notificações reutilizam a política de status e não repetem literais.

#### Antes e Depois

```python
# ANTES - 6d1ce62/controllers.py:188-220
dados = request.get_json()
usuario_id = dados.get("usuario_id")
itens = dados.get("itens", [])
if not itens or len(itens) == 0:
    return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400
resultado = models.criar_pedido(usuario_id, itens)
```

```python
# DEPOIS - src/domain/pedido.py:8-35
class StatusPedido(StrEnum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"

def transicao_permitida(status_atual: str, novo_status: str) -> bool:
    return novo_status in TRANSICOES_PEDIDO.get(status_atual, frozenset())

# DEPOIS - src/schemas/payloads.py:160-172
@dataclass(frozen=True)
class PedidoPayload:
    usuario_id: int
    itens: tuple[PedidoItemPayload, ...]

    @classmethod
    def from_mapping(cls, value: Any) -> PedidoPayload:
        data = _mapping(value)
        usuario_id = _positive_int(data.get("usuario_id"), "Usuario ID")
        raw_items = data.get("itens")
        if not isinstance(raw_items, (list, tuple)) or not raw_items:
            raise SchemaError("Pedido deve ter pelo menos 1 item")
        return cls(usuario_id, tuple(PedidoItemPayload.from_mapping(item) for item in raw_items))
```

### 8. Erros e Logging Centralizados

#### Diagnóstico e contexto

- **Anti-pattern:** Poor Error Handling, Silent Failures e Print Logging.
- **Severidade padrão:** MEDIUM.
- **Antes:** handlers capturavam `Exception`, imprimiam a exceção e devolviam
  texto cru (`6d1ce62/controllers.py:5-12`); o entrypoint também usava `print`
  (`6d1ce62/app.py:82-88`).

#### Estratégia arquitetural

- Erros de domínio carregam status HTTP sem conhecer Flask.
- Middleware produz envelopes JSON para domínio, HTTP, conflitos e 500.
- Logs usam `logging.getLogger(__name__)` e não expõem senhas ou tokens.
- Entrypoint registra lifecycle com logger.

#### Antes e Depois

```python
# ANTES - 6d1ce62/controllers.py:5-12
try:
    produtos = models.get_todos_produtos()
    print("Listando " + str(len(produtos)) + " produtos")
except Exception as e:
    print("ERRO: " + str(e))
    return jsonify({"erro": str(e)}), 500
```

```python
# DEPOIS - src/middlewares/error_handler.py:16-35
@app.errorhandler(DomainError)
def handle_domain_error(exc: DomainError):
    payload = {"erro": exc.message, "sucesso": False}
    return jsonify(payload), exc.status_code

@app.errorhandler(HTTPException)
def handle_http_error(exc: HTTPException):
    payload = {"erro": exc.description, "sucesso": False}
    return jsonify(payload), exc.code or 500

@app.errorhandler(Exception)
def handle_unexpected(exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500

# DEPOIS - app.py:17-19
if __name__ == "__main__":
    logger.info("Servidor iniciado em http://%s:%s", settings.host, settings.port)
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
```

## Guia Prático de Execução

1. Fazer uma leitura de stack e mapear o fluxo HTTP, persistência, dependências e
   tabelas antes de alterar o código.
2. Registrar cada achado com severidade, arquivo e intervalo de linhas no relatório
   da Fase 2; separar problemas históricos de problemas já corrigidos.
3. Criar o composition root e separar View, Controller, Schema, Service e Model,
   preservando paths e envelopes JSON.
4. Centralizar ambiente e segredos; falhar explicitamente em produção e não
   semear usuários sem senhas fornecidas por ambiente/teste.
5. Aplicar hashing, mappers públicos e autenticação assinada; proteger cada
   operação por identidade e papel e remover execução arbitrária de SQL.
6. Mover a unidade de trabalho para o Service, usar SQL condicional para estoque,
   tratar rollback e conferir `rowcount` para updates.
7. Colocar políticas compartilhadas no domínio, extrair DTOs e eliminar loops
   N+1 com JOIN/batch loading.
8. Normalizar erros e logging; retirar `print()` do código executável e restringir
   CORS às origens configuradas.
9. Executar testes unitários/integração, Ruff, lockfile e smoke checks; atualizar
   `README.md`, `AGENTS.md` e este playbook com linhas finais.

## Validação Final

- `.venv/bin/python -m pytest -q`: `17 passed`.
- `.venv/bin/ruff check .`: clean.
- `uv lock --check`: clean.
- `git diff --check`: clean.
- Nenhum uso executável encontrado de `datetime.utcnow()`, `Flask.__version__`,
  `hashlib.md5()` ou `hashlib.sha1()` para senhas.
