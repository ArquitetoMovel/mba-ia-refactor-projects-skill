# Severity Levels for Code & Architecture Issues

Guia de classificação de severidade para detecção de code smells, vulnerabilidades e anti-patterns na fase de análise arquitetural (**Phase 2**).

---

## 1. Classificação por Nível de Severidade

### CRITICAL (Crítico)
Problemas graves que comprometem a segurança da aplicação, causam vulnerabilidades exploráveis, expõem dados sensíveis/credenciais ou violam de forma estrutural a integridade do sistema.

- **Critérios de Enquadramento**:
  - Exposição de credenciais, chaves de API de produção ou segredos no código-fonte (*Hardcoded Secrets* — ex: `SECRET_KEY`, SMTP passwords).
  - Exposição ou gravação de dados sensíveis/PII em logs ou respostas públicas (*Sensitive Data Exposure* / *CWE-532* — ex: hash de senhas em `to_dict()`, número de cartão em logs).
  - Criptografia inadequada ou pseudo-hashing para senhas (*Insecure / Broken Cryptography* — ex: MD5, SHA-1 simples, ausência de salt).
  - Falha de autenticação/autorização (*Fake Authentication / Broken Access Control* — ex: tokens JWT falsos/estáticos `fake-jwt-token-{id}`, ausência de verificação de permissões).
  - Vulnerabilidades de injeção de código ou SQL (*SQL Injection* — ex: concatenação direta de strings em queries SQL).
  - *God Object* / *God Routes* onde todo o ciclo de vida (banco, regras, autenticação e HTTP) reside em um único módulo sem separação básica.
- **Ação Requerida**: Bloqueia release / prioridade imediata de correção no refactor.

---

### HIGH (Alto)
Violações graves de padrões arquiteturais (MVC, Clean Architecture, SOLID), ausência de delimitação transacional em operações críticas de negócio e gargalos severos de manutenibilidade ou escalabilidade.

- **Critérios de Enquadramento**:
  - Falta de separação de responsabilidades (*Lack of Separation of Concerns*): rotas orquestrando persistência, transações e regras de negócio sem camadas de Controller, Service ou Model.
  - Ausência de transações em escritas multi-tabela (*Missing Transaction Boundaries*): inserções sequenciais sem controle transacional ACID e sem rollback adequado.
  - Condição de corrida na inicialização (*Asynchronous Boot Race Condition* / *Missing Application Factory*): inicialização global rígida ou iniciar listener HTTP antes da finalização assíncrona de criação de tabelas e seeds.
  - Falha de integridade referencial e dados órfãos (*Orphan Records*): exclusão de entidades pai sem exclusão em cascata transacional dos registros dependentes.
  - *Shotgun Surgery*: lógica de negócio ou validações duplicadas em múltiplos módulos (ex: checagem de overdue copiada em 6+ arquivos, validações manuais de status).
  - Problema de Queries N+1 no banco de dados (*N+1 Queries*) gerando degradação exponencial de I/O por registros filhos.
  - Estado global mutável em memória (*Mutable Global State*) que impede escalabilidade horizontal e desincroniza instâncias em cluster/workers (ex: `self.notifications = []`).
  - Forte acoplamento (*Tight Coupling*) entre módulos ou ausência de controle do ciclo de vida de conexões com o banco.
- **Ação Requerida**: Correção obrigatória na fase de refatoração para garantir sustentabilidade e integridade do projeto.

---

### MEDIUM (Médio)
Problemas de manutenibilidade, complexidade ciclomática elevada, desorganização de domínios, aninhamento assíncrono excessivo ou tratamento inadequado de exceções.

- **Critérios de Enquadramento**:
  - Aninhamento excessivo de callbacks (*Callback Hell* / *Pyramid of Doom*) e coordenação manual de assincronia.
  - Métodos longos e complexos (*Long Method* / *Monster Function*) acumulando múltiplas responsabilidades e fluxos condicionais aninhados.
  - Domínios misturados (*Misplaced Responsibilities*), como endpoints de CRUD de uma entidade definidos dentro de arquivos de rotas de outra entidade (ex: CRUD de `/categories` em `report_routes.py`).
  - Tratamento inadequado de erros (*Poor Error Handling* / *Silent Failures*): uso de `bare except`, captura genérica com `print()` sem logger estruturado, ou retorno de status incoerente.
  - *Dead Code* e variáveis/dependências fantasmas (*Phantom Dependencies*): módulos existentes nunca instanciados (ex: `NotificationService` sem uso), pacotes não utilizados declarados em `requirements.txt` (ex: `marshmallow` sem schemas, `requests`), e funções auxiliares mortas.
  - Inveja de Recursos (*Feature Envy*): funções acessando intensivamente dados de outro objeto em vez de delegar o comportamento.
