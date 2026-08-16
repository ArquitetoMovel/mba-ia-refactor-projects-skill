# Playbook de Refatoração Arquitetural: Padrões de Transformação MVC

- **Análise do Commit:** `aa713e38ab7b3f7e05cfd2ded12437e9c1ad11f9`
- **Mensagem do Commit:** `task-manager-api refactored and fix the findings`
- **Escopo da Refatoração:** 48 arquivos alterados (+1.696 / -1.025 linhas), migração de rotas monolíticas (God Routes) para arquitetura em camadas MVC (Model-View-Controller) com validação por Schemas (Marshmallow), injeção de configurações seguras (12-Factor App) e observabilidade padronizada.

---

## Sumário Executivo dos 8 Padrões de Transformação

| # | Padrão de Transformação | Anti-Pattern / Code Smell Mitigado | Severidade | Camadas Afetadas |
|---|-------------------------|------------------------------------|------------|------------------|
| 1 | Decomposição de God Routes em Camadas MVC | Fat Controller / Lack of Separation of Concerns | CRITICAL | views/, controllers/, schemas/ |
| 2 | Externalização e Centralização de Configurações | Hardcoded Secrets / Configuration Drift | CRITICAL | config/settings.py, app.py |
| 3 | Criptografia Forte e Proteção de Dados Sensíveis | Insecure Crypto (MD5) & Password Leakage | CRITICAL | models/user.py, schemas/ |
| 4 | Substituição de Fake Token por Autenticação Assinada | Fake Authentication / Broken Access Control | CRITICAL | controllers/auth_controller.py |
| 5 | Eliminação de N+1 Queries via Eager Loading | N+1 Query Problem / Performance Bottleneck | HIGH | controllers/task_controller.py |
| 6 | Centralização de Regras de Domínio (Information Expert) | Shotgun Surgery / Duplicated Logic | HIGH | models/task.py, schemas/ |
| 7 | Segregação de Domínios Poluídos (Domain Extraction) | Misplaced Responsibilities / Bloated Modules | MEDIUM | views/, controllers/ |
| 8 | Tratamento Centralizado de Erros e Logging Estruturado | Silent Failures / Bare Except / Print Logging | MEDIUM | middlewares/error_handler.py |

---

## Diagrama de Fluxo da Arquitetura Alvo (MVC)

```
                            ARQUITETURA ALVO (MVC)
   
     [ HTTP Client ] 
           |
           v
    +--------------+      Validação DTO      +------------------+
    |  View / Blue | ----------------------> |  Schema (Marsh.) |
    +------+-------+                         +------------------+
           | Orquestra Caso de Uso
           v
    +--------------+      Regra / Notif      +------------------+
    |  Controller  | ----------------------> | Service (Notif.) |
    +------+-------+                         +------------------+
           | Consulta / Persistência
           v
    +--------------+      Eager Loading      +------------------+
    |  Model (ORM) | ----------------------> |   Database/DB    |
    +--------------+                         +------------------+
```

---

## Detalhamento dos 8 Padrões de Transformação

---

### Padrão 1: Decomposição de God Routes em Camadas MVC Especializadas

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** God Routes / Fat Controller (Severidade: CRITICAL).
- **Problema:** Módulos de rota (`routes/task_routes.py`, `routes/user_routes.py`) concentravam parsing de requisições HTTP, validação manual de payload, regras de negócio, transações diretas no banco de dados (`db.session`) e serialização manual de dicionários JSON.

#### 2. Estratégia de Transformação
- **View (`views/task_views.py`):** Responsável estritamente por mapear endpoints HTTP, capturar parâmetros e retornar respostas com códigos de status apropriados.
- **Schema (`schemas/task_schema.py`):** Isola validação de tipos, limites de tamanho e campos obrigatórios usando Marshmallow.
- **Controller (`controllers/task_controller.py`):** Orquestra o fluxo do caso de uso e persistência sem acoplamento a objetos de requisição HTTP diretos.

#### 3. Exemplos Antes e Depois

```python
# [ANTES] routes/task_routes.py — Mistura de HTTP, validação, query e persistência
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Título é obrigatório'}), 400
    if len(data.get('title', '')) > 200:
        return jsonify({'error': 'Título muito longo'}), 400
    
    task = Task()
    task.title = data['title']
    task.description = data.get('description', '')
    task.status = data.get('status', 'pending')
    task.priority = data.get('priority', 3)
    task.user_id = data.get('user_id')
    task.category_id = data.get('category_id')
    
    try:
        db.session.add(task)
        db.session.commit()
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao criar task'}), 500
```

