from flask import Flask, request, jsonify
from .config import Config
from .extensions import db, login_manager, migrate, csrf, mail


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialise extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)

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

    # Exempt all Flask-Admin blueprints from CSRF protection.
    # Flask-Admin manages its own form security; WTF CSRF tokens are not
    # included in Flask-Admin forms and would block every create/edit/delete.
    _app_blueprints = {'main', 'auth', 'cart', 'checkout'}
    for bp_name, bp in app.blueprints.items():
        if bp_name not in _app_blueprints:
            csrf.exempt(bp)

    # ── Newsletter subscribe endpoint ─────────────────────────────
    @app.route('/subscribe', methods=['POST'])
    @csrf.exempt
    def newsletter_subscribe():
        email = (request.json or {}).get('email', '').strip()
        if not email or '@' not in email:
            return jsonify({'ok': False, 'message': 'Invalid email.'}), 400
        try:
            from flask_mail import Message
            admin_addr = app.config.get('MAIL_ADMIN') or app.config.get('MAIL_DEFAULT_SENDER')
            if admin_addr and app.config.get('MAIL_USERNAME'):
                msg = Message(
                    subject='New Newsletter Subscriber',
                    recipients=[admin_addr],
                    body=f'New subscriber: {email}',
                )
                mail.send(msg)
                # Welcome email to subscriber
                try:
                    from app.models.company_setting import CompanySetting
                    with app.app_context():
                        name = CompanySetting.get().store_name or 'The Bodhi Tree'
                except Exception:
                    name = 'The Bodhi Tree'
                welcome = Message(
                    subject=f'Welcome to {name}',
                    recipients=[email],
                    body=(
                        f'Thank you for subscribing to {name}! '
                        'Your 10% discount code is: WELCOME10\n\n'
                        'We\'ll keep you posted on new arrivals and exclusive experiences.'
                    ),
                )
                mail.send(welcome)
        except Exception:
            pass  # Mail is best-effort; don't fail the request
        return jsonify({'ok': True})

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
