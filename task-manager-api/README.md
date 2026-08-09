# task-manager-api

API de Task Manager em Python/Flask, refatorada para arquitetura **MVC** (Model–View–Controller).

## Arquitetura

```
task-manager-api/
├── app.py                 # Composition root (create_app)
├── config/settings.py     # Configuração via variáveis de ambiente
├── models/                # Model — entidades e persistência
├── views/                 # View — blueprints HTTP finos
├── controllers/           # Controller — regras de negócio
├── schemas/               # Validação/serialização (Marshmallow)
├── services/              # Integrações (notificações/SMTP)
├── middlewares/           # Error handlers
├── utils/                 # Helpers compartilhados
├── database.py
└── seed.py
```

| Camada | Responsabilidade |
|--------|------------------|
| **Model** | Entidades SQLAlchemy (`User`, `Task`, `Category`) |
| **View** | Rotas Flask que validam input e devolvem JSON |
| **Controller** | Casos de uso, queries e orquestração de serviços |

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000` (ou `HOST`/`PORT` do `.env`).

Rode o `seed.py` antes do primeiro boot para popular o SQLite (`tasks.db`).

### Seed (senhas)

| Email | Senha | Role |
|-------|-------|------|
| joao@email.com | 12345678 | admin |
| maria@email.com | abcd1234 | user |
| pedro@email.com | pass1234 | manager |

## Endpoints principais

- `GET /health`, `GET /`
- `GET/POST /users`, `GET/PUT/DELETE /users/<id>`, `GET /users/<id>/tasks`
- `POST /login` (token assinado com `SECRET_KEY`)
- `GET/POST /tasks`, `GET/PUT/DELETE /tasks/<id>`, `GET /tasks/search`, `GET /tasks/stats`
- `GET/POST /categories`, `PUT/DELETE /categories/<id>`
- `GET /reports/summary`, `GET /reports/user/<id>`

## Configuração

Copie `.env.example` para `.env`. Segredos (`SECRET_KEY`, SMTP) **não** ficam hardcoded.

SMTP fica desligado por padrão (`SMTP_ENABLED=0`).
