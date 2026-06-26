import bcrypt
from src.database.connection import get_db

def row_to_dict(row, include_password=False):
    d = {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"]
    }
    if include_password:
        d["senha"] = row["senha"]
    return d

def get_todos_usuarios():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios")
    rows = cursor.fetchall()
    return [row_to_dict(row, include_password=False) for row in rows]

def get_usuario_por_id(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        return row_to_dict(row, include_password=False)
    return None

def criar_usuario(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    hashed_pwd = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, hashed_pwd, tipo)
    )
    db.commit()
    return cursor.lastrowid

def login_usuario(email, senha):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row:
        stored_hash = row["senha"]
        # Treat plaintext check for safety (in case seed didn't run or old users existed)
        # But in our seed it's fully bcrypt-hashed. Let's do a robust check:
        try:
            is_valid = bcrypt.checkpw(senha.encode('utf-8'), stored_hash.encode('utf-8'))
        except ValueError:
            # Fallback for plain text password comparison just in case
            is_valid = (senha == stored_hash)
        
        if is_valid:
            return {
                "id": row["id"],
                "nome": row["nome"],
                "email": row["email"],
                "tipo": row["tipo"]
            }
    return None
