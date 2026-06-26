# Criação de Skills — Refatoração Arquitetural Automatizada

Neste projeto,foi criada uma Skill que automatiza o processo de refatoração de projetos legados — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Capacidades

Essa Skill é capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill é agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a auditoria e os relatórios gerados pela IA, foi utilizada a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

---

## A) Análise Manual

Análise manual dos três projetos legados antes da criação da skill `refactor-arch`.

### code-smells-project (Python/Flask — API de E-commerce)

Monolito em 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`) sem separação MVC. Domínio: produtos, usuários e pedidos.

| Severidade | Arquivo:Linha | Descrição | Justificativa |
|------------|---------------|-----------|---------------|
| CRITICAL | `models.py:28`, `47-49`, `109-110` | SQL injection por concatenação de strings em queries (`WHERE id = " + str(id)`, INSERT/UPDATE com valores interpolados) | Permite execução de SQL arbitrário; falha grave de segurança (OWASP A03) |
| CRITICAL | `app.py:59-78` | Endpoint `/admin/query` executa SQL arbitrário enviado no body, sem autenticação | Equivalente a backdoor de banco de dados exposto publicamente |
| CRITICAL | `app.py:7` | `SECRET_KEY` hardcoded (`"minha-chave-super-secreta-123"`) | Compromete sessões, cookies assinados e qualquer mecanismo criptográfico da app |
| CRITICAL | `models.py:1-314` | God Class — ~314 linhas com CRUD, queries SQL, validação e formatação para produtos, usuários e pedidos | Viola SRP e impede testes isolados; qualquer mudança afeta múltiplos domínios |
| HIGH | `models.py:83`, `database.py:75-78` | Senhas em plaintext no seed e expostas no JSON de listagem (`"senha": row["senha"]`) | Credenciais vazam em responses e no banco; violação de proteção de dados |
| HIGH | `controllers.py:285-289` | Endpoint `/health` expõe `secret_key`, `db_path` e `debug: True` | Health check não deve vazar configuração interna; facilita ataques direcionados |
| MEDIUM | `models.py:187-199` | N+1 queries — loop de pedidos dispara query separada por item e por produto | Degrada performance linearmente com volume de pedidos |
| MEDIUM | `app.py:47-57` | Endpoint `/admin/reset-db` apaga todas as tabelas sem autenticação | Operação destrutiva exposta; risco de perda total de dados |
| LOW | `controllers.py:8,57,106,161,179` | Uso de `print()` como logging em handlers HTTP | Sem níveis, rotação ou correlação; inadequado para produção e observabilidade |
| LOW | `app.py:8` | `DEBUG=True` hardcoded na configuração da aplicação | Expõe stack traces e comportamento de dev em ambiente que simula produção |

**Resumo:** CRITICAL: 4 | HIGH: 2 | MEDIUM: 2 | LOW: 2 — **Total: 10 findings**

---

### ecommerce-api-legacy (Node.js/Express — LMS com checkout)

API de cursos com fluxo de checkout. Lógica concentrada em `AppManager.js` (~140 linhas) e config em `utils.js`.

