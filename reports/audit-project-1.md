# Relatório de Auditoria de Arquitetura — code-smells-project

## Resumo Executivo
- **Projeto:** code-smells-project
- **Stack Detectada:** Python + Flask
- **Arquitetura Atual:** Monolítica — lógicas acopladas diretamente na raiz em 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`).
- **Total de Problemas Encontrados:** 10

### Resumo por Severidade
- **CRITICAL:** 4
- **HIGH:** 2
- **MEDIUM:** 2
- **LOW:** 2

---

## Achados e Vulnerabilidades (Findings)

### [CRITICAL] SQL Injection por Concatenação de Strings
- **Arquivo:Linhas:** `models.py:28`, `47-49`, `57-60`, `68`, `92`, `109-110`, `126-129`, `140`, `148-151`, `157-160`, `163-166`, `174`, `188`, `192`, `220`, `224`, `279-281`, `289-299`
- **Descrição:** Valores recebidos diretamente do usuário são concatenados diretamente na string da query SQL executada pelo cursor, sem qualquer sanitização ou parametrização.
- **Impacto Técnico:** Permite que atacantes insiram instruções SQL maliciosas para ler, alterar ou deletar registros arbitrários do banco de dados (OWASP A03:2021).
- **Recomendação:** Substituir todas as concatenações por queries parametrizadas utilizando o marcador de posição `?` e passando os valores como uma tupla no segundo argumento do método `execute()`.

---

### [CRITICAL] Endpoint de Backdoor de Execução de SQL Arbitrário
- **Arquivo:Linhas:** `app.py:59-78`
- **Descrição:** O endpoint `/admin/query` aceita qualquer código SQL enviado no corpo da requisição e o executa diretamente no banco de dados, sem exigir autenticação.
- **Impacto Técnico:** Permite execução total de comandos administrativos e manipulação direta de qualquer tabela por qualquer usuário anônimo.
- **Recomendação:** Remover o endpoint completamente da aplicação ou restringi-lo fortemente com autenticação administrativa rígida e não permitir SQL bruto arbitrário de clientes.

---

### [CRITICAL] Credenciais Hardcoded no Código Fonte
- **Arquivo:Linhas:** `app.py:7`
- **Descrição:** A configuração da `SECRET_KEY` está chumbada diretamente no código com a string `"minha-chave-super-secreta-123"`.
- **Impacto Técnico:** Facilita a assinatura e decodificação de cookies e sessões da aplicação por agentes mal-intencionados caso tenham acesso ao repositório git.
- **Recomendação:** Extrair a chave para uma variável de ambiente (como `.env`) e carregá-la usando `os.environ.get('SECRET_KEY')`.

---

### [CRITICAL] God Class/Arquivo com Múltiplas Responsabilidades
- **Arquivo:Linhas:** `models.py:1-315`
- **Descrição:** O arquivo `models.py` é responsável pela lógica de persistência de produtos, usuários e pedidos de forma totalmente aglutinada. Ele lida com criação, listagem, cálculo de faturamento e regras de checkout no mesmo escopo.
- **Impacto Técnico:** Violação severa do Princípio de Responsabilidade Única (SRP). Torna os testes isolados impossíveis e eleva o risco de regressão a cada modificação.
- **Recomendação:** Decompor a lógica em classes ou módulos de modelo específicos por domínio (`produto_model.py`, `usuario_model.py`, `pedido_model.py`) dentro de uma pasta dedicada.

---

### [HIGH] Senhas Armazenadas e Expostas em Plaintext
- **Arquivo:Linhas:** `database.py:75-78`, `models.py:83`
- **Descrição:** As senhas dos usuários no seed são inseridas como texto limpo (`"admin123"`, `"123456"`, `"senha123"`) e são expostas sem qualquer hash nas rotas de listagem JSON de usuários.
- **Impacto Técnico:** Vazamento direto de credenciais em respostas de API e exposição total das senhas em caso de vazamento de banco de dados.
- **Recomendação:** Utilizar a biblioteca `bcrypt` para gerar hashes seguros no momento do cadastro do usuário e remover o campo de senha do retorno JSON de usuários.

---

### [HIGH] Vazamento de Configurações Internas no Endpoint `/health`
- **Arquivo:Linhas:** `controllers.py:285-289`
- **Descrição:** O endpoint de healthcheck expõe informações sensíveis como a `SECRET_KEY`, o caminho do banco de dados `db_path` e se o modo `debug` está ativo.
- **Impacto Técnico:** Facilita o mapeamento da infraestrutura interna e credenciais da aplicação por atacantes (Information Disclosure).
- **Recomendação:** Remover credenciais e detalhes internos da resposta JSON do healthcheck, mantendo apenas informações genéricas de saúde.

---

### [MEDIUM] Queries N+1 no Carregamento de Relatórios e Pedidos
- **Arquivo:Linhas:** `models.py:187-199`, `models.py:219-231`
- **Descrição:** Para cada pedido carregado, o sistema executa um select em loop para buscar os itens do pedido e, para cada item, executa outro select para buscar o nome do produto correspondente.
- **Impacto Técnico:** Gargalo de performance severo que cresce de forma linear com o número de pedidos no sistema, sobrecarregando o banco de dados.
- **Recomendação:** Utilizar uma consulta com `JOIN` para trazer as informações do pedido, dos itens e dos produtos relacionados de uma só vez.

---

### [MEDIUM] Endpoint Destrutivo `/admin/reset-db` Sem Autenticação
- **Arquivo:Linhas:** `app.py:47-57`
- **Descrição:** O endpoint `/admin/reset-db` apaga os dados de todas as tabelas do sistema e aceita requisições POST sem qualquer autenticação ou autorização.
- **Impacto Técnico:** Risco gravíssimo de destruição completa dos dados do banco de dados por requisições não autorizadas.
- **Recomendação:** Adicionar middleware de autenticação administrativa ou restringir para escopo puramente interno de desenvolvimento.

---

### [LOW] Uso de `print()` para Registro de Logs
- **Arquivo:Linhas:** `controllers.py:8`, `controllers.py:57`, `controllers.py:106`, `controllers.py:161`, `controllers.py:179`
- **Descrição:** O sistema utiliza `print()` para registrar eventos e erros críticos no console.
- **Impacto Técnico:** Impede controle de níveis de log (DEBUG, INFO, ERROR), rotação de arquivos e integração com ferramentas de monitoramento de logs centralizadas.
- **Recomendação:** Substituir por chamadas à biblioteca padrão `logging` do Python configurada com formato e nível adequados.

---

### [LOW] Modo `DEBUG` Hardcoded Ativo em Produção
- **Arquivo:Linhas:** `app.py:8`, `app.py:88`
- **Descrição:** O parâmetro `debug=True` está hardcoded na configuração e na inicialização da aplicação Flask.
- **Impacto Técnico:** Em produção, exibe stack traces detalhados e um console interativo em caso de falha, permitindo execução de código remoto.
- **Recomendação:** Configurar o modo de debug a partir de uma variável de ambiente (como `DEBUG=True` ou `False` no `.env`).