```python
# [DEPOIS] views/task_views.py — View enxuta delegando para Schema e Controller
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    payload = TaskCreateSchema().load(request.get_json() or {})
    data, status = TaskController.create_task(payload)
    return jsonify(data), status

# [DEPOIS] controllers/task_controller.py — Orquestração de negócio e persistência
class TaskController:
    @classmethod
    def create_task(cls, payload):
        cls._ensure_user(payload.get('user_id'))
        cls._ensure_category(payload.get('category_id'))

        task = Task(
            title=payload['title'],
            description=payload.get('description', ''),
            status=payload.get('status', 'pending'),
            priority=payload.get('priority', 3),
            user_id=payload.get('user_id'),
            category_id=payload.get('category_id'),
            due_date=to_datetime(payload.get('due_date')),
            tags=serialize_tags(payload.get('tags')),
        )
        db.session.add(task)
        db.session.commit()

        if task.user_id and task.user:
            notification_service.notify_task_assigned(task.user, task)

        return task.to_dict(), 201
```

---

### Padrão 2: Externalização e Centralização de Configurações e Segredos

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Hardcoded Secrets & Configuration Drift (Severidade: CRITICAL).
- **Problema:** Strings com chaves de criptografia e credenciais SMTP (`super-secret-key-123`, `senha123`) embutidas diretamente no código-fonte, violando o princípio 12-Factor App (Config).

#### 2. Estratégia de Transformação
- Criação de `config/settings.py` carregando valores via `os.getenv` com fallbacks seguros para ambiente de desenvolvimento.
- Criação do arquivo de modelo `.env.example` para documentar as variáveis necessárias.

#### 3. Exemplos Antes e Depois

```python
# [ANTES] app.py e services/notification_service.py — Segredos hardcoded
app.config['SECRET_KEY'] = 'super-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'

class NotificationService:
    def __init__(self):
        self.email_user = 'taskmanager@gmail.com'
        self.email_password = 'senha123'
```

```python
# [DEPOIS] config/settings.py — Configuração centralizada e 12-Factor
import os

class Settings:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_ENABLED = os.getenv('SMTP_ENABLED', 'false').lower() in ('true', '1', 'yes')
    TOKEN_MAX_AGE_SECONDS = int(os.getenv('TOKEN_MAX_AGE_SECONDS', '86400'))

# [DEPOIS] app.py — App Factory consumindo Settings
def create_app(config=None):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = Settings.SQLALCHEMY_DATABASE_URI
    app.config['SECRET_KEY'] = Settings.SECRET_KEY
    if config:
        app.config.update(config)
    ...
    return app
```

---

### Padrão 3: Criptografia Forte de Senhas e Proteção contra Vazamento de Dados Sensíveis

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Insecure Password Hashing (MD5) & Sensitive Data Exposure (Severidade: CRITICAL).
- **Problema:** Uso de MD5 (vulnerável a ataques de colisão e tabelas arco-íris) e exposição do hash da senha nas respostas de `User.to_dict()`.

#### 2. Estratégia de Transformação
- Substituição de `hashlib.md5` por `werkzeug.security` (`generate_password_hash` e `check_password_hash` com algoritmo com salt).
- Remoção definitiva da coluna de senha no método de serialização da entidade (`to_dict`).

#### 3. Exemplos Antes e Depois

```python
# [ANTES] models/user.py — Hash inseguro MD5 e vazamento de credenciais na API
class User(db.Model):
    ...
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': self.password,  # VAZAMENTO DE SENHA NA API!
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }

    def set_password(self, pwd):
        self.password = hashlib.md5(pwd.encode()).hexdigest()

    def check_password(self, pwd):
        return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

```python
# [DEPOIS] models/user.py — Criptografia segura com Werkzeug e senha suprimida
from werkzeug.security import check_password_hash, generate_password_hash

