import logging
from flask import Flask, jsonify
from flask_cors import CORS
from src.config.settings import Settings
from src.database.connection import get_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

get_db()

app = Flask(__name__)
app.config["SECRET_KEY"] = Settings.SECRET_KEY
app.config["DEBUG"] = Settings.DEBUG

CORS(app)

from src.routes.product_routes import product_bp
from src.routes.user_routes import user_bp
from src.routes.order_routes import order_bp
from src.routes.admin_routes import admin_bp

app.register_blueprint(product_bp)
app.register_blueprint(user_bp)
app.register_blueprint(order_bp)
app.register_blueprint(admin_bp)

@app.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja (Refatorada para MVC)",
        "versao": "1.1.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health"
        }
    })

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("SERVIDOR INICIADO (MVC)")
    logger.info(f"Rodando em http://localhost:5000 | Debug: {Settings.DEBUG}")
    logger.info("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=Settings.DEBUG)
