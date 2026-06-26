# Relatório de Auditoria de Arquitetura — task-manager-api

## Resumo Executivo
- **Projeto:** task-manager-api
- **Stack Detectada:** Python + Flask + SQLAlchemy
- **Arquitetura Atual:** Parcialmente estruturada — pastas `models/`, `routes/`, `services/`, `utils/` existem, mas possuem camadas mortas, violações de segurança críticas e vazamento de responsabilidades nas rotas.
- **Total de Problemas Encontrados:** 9

### Resumo por Severidade
- **CRITICAL:** 2
- **HIGH:** 3
- **MEDIUM:** 2
- **LOW:** 2

---

## Achados e Vulnerabilidades (Findings)

### [CRITICAL] Hash MD5 para Senhas e Exposição no JSON
- **Arquivo:Linhas:** `models/user.py:29`, `models/user.py:21`
- **Descrição:** O método `set_password()` usa `hashlib.md5()` para gerar o hash da senha dos usuários. MD5 é um algoritmo criptograficamente comprometido e trivialmente quebrável por rainbow tables. Além disso, o campo `password` é incluído no retorno de `to_dict()`, expondo o hash em qualquer response JSON.
- **Impacto Técnico:** Um vazamento do banco resultaria na exposição imediata de todas as senhas dos usuários. O campo de senha é devolvido em respostas públicas da API.
- **Recomendação:** Substituir `hashlib.md5` por `bcrypt` para hash de senhas. Remover o campo `password` do método `to_dict()`.

---

### [CRITICAL] SECRET_KEY Hardcoded no Código Fonte
- **Arquivo:Linhas:** `app.py:13`
- **Descrição:** A configuração `SECRET_KEY = 'super-secret-key-123'` está chumbada diretamente no código-fonte.
- **Impacto Técnico:** Compromete sessões e qualquer token criptográfico da aplicação quando o repositório é exposto.
- **Recomendação:** Extrair para variável de ambiente via arquivo `.env` e carregar com `os.environ.get('SECRET_KEY')`.

---

### [HIGH] Rotas CRUD Sem Autenticação ou Autorização
- **Arquivo:Linhas:** `routes/task_routes.py`, `routes/user_routes.py` (todos os endpoints)
- **Descrição:** Todos os endpoints de criação, atualização e deleção de tasks e usuários estão acessíveis publicamente sem exigir qualquer token de autenticação.
- **Impacto Técnico:** Qualquer cliente anônimo pode criar, modificar ou deletar dados arbitrariamente.
- **Recomendação:** Implementar um decorador de autenticação que valide um token de sessão ou Bearer token antes de permitir acesso às rotas protegidas.

---

### [HIGH] Queries N+1 na Listagem de Tasks
- **Arquivo:Linhas:** `routes/task_routes.py:41-57`
- **Descrição:** Para cada task listada, o código executa consultas separadas `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` dentro do loop, gerando N+1 queries ao banco para cada request de listagem.
- **Impacto Técnico:** Performance degrada linearmente com o volume de tasks cadastradas.
- **Recomendação:** Usar eager loading no SQLAlchemy com `joinedload()` ou acessar os relacionamentos via `t.user` e `t.category` que já estão configurados com `db.relationship()` no modelo.

---

### [HIGH] NotificationService Implementado mas Nunca Utilizado
- **Arquivo:Linhas:** `services/notification_service.py:4-48`
- **Descrição:** A classe `NotificationService` com métodos `send_email`, `notify_task_assigned` e `notify_task_overdue` existe mas não é importada nem chamada em nenhuma parte da aplicação. Além disso, contém senha de e-mail hardcoded na linha 10.
- **Impacto Técnico:** Código órfão que confunde manutenção, indica arquitetura incompleta e credenciais hardcoded representam risco de segurança.
- **Recomendação:** Remover ou integrar corretamente o serviço de notificação, e mover credenciais para variáveis de ambiente.

---

### [MEDIUM] Lógica `overdue` Duplicada (Violação de DRY)
- **Arquivo:Linhas:** `routes/task_routes.py:30-39`, `routes/task_routes.py:71-80`, `routes/task_routes.py:171-180`, `routes/task_routes.py:282-287` vs `models/task.py:50-60`
- **Descrição:** A lógica de verificação de `overdue` (verificar se `due_date < datetime.utcnow()` e se o status não é `done` ou `cancelled`) é repetida em 4 partes diferentes das rotas, ignorando o método `is_overdue()` já definido no modelo `Task`.
- **Impacto Técnico:** Violação do princípio DRY — qualquer mudança na regra de negócio de "overdue" exige alteração em múltiplos pontos.
- **Recomendação:** Centralizar o uso de `task.is_overdue()` (já implementado no modelo) em todos os lugares onde o campo `overdue` é calculado nas rotas.

---

### [MEDIUM] Helpers Definidos mas Não Utilizados nas Rotas
- **Arquivo:Linhas:** `utils/helpers.py:19-108`
- **Descrição:** Funções como `process_task_data`, `validate_email` e `log_action` estão definidas no arquivo de utilitários mas não são importadas nem usadas nas rotas onde seriam aplicáveis.
- **Impacto Técnico:** Código morto que infla o projeto e dificulta o entendimento da arquitetura real; validações são duplicadas inline nas rotas em vez de reutilizadas.
- **Recomendação:** Integrar os helpers nas rotas correspondentes ou removê-los se forem redundantes.

---

### [LOW] Imports Mortos e `print()` como Logging
- **Arquivo:Linhas:** `app.py:7`, `routes/task_routes.py:7`, `routes/user_routes.py:6`
- **Descrição:** Imports de `os`, `sys`, `json`, `time` são declarados mas nunca utilizados no código. O logging é feito com `print()` em diversas rotas.
- **Impacto Técnico:** Polui o namespace, dificulta análise estática e impede observabilidade estruturada.
- **Recomendação:** Remover imports não utilizados e substituir `print()` por chamadas à biblioteca `logging`.

---

### [LOW] Token JWT Simulado e Sem Implementação Real
- **Arquivo:Linhas:** `routes/user_routes.py:210`
- **Descrição:** O endpoint de login retorna `'fake-jwt-token-' + str(user.id)` como token de autenticação, sem qualquer implementação criptográfica real.
- **Impacto Técnico:** Tokens previsíveis e sem validade temporal, facilmente forjáveis por qualquer cliente que conheça um `user.id`.
- **Recomendação:** Implementar geração de token real com `secrets.token_urlsafe()` e associar validade, ou integrar uma biblioteca JWT como `PyJWT`.
