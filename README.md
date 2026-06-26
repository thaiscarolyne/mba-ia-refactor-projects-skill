# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

---

## A) Análise Manual

Análise manual dos três projetos legados antes da criação da skill `refactor-arch`. Os achados abaixo alimentam o catálogo de anti-patterns e servem de baseline para validar a Fase 2 (>= 5 findings por projeto).

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

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

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

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.