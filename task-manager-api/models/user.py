from database import db
from datetime import datetime
import bcrypt

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serializa o usuário sem expor a senha."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }

    def set_password(self, pwd):
        """Gera hash seguro com bcrypt."""
        self.password = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, pwd):
        """Verifica senha contra hash bcrypt armazenado."""
        try:
            return bcrypt.checkpw(pwd.encode('utf-8'), self.password.encode('utf-8'))
        except ValueError:
            return False

    def is_admin(self):
        return self.role == 'admin'
