# Anti-Patterns and Code Smells Catalog

Catálogo de referência para identificação, diagnóstico e refatoração de Anti-Patterns e Code Smells em projetos monolíticos e APIs web (Python/Flask, Node.js/Express, etc.), alinhado às diretrizes da skill **`refactor-arch`**.

---

## Sumário

1. [Anti-Patterns Arquiteturais](#1-anti-patterns-arquiteturais)
   - 1.1 [God Object / God Routes / Fat Controllers](#11-god-object--god-routes--fat-controllers)
   - 1.2 [Lack of Separation of Concerns](#12-lack-of-separation-of-concerns-falta-de-separação-de-responsabilidades)
   - 1.3 [Tight Coupling](#13-tight-coupling-acoplamento-forte)
   - 1.4 [Misplaced Responsibilities](#14-misplaced-responsibilities-domínios-cruzados--poluição-de-domínio)
   - 1.5 [Mutable Global State](#15-mutable-global-state-estado-global-mutável-em-memória)
   - 1.6 [Asynchronous Boot Race Condition & Missing Composition Root](#16-asynchronous-boot-race-condition--missing-composition-root)
2. [Anti-Patterns de Segurança e Configuração](#2-anti-patterns-de-segurança-e-configuração)
   - 2.1 [Hardcoded Secrets](#21-hardcoded-secrets-segredos-e-credenciais-no-código-fonte)
   - 2.2 [Insecure / Broken Cryptography](#22-insecure--broken-cryptography-criptografia-inadequada-ou-caseira)
   - 2.3 [Sensitive Data Exposure & Unsafe Logging](#23-sensitive-data-exposure--unsafe-logging-vazamento-de-dados-sensíveis-e-logs-inseguros)
   - 2.4 [Fake Authentication / Broken Access Control](#24-fake-authentication--broken-access-control-autenticação-fictícia-ou-frágil)
   - 2.5 [SQL Injection / String-Built Queries](#25-sql-injection--string-built-queries-injeção-de-sql)
3. [Anti-Patterns de Banco de Dados e Performance](#3-anti-patterns-de-banco-de-dados-e-performance)
   - 3.1 [N+1 Query Problem](#31-n1-query-problem-problema-de-consultas-n1)
   - 3.2 [Unscoped / Leaking Database Connections](#32-unscoped--leaking-database-connections-vazamento-de-conexões-de-banco)
   - 3.3 [Missing Transaction Boundaries](#33-missing-transaction-boundaries-ausência-de-limite-transacional--operações-não-atômicas)
   - 3.4 [Orphan Records & Missing Referential Integrity](#34-orphan-records--missing-referential-integrity-dados-órfãos-e-falha-de-integridade-referencial)
4. [Code Smells de Manutenibilidade e Limpeza de Código](#4-code-smells-de-manutenibilidade-e-limpeza-de-código)
   - 4.1 [Shotgun Surgery](#41-shotgun-surgery-cirurgia-por-espingarda--regras-espalhadas)
   - 4.2 [Duplicated Code / Copy-Paste Programming](#42-duplicated-code--copy-paste-programming-código-duplicado)
   - 4.3 [Long Method / Monster Function](#43-long-method--monster-function-métodos-longos-e-complexos)
   - 4.4 [Feature Envy](#44-feature-envy-inveja-de-recursos)
   - 4.5 [Dead Code & Phantom Dependencies](#45-dead-code--phantom-dependencies-código-morto-e-dependências-fantasmas)
   - 4.6 [Deprecated APIs / Framework Incompatibilities](#46-deprecated-apis--framework-incompatibilities-apis-depreciadas)
   - 4.7 [Magic Numbers & Primitive Obsession](#47-magic-numbers--primitive-obsession-números-mágicos-e-literais-soltos)
   - 4.8 [Callback Hell / Pyramid of Doom](#48-callback-hell--pyramid-of-doom-aninhamento-excessivo-de-callbacks-assíncronos)
   - 4.9 [Cryptic Naming & Parameter Obfuscation](#49-cryptic-naming--parameter-obfuscation-nomenclatura-críptica-e-parâmetros-ofuscados)
5. [Anti-Patterns de Tratamento de Erros e Observabilidade](#5-anti-patterns-de-tratamento-de-erros-e-observabilidade)
   - 5.1 [Poor Error Handling / Silent Failures](#51-poor-error-handling--silent-failures-tratamento-pobre-de-erros-e-supressão-de-exceções)
6. [Guia de Mapeamento para Arquitetura MVC](#6-guia-de-mapeamento-para-arquitetura-mvc)

---

## 1. Anti-Patterns Arquiteturais

### 1.1. God Object / God Routes / Fat Controllers
- **Severidade Padrão**: **CRITICAL** / **HIGH**
- **Sinônimos**: *The Blob, Monolithic Controller, Smart UI/Router, Monolithic Manager*.
- **Descrição**: Módulos de rota ou classes controladoras gigantes que concentram múltiplas responsabilidades descorrelacionadas: inicialização de infraestrutura/esquemas, roteamento HTTP, parsing de requisição, validações manuais de payload, regras de negócio de múltiplos domínios, persistência direta via ORM/SQL e serialização de resposta.
- **Sintomas no Código**:
  - Arquivos gigantes (`routes/task_routes.py`, `AppManager.js`) com centenas de linhas concentrando ciclo de vida completo da aplicação.
  - Funções de rota instanciando models, executando queries complexas, tratando exceções de banco e serializando JSON manualmente.
- **Impacto**: Dificuldade extrema de teste unitário, alto acoplamento, impossibilidade de reaproveitamento de regras de negócio.
- **Solução Arquitetural**:
  - Separar em camadas: **View** (declaração de rotas e status HTTP) $\to$ **Controller** (orquestração do caso de uso) $\to$ **Service** (regras de domínio puras e integrações) $\to$ **Model** (entidades e persistência).
  - Extrair validações para **Schemas/DTOs** dedicados (ex: Marshmallow no Python, Joi/Zod no Node.js).

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
  - Injeção de dependências, uso de configurações centralizadas e gerenciamento de contexto de conexão (ex: `flask.g` ou Middleware/helper de banco de dados).

---

### 1.4. Misplaced Responsibilities (Domínios Cruzados / Poluição de Domínio)
- **Severidade Padrão**: **MEDIUM**
- **Descrição**: Funcionalidades de uma entidade ou domínio de negócio alocadas dentro do módulo de outro domínio sem justificativa arquitetural.
- **Sintomas no Código**:
  - Endpoints de CRUD de Categorias (`/categories`) implementados dentro de `report_routes.py`.
  - Métodos de manipulação de usuários definidos dentro de classes de gerenciamento de tarefas.
- **Solução Arquitetural**:
  - Criar Blueprints/Módulos/Controllers dedicados para cada domínio (`category_views.py`, `CategoryController`, `CategoryService`, `userController.js`, `courseModel.js`).

---

### 1.5. Mutable Global State (Estado Global Mutável em Memória)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Armazenamento de dados transacionais ou de negócio em estruturas em memória (listas, dicionários globais, objetos exportados) dentro de módulos singleton.
- **Sintomas no Código**:
  - `self.notifications = []` ou `let globalCache = {}; let totalRevenue = 0;` em módulos utilitários ou serviços.
  - Listas globais de sessões ativas sem persistência em banco ou cache distribuído (Redis).
- **Impacto**: Perda total de dados ao reiniciar o processo, inconsistência severa em ambientes com múltiplos workers/processos (ex: Gunicorn/Uvicorn/PM2/Cluster).
- **Solução Arquitetural**:
  - Persistir dados transacionais em banco de dados ou mensageria; externalizar serviços voláteis para filas ou chamadas síncronas parametrizadas.

---

### 1.6. Asynchronous Boot Race Condition & Missing Composition Root
- **Severidade Padrão**: **HIGH**
- **Descrição**: Inicialização de instâncias globais rígidas sem padrão fábrica (Application Factory) ou inicialização do servidor HTTP (ex: `app.listen()`) antes da conclusão de rotinas assíncronas essenciais de inicialização (tabelas DDL, migrações de schema, carga de seeds ou abertura de pools de conexão).
- **Sintomas no Código**:
  - `app.py` instanciando diretamente o app no escopo global sem função `create_app()`.
  - `manager.initDb(); app.listen(port);` onde `initDb()` executa queries/callbacks de forma assíncrona em segundo plano sem sincronização.
  - Primeiras requisições recebidas pela API falhando intermitentemente com `no such table` ou erros de conexão.
- **Impacto**: Dificuldade de testes isolados, instabilidade no deploy e indisponibilidade temporária na inicialização.
- **Solução Arquitetural**:
  - Padrão **Composition Root** com Application Factory (`create_app()`) no Flask ou bootstrap assíncrono explícito (`async start()` aguardando `await initDatabase()`) no Node.js.

---

## 2. Anti-Patterns de Segurança e Configuração

### 2.1. Hardcoded Secrets (Segredos e Credenciais no Código-Fonte)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Presença de chaves de criptografia (`SECRET_KEY`), credenciais de banco de dados, senhas de SMTP ou tokens de API embutidos diretamente no código-fonte.
- **Sintomas no Código**:
  - `app.config['SECRET_KEY'] = 'super-secret-key-123'`
  - `SMTP_USER = "taskmanager@gmail.com"`, `SMTP_PASSWORD = "secretpassword"`
  - `const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123..." }`
- **Impacto**: Vazamento de credenciais em repositórios, comprometimento total da aplicação e infraestrutura.
- **Solução Arquitetural**:
  - Centralizar configurações em módulo `config/settings.py` / `config/settings.js`, consumindo variáveis de ambiente (`os.getenv`, `process.env`, `dotenv`), mantendo `.env.example` versionado e `.env` no `.gitignore`.

---

### 2.2. Insecure / Broken Cryptography (Criptografia Inadequada ou Caseira)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Uso de algoritmos de hash rápidos e obsoletos (MD5, SHA-1), ausência de salt na persistência de senhas ou implementação de algoritmos de pseudo-criptografia caseiros (*homebrewed crypto*).
- **Sintomas no Código**:
  - `hashlib.md5(password.encode()).hexdigest()`
  - Funções de hashing artesanais, como loops de concatenação de substrings em Base64 (`badCrypto(pwd)`).
- **Impacto**: Vulnerabilidade imediata a ataques de força bruta, dicionário e tabelas arco-íris (*rainbow tables*).
- **Solução Arquitetural**:
  - Adotar bibliotecas padrão da indústria com algoritmos com salt e derivação de chave adequada: `werkzeug.security` (`generate_password_hash`, `check_password_hash` com Scrypt/PBKDF2) ou `bcrypt` / `argon2`.

---

### 2.3. Sensitive Data Exposure & Unsafe Logging (Vazamento de Dados Sensíveis e Logs Inseguros)
- **Severidade Padrão**: **CRITICAL**
- **Sinônimos**: *CWE-532 (Insertion of Sensitive Information into Log File), Plaintext PII Logging, Password Leakage*.
- **Descrição**: Exposição de dados confidenciais (senhas em texto plano ou hash, chaves privadas, números completos de cartão/CVVs, tokens internos) em respostas públicas da API ou em logs de aplicação (`console.log`, `logging.info`, `print`).
- **Sintomas no Código**:
  - `def to_dict(self): return {'id': self.id, 'email': self.email, 'password': self.password}`
  - `console.log("Processando cartão " + cc + " na chave " + config.paymentGatewayKey)`.
  - Endpoints `/users` ou `/login` retornando o campo `password`.
- **Impacto**: Violação de legislações de privacidade (LGPD, GDPR) e normas de segurança (PCI-DSS); exposição de credenciais e dados em ferramentas de observabilidade.
- **Solução Arquitetural**:
  - Omitir senhas e campos confidenciais nos serializers/mappers.
  - Configurar schemas DTO (Marshmallow/Pydantic/Zod) com campos sensíveis definidos como `load_only=True` (apenas entrada, nunca saída).
  - Eliminar impressões de credenciais em logs e aplicar mascaramento (*masking*).

---

### 2.4. Fake Authentication / Broken Access Control (Autenticação Fictícia ou Frágil)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Emissão de tokens de autenticação estáticos, falsos ou não assinados criptograficamente, sem expiração ou validação nos endpoints protegidos.
- **Sintomas no Código**:
  - Endpoint `/login` retornando `"fake-jwt-token-" + str(user.id)`.
  - Ausência de middleware ou decorador de validação de autenticação e verificação de papéis/roles (`admin`, `manager`, `user`).
- **Solução Arquitetural**:
  - Implementar tokens assinados com expiração configurável (ex: `itsdangerous.URLSafeTimedSerializer`, `PyJWT` ou `jsonwebtoken`) e middleware de autorização.

---

### 2.5. SQL Injection / String-Built Queries (Injeção de SQL)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Construção de comandos SQL utilizando interpolação ou concatenação de strings com dados fornecidos pelo usuário.
- **Sintomas no Código**:
  - `cursor.execute(f"SELECT * FROM produtos WHERE nome = '{nome}'")` ou `db.run("DELETE FROM users WHERE id = " + id)`
- **Solução Arquitetural**:
  - Utilizar exclusivamente consultas parametrizadas com placeholders (`?` no SQLite/Python/Node, `%s` no PostgreSQL) ou ORM com query builder seguro.

---

## 3. Anti-Patterns de Banco de Dados e Performance

### 3.1. N+1 Query Problem (Problema de Consultas N+1)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Execução de uma query inicial para buscar $N$ registros pai, seguida de $N$ queries individuais em um loop para buscar os relacionamentos de cada item filho.
- **Sintomas no Código**:
  - Iteração sobre tarefas com `User.query.get(task.user_id)` e `Category.query.get(task.category_id)` dentro do loop.
  - Iteração sobre cursos disparando queries individuais em matrículas e pagamentos com contadores manuais.
- **Impacto**: Degradação exponencial de tempo de resposta e sobrecarga severa no banco de dados com aumento de volume.
- **Solução Arquitetural**:
  - Utilizar Eager Loading com `joinedload` / `selectinload` no SQLAlchemy ou queries SQL explícitas com `JOIN` (`LEFT JOIN`) e agregação estruturada.

---

### 3.2. Unscoped / Leaking Database Connections (Vazamento de Conexões de Banco)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Criação de conexões globais com o banco de dados que não respeitam o ciclo de vida da requisição HTTP ou que nunca são fechadas.
- **Solução Arquitetural**:
  - Vincular a conexão ao ciclo de vida da requisição (ex: Flask `g.db` com hook `@app.teardown_appcontext`, pool gerenciado pelo ORM ou helpers encapsulados de banco de dados).

---

### 3.3. Missing Transaction Boundaries (Ausência de Limite Transacional / Operações Não-Atômicas)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Execução de fluxos de negócio que realizam múltiplas alterações interdependentes no banco de dados através de operações avulsas, sem encapsulamento em uma transação ACID (`BEGIN TRANSACTION` / `COMMIT` / `ROLLBACK`).
- **Sintomas no Código**:
  - Operações multi-tabela onde uma falha na segunda etapa deixa os dados da primeira etapa persistidos permanentemente no banco.
  - Falta de `db.session.rollback()` no bloco `except` de operações complexas no SQLAlchemy.
- **Impacto**: Inconsistência irreparável de dados, registros financeiros/operacionais fantasmas e violação das garantias ACID.
- **Solução Arquitetural**:
  - Encapsular operações multi-tabela em blocos transacionais com rollback automático (ex: `withTransaction(db, async () => { ... })` ou `db.session.begin()` / `try ... commit ... except ... rollback`).

---

### 3.4. Orphan Records & Missing Referential Integrity (Dados Órfãos e Falha de Integridade Referencial)
- **Severidade Padrão**: **HIGH** / **MEDIUM**
- **Descrição**: Exclusão de registros pai sem exclusão coordenada ou em cascata dos seus registros dependentes, gerando registros órfãos que violam a integridade referencial.
- **Sintomas no Código**:
  - Rota `DELETE /users/:id` executando exclusão direta do usuário mantendo tarefas, pagamentos ou matrículas apontando para um `user_id` inexistente.
- **Impacto**: Falhas em consultas com integridade referencial estrita, poluição da base com registros zumbis e distorção em relatórios analíticos e contábeis.
- **Solução Arquitetural**:
  - Implementar exclusão transacional em cascata coordenada na camada de serviço/controller ou habilitar constraints de banco com `ON DELETE CASCADE` e suporte ativo a foreign keys.

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
- **Descrição**: Classes/serviços existentes que nunca são instanciados ou chamados no fluxo da aplicação, funções utilitárias obsoletas, variáveis exportadas não utilizadas e pacotes listados em dependências que não são utilizados.
- **Sintomas no Código**:
  - Classes como `NotificationService` prontas mas sem nenhuma chamada no código; pacotes como `marshmallow` ou `requests` em requirements sem uso.
- **Solução Arquitetural**:
  - Remover código morto e dependências não utilizadas, ou integrá-los adequadamente na arquitetura caso façam parte dos requisitos do sistema.

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

### 4.8. Callback Hell / Pyramid of Doom (Aninhamento Excessivo de Callbacks Assíncronos)
- **Severidade Padrão**: **MEDIUM**
- **Descrição**: Encadeamento profundo de funções de callback assíncronas (4+ níveis) para controle de fluxo de I/O sequencial, dificultando a rastreabilidade, tratamento de erros e delimitação transacional.
- **Solução Arquitetural**:
  - Promisificar operações de banco de dados e adotar `async/await` estruturado.

---

### 4.9. Cryptic Naming & Parameter Obfuscation (Nomenclatura Críptica e Parâmetros Ofuscados)
- **Severidade Padrão**: **LOW**
- **Descrição**: Uso de variáveis, parâmetros ou propriedades com identificadores truncados ou abreviados (ex: `usr`, `eml`, `pwd`, `c_id`, `cat`), prejudicando a clareza do modelo de domínio.
- **Solução Arquitetural**:
  - Mapear na camada de borda (Controller/Schema) para nomes semânticos e expressivos (`username`, `email`, `password`, `category`) nas camadas internas.

---

## 5. Anti-Patterns de Tratamento de Erros e Observabilidade

### 5.1. Poor Error Handling / Silent Failures (Tratamento Pobre de Erros e Supressão de Exceções)
- **Severidade Padrão**: **MEDIUM**
- **Descrição**: Uso de blocos `try/except Exception:` com chamadas simples de `print(e)`, supressão de parâmetros de erro em callbacks, mascaramento da causa raiz, retorno de status HTTP 200 em operações falhas ou vazamento de rastros de pilha de forma insegura.
- **Solução Arquitetural**:
  - Criar exceções de aplicação customizadas (ex: `AppError`, `ResourceNotFoundError`, `BusinessRuleError`).
  - Registrar handlers centralizados na aplicação (`register_error_handlers(app)` ou middleware Express) com mapeamento consistente de status HTTP e logging estruturado (`logging.getLogger(__name__)`).

---

## 6. Guia de Mapeamento para Arquitetura MVC

Ao refatorar um projeto para o padrão **MVC**, siga o mapeamento de responsabilidades abaixo:

| Camada | Arquivos Típicos (Python / Node) | Responsabilidade Principal | O que DEVE Conter | O que NÃO DEVE Conter |
|---|---|---|---|---|
| **View** | `views/*_views.py`, `views/httpResponses.js` | Ponto de entrada HTTP e formatação | Blueprints de rota, recebimento de requests, delegar para Controller/Schema, retorno de status HTTP/JSON | Queries de banco, validações manuais de negócio, SQL bruto |
| **Controller** | `controllers/*_controller.py`, `controllers/*Controller.js` | Orquestração do caso de uso | Coordenação entre Schemas, Services e Models; transações e controle de fluxo | Regras de cálculo puro de negócio, SQL manual bruto |
| **Service** | `services/*_service.py`, `services/*Service.js` | Regras de negócio e integrações | Lógica de domínio, transações complexas, integração externa (SMTP, pagamentos) | Objetos de request/response HTTP (Flask `request`, Express `req`/`res`) |
| **Model** | `models/*.py`, `models/*Model.js` | Entidades de domínio e persistência | Definição de tabelas/colunas, relacionamentos, queries parametrizadas, métodos de domínio (`is_overdue()`) | Dependência direta de contextos de request HTTP |
| **Schema / DTO** | `schemas/*_schema.py`, Joi/Zod | Validação e serialização (DTO) | Validação de tipos, comprimentos, campos obrigatórios, sanitização, `load_only` para senhas | Acesso ao banco de dados ou orquestração de rotas |
| **Middleware / Errors** | `middlewares/error_handler.py`, `services/errors.js` | Tratamento transversal | Handlers globais de erros (`AppError`, `400`, `404`, `500`), logging centralizado | Lógicas específicas de um único domínio |
| **Config** | `config/settings.py`, `config/settings.js` | Configurações do ambiente | Leitura de variáveis de ambiente (`os.getenv`, `process.env`), constantes, defaults seguros | Lógica executável da aplicação, credenciais hardcoded |
| **Database / DB** | `database.py`, `db/database.js` | Conexão e infraestrutura de banco | Instanciação de DB/ORM, pool de conexões, helpers transacionais | Regras de negócio de domínios específicos |
