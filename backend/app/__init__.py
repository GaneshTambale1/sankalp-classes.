import os
from datetime import timedelta
from flask import Flask, jsonify
from sqlalchemy.exc import IntegrityError
from .extensions import db, migrate, jwt, limiter, cors


def create_app(config_override=None):
    app = Flask(__name__)
    db_url = os.getenv('DATABASE_URL', 'sqlite:///local.db')
    if db_url.startswith('postgres://'):
        db_url = 'postgresql+psycopg://' + db_url[len('postgres://'):]
    elif db_url.startswith('postgresql://'):
        db_url = 'postgresql+psycopg://' + db_url[len('postgresql://'):]
    app.config.update(
        SQLALCHEMY_DATABASE_URI=db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={'pool_pre_ping': True} if not db_url.startswith('sqlite:') else {},
        SECRET_KEY=os.environ.get('SECRET_KEY','development-only-not-for-production'),
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY','development-only-jwt-not-for-production'),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=2),
        JWT_ERROR_MESSAGE_KEY='error',
        MAX_CONTENT_LENGTH=2*1024*1024,
        JSON_SORT_KEYS=False,
    )
    if config_override:
        app.config.update(config_override)
    if os.getenv('APP_ENV') == 'production' and (
        len(app.config['SECRET_KEY']) < 32 or app.config['SECRET_KEY'].startswith('development-only') or len(app.config['JWT_SECRET_KEY']) < 32
        or app.config['JWT_SECRET_KEY'].startswith('development-only')
        or not os.environ.get('DATABASE_URL')
    ):
        raise RuntimeError('Production requires secure SECRET_KEY, JWT_SECRET_KEY and DATABASE_URL')
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    origin = os.getenv('FRONTEND_ORIGIN','http://localhost:4200')
    cors.init_app(app, resources={r'/api/*': {'origins': [origin]}}, supports_credentials=False)
    from .models import TokenBlocklist
    @jwt.token_in_blocklist_loader
    def revoked(_header, data):
        return db.session.get(TokenBlocklist, data['jti']) is not None
    from .api import api
    app.register_blueprint(api, url_prefix='/api/v1')
    @app.get('/health')
    def health():
        return jsonify(status='ok',service='sankalp-classes')
    @app.errorhandler(413)
    def oversized(_e):
        return jsonify(error='Request too large'),413
    @app.errorhandler(429)
    def throttled(_e):
        return jsonify(error='Rate limit exceeded'),429
    @app.errorhandler(IntegrityError)
    def integrity(_e):
        db.session.rollback()
        return jsonify(error='A conflicting or referenced record prevents this operation'),409
    return app
