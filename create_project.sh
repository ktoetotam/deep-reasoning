#!/bin/bash
# Script to create the Flask project structure for llm-api-frontend

# Define the base directory
BASE_DIR="llm-api-frontend"

# Create directories
mkdir -p $BASE_DIR/app/api \
         $BASE_DIR/app/frontend \
         $BASE_DIR/app/static/css \
         $BASE_DIR/app/static/js \
         $BASE_DIR/app/static/images \
         $BASE_DIR/app/templates \
         $BASE_DIR/migrations \
         $BASE_DIR/tests

# Create app/__init__.py with an application factory
cat <<'EOF' > $BASE_DIR/app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)
    # Load configuration
    app.config.from_object('app.config.Config')

    # Initialize extensions
    from app.extensions import init_extensions
    init_extensions(app)

    # Register blueprints
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.frontend import frontend_bp
    app.register_blueprint(frontend_bp)

    return app
EOF

# Create app/config.py
cat <<'EOF' > $BASE_DIR/app/config.py
class Config:
    DEBUG = True
    SECRET_KEY = 'your-secret-key'
EOF

# Create app/extensions.py
cat <<'EOF' > $BASE_DIR/app/extensions.py
def init_extensions(app):
    # Initialize your extensions here (e.g., database, login_manager)
    pass
EOF

# Create app/models.py (empty for now)
cat <<'EOF' > $BASE_DIR/app/models.py
# Define your database models here
EOF

# Create app/api/__init__.py for API blueprint
cat <<'EOF' > $BASE_DIR/app/api/__init__.py
from flask import Blueprint

api_bp = Blueprint('api', __name__)

from app.api import routes
EOF

# Create app/api/routes.py with a sample endpoint
cat <<'EOF' > $BASE_DIR/app/api/routes.py
from flask import jsonify
from app.api import api_bp

@api_bp.route('/hello', methods=['GET'])
def hello_api():
    return jsonify(message="Hello from the API!")
EOF

# Create app/frontend/__init__.py for frontend blueprint
cat <<'EOF' > $BASE_DIR/app/frontend/__init__.py
from flask import Blueprint

frontend_bp = Blueprint('frontend', __name__)

from app.frontend import routes
EOF

# Create app/frontend/routes.py with a sample route
cat <<'EOF' > $BASE_DIR/app/frontend/routes.py
from flask import render_template
from app.frontend import frontend_bp

@frontend_bp.route('/')
def index():
    return render_template('index.html')
EOF

# Create app/static/css/main.css
cat <<'EOF' > $BASE_DIR/app/static/css/main.css
/* Add your custom styles here */
EOF

# Create app/static/js/app.js
cat <<'EOF' > $BASE_DIR/app/static/js/app.js
// Add your custom JavaScript here
EOF

# Create a placeholder for app/static/images/logo.png
touch $BASE_DIR/app/static/images/logo.png

# Create app/templates/layout.html
cat <<'EOF' > $BASE_DIR/app/templates/layout.html
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}LLM API Frontend{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
EOF

# Create app/templates/index.html
cat <<'EOF' > $BASE_DIR/app/templates/index.html
{% extends "layout.html" %}
{% block title %}Home{% endblock %}
{% block content %}
<h1>Welcome to LLM API Frontend</h1>
{% endblock %}
EOF

# Create tests/__init__.py (empty file)
touch $BASE_DIR/tests/__init__.py

# Create tests/test_app.py with a basic test case
cat <<'EOF' > $BASE_DIR/tests/test_app.py
import unittest
from app import create_app

class BasicTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app().test_client()

    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
EOF

# Create .env file
cat <<'EOF' > $BASE_DIR/.env
# Environment variables
SECRET_KEY=your-secret-key
EOF

# Create requirements.txt
cat <<'EOF' > $BASE_DIR/requirements.txt
Flask
EOF

# Create run.py as the entry point for the Flask app
cat <<'EOF' > $BASE_DIR/run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
EOF

# Create README.md
cat <<'EOF' > $BASE_DIR/README.md
# LLM API Frontend

This project is a Flask application with separated frontend and backend (API) blueprints.
EOF

echo "Flask project structure created successfully in '$BASE_DIR'!"

