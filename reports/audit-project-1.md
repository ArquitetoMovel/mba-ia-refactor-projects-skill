# Architecture Audit Report — Project 1: code-smells-project

**Stack:** Python 3 + Flask 3.1.1 + SQLite (`loja.db`)  
**Domain:** E-commerce RESTful API (produtos, pedidos, usuários, relatórios de vendas)  
**Execution Phase:** Phase 2 (Code Smells & Architecture Issues Detection)  
**Skill:** `refactor-arch`

---

## 1. Summary of Findings

| Severity | Count | Primary Impact Areas |
|----------|-------|----------------------|
| **CRITICAL** | 5 | SQL Injection, Arbitrary SQL Execution, Unauthenticated DB Reset, Plaintext Credentials Leakage, God Class/Module |
| **HIGH** | 5 | Broken MVC, Business Logic in Controllers, Global Mutable DB Connection, Tight Coupling, N+1 Queries |
| **MEDIUM** | 4 | Duplicated Code, Long Methods, Generic Error Handling / Leaked Exceptions, Weak Input Validation |
| **LOW** | 3 | Magic Numbers in Discounts, Port/Config Inconsistencies, Unused Imports |
| **TOTAL** | **17** | **Exceeds minimum threshold (≥ 5 findings)** |

---

## 2. Detailed Findings (Ordered by Severity)

### [CRITICAL] SQL Injection via String Concatenation
- **Location:** `models.py` (`get_produto_por_id`, `criar_produto`, `atualizar_produto`, `deletar_produto`, `login_usuario`, `criar_usuario`, `criar_pedido`, `get_pedidos_usuario`, `get_todos_pedidos`, `atualizar_status_pedido`, `buscar_produtos`)
- **Description:** Queries SQL construídas concatenando strings com dados fornecidos diretamente pelo usuário sem uso de queries parametrizadas (`?`).
- **Impact:** Permite evasão de autenticação, extração integral de dados, bypass de estoque e alteração arbitrária da base.
- **Recommendation:** Substituir todas as queries por queries 100% parametrizadas com placeholders `?` e cursores do SQLite.

### [CRITICAL] Arbitrary SQL Execution Endpoint (`POST /admin/query`)
- **Location:** `app.py` (`executar_query`)
- **Description:** Rota administrativa pública que aceita strings SQL arbitrárias no corpo da requisição JSON e as executa diretamente no banco sem autenticação.
- **Impact:** RCE equivalente no banco de dados com poder de leitura, escrita e exclusão DDL irrestrita.
- **Recommendation:** Remover permanentemente o endpoint da aplicação.

### [CRITICAL] Unauthenticated Destructive Database Reset (`POST /admin/reset-db`)
- **Location:** `app.py` (`reset_database`)
- **Description:** Endpoint que apaga todas as tabelas e dados do banco sem autenticação ou confirmação de token.
- **Impact:** Negação de serviço e perda irreversível de dados por agentes maliciosos.
- **Recommendation:** Proteger o endpoint exigindo header `X-Admin-Token` configurado via variável de ambiente `ADMIN_TOKEN`.

### [CRITICAL] Plaintext Credentials & Secrets Exposure
- **Location:** `app.py` (`SECRET_KEY` hardcoded), `controllers.py` (`health_check`), `database.py` (senhas em plaintext no seed), `models.py` (`get_todos_usuarios`, `get_usuario_por_id` retornando campo `senha`)
- **Description:** Chave secreta embutida no código, senhas salvas em texto puro sem salt/hash e vazamento do hash/senha em endpoints de listagem de usuários e health check.
- **Impact:** Comprometimento total de contas de usuários e administradores.
- **Recommendation:** Externalizar `SECRET_KEY` para variáveis de ambiente, adotar hashing forte via Werkzeug (`generate_password_hash`/`check_password_hash`) e sanitizar saídas HTTP.