| Severidade | Arquivo:Linha | Descrição | Justificativa |
|------------|---------------|-----------|---------------|
| CRITICAL | `utils.js:3-4` | Credenciais hardcoded (`dbPass`, `paymentGatewayKey`) no código-fonte | Chaves de produção no repositório; violação PCI-DSS e boas práticas de secrets management |
| CRITICAL | `AppManager.js:45` | PAN do cartão e chave do gateway logados em `console.log` | Expõe dados de pagamento (PCI) e credenciais em logs acessíveis |
| CRITICAL | `AppManager.js:80-128` | Relatório financeiro `/api/admin/financial-report` sem autenticação | Dados sensíveis de receita e alunos acessíveis por qualquer requisição |
| HIGH | `AppManager.js:4-138` | God class monolítica — DB init, rotas, checkout, pagamento e relatório no mesmo arquivo | Impossível testar ou evoluir camadas independentemente; viola MVC e SRP |
| HIGH | `AppManager.js:50-63` | Checkout sem transação DB — INSERT em enrollments, payments e audit_logs em callbacks separados | Falha parcial deixa matrícula sem pagamento ou vice-versa (inconsistência de dados) |
| MEDIUM | `AppManager.js:37-127` | Callback hell — sqlite3 callback API aninhada 4+ níveis | Código difícil de ler, testar e tratar erros; API deprecated em favor de async/await |
| MEDIUM | `utils.js:9-15` | Estado global mutável (`globalCache`) compartilhado entre requests | Race conditions e acoplamento oculto entre requisições concorrentes |
| LOW | `AppManager.js:35,48,135` | Respostas HTTP inconsistentes — mistura `res.send(string)`, `res.json()` e status codes ad hoc | Dificulta consumo da API e tratamento uniforme de erros no cliente |
| LOW | `AppManager.js:29-33` | Nomenclatura críptica de variáveis (`u`, `e`, `p`, `cc`) nos parâmetros do checkout | Reduz legibilidade e aumenta risco de bugs em manutenção |

**Resumo:** CRITICAL: 3 | HIGH: 2 | MEDIUM: 2 | LOW: 2 — **Total: 9 findings**

---

### task-manager-api (Python/Flask — API de Task Manager)

Projeto com organização parcial (`models/`, `routes/`, `services/`, `utils/`), mas com falhas de segurança e camadas mortas.

| Severidade | Arquivo:Linha | Descrição | Justificativa |
|------------|---------------|-----------|---------------|
| CRITICAL | `models/user.py:21,29` | Hash MD5 para senhas e campo `password` incluído em `to_dict()` | MD5 é criptograficamente fraco; hash de senha vaza em toda response JSON |
| CRITICAL | `app.py:13` | `SECRET_KEY` hardcoded (`'super-secret-key-123'`) | Mesmo risco do projeto 1 — sessões e tokens previsíveis em produção |
| HIGH | `routes/*.py` (ex.: `task_routes.py`, `user_routes.py`) | Rotas CRUD sem autenticação ou autorização | Qualquer cliente pode criar, alterar ou deletar tasks e usuários |
| HIGH | `routes/task_routes.py:14-57` | N+1 queries — `User.query.get()` e `Category.query.get()` dentro do loop de tasks | Performance degrada com listagens grandes; JOIN ou eager load resolve |
| HIGH | `services/notification_service.py:4-48` | `NotificationService` implementado mas nunca importado/usado nas rotas | Camada de serviço morta — indica arquitetura incompleta e código órfão |
| MEDIUM | `routes/task_routes.py:30-39` vs `models/task.py:50-60` | Lógica de `overdue` duplicada na rota e no model (`is_overdue()`) | Viola DRY; mudança de regra exige editar múltiplos pontos |
| MEDIUM | `utils/helpers.py:19-108` | Helpers (`process_task_data`, `validate_email`, `log_action`) definidos mas não usados nas rotas | Código morto que confunde manutenção; validação duplicada inline nas routes |
| LOW | `app.py:7`, `routes/task_routes.py:7,149` | Imports mortos (`os`, `sys`, `json`) e `print()` como logging | Polui namespace e dificulta análise estática; logging estruturado ausente |
| LOW | `routes/user_routes.py:210` | Login retorna `'fake-jwt-token-' + str(user.id)` sem implementação real de JWT | Autenticação simulada; tokens previsíveis e sem validade criptográfica |

**Resumo:** CRITICAL: 2 | HIGH: 3 | MEDIUM: 2 | LOW: 2 — **Total: 9 findings**

---

## B) Construção da Skill

### Decisões de design

A skill `refactor-arch` foi organizada em **6 arquivos Markdown** dentro de `.agents/skills/refactor-arch/` (convenção Cursor, equivalente a `.claude/skills/`):

