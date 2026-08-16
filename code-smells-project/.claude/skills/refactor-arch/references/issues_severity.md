# Severity Levels for Code & Architecture Issues

Guia de classificação de severidade para detecção de code smells, vulnerabilidades e anti-patterns na fase de análise arquitetural (**Phase 2**).

---

## 1. Classificação por Nível de Severidade

### CRITICAL (Crítico)
Problemas graves que comprometem a segurança da aplicação, causam vulnerabilidades exploráveis, expõem dados sensíveis ou violam de forma estrutural a integridade do sistema.

- **Critérios de Enquadramento**:
  - Exposição de credenciais, chaves de API ou segredos no código-fonte (*Hardcoded Secrets*).
  - Criptografia insegura ou hashing inadequado para senhas (ex: MD5, SHA-1 simples, texto plano).
  - Vazamento de dados sensíveis/PII em respostas de API públicas (ex: retorno de hash de senha em serializers/`to_dict`).
  - Falha de autenticação/autorização (ex: tokens JWT falsos/estáticos, endpoints sem validação de acesso).
  - Vulnerabilidades de injeção de código ou SQL (ex: concatenação direta de strings em queries SQL).
  - *God Object* / *God Routes* onde todo o ciclo de vida (banco, regras, autenticação e HTTP) reside em um único módulo sem separação básica.
- **Ação Requerida**: Bloqueia release / prioridade imediata de correção no refactor.

---

### HIGH (Alto)
Violações graves de padrões arquiteturais (MVC, Clean Architecture, SOLID) e gargalos severos de manutenibilidade ou escalabilidade.

- **Critérios de Enquadramento**:
  - Falta de separação de responsabilidades (*Lack of Separation of Concerns*): rotas orquestrando persistência, transações e regras de negócio pesadas sem camadas de Controller ou Service.
  - *Shotgun Surgery*: lógica de negócio ou validações duplicadas em múltiplos módulos (ex: cálculo de atraso, regras de desconto, validação de formato de email).
  - Problema de Queries N+1 no banco de dados (*N+1 Queries*) gerando degradação exponencial de I/O.
  - Estado global mutável em memória (*Mutable Global State*) que impede escalabilidade horizontal e sobrevive de forma inconsistente entre requisições.
  - Forte acoplamento (*Tight Coupling*) entre camadas ou ausência de controle de ciclo de vida de conexões com o banco de dados.
- **Ação Requerida**: Correção obrigatória na fase de refatoração para garantir sustentabilidade do projeto.

---

### MEDIUM (Médio)
Problemas de manutenibilidade, complexidade ciclomática elevada, desorganização de domínios ou tratamento inadequado de exceções.

- **Critérios de Enquadramento**:
  - Métodos longos e complexos (*Long Method* / *Blob Procedure*) acumulando múltiplas responsabilidades.
  - Domínios misturados (*Misplaced Responsibilities*), como endpoints de uma entidade definidos dentro de arquivos de rotas de outra entidade.
  - Tratamento inadequado de erros (*Poor Error Handling*): uso de `except Exception:` genérico, `bare except`, engolimento silencioso de erros e uso de `print()` em vez de logging estruturado.
  - *Dead Code* e dependências fantasmas (*Phantom Dependencies*): módulos, classes ou pacotes declarados em requirements/package.json que não são utilizados.
  - Inveja de Recursos (*Feature Envy*): funções acessando intensivamente dados de outro objeto em vez de delegar o comportamento.
- **Ação Requerida**: Refatoração estruturada durante a reorganização das camadas.

---

### LOW (Baixo)
Inconsistências cosméticas, legibilidade de código, convenções de nomenclatura e obsolescências menores.

- **Critérios de Enquadramento**:
  - Uso de APIs ou funções depreciadas que ainda funcionam, mas estão obsoletas (ex: `datetime.utcnow()` no Python 3.12+).
  - *Magic Numbers* e literais soltos no código sem constantes nomeadas.
  - Expressões booleanas redundantes ou retornos excessivamente verbosos (`if condition: return True else: return False`).
  - Inconsistências menores de nomenclatura (ex: mistura de snake_case e camelCase, abreviações crípticas).
  - Políticas de validação brandas ou tolerantes demais (ex: tamanho mínimo de senha de 4 caracteres).
- **Ação Requerida**: Correção oportuna durante a limpeza e padronização do código.

---

## 2. Matriz Rápida de Decisão

| Tipo de Problema | Exemplo Típico | Severidade Padrão |
|------------------|----------------|-------------------|
| Credenciais hardcoded / Secret Key | `SECRET_KEY = '123456'` | **CRITICAL** |
| Hashing fraco / Vazamento de senha | `hashlib.md5(pwd)` / `return {'password': self.password}` | **CRITICAL** |
| SQL Injection / Concatenação | `"SELECT * FROM users WHERE id = " + id` | **CRITICAL** |
| Autenticação fictícia | `return 'fake-jwt-token-' + user.id` | **CRITICAL** |
| Fat Controller / God Routes | Rota com 150 linhas fazendo query, validação e lógica | **HIGH** |
| Regra duplicada em 3+ locais | Cálculo de juros/overdue replicado em várias rotas | **HIGH** |
| Query N+1 | Loop fazendo `SELECT` individual para cada registro filho | **HIGH** |
| Estado global em memória | Lista global `notifications = []` guardando dados de usuários | **HIGH** |
| Método Longo | Método de relatório com 90 linhas e múltiplos loops aninhados | **MEDIUM** |
| Endpoint no módulo errado | CRUD de `/categories` dentro de `report_routes.py` | **MEDIUM** |
| Código morto / Dep não usada | `marshmallow` em requirements mas validação feita manual | **MEDIUM** |
| `print()` em vez de logger / Bare except | `except: print(err)` | **MEDIUM** |
| API depreciada | `datetime.utcnow()` no Python 3.12 | **LOW** |
| Magic numbers | `if len(pwd) < 4:` / `priority = 3` sem constante | **LOW** |
| Booleano verboso | `if valid: return True else: return False` | **LOW** |
