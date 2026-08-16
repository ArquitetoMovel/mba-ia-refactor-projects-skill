# Anti-Patterns and Code Smells Catalog

Catálogo de referência para identificação, diagnóstico e refatoração de Anti-Patterns e Code Smells em projetos monolíticos e APIs web (Python/Flask, Node.js/Express, etc.), alinhado às diretrizes da skill **`refactor-arch`**.

---

## Sumário

1. [Anti-Patterns Arquiteturais](#1-anti-patterns-arquiteturais)
2. [Anti-Patterns de Segurança e Configuração](#2-anti-patterns-de-segurança-e-configuração)
3. [Anti-Patterns de Banco de Dados e Performance](#3-anti-patterns-de-banco-de-dados-e-performance)
4. [Code Smells de Manutenibilidade e Limpeza de Código](#4-code-smells-de-manutenibilidade-e-limpeza-de-código)
5. [Anti-Patterns de Tratamento de Erros e Observabilidade](#5-anti-patterns-de-tratamento-de-erros-e-observabilidade)
6. [Guia de Mapeamento para Arquitetura MVC](#6-guia-de-mapeamento-para-arquitetura-mvc)

---

## 1. Anti-Patterns Arquiteturais

### 1.1. God Object / God Routes / Fat Controllers
- **Severidade Padrão**: **CRITICAL** / **HIGH**
- **Sinônimos**: *The Blob, Monolithic Controller, Smart UI/Router*.
- **Descrição**: Módulos de rota ou classes controladoras gigantes que concentram múltiplas responsabilidades descorrelacionadas: roteamento HTTP, parsing de requisição, validações, regras de negócio de múltiplos domínios, persistência direta via ORM/SQL e formatação de resposta.
- **Sintomas no Código**:
  - Arquivos de rota (`routes/task_routes.py`, `AppManager.js`) com centenas de linhas.
  - Funções de rota instanciando models, executando queries complexas, tratando exceções de banco e serializando JSON manualmente.
- **Impacto**: Dificuldade extrema de teste unitário, alto acoplamento, impossibilidade de reaproveitamento de regras.
- **Solução Arquitetural**:
  - Separar em camadas: **View** (declaração de rotas e status HTTP) $\to$ **Controller** (orquestração do caso de uso) $\to$ **Service** (regras de domínio puras) $\to$ **Model** (entidades e persistência).
  - Extrair validações para **Schemas/DTOs** dedicados (ex: Marshmallow, Joi, Zod).

---

### 1.2. Lack of Separation of Concerns (Falta de Separação de Responsabilidades)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Ausência de limites claros entre a camada de apresentação, a camada de aplicação/serviço e a camada de persistência de dados.
- **Sintomas no Código**:
  - Models executando parsing de HTTP ou retornando respostas formatadas com códigos HTTP.
  - Rotas chamando diretamente `db.session.commit()`, `db.session.rollback()` ou queries SQL brutas.
  - Ausência de uma camada de serviço ou controller independente do framework web.
- **Solução Arquitetural**:
  - Definir interfaces claras entre camadas onde cada componente conhece apenas seu nível de abstração imediato.

---

### 1.3. Tight Coupling (Acoplamento Forte)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Classes ou módulos que dependem diretamente de implementações concretas, variáveis globais mutáveis ou estados estáticos externos em vez de abstrações ou injeção de dependência.
- **Sintomas no Código**:
  - Instanciação direta e rígida de serviços de terceiros (ex: chamadas diretas de envio de email ou gateways de pagamento dentro de controladores).
  - Dependência de variáveis de conexão globais não vinculadas ao ciclo de vida da requisição.
- **Solução Arquitetural**:
  - Injeção de dependências, uso de configurações centralizadas e gerenciamento de contexto de conexão (ex: `flask.g` ou Middleware de banco de dados).

---

### 1.4. Misplaced Responsibilities (Domínios Cruzados / Poluição de Domínio)
- **Severidade Padrão**: **MEDIUM**
- **Descrição**: Funcionalidades de uma entidade ou domínio de negócio alocadas dentro do módulo de outro domínio sem justificativa arquitetural.
- **Sintomas no Código**:
  - Endpoints de CRUD de Categorias (`/categories`) implementados dentro de `report_routes.py`.
  - Métodos de manipulação de usuários definidos dentro de classes de gerenciamento de tarefas.
- **Solução Arquitetural**:
  - Criar Blueprints/Módulos dedicados para cada domínio (`category_views.py`, `CategoryController`, `CategoryService`).

---

### 1.5. Mutable Global State (Estado Global Mutável em Memória)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Armazenamento de dados transacionais ou de negócio em estruturas em memória (listas, dicionários globais) dentro de módulos singleton.
- **Sintomas no Código**:
  - `self.notifications = []` armazenando histórico de notificações na memória do servidor.
  - Listas globais de sessões ativas sem persistência em banco ou cache distribuído (Redis).
- **Impacto**: Perda total de dados ao reiniciar o processo, inconsistência severa em ambientes com múltiplos workers/processos (ex: Gunicorn/Uvicorn/PM2).
- **Solução Arquitetural**:
  - Persistir dados transacionais em banco de dados ou mensageria; externalizar serviços voláteis para filas ou chamadas síncronas parametrizadas.

---

## 2. Anti-Patterns de Segurança e Configuração

### 2.1. Hardcoded Secrets (Segredos e Credenciais no Código-Fonte)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Presença de chaves de criptografia (`SECRET_KEY`), credenciais de banco de dados, senhas de SMTP ou tokens de API embutidos diretamente no código-fonte.
- **Sintomas no Código**:
  - `app.config['SECRET_KEY'] = 'super-secret-key-123'`
  - `SMTP_USER = "admin@email.com"`, `SMTP_PASSWORD = "secretpassword"`
- **Impacto**: Vazamento de credenciais em repositórios, comprometimento total da aplicação e infraestrutura.
- **Solução Arquitetural**:
  - Centralizar configurações em módulo `config/settings.py`, consumindo variáveis de ambiente (`os.getenv`, `dotenv`), com arquivo `.env.example` versionado e `.env` no `.gitignore`.

---

### 2.2. Insecure / Broken Cryptography (Criptografia Inadequada para Senhas)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Uso de algoritmos de hash rápidos e obsoletos (MD5, SHA-1) ou ausência de salt na persistência e conferência de senhas de usuários.
- **Sintomas no Código**:
  - `hashlib.md5(password.encode()).hexdigest()`
- **Impacto**: Vulnerabilidade imediata a ataques de força bruta e tabelas arco-íris (*rainbow tables*).
- **Solução Arquitetural**:
  - Adotar bibliotecas padrão da indústria com algoritmos com salt e derivação de chave adequada: `werkzeug.security` (`generate_password_hash`, `check_password_hash` com Scrypt/PBKDF2) ou `bcrypt`.

---

### 2.3. Sensitive Data Exposure / Password Leakage (Vazamento de Dados Sensíveis na API)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Serialização de campos confidenciais (hash de senhas, chaves privadas, tokens internos) em respostas públicas ou endpoints de listagem de usuários.
- **Sintomas no Código**:
  - `def to_dict(self): return {'id': self.id, 'email': self.email, 'password': self.password}`
  - Listagem `GET /users` retornando hashes de senha de todos os usuários cadastrados.
- **Solução Arquitetural**:
  - Omitir senhas e campos confidenciais nos serializers/mappers.
  - Configurar schemas (Marshmallow/Pydantic/DTO) com campos sensíveis definidos como `load_only=True` (apenas entrada, nunca saída).

---

### 2.4. Fake Authentication / Broken Access Control (Autenticação Fictícia ou Frágil)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Emissão de tokens de autenticação estáticos, falsos ou não assinados criptograficamente, sem expiração ou validação nos endpoints protegidos.
- **Sintomas no Código**:
  - Endpoint `/login` retornando `"fake-jwt-token-" + str(user.id)`.
  - Ausência de middleware ou decorador de validação de autenticação e verificação de papéis/roles (`admin`, `manager`, `user`).
- **Solução Arquitetural**:
  - Implementar tokens assinados com expiração configurável (ex: `itsdangerous.URLSafeTimedSerializer` ou `PyJWT`) e middleware de autorização.

---

### 2.5. SQL Injection / String-Built Queries (Injeção de SQL)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Construção de comandos SQL utilizando interpolação ou concatenação de strings com dados fornecidos pelo usuário.
- **Sintomas no Código**:
  - `cursor.execute(f"SELECT * FROM produtos WHERE nome = '{nome}'")`
- **Solução Arquitetural**:
  - Utilizar exclusivamente consultas parametrizadas com placeholders (`?` no SQLite, `%s` no PostgreSQL) ou ORM com query builder seguro.

---

## 3. Anti-Patterns de Banco de Dados e Performance

### 3.1. N+1 Query Problem (Problema de Consultas N+1)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Execução de uma query inicial para buscar $N$ registros pai, seguida de $N$ queries individuais em um loop para buscar os relacionamentos de cada item filho.
- **Sintomas no Código**:
  - Iteração sobre tarefas com `User.query.get(task.user_id)` e `Category.query.get(task.category_id)` dentro do loop.
- **Impacto**: Degradação exponencial de tempo de resposta e sobrecarga severa no banco de dados com aumento de volume.
- **Solução Arquitetural**:
  - Utilizar Eager Loading com `joinedload` / `selectinload` no SQLAlchemy ou queries SQL explícitas com `JOIN`.

---

### 3.2. Unscoped / Leaking Database Connections (Vazamento de Conexões de Banco)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Criação de conexões globais com o banco de dados que não respeitam o ciclo de vida da requisição HTTP ou que nunca são fechadas.
- **Solução Arquitetural**:
  - Vincular a conexão ao ciclo de vida da requisição (ex: Flask `g.db` com hook `@app.teardown_appcontext` ou pool gerenciado pelo ORM).

---

## 4. Code Smells de Manutenibilidade e Limpeza de Código

### 4.1. Shotgun Surgery (Cirurgia por Espingarda / Regras Espalhadas)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Uma única regra de negócio (ex: checagem de tarefa atrasada `is_overdue`, cálculo de desconto ou validação de status) duplicada em dezenas de arquivos diferentes, exigindo edições espalhadas a cada mudança de especificação.
- **Sintomas no Código**:
  - A mesma comparação `due_date < datetime.utcnow()` copiada em rotas de tarefas, rotas de usuários, relatórios e helpers.
- **Solução Arquitetural**:
  - Centralizar a regra de negócio no Model de domínio (ex: `Task.is_overdue()`) ou em um Service especializado.

---

### 4.2. Duplicated Code / Copy-Paste Programming (Código Duplicado)
- **Severidade Padrão**: **MEDIUM**
- **Descrição**: Blocos idênticos ou quase idênticos de validação de payload, formatação de datas ou queries repetidos em múltiplos endpoints.
- **Solução Arquitetural**:
  - Extrair para Schemas reutilizáveis, funções utilitárias puras ou middlewares.

---

### 4.3. Long Method / Monster Function (Métodos Longos e Complexos)
- **Severidade Padrão**: **MEDIUM**
- **Descrição**: Funções com mais de 40-50 linhas acumulando condicionais aninhadas, loops de agregação manual e tratamentos de erro múltiplos.
- **Solução Arquitetural**:
  - Aplicar refatoração *Extract Method*, delegando cálculos para métodos de modelo ou serviços específicos.

---

### 4.4. Feature Envy (Inveja de Recursos)
- **Severidade Padrão**: **MEDIUM**
- **Descrição**: Um método em uma classe ou rota que acessa e manipula excessivamente os campos internos de outro objeto para tomar decisões que deveriam pertencer ao próprio objeto.
- **Solução Arquitetural**:
  - Mover o comportamento para o objeto dono dos dados (*Information Expert*).

---

### 4.5. Dead Code & Phantom Dependencies (Código Morto e Dependências Fantasmas)
- **Severidade Padrão**: **MEDIUM**
- **Descrição**: Classes/serviços existentes que nunca são instanciados ou chamados no fluxo da aplicação, funções utilitárias obsoletas e pacotes listados em dependências que não são utilizados.
- **Sintomas no Código**:
  - Classes como `NotificationService` prontas mas sem nenhuma chamada no código; pacotes como `marshmallow` em requirements mas sem uso.
- **Solução Arquitetural**:
  - Remover código morto ou integrá-lo adequadamente na arquitetura caso faça parte do escopo de requisitos.

---

### 4.6. Deprecated APIs / Framework Incompatibilities (APIs Depreciadas)
- **Severidade Padrão**: **LOW**
- **Descrição**: Uso de métodos marcados como obsoletos em versões recentes das linguagens ou frameworks.
- **Exemplo**: `datetime.utcnow()` no Python 3.12+ (deve ser substituído por `datetime.now(timezone.utc)`).
- **Solução**:
  - Atualizar para chamadas modernas e timezone-aware.

---

### 4.7. Magic Numbers & Primitive Obsession (Números Mágicos e Literais Soltos)
- **Severidade Padrão**: **LOW**
- **Descrição**: Uso de números e strings soltos no meio do código para definir limites de validação, prioridades padrão ou status sem constantes declaradas.
- **Solução**:
  - Declarar constantes em `Settings` ou enums do domínio (ex: `VALID_STATUSES`, `MIN_PASSWORD_LENGTH = 8`).

---

## 5. Anti-Patterns de Tratamento de Erros e Observabilidade

### 5.1. Poor Error Handling / Silent Failures (Tratamento Pobre de Erros)
- **Severidade Padrão**: **MEDIUM**
- **Descrição**: Uso de blocos `try/except Exception:` com chamadas simples de `print(e)`, mascarando a causa raiz, retornando mensagens vagas ou vazando rastros de pilha de forma insegura.
- **Solução Arquitetural**:
  - Criar exceções de aplicação customizadas (ex: `AppError`, `ResourceNotFoundError`, `BusinessRuleError`).
  - Registrar handlers centralizados na aplicação (`register_error_handlers(app)`) com mapeamento consistente de status HTTP e logging estruturado (`logging.getLogger(__name__)`).

---

## 6. Guia de Mapeamento para Arquitetura MVC

Ao refatorar um projeto para o padrão **MVC**, siga o mapeamento de responsabilidades abaixo:

| Camada | Responsabilidade Principal | O que DEVE Conter | O que NÃO DEVE Conter |
|--------|----------------------------|-------------------|-----------------------|
| **View** (`views/`) | Ponto de entrada HTTP e roteamento | Blueprints de rota, recebimento de requests, retorno de status HTTP/JSON | Queries de banco, validações manuais de negócio, SQL |
| **Controller** (`controllers/`) | Orquestração do caso de uso | Coordenação entre Schemas, Services e Models; controle de fluxo | Regras de cálculo puro de negócio, SQL manual bruto |
| **Service** (`services/`) | Regras de negócio e integrações | Lógica de domínio, integração com gateways externos (SMTP, pagamentos) | Objetos de request/response HTTP (Flask `request`/`Response`) |
| **Model** (`models/`) | Entidades de domínio e persistência | Definição de tabelas/colunas, relacionamentos, métodos de entidade (`is_overdue()`) | Dependência direta de contextos de request HTTP |
| **Schema** (`schemas/`) | Validação e serialização (DTO) | Validação de tipos, comprimentos, campos obrigatórios, sanitização | Acesso ao banco de dados ou orquestração de rotas |
| **Middleware** (`middlewares/`) | Tratamento transversal | Handlers globais de erros (`AppError`, `404`, `500`), autenticação | Lógicas específicas de um único domínio |
| **Config** (`config/`) | Configurações do ambiente | Leitura de variáveis de ambiente (`Settings.py`), constantes | Lógica executável da aplicação |
