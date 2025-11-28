from flask import Flask

from .blueprints.core import bp_core
from .blueprints.printers import bp_printers
from .config import Config
from .logging_setup import configure_logging
from .middleware import register_cors


def create_app(config=None) -> Flask:
    """Factory that configures the Flask application with blueprints and middleware."""
    configure_logging()

    app = Flask(__name__)
    app.config.from_object(config or Config)
    register_cors(app)
    app.register_blueprint(bp_core)
    app.register_blueprint(bp_printers)
    return app
