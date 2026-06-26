---
name: refactor-arch
description: Analisa, audita e refatora uma codebase para o padrão MVC, eliminando anti-patterns e garantindo segurança e qualidade.
---
# Skill refactor-arch

Esta skill executa uma refatoração arquitetural automatizada em três fases sequenciais: Análise, Auditoria e Refatoração.

## Diretrizes de Execução

### Fase 1: Análise do Projeto
1. Detectar a linguagem predominante (Python ou JavaScript/TypeScript).
2. Identificar o framework utilizado (Flask ou Express).
3. Identificar o banco de dados e drivers utilizados (SQLite direto, SQLAlchemy, sqlite3 do Node).
4. Mapear a arquitetura atual (arquivos de código, estimativa de linhas de código, responsabilidades de cada arquivo).
5. Imprimir um resumo estruturado no console, indicando a stack tecnológica, domínio do negócio, número de arquivos analisados e descrição da arquitetura atual.

### Fase 2: Auditoria e Relatório
1. Analisar todos os arquivos de código do projeto contra as definições do `antipatterns_catalog.md`.
2. Identificar pelo menos 5 findings de severidades variadas (CRITICAL, HIGH, MEDIUM, LOW) conforme as regras do catálogo.
3. Para cada finding, mapear arquivo exato, linhas exatas, severidade, descrição, impacto técnico e uma recomendação de correção.
4. Ordenar os findings por severidade decrescente (CRITICAL -> HIGH -> MEDIUM -> LOW).
5. Formatar o relatório usando o template descrito em `report_template.md`.
6. Exibir o relatório completo na tela.
7. **Pausar e solicitar confirmação explícita do usuário** para prosseguir para a Fase 3 (Refatoração). Exibir exatamente a pergunta:
   `Proceed with refactoring (Phase 3)? [y/n]`
   Se a resposta for diferente de `y` ou `yes`, parar a execução imediatamente.

### Fase 3: Refatoração para MVC
1. Reestruturar a codebase para o padrão MVC conforme as regras do `mvc_guidelines.md` e as técnicas do `refactoring_playbook.md`.
2. Criar a nova estrutura de diretórios do projeto:
   - `src/config/` para segredos e variáveis de ambiente (carregados via `.env` no arquivo de configuração do projeto).
   - `src/models/` para lógica de dados e acesso ao banco (com consultas parametrizadas e hash seguro).
   - `src/controllers/` para orquestração de negócios e processamento de requests.
   - `src/routes/` ou `src/views/` para roteamento e mapeamento HTTP.
   - `src/middlewares/` para autenticação e tratamento de erros.
   - `src/app.py` ou `src/app.js` como Composition Root.
3. Substituir todo o código legado e vulnerável pelo código refatorado e seguro.
4. Validar o resultado:
   - Certificar-se de que a aplicação inicia sem erros (ex: `python src/app.py` ou `node src/app.js`).
   - Certificar-se de que os endpoints originais continuam respondendo corretamente com as assinaturas e comportamentos originais mantidos (salvo correções de segurança necessárias).
5. Salvar o relatório de auditoria gerado na Fase 2 em `reports/audit-project-{id}.md` na raiz do repositório (substituindo `{id}` por `1`, `2` ou `3` conforme o projeto).
