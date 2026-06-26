# Catálogo de Anti-Patterns

Este catálogo define as regras de detecção de problemas de arquitetura, segurança e qualidade de código para a skill `refactor-arch`.

---

## 1. SQL Injection (SQLI)
- **Severidade:** CRITICAL
- **Sinais de Detecção:** 
  - Concatenação direta de strings em strings de consulta SQL (ex: `WHERE id = " + str(id)` ou `execute("SELECT ... %s" % var)`).
  - Interpolação de valores não sanitizados no corpo do comando SQL.
- **Impacto:** Permite a execução de comandos SQL arbitrários, roubo de dados, bypass de autenticação e destruição do banco.
- **Recomendação:** Substituir por consultas parametrizadas (placeholders `?` ou `%s` com tupla de argumentos).

---

## 2. Hardcoded Secrets
- **Severidade:** CRITICAL
- **Sinais de Detecção:**
  - Definição direta de chaves secretas, chaves de API, senhas de banco ou chaves de gateway no código fonte (ex: `SECRET_KEY = "minha-chave"` ou `paymentGatewayKey = "pk_live..."`).
- **Impacto:** Exposição de credenciais de produção no repositório de controle de versão (Git), facilitando ataques de larga escala.
- **Recomendação:** Extrair credenciais para variáveis de ambiente (arquivo `.env`) e carregá-las dinamicamente usando `os.environ` ou `process.env`.

---

## 3. Endpoints Administrativos ou Sensíveis Sem Autenticação
- **Severidade:** CRITICAL
- **Sinais de Detecção:**
  - Endpoints que executam consultas SQL enviadas pelo cliente (backdoors), deletam ou alteram dados cruciais, ou geram relatórios financeiros (ex: `/admin/query`, `/admin/reset-db`, `/api/admin/financial-report`) sem qualquer middleware ou validação de token/autenticação antes da execução.
- **Impacto:** Acesso não autorizado a dados confidenciais ou destruição de dados por qualquer requisição maliciosa externa.
- **Recomendação:** Implementar middleware de autenticação (JWT ou chave API robusta) e controle de autorização baseado em perfis (roles).

---

## 4. God Class / Arquivo Monolítico
- **Severidade:** HIGH
- **Sinais de Detecção:**
  - Arquivos únicos que acumulam todas as responsabilidades do sistema: inicialização de banco, definição de esquemas, lógica de negócios, tratamento de requisições HTTP, envio de e-mails/notificações e formatação de respostas.
  - Exemplos: `models.py` agregando lógicas de múltiplos domínios (Usuários, Produtos, Pedidos) ou `AppManager.js` com ~140 linhas contendo rotas e banco acoplados.
- **Impacto:** Código impossível de testar em isolamento, acoplamento extremamente alto e alta taxa de regressão em manutenções simples.
- **Recomendação:** Decompor em controllers, models, rotas e middlewares separados de acordo com seus respectivos domínios de negócio.

---

## 5. Armazenamento Inseguro de Senhas e Vazamento de Dados Sensíveis
- **Severidade:** HIGH
- **Sinais de Detecção:**
  - Armazenamento de senhas em plaintext no banco ou uso de algoritmos criptográficos fracos/obsoletos (como MD5 ou SHA1) para hash de senhas (ex: `hashlib.md5(pwd)` ou `badCrypto()` personalizado).
  - Inclusão do campo de senha diretamente no retorno de serialização (como no `to_dict()` de modelos ou loops de listagem).
- **Impacto:** Se o banco for comprometido, todas as senhas dos usuários estarão imediatamente expostas. Vazamento de dados em responses JSON públicos.
- **Recomendação:** Utilizar um algoritmo moderno com fator de trabalho (como `bcrypt` ou `argon2`) e omitir explicitamente campos de senha em retornos de API.

---

## 6. Ausência de Transações de Banco em Operações Multi-Etapas (Non-Atomic)
- **Severidade:** HIGH
- **Sinais de Detecção:**
  - Execução de múltiplos comandos de escrita (`INSERT` / `UPDATE`) relacionados ao mesmo fluxo de negócio (como um checkout que cria usuário, cria matrícula e registra pagamento) sequencialmente sem o uso de transações bancárias explícitas (`BEGIN TRANSACTION` / `commit` / `rollback`).
- **Impacto:** Inconsistência de dados severa caso ocorra uma falha no meio do processo (ex: usuário criado e cobrado no gateway, mas sem matrícula registrada no banco).
- **Recomendação:** Envolver operações multi-etapas em um bloco de transação (`db.begin()`, `db.commit()` e tratamento de erros com `db.rollback()`).

---

## 7. Callback Hell (Node.js API Deprecada)
- **Severidade:** MEDIUM
- **Sinais de Detecção:**
  - Uso intensivo de callbacks aninhados do driver `sqlite3` tradicional no Node.js para consultas sequenciais (4+ níveis de indentação com callbacks).
- **Impacto:** Código de difícil legibilidade, depuração complexa e tratamento de erros altamente propenso a falhas (exemplo clássico de pirâmide do caos).
- **Recomendação:** Refatorar para usar Promises e a sintaxe moderna `async/await`.

---

## 8. Queries N+1
- **Severidade:** MEDIUM
- **Sinais de Detecção:**
  - Execução de consultas de banco de dados dentro de loops que iteram sobre uma lista de registros (ex: buscar um pedido, e então no loop de itens do pedido fazer um `SELECT` individual para cada produto; ou em um loop de tarefas fazer um `SELECT` individual do criador da tarefa).
- **Impacto:** Degradação severa de performance que escala linearmente com o volume de dados do banco (O(N) queries adicionais).
- **Recomendação:** Usar joins (`SELECT ... JOIN ...`) ou carregamento ansioso (eager loading) para buscar as informações relacionadas em uma única consulta.

---

## 9. Código Morto ou Não Utilizado
- **Severidade:** LOW
- **Sinais de Detecção:**
  - Imports declarados mas não utilizados.
  - Funções, variáveis auxiliares ou classes de serviço inteiras que são criadas no projeto mas nunca importadas ou chamadas por nenhuma rota ou controller (ex: `NotificationService` sem uso).
- **Impacto:** Aumenta a complexidade cognitiva do projeto, confunde os desenvolvedores de manutenção e polui o repositório.
- **Recomendação:** Remover qualquer importação, função, helper ou arquivo de serviço não utilizado.

---

## 10. Uso Inadequado de Logging (Print-based Logging)
- **Severidade:** LOW
- **Sinais de Detecção:**
  - Uso de comandos `print()` (Python) ou `console.log()` (Node.js) para rastrear fluxos de requisição e erros em ambiente simulado de produção, em vez de uma biblioteca de logs configurada.
- **Impacto:** Logs desestruturados, sem níveis de severidade (INFO, WARN, ERROR), sem controle de rotação e impróprios para observabilidade em produção.
- **Recomendação:** Configurar e utilizar a biblioteca de logging padrão da linguagem/framework.
