# Resultados de Validação — Refatoração Arquitetural

Data: 2026-06-26

## Projeto 1 — code-smells-project

```
GET /health          → 200 {"status":"ok","database":"connected",...}
GET /produtos        → 200 (10 produtos)
GET /usuarios        → 200 (3 usuários)
GET /pedidos         → 200
```

Boot: `python app.py` — OK via Flask test client após `pip install -r requirements.txt` e `.env` configurado.

## Projeto 2 — ecommerce-api-legacy

```
GET /                                    → 200 {"message":"Frankenstein LMS API (Refatorada para MVC)",...}
GET /api/admin/financial-report (sem auth) → 401 (protegido)
```

Boot: `node src/app.js` — OK na porta 3000 após `npm install` e `.env` configurado.

## Projeto 3 — task-manager-api

```
GET /health                              → 200 {"status":"ok",...}
POST /login (joao@email.com / 1234)      → 200 + token
GET /tasks/stats (Bearer token)          → 200
GET /tasks (público)                     → 200 (10 tasks)
```

Boot: `python app.py` — OK após `python seed.py`, `pip install -r requirements.txt` e `.env` configurado.

## Comandos utilizados

```bash
# Projeto 1
cd code-smells-project
cp .env.example .env   # editar valores
pip install -r requirements.txt
python app.py

# Projeto 2
cd ecommerce-api-legacy
cp .env.example .env
npm install
node src/app.js

# Projeto 3
cd task-manager-api
cp .env.example .env
pip install -r requirements.txt
python seed.py
python app.py
```
