# Severity Levels for Code & Architecture Issues

Guia de classificação de severidade para detecção de code smells, vulnerabilidades e anti-patterns na fase de análise arquitetural (**Phase 2**).

---

## 1. Classificação por Nível de Severidade

### CRITICAL (Crítico)
Problemas graves que comprometem a segurança da aplicação, causam vulnerabilidades exploráveis, expõem dados sensíveis/credenciais ou violam de forma estrutural a integridade do sistema.

- **Critérios de Enquadramento**:
  - Exposição de credenciais, chaves de API de produção ou segredos no código-fonte (*Hardcoded Secrets*).
  - Exposição ou gravação de dados sensíveis/PII em logs de aplicação (*Sensitive Data Logging* / *CWE-532* — ex: número de cartão de crédito, CVV, senhas ou payment keys em `console.log`).
  - Criptografia inadequada ou pseudo-hashing caseiro para senhas (*Insecure / Broken Cryptography* — ex: MD5, SHA-1 simples, loops de substrings Base64 como `badCrypto`, ausência de salt).
  - Vazamento de dados sensíveis em respostas de API públicas (ex: retorno de hash de senha em serializers/`to_dict`).
  - Falha de autenticação/autorização (ex: tokens JWT falsos/estáticos, endpoints sem validação de acesso).
  - Vulnerabilidades de injeção de código ou SQL (ex: concatenação direta de strings em queries SQL).
  - *God Object* / *God Routes* onde todo o ciclo de vida (banco, regras, pagamento, autenticação e HTTP) reside em um único módulo sem separação básica.
- **Ação Requerida**: Bloqueia release / prioridade imediata de correção no refactor.

---

### HIGH (Alto)
Violações graves de padrões arquiteturais (MVC, Clean Architecture, SOLID), ausência de delimitação transacional em operações críticas de negócio e gargalos severos de manutenibilidade ou escalabilidade.

- **Critérios de Enquadramento**:
  - Falta de separação de responsabilidades (*Lack of Separation of Concerns*): rotas orquestrando persistência, transações e regras de negócio sem camadas de Controller, Service ou Model.
  - Ausência de transações em escritas multi-tabela (*Missing Transaction Boundaries*): inserções sequenciais sem `BEGIN`/`COMMIT`/`ROLLBACK`, gerando inconsistência e corrupção de estado.
  - Condição de corrida na inicialização (*Asynchronous Boot Race Condition*): iniciar listener HTTP (`app.listen()`) antes da finalização assíncrona de criação de tabelas, migrações e seeds.
  - Falha de integridade referencial e dados órfãos (*Orphan Records*): exclusão de entidades pai sem exclusão em cascata transacional dos registros dependentes.
  - *Shotgun Surgery*: lógica de negócio ou validações duplicadas em múltiplos módulos (ex: validação de cartão, regras de cálculo, checagens de status).
  - Problema de Queries N+1 no banco de dados (*N+1 Queries*) gerando degradação exponencial de I/O e contenção assíncrona.
  - Estado global mutável em memória (*Mutable Global State*) que impede escalabilidade horizontal e desincroniza instâncias em cluster/workers.
  - Forte acoplamento (*Tight Coupling*) entre módulos ou ausência de controle do ciclo de vida de conexões com o banco.
- **Ação Requerida**: Correção obrigatória na fase de refatoração para garantir sustentabilidade e integridade do projeto.

---

### MEDIUM (Médio)
Problemas de manutenibilidade, complexidade ciclomática elevada, desorganização de domínios, aninhamento assíncrono excessivo ou tratamento inadequado de exceções.

- **Critérios de Enquadramento**:
  - Aninhamento excessivo de callbacks (*Callback Hell* / *Pyramid of Doom*) e coordenação manual de assincronia via contadores manuais.
  - Métodos longos e complexos (*Long Method* / *Blob Procedure*) acumulando múltiplas responsabilidades e fluxos condicionais aninhados.
  - Domínios misturados (*Misplaced Responsibilities*), como endpoints de uma entidade definidos dentro de arquivos de rotas de outra entidade.
  - Tratamento inadequado de erros (*Poor Error Handling* / *Silent Failures*): supressão de parâmetros de erro em callbacks, captura com `print()` genérico, retorno de 200 em entidades inexistentes e ausência de classes de erro de domínio (`AppError`).
  - *Dead Code* e variáveis/dependências fantasmas (*Phantom Dependencies*): módulos, constantes ou pacotes declarados que não são utilizados no fluxo da aplicação.
  - Inveja de Recursos (*Feature Envy*): funções acessando intensivamente dados de outro objeto em vez de delegar o comportamento.
