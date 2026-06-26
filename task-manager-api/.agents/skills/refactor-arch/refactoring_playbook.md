# Playbook de Refatoração

Este playbook fornece padrões concretos de transformação antes/depois para os 10 anti-patterns definidos no catálogo, cobrindo Python e Node.js.

---

## 1. Consultas Parametrizadas (Segurança contra SQLI)

### Python (Antes - Concatenação)
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```
### Python (Depois - Parametrizado)
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```

### Node.js (Antes - Concatenação)
```javascript
db.run("SELECT * FROM users WHERE email = '" + email + "'");
```
### Node.js (Depois - Parametrizado)
```javascript
db.run("SELECT * FROM users WHERE email = ?", [email], callback);
```

---

## 2. Configurações por Variáveis de Ambiente (Segredos Seguros)

### Python (Antes - Hardcoded)
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```
### Python (Depois - Env e dotenv)
```python
import os
from dotenv import load_dotenv
load_dotenv()
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fallback-key")
```

### Node.js (Antes - Hardcoded)
```javascript
const config = { paymentGatewayKey: "pk_live_12345" };
```
### Node.js (Depois - Env e dotenv)
```javascript
require('dotenv').config();
const config = { paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY };
```

---

## 3. Criptografia Segura de Senhas (bcrypt) e Filtro de Resposta

### Python (Antes - MD5 e Exposição)
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
def to_dict(self):
    return { 'password': self.password, 'email': self.email }
```
### Python (Depois - bcrypt e Sanitização)
```python
import bcrypt
def set_password(self, pwd):
    self.password = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(self, pwd):
    return bcrypt.checkpw(pwd.encode('utf-8'), self.password.encode('utf-8'))

def to_dict(self):
    # Omitir campo password da serialização pública
    return { 'email': self.email }
```

---

## 4. Separação de Arquivos de Domínio (Decomposição MVC)

### Antes (Monolito acoplado)
Um único arquivo `models.py` contendo tabelas de Usuários, Pedidos e Produtos misturadas em métodos estáticos gerais.
### Depois (MVC Separado por Domínio)
Pastas separadas com arquivos contendo propósitos únicos de negócio:
- `src/models/produto.py`
- `src/models/usuario.py`
- `src/models/pedido.py`

---

## 5. Transações de Banco de Dados (Atomicidade)

### Node.js (Antes - Callbacks sequenciais sem controle de transação)
```javascript
db.run("INSERT INTO enrollments ...", [], function(err) {
    db.run("INSERT INTO payments ...", [], function(err) {
        // Se falhar o pagamento, a matrícula permanece órfã
    });
});
```
### Node.js (Depois - Async/Await com Controle de Transação)
```javascript
async function executeCheckout(db, userId, courseId, amount) {
    await db.run("BEGIN TRANSACTION");
    try {
        const enrollment = await db.run("INSERT INTO enrollments ...", [userId, courseId]);
        await db.run("INSERT INTO payments ...", [enrollment.lastID, amount, 'PAID']);
        await db.run("COMMIT");
    } catch (err) {
        await db.run("ROLLBACK");
        throw err;
    }
}
```

---

## 6. Proteção de Rotas com Middleware de Autenticação

### Python/Flask (Antes - Rota Admin Sem Autenticação)
```python
@app.route("/admin/reset-db")
def reset_database():
    # Executa operação destrutiva
```
### Python/Flask (Depois - Rota com Validação de Cabeçalho / Token)
```python
from functools import wraps
from flask import request, jsonify

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or token != f"Bearer {os.environ.get('ADMIN_TOKEN')}":
            return jsonify({"erro": "Não autorizado"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/admin/reset-db")
@admin_required
def reset_database():
    # Operação segura
```

---

## 7. Evitando Queries N+1 (SQL Joins)

### Python (Antes - Select em loop)
```python
pedidos = cursor.execute("SELECT * FROM pedidos").fetchall()
for p in pedidos:
    p['itens'] = cursor.execute("SELECT * FROM itens WHERE pedido_id = " + str(p['id'])).fetchall()
```
### Python (Depois - Eager Loading ou Join único)
```python
# Consulta com JOIN unificado que traz tudo em uma única viagem ao banco
rows = cursor.execute("""
    SELECT p.id, p.total, i.produto_id, i.quantidade 
    FROM pedidos p 
    LEFT JOIN itens_pedido i ON p.id = i.pedido_id
""").fetchall()
# Agrupar itens por pedido no código
```

---

## 8. Node.js Callback Hell para Async/Await (Promisify)

### Node.js (Antes - Ninho de callbacks)
```javascript
db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
        // ...
    });
});
```
### Node.js (Depois - Invólucro de Promise com Async/Await)
```javascript
const dbGet = (sql, params) => new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => err ? reject(err) : resolve(row));
});

// Uso:
const course = await dbGet("SELECT * FROM courses WHERE id = ?", [cid]);
const user = await dbGet("SELECT id FROM users WHERE email = ?", [e]);
```