class User(db.Model):
    ...
    def to_dict(self, include_task_count=False):
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_task_count:
            data['task_count'] = len(self.tasks) if self.tasks is not None else 0
        return data

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
```

---

### Padrão 4: Substituição de Fake Token por Autenticação Assinada Criptograficamente

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Fake Authentication / Broken Access Control (Severidade: CRITICAL).
- **Problema:** O endpoint `/login` devolvia uma string de token fictícia (`fake-jwt-token-{id}`) sem assinatura criptográfica, sem expiração e sem validação nos endpoints protegidos.

#### 2. Estratégia de Transformação
- Criação de `AuthController` utilizando `itsdangerous.URLSafeTimedSerializer` com expiração configurável e assinatura segura baseada em `SECRET_KEY`.

#### 3. Exemplos Antes e Depois

```python
# [ANTES] routes/user_routes.py — Token fictício sem integridade ou expiração
@user_bp.route('/login', methods=['POST'])
def login():
    ...
    if not user.check_password(password):
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': 'fake-jwt-token-' + str(user.id)
    }), 200
```

```python
# [DEPOIS] controllers/auth_controller.py — Token assinado e temporizado
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from config.settings import Settings
from middlewares.error_handler import AppError
from models.user import User

class AuthController:
    @staticmethod
    def _serializer():
        return URLSafeTimedSerializer(Settings.SECRET_KEY, salt='task-manager-auth')

    @classmethod
    def create_token(cls, user_id):
        return cls._serializer().dumps({'user_id': user_id})

    @classmethod
    def verify_token(cls, token):
        try:
            payload = cls._serializer().loads(token, max_age=Settings.TOKEN_MAX_AGE_SECONDS)
            return payload.get('user_id')
        except SignatureExpired as exc:
            raise AppError('Token expirado', 401) from exc
        except BadSignature as exc:
            raise AppError('Token inválido', 401) from exc

    @classmethod
    def login(cls, email, password):
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            raise AppError('Credenciais inválidas', 401)
        if not user.active:
            raise AppError('Usuário inativo', 403)

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': cls.create_token(user.id),
        }
```

---

### Padrão 5: Otimização de Performance e Eliminação de N+1 Queries via Eager Loading

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** N+1 Query Problem (Severidade: HIGH).
- **Problema:** A listagem de tarefas iterava sobre todos os registros executando `User.query.get` e `Category.query.get` manualmente para cada linha, gerando 1 + 2N queries ao banco.

#### 2. Estratégia de Transformação
- Utilização de `joinedload` do SQLAlchemy ORM no Controller para carregar `Task.user` e `Task.category` em um único comando SQL com `LEFT OUTER JOIN`.

#### 3. Exemplos Antes e Depois

```python
# [ANTES] routes/task_routes.py — 1 query de tasks + 2 queries adicionais por item
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    result = []
    for t in tasks:
        task_data = t.to_dict()
        if t.user_id:
            user = User.query.get(t.user_id)          # Query N+1
            task_data['user_name'] = user.name if user else None
        if t.category_id:
            cat = Category.query.get(t.category_id)   # Query N+1
            task_data['category_name'] = cat.name if cat else None
        result.append(task_data)
    return jsonify(result), 200
```

```python
# [DEPOIS] controllers/task_controller.py — Query única otimizada via joinedload
from sqlalchemy.orm import joinedload

class TaskController:
    @staticmethod
    def list_tasks():
        tasks = Task.query.options(
            joinedload(Task.user),
            joinedload(Task.category),
        ).all()
        return [task.to_dict(include_relations=True) for task in tasks]
```

---

### Padrão 6: Encapsulamento de Regras de Domínio e Eliminação de Shotgun Surgery

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Shotgun Surgery & Duplicated Code (Severidade: HIGH).
- **Problema:** A checagem condicional de tarefa atrasada (`is_overdue`) e validações de integridade estavam duplicadas em múltiplos arquivos (`task_routes.py`, `user_routes.py`, `report_routes.py` e `helpers.py`). Qualquer mudança de especificação exigia alterações em cascata.

#### 2. Estratégia de Transformação
- Aplicação do padrão Information Expert: a regra de negócio do atraso passa a pertencer exclusivamente à entidade `Task` em `models/task.py`, com suporte a `timezone.utc`.

#### 3. Exemplos Antes e Depois

```python
# [ANTES] Repetido em task_routes.py, user_routes.py, report_routes.py, helpers.py
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
        else:
            task_data['overdue'] = False
    else:
        task_data['overdue'] = False
else:
    task_data['overdue'] = False
```

```python
# [DEPOIS] models/task.py — Método de domínio centralizado e timezone-aware
def utcnow():
    return datetime.now(timezone.utc)

class Task(db.Model):
    ...
    def is_overdue(self):
        if not self.due_date:
            return False
        if self.status in ('done', 'cancelled'):
            return False
        due = self.due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        return due < utcnow()
