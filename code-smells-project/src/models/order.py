from src.database.connection import get_db

def criar_pedido(usuario_id, itens):
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Começa transação explícita
        db.execute("BEGIN TRANSACTION")
        
        total = 0
        for item in itens:
            cursor.execute("SELECT nome, preco, estoque FROM produtos WHERE id = ?", (item["produto_id"],))
            produto = cursor.fetchone()
            if produto is None:
                db.rollback()
                return {"erro": f"Produto {item['produto_id']} não encontrado"}
            if produto["estoque"] < item["quantidade"]:
                db.rollback()
                return {"erro": f"Estoque insuficiente para {produto['nome']}"}
            total += (produto["preco"] * item["quantidade"])
            
        cursor.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total)
        )
        pedido_id = cursor.lastrowid
        
        for item in itens:
            cursor.execute("SELECT preco FROM produtos WHERE id = ?", (item["produto_id"],))
            produto = cursor.fetchone()
            cursor.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
            )
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"])
            )
            
        db.commit()
        return {"pedido_id": pedido_id, "total": total}
    except Exception as e:
        db.rollback()
        return {"erro": f"Erro interno ao criar pedido: {str(e)}"}

def get_pedidos_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.id as pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
               i.produto_id, i.quantidade, i.preco_unitario, pr.nome as produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON p.id = i.pedido_id
        LEFT JOIN produtos pr ON i.produto_id = pr.id
        WHERE p.usuario_id = ?
    """, (usuario_id,))
    rows = cursor.fetchall()
    
    pedidos_dict = {}
    for row in rows:
        pid = row["pedido_id"]
        if pid not in pedidos_dict:
            pedidos_dict[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": []
            }
        
        if row["produto_id"] is not None:
            pedidos_dict[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"]
            })
            
    return list(pedidos_dict.values())

def get_todos_pedidos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.id as pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
               i.produto_id, i.quantidade, i.preco_unitario, pr.nome as produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON p.id = i.pedido_id
        LEFT JOIN produtos pr ON i.produto_id = pr.id
    """)
    rows = cursor.fetchall()
    
    pedidos_dict = {}
    for row in rows:
        pid = row["pedido_id"]
        if pid not in pedidos_dict:
            pedidos_dict[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": []
            }
        
        if row["produto_id"] is not None:
            pedidos_dict[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"]
            })
            
    return list(pedidos_dict.values())

def atualizar_status_pedido(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    return True

def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total) FROM pedidos")
    faturamento = cursor.fetchone()[0]
    if faturamento is None:
        faturamento = 0
        
    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]
    
    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02
        
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0
    }
