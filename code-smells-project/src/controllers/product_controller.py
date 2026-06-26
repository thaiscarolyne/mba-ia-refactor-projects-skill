import logging
from flask import request, jsonify
import src.models.product as product_model

logger = logging.getLogger(__name__)

def listar_produtos():
    try:
        produtos = product_model.get_todos_produtos()
        logger.info(f"Listando {len(produtos)} produtos")
        return jsonify({"dados": produtos, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def buscar_produto(id):
    try:
        produto = product_model.get_produto_por_id(id)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        else:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception as e:
        logger.error(f"Erro ao buscar produto {id}: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def criar_produto():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        if "nome" not in dados:
            return jsonify({"erro": "Nome é obrigatório"}), 400
        if "preco" not in dados:
            return jsonify({"erro": "Preço é obrigatório"}), 400
        if "estoque" not in dados:
            return jsonify({"erro": "Estoque é obrigatório"}), 400

        nome = dados["nome"]
        descricao = dados.get("descricao", "")
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")

        if preco < 0:
            return jsonify({"erro": "Preço não pode ser negativo"}), 400
        if estoque < 0:
            return jsonify({"erro": "Estoque não pode ser negativo"}), 400
        if len(nome) < 2:
            return jsonify({"erro": "Nome muito curto"}), 400
        if len(nome) > 200:
            return jsonify({"erro": "Nome muito longo"}), 400

        categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
        if categoria not in categorias_validas:
            return jsonify({"erro": f"Categoria inválida. Válidas: {str(categorias_validas)}"}), 400

        produto_id = product_model.criar_produto(nome, descricao, preco, estoque, categoria)
        logger.info(f"Produto criado com ID: {produto_id}")
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201
    except Exception as e:
        logger.error(f"Erro ao criar produto: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def atualizar_produto(id):
    try:
        dados = request.get_json()
        produto_existente = product_model.get_produto_por_id(id)
        if not produto_existente:
            return jsonify({"erro": "Produto não encontrado"}), 404

        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        if "nome" not in dados:
            return jsonify({"erro": "Nome é obrigatório"}), 400
        if "preco" not in dados:
            return jsonify({"erro": "Preço é obrigatório"}), 400
        if "estoque" not in dados:
            return jsonify({"erro": "Estoque é obrigatório"}), 400

        nome = dados["nome"]
        descricao = dados.get("descricao", "")
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")

        if preco < 0:
            return jsonify({"erro": "Preço não pode ser negativo"}), 400
        if estoque < 0:
            return jsonify({"erro": "Estoque não pode ser negativo"}), 400

        product_model.atualizar_produto(id, nome, descricao, preco, estoque, categoria)
        logger.info(f"Produto {id} atualizado com sucesso")
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200
    except Exception as e:
        logger.error(f"Erro ao atualizar produto {id}: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def deletar_produto(id):
    try:
        produto = product_model.get_produto_por_id(id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404

        product_model.deletar_produto(id)
        logger.info(f"Produto {id} deletado")
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
    except Exception as e:
        logger.error(f"Erro ao deletar produto {id}: {str(e)}")
        return jsonify({"erro": str(e)}), 500

def buscar_produtos():
    try:
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)

        if preco_min:
            preco_min = float(preco_min)
        if preco_max:
            preco_max = float(preco_max)

        resultados = product_model.buscar_produtos(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao buscar produtos com filtros: {str(e)}")
        return jsonify({"erro": str(e)}), 500
