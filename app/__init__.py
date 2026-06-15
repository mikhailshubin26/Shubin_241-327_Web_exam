import os

from flask import Flask
from sqlalchemy import event
from sqlalchemy.engine import Engine

from config import Config
from app.extensions import db, login_manager
from app.utils import render_markdown


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_message = "Для выполнения данного действия необходимо пройти процедуру аутентификации"
    login_manager.login_message_category = "warning"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.books.routes import books_bp
    from app.reviews.routes import reviews_bp
    from app.stats.routes import stats_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(stats_bp)

    app.jinja_env.filters["markdown"] = render_markdown

    return app
