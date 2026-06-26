import logging
from flask import Flask
from flask_cors import CORS
from database import db
from config.settings import Settings
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp
import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = Settings.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = Settings.SECRET_KEY

CORS(app)
db.init_app(app)

app.register_blueprint(task_bp)
app.register_blueprint(user_bp)
app.register_blueprint(report_bp)

@app.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}

@app.route('/')
def index():
    return {'message': 'Task Manager API (Refatorada para MVC)', 'version': '1.1'}

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    logger.info("Iniciando Task Manager API...")
    app.run(debug=Settings.DEBUG, host='0.0.0.0', port=5000)
