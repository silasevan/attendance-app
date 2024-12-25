from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config
import os
from flask_wtf import FlaskForm

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()

def create_app(config_class=Config):
    """
    Factory function to create and configure the Flask app instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Sanitize and validate configuration
    if 'SECRET_KEY' not in app.config or not app.config['SECRET_KEY']:
        raise ValueError("SECRET_KEY is not set. Please set it in the environment or config file.")

    if 'SQLALCHEMY_DATABASE_URI' not in app.config or not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("SQLALCHEMY_DATABASE_URI is not set. Please set it in the environment or config file.")

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # Customize to match your login route

    mail.init_app(app)

    # Automatically create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

# initiate user loader
@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))
