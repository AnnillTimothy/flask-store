from flask import Flask, request, jsonify, render_template
from .config import Config
from .extensions import db, login_manager, migrate, csrf, mail
import uuid


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
        data  = request.json or {}
        email = data.get('email', '').strip()
        name  = data.get('name', '').strip()
        if not email or '@' not in email:
            return jsonify({'ok': False, 'message': 'Invalid email.'}), 400

        from app.models.subscriber import Subscriber
        from app.services import klaviyo_service

        existing = Subscriber.query.filter_by(email=email).first()
        if existing:
            if not existing.is_subscribed:
                existing.is_subscribed = True
                if name and not existing.name:
                    existing.name = name
                try:
                    db.session.commit()
                    klaviyo_service.sync_subscriber(existing)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
            return jsonify({'ok': True})

        sub = Subscriber(email=email, name=name or None, is_subscribed=True, source='popup')
        try:
            db.session.add(sub)
            db.session.commit()
            klaviyo_service.sync_subscriber(sub)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return jsonify({'ok': True})

    # ── Contact form submission endpoint ──────────────────────────
    @app.route('/contact', methods=['POST'])
    @csrf.exempt
    def contact_submit():
        data    = request.json or {}
        name    = (data.get('name') or '').strip()
        email   = (data.get('email') or '').strip()
        subject = (data.get('subject') or '').strip()
        message = (data.get('message') or '').strip()

        if not name or not email or '@' not in email or not message:
            return jsonify({'ok': False, 'message': 'Please fill in all required fields.'}), 400

        from app.models.contact_ticket import ContactTicket
        from app.models.subscriber import Subscriber
        from app.services import ses_service

        # Generate a short ticket reference
        ref = 'TKT-' + uuid.uuid4().hex[:8].upper()
        ticket = ContactTicket(
            ticket_ref=ref,
            name=name,
            email=email,
            subject=subject or None,
            message=message,
            status=ContactTicket.STATUS_NEW,
        )
        try:
            db.session.add(ticket)
            # Also upsert as a subscriber record
            existing_sub = Subscriber.query.filter_by(email=email).first()
            if not existing_sub:
                sub = Subscriber(email=email, name=name, is_subscribed=False, source='contact_form')
                db.session.add(sub)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({'ok': False, 'message': 'Could not save your message. Please try again.'}), 500

        # Send notifications (best-effort)
        try:
            ses_service.send_contact_ticket_confirmation(ticket)
            admin_email = app.config.get('MAIL_ADMIN') or app.config.get('MAIL_DEFAULT_SENDER', '')
            if admin_email:
                ses_service.send_contact_ticket_notification(ticket, admin_email)
        except Exception:
            pass

        return jsonify({'ok': True, 'ref': ref})

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

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app
