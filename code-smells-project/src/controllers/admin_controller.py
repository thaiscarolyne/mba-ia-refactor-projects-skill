import logging
from flask import jsonify
from src.database.connection import get_db

logger = logging.getLogger(__name__)

def reset_database():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM itens_pedido")
        cursor.execute("DELETE FROM pedidos")
        cursor.execute("DELETE FROM produtos")
        cursor.execute("DELETE FROM usuarios")
        db.commit()
        logger.info("!!! BANCO DE DADOS RESETADO PELO ADMINISTRADOR !!!")
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao resetar o banco de dados: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def health_check():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.execute("SELECT COUNT(*) FROM produtos")
        produtos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos = cursor.fetchone()[0]

        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": produtos,
                "usuarios": usuarios,
                "pedidos": pedidos
            },
            "versao": "1.0.0",
            "ambiente": "producao"
        }), 200
    except Exception as e:
        logger.error(f"Falha no Health Check: {str(e)}")
        return jsonify({"status": "erro", "detalhes": str(e)}), 500