```

---

### Padrão 7: Reorganização e Segregação de Domínios Poluídos (Domain Extraction)

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Misplaced Responsibilities / Domain Pollution (Severidade: MEDIUM).
- **Problema:** O CRUD de Categorias (`/categories`) estava acoplado dentro de `routes/report_routes.py`, dificultando a manutenção, testes e extensão das regras de categoria.

#### 2. Estratégia de Transformação
- Criação de um módulo coeso para Categorias: Blueprint de apresentação (`views/category_views.py`), controlador de caso de uso (`controllers/category_controller.py`) e contrato de validação (`schemas/category_schema.py`).

#### 3. Exemplos Antes e Depois

```python
# [ANTES] routes/report_routes.py — CRUD de categorias escondido dentro de relatórios
report_bp = Blueprint('reports', __name__)

@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    ...

@report_bp.route('/categories', methods=['POST'])
def create_category():
    # Endpoints de categoria misturados no domínio de relatórios
    data = request.get_json()
    ...
```

```python
# [DEPOIS] views/category_views.py — Domínio isolado com Blueprint dedicado
category_bp = Blueprint('categories', __name__)

@category_bp.route('/categories', methods=['GET'])
def list_categories():
    return jsonify(CategoryController.list_categories()), 200

@category_bp.route('/categories', methods=['POST'])
def create_category():
    payload = CategoryCreateSchema().load(request.get_json() or {})
    data, status = CategoryController.create_category(payload)
    return jsonify(data), status
```

---

### Padrão 8: Centralização de Tratamento de Erros e Observabilidade Estruturada

#### 1. Diagnóstico e Contexto
- **Anti-Pattern:** Silent Failures & Bare Except with Print (Severidade: MEDIUM).
- **Problema:** Uso disseminado de blocos `try...except:` genéricos, mascaramento de erros com `print(e)` e respostas HTTP com mensagens e formatos inconsistentes.

#### 2. Estratégia de Transformação
- Criação da classe `AppError` para erros de aplicação com código HTTP customizável.
- Criação de `middlewares/error_handler.py` registrando tratadores globais para `AppError`, `ValidationError` (Marshmallow), `IntegrityError` (banco), 404 e 500 com logging via módulo `logging`.

#### 3. Exemplos Antes e Depois

```python
# [ANTES] Espalhado em dezenas de rotas — Bare except e logging com print
@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        ...
        db.session.commit()
        return jsonify(task.to_dict()), 200
    except Exception as e:
        print(f"Erro: {e}")  # Perda de contexto e poluição de stdout
        db.session.rollback()
        return jsonify({'error': 'Erro ao atualizar'}), 500
```

```python
# [DEPOIS] middlewares/error_handler.py — Middleware centralizado e tipado
import logging
from flask import jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class AppError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({'error': error.message}), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        messages = error.messages
        if isinstance(messages, dict):
            first = next(iter(messages.values()))
            message = first[0] if isinstance(first, list) else str(first)
        else:
            message = str(messages)
        return jsonify({'error': message}), 400

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        logger.exception('Integrity error')
        return jsonify({'error': 'Conflito de dados'}), 409

    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.exception('Internal server error')
        return jsonify({'error': 'Erro interno'}), 500
```

---

## Guia Prático de Execução do Playbook (Passo a Passo)

1. **Isolar Configurações:** Extraia constantes, chaves e credenciais para `config/settings.py` alimentado por variáveis de ambiente via `os.getenv`.
2. **Sanear Segurança de Dados:** Remova campos confidenciais de serializadores (`to_dict`) e adote hashing robusto (`werkzeug.security`).
3. **Implantar Middleware de Erros:** Configure a hierarquia `AppError` e registro global de exceções antes de refatorar as rotas.
4. **Criar Camada de Schemas (DTOs):** Modele a validação de entrada de cada entidade com Marshmallow/Pydantic.
5. **Extrair Controllers e Services:** Mova a lógica de negócio e consultas de banco das rotas para classes controladoras puras.
6. **Otimizar Queries com Eager Loading:** Revise listagens com relacionamentos e aplique `joinedload` ou `JOIN` explícito para evitar consultas N+1.
7. **Reduzir as Rotas a Views Enxutas:** Substitua o corpo das rotas por apenas `Schema.load()` seguido da chamada ao `Controller`.
8. **Validar com Testes de Fumaça e Regressão:** Execute testes unitários e de integração validando a integridade dos contratos de API.
