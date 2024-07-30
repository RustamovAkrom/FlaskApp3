from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_babel import Babel
# from flask_socketio import SocketIO


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
admin = Admin(name="Flask Administrations")
babel = Babel()
# socketio = SocketIO()


def create_app(config_class = "config.Config"):

    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    babel.init_app(app)
    # socketio.init_app(app)

    login_manager.login_view = 'app.auth.login'


    from app.models import User, Post
    
    admin.init_app(app)
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Post, db.session))

    from .main import main as auth_blueprint
    app.register_blueprint(auth_blueprint, url_perfix="/main")

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_perfix="/auth")

    from .api import api_db as api_blueprint
    app.register_blueprint(api_blueprint, url_perfix="/api")

    return app

