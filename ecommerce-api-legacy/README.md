# ecommerce-api-legacy

API legada de LMS com fluxo de checkout, escrita em Node.js e Express. Este
projeto é a entrada do desafio `refactor-arch` e mantém, de propósito, uma
arquitetura monolítica para análise e refatoração.

> Aviso: o código contém comportamentos inseguros usados como material de
> estudo. Não use credenciais, cartões ou o fluxo de pagamento em produção.

## Visão geral

- Runtime: Node.js
- Framework HTTP: Express 4
- Banco: SQLite em memória através de `sqlite3`
- Módulos: CommonJS (`require`/`module.exports`)
- Porta atual: `3000`
- Persistência: recriada e populada a cada inicialização

O projeto não possui build, migrações externas, autenticação, testes
automatizados ou script de lint configurados no `package.json`.

## Estrutura do projeto

```text
ecommerce-api-legacy/
├── src/
│   ├── app.js                    # Bootstrap do Express e entrada do processo
│   ├── AppManager.js             # Banco, seeds, rotas e regras de negócio
│   └── utils.js                  # Configuração, cache, logs e helper legado
├── api.http                      # Requisições para clientes HTTP do editor
├── package.json                  # Dependências e script start
├── package-lock.json             # Versões resolvidas pelo npm
├── AGENTS.md                     # Contexto e regras para agentes de código
├── javascript-development-guidelines.md
└── README.md
```

### Fluxo de inicialização

`src/app.js` executa a sequência abaixo:

1. Cria uma aplicação Express.
2. Habilita `express.json()`.
3. Cria uma instância de `AppManager`.
4. Abre um banco SQLite `:memory:`.
5. Cria as tabelas e insere os seeds.
6. Registra as rotas da API.
7. Escuta na porta definida em `src/utils.js` (`3000`).

As operações de schema e seed usam callbacks do `sqlite3` e não são aguardadas
explicitamente antes de `app.listen()`. Portanto, uma requisição imediata após
o boot pode disputar com a inicialização do banco.

Toda a aplicação está concentrada em `AppManager` atualmente. A classe combina
infraestrutura, persistência, controladores HTTP, regras de checkout, relatório
financeiro e exclusão de usuários.

### Modelo de dados

O banco cria estas tabelas durante o boot:

| Tabela | Responsabilidade |
| --- | --- |
| `users` | Usuários e credenciais legadas |
| `courses` | Cursos, preços e status ativo |
| `enrollments` | Relação entre usuários e cursos |
| `payments` | Pagamentos associados a matrículas |
| `audit_logs` | Registro textual de eventos de checkout |

Não há arquivo de banco persistente. Reiniciar o processo apaga todos os
registros criados durante a execução.

## Como instalar e iniciar

### Requisitos

Tenha Node.js e npm instalados. O projeto não declara uma versão de Node em
`engines`; use uma versão suportada pelo pacote `sqlite3` instalado.

### Instalação reproduzível

```bash
cd ecommerce-api-legacy
npm ci
```

`npm ci` utiliza exatamente o `package-lock.json`. Para uma instalação local
normal, `npm install` também funciona:

```bash
npm install
```

### Iniciar a API

```bash
npm start
```

O comando executa `node src/app.js`. Ao iniciar, a aplicação imprime uma
mensagem semelhante a:

```text
Frankenstein LMS rodando na porta 3000...
```

A API fica disponível em:

```text
http://localhost:3000
```

O processo não lê `PORT` ou `.env`; a porta está fixa na configuração atual.
Para encerrar, pressione `Ctrl+C`.

## Verificação rápida

Com a API em execução, consulte o relatório:

```bash
curl http://localhost:3000/api/admin/financial-report
```

Teste um checkout aprovado usando um cartão fictício começando com `4`:

```bash
curl -X POST http://localhost:3000/api/checkout \
  -H 'Content-Type: application/json' \
  -d '{
    "usr": "Smoke Test",
    "eml": "smoke@example.com",
    "pwd": "test-only",
    "c_id": 2,
    "card": "4111111111111111"
  }'
```

O resultado esperado é semelhante a:

```json
{
  "msg": "Sucesso",
  "enrollment_id": 2
}
```

O arquivo [`api.http`](./api.http) contém os cenários de checkout aprovado,
pagamento recusado, relatório financeiro e exclusão de usuário.

## Endpoints atuais

### `POST /api/checkout`

Cria ou reutiliza um usuário e tenta matriculá-lo em um curso ativo.

Corpo legado:

| Campo | Tipo | Uso |
| --- | --- | --- |
| `usr` | string | Nome do usuário |
| `eml` | string | E-mail usado para localizar o usuário |
| `pwd` | string | Senha recebida na criação |
| `c_id` | number | ID do curso |
| `card` | string | Cartão fictício; prefixo `4` aprova |

Comportamentos observáveis:

- `400 Bad Request` quando `usr`, `eml`, `c_id` ou `card` não existem.
- `404` quando o curso não existe ou está inativo.
- `400` quando o pagamento é recusado.
- `200` com `msg` e `enrollment_id` quando o fluxo termina.
- `500` para alguns erros de banco ou de criação de usuário.

O fluxo atual não usa transação. Uma falha depois de inserir a matrícula pode
deixar dados parciais.

### `GET /api/admin/financial-report`

Retorna uma lista com:

```json
[
  {
    "course": "Clean Architecture",
    "revenue": 997,
    "students": [
      {
        "student": "Leonan",
        "paid": 997
      }
    ]
  }
]
```

Apesar do nome administrativo, a rota não possui autenticação ou autorização.
As consultas são aninhadas e assíncronas; portanto, a ordem dos cursos na
resposta pode variar.

### `DELETE /api/users/:id`

Remove uma linha de `users`. A implementação atual não remove matrículas,
pagamentos ou logs relacionados e sempre envia uma resposta de sucesso mesmo
quando ignora um erro do banco.

## Seeds iniciais

No boot, `AppManager.initDb()` cria:

- Um usuário inicial.
- Os cursos `Clean Architecture` e `Docker`.
- Uma matrícula para o primeiro curso.
- Um pagamento `PAID` de `997.00` para essa matrícula.

Os IDs são previsíveis apenas enquanto o processo não recebe novas inserções.

## Limitações legadas importantes

- `src/utils.js` contém valores de configuração sensíveis hard-coded.
- `badCrypto` não é um algoritmo de hash de senha seguro.
- O fluxo imprime dados de cartão e a chave de pagamento no log.
- Não há validação de formato, tamanho ou tipo para todo o payload.
- Não há transação envolvendo matrícula, pagamento e auditoria.
- O schema não declara relacionamentos com foreign keys ou cascatas.
- O relatório financeiro faz várias consultas por registro e pode sofrer com
  condições de corrida na montagem do resultado.
- A exclusão de usuário pode deixar registros órfãos.
- Os erros não são centralizados e alguns callbacks ignoram `err`.
- Não existem health checks, suíte automatizada ou pipeline de qualidade.

Esses pontos são parte do cenário legado. Ao alterar o projeto, preserve o
contrato existente ou documente explicitamente qualquer quebra.

## Documentação para agentes

Leia [`AGENTS.md`](./AGENTS.md) antes de modificar o código. O arquivo descreve
as responsabilidades atuais, o contrato das rotas, o fluxo de inicialização e
as regras de segurança para mudanças.

Para recomendações gerais de JavaScript e Node.js, consulte
[`javascript-development-guidelines.md`](./javascript-development-guidelines.md).
