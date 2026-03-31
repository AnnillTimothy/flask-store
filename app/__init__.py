from flask import Flask
from .config import Config
from .extensions import db, login_manager, migrate, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialise extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # User loader for Flask-Login
    from .models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.cart import cart_bp
    from .routes.checkout import checkout_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(checkout_bp, url_prefix='/checkout')

    # Setup Flask-Admin (must happen after blueprints so url_for works)
    from .admin.views import setup_admin
    setup_admin(app)

    # Inject cart count into every template
    from .services import cart_service

    @app.context_processor
    def inject_cart():
        try:
            count = cart_service.get_cart_count()
        except Exception:
            count = 0
        return {'cart_count': count}

    # Inject branding into every template
    from .context_processors import inject_branding
    app.context_processor(inject_branding)

    return app
