from flask import Flask, jsonify
from .config import Config
from .extensions import mongo, bcrypt, jwt
from .routes.org_routes import org_bp
from .routes.auth_routes import auth_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Register blueprints
    app.register_blueprint(org_bp, url_prefix="/org")
    app.register_blueprint(auth_bp, url_prefix="/admin")

    @app.get("/")
    def health_check():
        return jsonify({"status": "ok", "service": "Organization Management Service"})

    return app