- **Ação Requerida**: Refatoração estruturada durante a reorganização das camadas.

---

### LOW (Baixo)
Inconsistências cosméticas, legibilidade de código, nomenclatura críptica, convenções e obsolescências menores.

- **Critérios de Enquadramento**:
  - Nomenclatura críptica e parâmetros ofuscados (*Cryptic Naming* — ex: `usr`, `eml`, `pwd`, `cat`, `p`).
  - Uso de APIs ou funções depreciadas que ainda funcionam, mas estão obsoletas (ex: `datetime.utcnow()` no Python 3.12+).
  - *Magic Numbers* e literais soltos no código sem constantes nomeadas.
  - Expressões booleanas redundantes ou retornos excessivamente verbosos (`if condition: return True else: return False`).
  - Políticas de validação brandas ou tolerantes demais (ex: tamanho mínimo de senha de 4 caracteres).
  - Inconsistências menores de estilo e formatação.
- **Ação Requerida**: Correção oportuna durante a limpeza e padronização do código.

---

## 2. Matriz Rápida de Decisão

| Tipo de Problema | Exemplo Típico | Severidade Padrão |
|---|---|---|
| Credenciais hardcoded / Secret Key | `SECRET_KEY = '123456'` / `SMTP_USER = "admin@email.com"` | **CRITICAL** |
| Dados sensíveis em log / API | `console.log(cc)` / `return {'password': self.password}` | **CRITICAL** |
| Hashing fraco / Crypto caseira | `hashlib.md5(pwd)` sem salt / `badCrypto(pwd)` via Base64 | **CRITICAL** |
| SQL Injection / Concatenação | `cursor.execute(f"SELECT * FROM users WHERE id = '{id}'")` | **CRITICAL** |
| Autenticação fictícia | `return 'fake-jwt-token-' + user.id` | **CRITICAL** |
| God Object / Monolithic Routes | Rota com 200+ linhas fazendo query, validação e serialização | **CRITICAL** / **HIGH** |
| Operação multi-tabela sem transação | Inserir múltiplos registros dependentes sem controle atômico | **HIGH** |
| Boot Race Condition / Sem Factory | `app.listen()` antes de `initDb()` / app sem `create_app()` | **HIGH** |
| Dados órfãos / DELETE sem cascade | `DELETE FROM users` mantendo tarefas associadas no banco | **HIGH** / **MEDIUM** |
| Query N+1 | Loop fazendo `User.query.get(id)` para cada registro filho | **HIGH** |
| Estado global em memória | `self.notifications = []` guardando histórico volátil | **HIGH** |
| Regra duplicada em 3+ locais | Cálculo de overdue copiado em rotas, models e helpers | **HIGH** |
| Callback Hell / Pyramid of Doom | 4+ níveis de callbacks assíncronos aninhados (`db.get -> db.run`) | **MEDIUM** |
| Método Longo / Monster Function | Endpoint com 90 linhas contendo queries, loops e validações | **MEDIUM** |
| Endpoint no módulo errado | CRUD de `/categories` dentro de `report_routes.py` | **MEDIUM** |
| `print()` em vez de logger / Bare except | `except: print(err)` mascarando erros reais | **MEDIUM** |
| Código morto / Dep não usada | `NotificationService` nunca chamado / `marshmallow` sem schemas | **MEDIUM** |
| Nomenclatura críptica / parâmetros | `usr`, `eml`, `pwd`, `cat` em vez de identificadores semânticos | **LOW** |
| API depreciada | `datetime.utcnow()` no Python 3.12 | **LOW** |
| Magic numbers / política fraca | `MIN_PASSWORD_LENGTH = 4` / `priority = 3` sem constante | **LOW** |
| Booleano verboso | `if valid: return True else: return False` | **LOW** |
