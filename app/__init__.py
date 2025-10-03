# app/__init__.py

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from markupsafe import escape, Markup
from sqlalchemy import MetaData # <-- 1. NOVA IMPORTAÇÃO

# --- 2. NOVA REGRA DE NOMES ---
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
# -----------------------------

# --- 3. ATUALIZE A INICIALIZAÇÃO DO DB ---
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate()
# ----------------------------------------

login = LoginManager()
login.login_view = 'main.login'
login.login_message = 'Por favor, faça login para acessar esta página.'
login.login_message_category = 'info'

def nl2br(value):
    return Markup(escape(value).replace('\n', '<br>\n'))




def create_app(config_class=Config):
    # Apenas __name__ é necessário. O Flask encontrará as pastas automaticamente.
    app = Flask(__name__)
    app.config.from_object(config_class)

    # A inicialização do db e migrate agora é feita fora da função
    db.init_app(app)
    migrate.init_app(app, db)
    
    login.init_app(app)

    from app.routes import bp as main_blueprint
    app.register_blueprint(main_blueprint)
    
    app.jinja_env.filters['nl2br'] = nl2br
    
    return app

from app import models
