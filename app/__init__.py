from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv("app/api/.env")
load_dotenv("app/frontend/.env")


def create_app():
    app = Flask(__name__)
    # Load configuration
    app.config.from_object('app.config.Config')

    # Initialize extensions
    from app.extensions import init_extensions
    init_extensions(app)

    # Register blueprints
  #  from app.api import api_bp
  #  app.register_blueprint(api_bp, url_prefix='/api')

    from app.frontend import frontend_bp
    
    app.register_blueprint(frontend_bp)
    print(os.environ.get("LLM_API_KEY"))
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