### [CRITICAL] God Object / God Module (`models.py`)
- **Location:** `models.py` (~314 LOC)
- **Description:** Arquivo único contendo persistência SQL, regras de estoque, cálculos de faturamento, autenticação, mappers de dados e envio de notificações para 4 domínios diferentes.
- **Impact:** Violação severa de SRP (Single Responsibility Principle), impossibilidade de testes unitários isolados e alto risco de regressão.
- **Recommendation:** Decompor em models (`produto_model.py`, `usuario_model.py`, `pedido_model.py`, `relatorio_model.py`) e serviços de domínio dedicados.

### [HIGH] Lack of Separation of Concerns (Quebra de MVC)
- **Location:** `app.py`, `controllers.py`, `models.py`, `database.py`
- **Description:** Controladores contendo regras de negócio e validações; models contendo lógica de desconto e SQL; ausência de camada de serviços e ausência de desacoplamento.
- **Recommendation:** Reestruturar em Views (rotas e status HTTP), Controllers (adaptadores), Services (regras de negócio) e Models (persistência).

### [HIGH] Business Logic & Side Effects in Controllers
- **Location:** `controllers.py` (`criar_produto`, `atualizar_produto`, `criar_pedido`, `atualizar_status_pedido`)
- **Description:** Notificações mockadas (e-mail, SMS, push) e validações de regras de catálogo acopladas diretamente nos manipuladores HTTP.
- **Recommendation:** Extrair para `services/notificacao_service.py` e `services/produto_service.py`.

### [HIGH] Global Mutable Database Connection
- **Location:** `database.py` (`db_connection`, `get_db`)
- **Description:** Objeto de conexão SQLite único e global compartilhado com `check_same_thread=False`.
- **Recommendation:** Gerenciar conexões por ciclo de vida de requisição usando o contexto `flask.g` com fechamento automático em `teardown_appcontext`.

### [HIGH] Tight Coupling without Dependency Injection
- **Location:** `controllers.py` importando `models` e `database` diretamente.
- **Description:** Acoplamento estático e direto impedindo mock e testes unitários independentes.
- **Recommendation:** Estruturar controllers e services com injeção de dependências em `deps.py`.

### [HIGH] N+1 Query Antipattern
- **Location:** `models.py` (`get_pedidos_usuario`, `get_todos_pedidos`)
- **Description:** Para cada pedido retornado, uma query secundária é executada para buscar `itens_pedido` e outra para `produtos`.
- **Recommendation:** Utilizar queries otimizadas com `JOIN` agrupando itens de pedido em uma única consulta.

### [MEDIUM] Duplicated Code
- **Location:** `controllers.py` (validações repetidas em criação e edição); `models.py` (mapeamentos `row -> dict`).
- **Recommendation:** Centralizar mappers de dados em `models/mappers.py` e validações nos serviços.

### [MEDIUM] Long Methods
- **Location:** `controllers.criar_produto`, `models.criar_pedido`, `models.relatorio_vendas`, `models.get_todos_pedidos`.
- **Recommendation:** Quebrar métodos longos em funções especializadas de validação, cálculo e persistência.

### [MEDIUM] Poor Error Handling and Logging
- **Location:** `controllers.py` (`except Exception as e:` com `print(e)`).
- **Recommendation:** Implementar middleware centralizado `middlewares/error_handler.py` com exceções customizadas (`AppError`) e módulo padrão `logging`.

### [MEDIUM] Weak Input Validation
- **Location:** `controllers.criar_usuario`, `controllers.login`, `controllers.criar_pedido`.
- **Recommendation:** Validar formato de e-mail, tipos de dados, preços positivos e limites de campos.

### [LOW] Magic Numbers
- **Location:** `models.relatorio_vendas` (valores `10000`, `5000`, `1000` e alíquotas `0.10`, `0.05`, `0.02`).
- **Recommendation:** Extrair constantes nomeadas `DESCONTO_FAIXAS` em `config/settings.py`.

### [LOW] Inconsistent Documentation / Settings
- **Location:** `README.md` mencionava porta `5000`, mas código rodava na porta `5003`.
- **Recommendation:** Padronizar configurações via `config/settings.py` e documentar portas e variáveis.

### [LOW] Dead / Unused Imports
- **Location:** `models.py` (`import sqlite3`).
- **Recommendation:** Remover imports desnecessários.