| Arquivo | Papel |
|---------|-------|
| `SKILL.md` | Orquestra as 3 fases e define regras de execução (pausa obrigatória na Fase 2) |
| `analysis_heuristics.md` | Heurísticas para detectar linguagem, framework, banco e arquitetura |
| `antipatterns_catalog.md` | 10 anti-patterns com sinais de detecção e severidade |
| `report_template.md` | Formato padronizado do relatório de auditoria |
| `mvc_guidelines.md` | Estrutura MVC alvo e responsabilidades por camada |
| `refactoring_playbook.md` | 8 transformações antes/depois (Python e Node.js) |

O `SKILL.md` funciona como **prompt de orquestração**; os arquivos de referência fornecem o conhecimento de domínio que o agente consulta durante cada fase.

### Anti-patterns incluídos no catálogo

Foram incluídos 10 anti-patterns cobrindo os problemas encontrados na análise manual:

1. SQL Injection (CRITICAL)
2. Hardcoded Secrets (CRITICAL)
3. Endpoints administrativos sem autenticação (CRITICAL)
4. God Class / Arquivo monolítico (HIGH)
5. Armazenamento inseguro de senhas (HIGH)
6. Operações multi-etapas sem transação (HIGH)
7. Callback Hell / API deprecated do sqlite3 (MEDIUM)
8. Queries N+1 (MEDIUM)
9. Código morto ou não utilizado (LOW)
10. Print-based logging (LOW)

### Agnosticismo de tecnologia

A skill detecta Python/Flask e Node.js/Express via heurísticas de imports e estrutura de arquivos. O catálogo e o playbook trazem **exemplos duplos** (Python e Node.js) para cada transformação. A Fase 3 adapta a estrutura de diretórios ao contexto: monolitos viram `src/` completo; projetos parcialmente organizados recebem `middlewares/`, `config/` e integração de camadas existentes.

### Desafios encontrados

- **Projeto 3 parcialmente organizado:** a refatoração não exige recriar tudo em `src/` — melhorias incrementais (auth, bcrypt, limpeza de dead code) foram suficientes mantendo `models/` e `routes/`.
- **Detecção de APIs deprecated:** mapeada ao anti-pattern #7 (callbacks aninhados do sqlite3), presente no `ecommerce-api-legacy`.
- **Confirmação humana:** a Fase 2 pausa com `Proceed with refactoring (Phase 3)? [y/n]` antes de qualquer modificação.

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---------|----------|------|--------|-----|-------|
| code-smells-project | 4 | 2 | 2 | 2 | **10** |
| ecommerce-api-legacy | 3 | 2 | 2 | 2 | **9** |
| task-manager-api | 2 | 3 | 2 | 2 | **9** |

Relatórios completos em [`reports/audit-project-1.md`](reports/audit-project-1.md), [`reports/audit-project-2.md`](reports/audit-project-2.md) e [`reports/audit-project-3.md`](reports/audit-project-3.md).

### Comparação antes/depois da estrutura

**code-smells-project (antes → depois)**

```
app.py, controllers.py, models.py, database.py   →   src/{config,models,controllers,routes,middlewares,database}/ + app.py shim
```

**ecommerce-api-legacy (antes → depois)**

```
src/AppManager.js, src/utils.js, src/app.js   →   src/{config,controllers,models,routes,middlewares,database}/ + src/app.js
```

**task-manager-api (antes → depois)**

```
models/, routes/, services/, utils/   →   + config/, middlewares/ + services e helpers integrados
```

### Checklist de validação

Detalhes de execução em [`reports/validation-results.md`](reports/validation-results.md).

#### Projeto 1 — code-smells-project

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask)
- [x] Domínio descrito (E-commerce API)
- [x] Arquivos analisados condizem com a realidade