- **Ação Requerida**: Refatoração estruturada durante a reorganização das camadas.

---

### LOW (Baixo)
Inconsistências cosméticas, legibilidade de código, nomenclatura críptica, convenções e obsolescências menores.

- **Critérios de Enquadramento**:
  - Nomenclatura críptica e parâmetros ofuscados (*Cryptic Naming* — ex: `usr`, `eml`, `pwd`, `c_id`, `card`, `u`, `e`, `p`).
  - Uso de APIs ou funções depreciadas que ainda funcionam, mas estão obsoletas (ex: `datetime.utcnow()` no Python 3.12+).
  - *Magic Numbers* e literais soltos no código sem constantes nomeadas.
  - Expressões booleanas redundantes ou retornos excessivamente verbosos (`if condition: return True else: return False`).
  - Inconsistências menores de estilo e formatação.
- **Ação Requerida**: Correção oportuna durante a limpeza e padronização do código.

---

## 2. Matriz Rápida de Decisão

| Tipo de Problema | Exemplo Típico | Severidade Padrão |
|---|---|---|
| Credenciais hardcoded / Secret Key | `const config = { dbPass: "secret123" }` / `SECRET_KEY = '123'` | **CRITICAL** |
| Dados sensíveis em log (CWE-532) | `console.log("Cartão:", cc, "Chave:", key)` | **CRITICAL** |
| Hashing fraco / Crypto caseira | `badCrypto(pwd)` via Base64 / `hashlib.md5(pwd)` sem salt | **CRITICAL** |
| SQL Injection / Concatenação | `"DELETE FROM users WHERE id = " + id` | **CRITICAL** |
| Autenticação fictícia | `return 'fake-jwt-token-' + user.id` | **CRITICAL** |
| God Object / Monolithic Class | `AppManager.js` com DB, HTTP, rotas, regras e pagamentos | **CRITICAL** / **HIGH** |
| Operação multi-tabela sem transação | Inserir matrícula e pagamento sem `withTransaction` / `COMMIT` | **HIGH** |
| Boot Race Condition | `app.listen()` invocado antes de `initDb()` assíncrono concluir | **HIGH** |
| Dados órfãos / DELETE sem cascade | `DELETE FROM users` mantendo matrículas e pagamentos no banco | **HIGH** / **MEDIUM** |
| Query N+1 | Loop fazendo queries individuais por item pai com contadores manuais | **HIGH** |
| Estado global em memória | `globalCache = {}`, `notifications = []` em módulo singleton | **HIGH** |
| Callback Hell / Pyramid of Doom | 4+ níveis de callbacks assíncronos aninhados (`db.get -> db.run`) | **MEDIUM** |
| Método Longo / Monster Function | Endpoint com 100 linhas contendo queries, loops e validações | **MEDIUM** |
| Endpoint no módulo errado | CRUD de `/categories` dentro de `report_routes.py` | **MEDIUM** |
| Silenciamento / Erro inconsistente | Callback ignorando `err` ou `DELETE` retornando 200 para ID inexistente | **MEDIUM** |
| Código morto / Variável não usada | `totalRevenue = 0` exportada em `utils.js` sem nenhum consumidor | **MEDIUM** |
| Nomenclatura críptica / parâmetros | `usr`, `eml`, `pwd`, `c_id`, `cc` em vez de identificadores semânticos | **LOW** |
| API depreciada | `datetime.utcnow()` no Python 3.12 | **LOW** |
| Magic numbers / literais soltos | `if (status === 1)` / `MIN_LEN = 4` sem constantes | **LOW** |
| Booleano verboso | `if (valid) return true; else return false;` | **LOW** |
