# Relatório de Auditoria de Arquitetura — ecommerce-api-legacy

## Resumo Executivo
- **Projeto:** ecommerce-api-legacy
- **Stack Detectada:** Node.js + Express
- **Arquitetura Atual:** Monolítica — Lógicas e banco acoplados em dois arquivos centrais (`src/AppManager.js` e `src/utils.js`).
- **Total de Problemas Encontrados:** 9

### Resumo por Severidade
- **CRITICAL:** 3
- **HIGH:** 2
- **MEDIUM:** 2
- **LOW:** 2

---

## Achados e Vulnerabilidades (Findings)

### [CRITICAL] Credenciais Hardcoded no Código Fonte
- **Arquivo:Linhas:** `src/utils.js:3-4`
- **Descrição:** O arquivo `utils.js` contém a chave privada do gateway de pagamentos (`paymentGatewayKey`) e a senha de banco (`dbPass`) chumbadas em texto plano.
- **Impacto Técnico:** Expõe chaves críticas de produção em repositórios de controle de versão (violação das diretrizes de segurança da OWASP e PCI-DSS).
- **Recomendação:** Extrair as credenciais para variáveis de ambiente locais (arquivo `.env`) e carregá-las no Express através da biblioteca `dotenv`.

---

### [CRITICAL] Vazamento de Dados de Pagamento (PAN) em Logs do Servidor
- **Arquivo:Linhas:** `src/AppManager.js:45`
- **Descrição:** O número completo do cartão de crédito (`cc`) do cliente e a chave privada do gateway são registrados no console em texto limpo.
- **Impacto Técnico:** Risco gravíssimo de vazamento de PAN e dados de cartões em logs de produção, violando os requisitos básicos de conformidade PCI-DSS.
- **Recomendação:** Remover o log de depuração contendo dados confidenciais ou mascarar os dados do cartão deixando visível apenas os últimos 4 dígitos.

---

### [CRITICAL] Endpoint Administrativo Sensível Sem Autenticação
- **Arquivo:Linhas:** `src/AppManager.js:80-128`
- **Descrição:** O endpoint `/api/admin/financial-report` retorna o relatório financeiro do LMS com receitas de vendas e dados de estudantes, sem exigir qualquer tipo de autenticação.
- **Impacto Técnico:** Acesso público não autorizado a dados financeiros sensíveis da empresa e vazamento de e-mails de estudantes.
- **Recomendação:** Implementar um middleware de validação de cabeçalhos de autorização com Token de Admin ou JWT para proteger a rota.

---

### [HIGH] Monolito God Class Acoplado
- **Arquivo:Linhas:** `src/AppManager.js:4-138`
- **Descrição:** A classe `AppManager` lida de forma aglomerada com conexões de banco de dados SQLite, definições de schemas, roteamento de requisições HTTP, checkout, relatórios e exclusões de usuários.
- **Impacto Técnico:** Violação do princípio SRP (Single Responsibility Principle) e alta dificuldade para cobertura de testes de unidade e manutenção.
- **Recomendação:** Decompor a lógica do monolito no padrão MVC estruturado em diretórios independentes.

---

### [HIGH] Operações de Banco Multi-Etapas Sem Controle de Transação
- **Arquivo:Linhas:** `src/AppManager.js:50-63`
- **Descrição:** No fluxo de checkout, os registros são inseridos em `enrollments`, `payments` e `audit_logs` de forma sequencial por meio de callbacks, mas sem estarem inseridos dentro de um bloco de transação atômica.
- **Impacto Técnico:** Risco severo de inconsistência de dados (ex: se a inserção do pagamento falhar após a criação da matrícula, o estudante terá acesso ao curso sem ter pago).
- **Recomendação:** Envolver o fluxo de inserção em blocos de transação explícita do SQLite (`BEGIN TRANSACTION`, `COMMIT` e `ROLLBACK`).

---

### [MEDIUM] Callback Hell (Pirâmide do Caos)
- **Arquivo:Linhas:** `src/AppManager.js:37-127`
- **Descrição:** O acesso ao banco é realizado via APIs legadas de callbacks aninhadas em múltiplos níveis de profundidade, gerando fluxo assíncrono complexo.
- **Impacto Técnico:** Código de difícil legibilidade, alta taxa de erros e alta complexidade cognitiva em tratamentos de exceção.
- **Recomendação:** Promisificar os métodos do driver `sqlite3` e migrar todo o código assíncrono para o padrão moderno `async/await`.

---

### [MEDIUM] Estado Global Mutável Compartilhado
- **Arquivo:Linhas:** `src/utils.js:9-15`
- **Descrição:** O objeto `globalCache` e a variável `totalRevenue` são definidos em escopo global no módulo e modificados diretamente a cada requisição HTTP de checkout.
- **Impacto Técnico:** Race conditions, comportamento imprevisível em processamentos paralelos de requisições concorrentes e acoplamento inadequado de estados em memória.
- **Recomendação:** Substituir por soluções de armazenamento persistentes estruturadas ou em memória isolada e desacoplar contadores globais.

---

### [LOW] Respostas HTTP Inconsistentes
- **Arquivo:Linhas:** `src/AppManager.js:35`, `src/AppManager.js:48`, `src/AppManager.js:135`
- **Descrição:** Mistura de retornos usando `res.send()` retornando strings simples de texto com retornos estruturados em `res.json()`, além de códigos de status indefinidos.
- **Impacto Técnico:** Dificulta a integração uniforme e tratamento de erros do lado do cliente (frontend) que consome a API.
- **Recomendação:** Padronizar todas as respostas HTTP para o formato JSON estruturado `{ sucesso, dados, erro }` e retornar status codes apropriados.

---

### [LOW] Parâmetros de Entrada com Nomes Crípticos
- **Arquivo:Linhas:** `src/AppManager.js:29-33`
- **Descrição:** Uso de variáveis como `u`, `e`, `p`, `cid`, `cc` para representar nome, email, senha, curso_id e número do cartão no payload do checkout.
- **Impacto Técnico:** Dificulta a legibilidade e documentação da API, tornando o código de manutenção confuso.
- **Recomendação:** Substituir os nomes das variáveis e chaves de payload por descritores claros: `name`, `email`, `password`, `courseId`, `cardNumber`.