**Fase 2 — Auditoria**
- [x] Relatório segue o template
- [x] Findings com arquivo e linhas exatos
- [x] Ordenados por severidade
- [x] 10 findings (≥ 5)
- [x] APIs deprecated detectadas (N/A neste projeto)
- [x] Pausa antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura MVC em `src/`
- [x] Config extraída para `src/config/settings.py`
- [x] Models, routes, controllers e middlewares separados
- [x] Aplicação inicia sem erros
- [x] Endpoints respondem (`/health`, `/produtos`, `/usuarios`, `/pedidos`)

#### Projeto 2 — ecommerce-api-legacy

**Fase 1 — Análise**
- [x] Linguagem detectada (Node.js)
- [x] Framework detectado (Express)
- [x] Domínio descrito (LMS com checkout)
- [x] Arquivos analisados corretamente

**Fase 2 — Auditoria**
- [x] Relatório segue o template
- [x] Findings com arquivo e linhas
- [x] 9 findings
- [x] Callback hell / API deprecated incluída
- [x] Pausa antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura MVC completa
- [x] Config via `dotenv`
- [x] Transações no checkout
- [x] Admin report protegido (401 sem token)
- [x] App inicia na porta 3000

#### Projeto 3 — task-manager-api

**Fase 1 — Análise**
- [x] Python/Flask detectado
- [x] Domínio Task Manager identificado
- [x] Arquitetura parcial mapeada

**Fase 2 — Auditoria**
- [x] 9 findings em projeto parcialmente organizado
- [x] Pausa antes da Fase 3

**Fase 3 — Refatoração**
- [x] `middlewares/auth.py` com `@auth_required` e `@admin_required`
- [x] bcrypt, config via env, NotificationService integrado
- [x] Helpers reutilizados, N+1 corrigido em reports
- [x] Login + endpoints autenticados funcionando

### Logs de validação

```
code-smells:  GET /health → 200 | GET /produtos → 200 (10 itens)
ecommerce:    GET / → 200 | GET /api/admin/financial-report → 401 (sem auth)
task-manager: POST /login → 200 + token | GET /tasks/stats → 200 (com Bearer)
```

---

## D) Como Executar

### Pré-requisitos

- **Cursor** (ou Claude Code / Gemini CLI / Codex) com suporte a Custom Skills
- Python 3.9+ com `pip`
- Node.js 18+ com `npm`
- Git

### Executar a skill

A skill está em `.agents/skills/refactor-arch/` dentro de cada projeto. No Cursor, invoque com o comando da skill ou referenciando `refactor-arch`.

```bash
# Projeto 1
cd code-smells-project
# Invocar skill refactor-arch → confirmar Fase 3 com "y"

# Projeto 2
cd ../ecommerce-api-legacy

# Projeto 3
cd ../task-manager-api
```

### Configurar e rodar cada API

```bash
# Projeto 1 — code-smells-project
cd code-smells-project
cp .env.example .env          # editar SECRET_KEY e ADMIN_TOKEN
pip install -r requirements.txt
python app.py                 # http://localhost:5000

# Projeto 2 — ecommerce-api-legacy
cd ecommerce-api-legacy
cp .env.example .env
npm install
node src/app.js               # http://localhost:3000

# Projeto 3 — task-manager-api
cd task-manager-api
cp .env.example .env
pip install -r requirements.txt
python seed.py                # popular banco (obrigatório na 1ª execução)
python app.py                 # http://localhost:5000
```

### Validar a refatoração

```bash
# code-smells-project
curl http://localhost:5000/health
curl http://localhost:5000/produtos

# ecommerce-api-legacy
curl http://localhost:3000/
curl http://localhost:3000/api/admin/financial-report   # deve retornar 401

# task-manager-api
curl -X POST http://localhost:5000/login -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}'
# Usar o token retornado:
curl http://localhost:5000/tasks/stats -H "Authorization: Bearer <token>"
```

---
