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
   - 1.6 [Asynchronous Boot Race Condition](#16-asynchronous-boot-race-condition-condição-de-corrida-na-inicialização-assíncrona)
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
- **Descrição**: Módulos de rota ou classes controladoras gigantes que concentram múltiplas responsabilidades descorrelacionadas: inicialização de banco/esquemas, roteamento HTTP, parsing de requisição, validações, regras de negócio de múltiplos domínios, persistência direta via ORM/SQL e formatação de resposta.
- **Sintomas no Código**:
  - Arquivos gigantes (`routes/task_routes.py`, `AppManager.js`) com centenas de linhas concentrando ciclo de vida completo da aplicação.
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
  - `self.notifications = []` ou `let globalCache = {}; let totalRevenue = 0;` em módulos utilitários.
  - Listas globais de sessões ativas sem persistência em banco ou cache distribuído (Redis).
- **Impacto**: Perda total de dados ao reiniciar o processo, inconsistência severa em ambientes com múltiplos workers/processos (ex: Gunicorn/Uvicorn/PM2/Cluster).
- **Solução Arquitetural**:
  - Persistir dados transacionais em banco de dados ou mensageria; externalizar serviços voláteis para filas ou chamadas síncronas parametrizadas.

---

### 1.6. Asynchronous Boot Race Condition (Condição de Corrida na Inicialização Assíncrona)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Inicialização do servidor HTTP (ex: `app.listen()`) antes da conclusão de rotinas assíncronas essenciais de inicialização, tais como criação de tabelas DDL, migrações de schema, carga de sementes (seeds) ou abertura do pool de banco de dados.
- **Sintomas no Código**:
  - `manager.initDb(); app.listen(port);` onde `initDb()` executa queries/callbacks de forma assíncrona em segundo plano sem sincronização.
  - Primeiras requisições recebidas pela API falhando intermitentemente com `SQLITE_ERROR: no such table` ou erros de conexão.
- **Impacto**: Instabilidade no deploy, falhas em testes automatizados de integração, indisponibilidade temporária e corrupção de inicialização.
- **Solução Arquitetural**:
  - Padrão **Composition Root** com bootstrap assíncrono explícito (ex: `server.js` chamando `async start()` que aguarda `await initDatabase(db)` antes de acionar `app.listen()`).

---

## 2. Anti-Patterns de Segurança e Configuração

### 2.1. Hardcoded Secrets (Segredos e Credenciais no Código-Fonte)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Presença de chaves de criptografia (`SECRET_KEY`), credenciais de banco de dados, senhas de SMTP ou tokens de API embutidos diretamente no código-fonte.
- **Sintomas no Código**:
  - `const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123..." }`
  - `app.config['SECRET_KEY'] = 'super-secret-key-123'`
- **Impacto**: Vazamento de credenciais em repositórios, comprometimento total da aplicação e infraestrutura.
- **Solução Arquitetural**:
  - Centralizar configurações em módulo `config/settings.js` / `config/settings.py`, consumindo variáveis de ambiente (`process.env`, `dotenv`, `os.getenv`), mantendo `.env.example` versionado e `.env` no `.gitignore`.

---

### 2.2. Insecure / Broken Cryptography (Criptografia Inadequada ou Caseira)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Uso de algoritmos de hash rápidos e obsoletos (MD5, SHA-1), ausência de salt na persistência de senhas ou implementação de algoritmos de pseudo-criptografia caseiros (*homebrewed crypto*).
- **Sintomas no Código**:
  - Funções de hashing artesanais, como loops de concatenação de substrings em Base64 (`badCrypto(pwd)`).
  - `hashlib.md5(password.encode()).hexdigest()` ou salvamento de senhas sem salt.
- **Impacto**: Vulnerabilidade imediata a ataques de força bruta, dicionário e tabelas arco-íris (*rainbow tables*).
- **Solução Arquitetural**:
  - Adotar bibliotecas e algoritmos padrão da indústria com derivação de chave e salt configurável: `crypto.scryptSync(password, salt, 32)` / `bcrypt` / `argon2` no Node.js; `werkzeug.security` (`generate_password_hash`, `check_password_hash`) no Python.

---

### 2.3. Sensitive Data Exposure & Unsafe Logging (Vazamento de Dados Sensíveis e Logs Inseguros)
- **Severidade Padrão**: **CRITICAL**
- **Sinônimos**: *CWE-532 (Insertion of Sensitive Information into Log File), Plaintext PII Logging, Password Leakage*.
- **Descrição**: Exposição de dados confidenciais (números completos de cartão de crédito/PAN, CVVs, senhas em texto plano, tokens de autenticação ou chaves secretas de produção) através de saídas de log (`console.log`, `logging.info`) ou em serializers/respostas públicas de API.
- **Sintomas no Código**:
  - `console.log("Processando cartão " + cc + " na chave " + config.paymentGatewayKey)`.
  - Serializers retornando campos confidenciais: `def to_dict(self): return {'id': self.id, 'password': self.password}`.
- **Impacto**: Violação de legislações de privacidade (LGPD, GDPR) e padrões da indústria de pagamentos (PCI-DSS); exposição de dados de clientes e credenciais operacionais em ferramentas de observabilidade (CloudWatch, Datadog, ELK).
- **Solução Arquitetural**:
  - Eliminar impressões de credenciais e dados de cartões em logs; adotar mascaramento (*masking* / tokenização).
  - Configurar schemas e serializadores DTO com campos sensíveis marcados como `load_only` (apenas entrada, nunca saída).

---

### 2.4. Fake Authentication / Broken Access Control (Autenticação Fictícia ou Frágil)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Emissão de tokens de autenticação estáticos, falsos ou não assinados criptograficamente, sem expiração ou validação nos endpoints protegidos.
- **Sintomas no Código**:
  - Endpoint `/login` retornando `"fake-jwt-token-" + str(user.id)`.
  - Ausência de middleware ou decorador de validação de autenticação e verificação de papéis/roles (`admin`, `manager`, `user`).
- **Solução Arquitetural**:
  - Implementar tokens assinados com expiração configurável (ex: `itsdangerous.URLSafeTimedSerializer`, `jsonwebtoken` ou `PyJWT`) e middleware de autorização.

---

### 2.5. SQL Injection / String-Built Queries (Injeção de SQL)
- **Severidade Padrão**: **CRITICAL**
- **Descrição**: Construção de comandos SQL utilizando interpolação ou concatenação de strings com dados fornecidos pelo usuário.
- **Sintomas no Código**:
  - `cursor.execute(f"SELECT * FROM produtos WHERE nome = '{nome}'")` ou `db.run("DELETE FROM users WHERE id = " + id)`
- **Solução Arquitetural**:
  - Utilizar exclusivamente consultas parametrizadas com placeholders (`?` no SQLite/Node/Python, `%s` no PostgreSQL) ou ORM com query builder seguro.

---

## 3. Anti-Patterns de Banco de Dados e Performance

### 3.1. N+1 Query Problem (Problema de Consultas N+1)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Execução de uma query inicial para buscar $N$ registros pai, seguida de $N$ queries individuais em um loop para buscar os relacionamentos de cada item filho, frequentemente coordenada por contadores manuais suscetíveis a condições de corrida.
- **Sintomas no Código**:
  - Iteração sobre cursos disparando queries individuais em `enrollments`, e dentro de cada matrícula disparando queries em `users` e `payments` (`coursesPending--`, `enrPending--`).
  - Iteração sobre tarefas com `User.query.get(task.user_id)` dentro do loop.
- **Impacto**: Degradação exponencial de tempo de resposta e sobrecarga severa no banco de dados com aumento de volume.
- **Solução Arquitetural**:
  - Utilizar Eager Loading com `joinedload` / `selectinload` no SQLAlchemy ou queries SQL explícitas com `JOIN` (`LEFT JOIN enrollments ... LEFT JOIN payments`) e agregação estruturada em memória ou via `GROUP BY`.

---

### 3.2. Unscoped / Leaking Database Connections (Vazamento de Conexões de Banco)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Criação de conexões globais com o banco de dados que não respeitam o ciclo de vida da requisição HTTP ou que nunca são fechadas.
- **Solução Arquitetural**:
  - Vincular a conexão ao ciclo de vida da requisição (ex: Flask `g.db` com hook `@app.teardown_appcontext`, pool gerenciado pelo ORM ou helpers encapsulados de banco de dados).

---

### 3.3. Missing Transaction Boundaries (Ausência de Limite Transacional / Operações Não-Atômicas)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Execução de fluxos de negócio que realizam múltiplas alterações interdependentes no banco de dados (ex: criação de usuário $\to$ criação de matrícula $\to$ registro de pagamento $\to$ log de auditoria) através de queries avulsas, sem encapsulamento em uma transação ACID (`BEGIN TRANSACTION` / `COMMIT` / `ROLLBACK`).
- **Sintomas no Código**:
  - Inserções sequenciais em callbacks ou awaits sucessivos onde uma falha na etapa 2 ou 3 deixa os dados da etapa 1 persistidos permanentemente no banco.
  - Aluno criado e matriculado sem que o pagamento correspondente tenha sido registrado devido a uma falha intermediária de rede ou banco.
- **Impacto**: Inconsistência irreparável de dados, registros financeiros fantasmas, violação das garantias ACID e prejuízo financeiro/operacional.
- **Solução Arquitetural**:
  - Encapsular operações multi-tabela em helpers transacionais com rollback automático (ex: `withTransaction(db, async () => { ... })` ou `db.session.begin()`).

---

### 3.4. Orphan Records & Missing Referential Integrity (Dados Órfãos e Falha de Integridade Referencial)
- **Severidade Padrão**: **HIGH** / **MEDIUM**
- **Descrição**: Exclusão de registros pai (ex: exclusão de um usuário) sem exclusão coordenada ou em cascata dos seus registros dependentes (ex: matrículas, pagamentos, tarefas associadas), gerando registros órfãos que violam a integridade referencial.
- **Sintomas no Código**:
  - Rota `DELETE /api/users/:id` executando apenas `DELETE FROM users WHERE id = ?` e retornando sucesso, deixando linhas em `enrollments` e `payments` apontando para um `user_id` inexistente.
- **Impacto**: Falhas em consultas com integridade referencial estrita, poluição da base com registros zumbis e distorção em relatórios analíticos e contábeis.
- **Solução Arquitetural**:
  - Implementar exclusão transacional em cascata coordenada na camada de serviço (`deletePaymentsByUserId` $\to$ `deleteEnrollmentsByUserId` $\to$ `deleteUserById`) ou habilitar constraints de banco com `ON DELETE CASCADE` e suporte ativo a foreign keys.

---

## 4. Code Smells de Manutenibilidade e Limpeza de Código

### 4.1. Shotgun Surgery (Cirurgia por Espingarda / Regras Espalhadas)
- **Severidade Padrão**: **HIGH**
- **Descrição**: Uma única regra de negócio (ex: checagem de tarefa atrasada `is_overdue`, cálculo de desconto ou validação de status) duplicada em dezenas de arquivos diferentes, exigindo edições espalhadas a cada mudança de especificação.
- **Sintomas no Código**:
  - A mesma comparação `due_date < datetime.utcnow()` ou validação de cartão copiada em rotas de tarefas, rotas de usuários, relatórios e helpers.
- **Solução Arquitetural**:
  - Centralizar a regra de negócio no Model de domínio (ex: `Task.is_overdue()`) ou em um Service especializado (`checkoutService.js`, `paymentGateway.js`).

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
- **Descrição**: Classes/serviços existentes que nunca são instanciados ou chamados no fluxo da aplicação, variáveis/constantes exportadas que nunca são lidas e pacotes listados em dependências que não são utilizados.
- **Sintomas no Código**:
  - Variáveis como `totalRevenue = 0` ou `smtpUser` exportadas em `utils.js` mas sem uso real no fluxo da aplicação.
- **Solução Arquitetural**:
  - Remover código morto e variáveis obsoletas, ou integrá-los adequadamente na arquitetura caso façam parte do escopo de requisitos.

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
- **Sintomas no Código**:
  - Estruturas em pirâmide (`db.get(..., () => { db.get(..., () => { db.run(..., () => { ... }) }) })`).
- **Impacto**: Código ilegível, alta propensão a bugs de concorrência, dificuldade de manutenção e falhas silenciosas na propagação de erros.
- **Solução Arquitetural**:
  - Promisificar operações de banco de dados com wrappers (`dbRun`, `dbGet`, `dbAll`) e adotar `async/await` estruturado.

---

### 4.9. Cryptic Naming & Parameter Obfuscation (Nomenclatura Críptica e Parâmetros Ofuscados)
- **Severidade Padrão**: **LOW**
- **Descrição**: Uso de variáveis, parâmetros ou propriedades com identificadores truncados ou abreviados (ex: `usr`, `eml`, `pwd`, `c_id`, `cc`, `u`, `e`, `p`, `cid`), prejudicando a clareza do modelo de domínio.
- **Solução Arquitetural**:
  - Manter compatibilidade com contratos legados na camada de borda (Controller/DTO) mapeando as propriedades para nomes semânticos e expressivos (`username`, `email`, `password`, `courseId`, `cardNumber`) nas camadas internas de Serviço e Modelo.

---

## 5. Anti-Patterns de Tratamento de Erros e Observabilidade

### 5.1. Poor Error Handling / Silent Failures (Tratamento Pobre de Erros e Supressão de Exceções)
- **Severidade Padrão**: **MEDIUM**
- **Descrição**: Ignorar argumentos de erro em callbacks (`if (err) /* nada */`), capturar exceções genéricas com simples `print(e)` sem tratamento, retornar status HTTP 200 em operações falhas ou quando entidades não existem, ou mascarar a causa raiz do problema.
- **Sintomas no Código**:
  - Callback de `audit_logs` ignorando o parâmetro `err`.
  - `DELETE /api/users/:id` retornando mensagem de sucesso mesmo se a exclusão afetar 0 linhas no banco ou disparar erro de SQL.
- **Solução Arquitetural**:
  - Criar classe de erro customizada de aplicação (`AppError` com `statusCode`).
  - Centralizar a formatação de respostas de erro na camada **View** (`httpResponses.sendError`), garantindo status HTTP corretos (400 para validação/regras, 404 para não encontrado, 500 para falhas internas) e logging estruturado.

---

## 6. Guia de Mapeamento para Arquitetura MVC

Ao refatorar um projeto para o padrão **MVC**, siga o mapeamento de responsabilidades abaixo (compatível com Node.js/Express e Python/Flask):

| Camada | Arquivos Típicos (Node.js / Python) | Responsabilidade Principal | O que DEVE Conter | O que NÃO DEVE Conter |
|---|---|---|---|---|
| **View** | `views/httpResponses.js`, templates / serializers | Formatação de respostas e apresentação | Funções de envio de resposta HTTP (`sendJson`, `sendError`, `sendText`), serialização DTO | Queries SQL, regras de negócio de domínio, persistência |
| **Routes** | `routes/index.js`, Blueprints Flask | Mapeamento de URLs para Controllers | Declaração de endpoints HTTP (`GET`, `POST`, `DELETE`), aplicação de middlewares | Lógica de negócio, queries de banco, parsing complexo |
| **Controller** | `controllers/*Controller.js`, `controllers/*_controller.py` | Orquestração do caso de uso HTTP | Extração de parâmetros de `req.body`/`req.params`, chamada dos Services, delegação da resposta para a View | Queries SQL diretas, regras de cálculo complexas de domínio |
| **Service** | `services/*Service.js`, `services/*_service.py` | Regras de negócio e casos de uso | Lógica de domínio, orquestração de transações (`withTransaction`), integrações externas (pagamentos, senhas) | Objetos de requisição/resposta HTTP (`req`, `res`, `Flask request`) |
| **Model** | `models/*Model.js`, `models/*_model.py` | Acesso a dados e entidades | Queries SQL parametrizadas, métodos de busca/inserção/deleção, mapeamento de tabelas | Tratamento de requisições HTTP, formatação de status de resposta |
| **Config** | `config/settings.js`, `config/settings.py` | Configuração centralizada | Leitura de variáveis de ambiente (`process.env`, `os.getenv`), portas, chaves, defaults seguros | Lógica executável da aplicação, credenciais hardcoded |
| **Database / DB** | `db/database.js`, `db/database.py` | Conexão e infraestrutura de banco | Abertura de conexão, helpers de Promises (`dbRun`, `dbGet`, `dbAll`), execução de transações (`withTransaction`), inicialização de schema | Regras de negócio de domínios específicos |
| **Middleware / Errors** | `services/errors.js`, `middlewares/` | Tratamento transversal e erros | Classes de exceção (`AppError`), interceptadores de autenticação, handlers globais de erro | Regras específicas de um único domínio |
