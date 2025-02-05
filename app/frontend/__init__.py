from flask import Blueprint

frontend_bp = Blueprint('frontend', __name__)
#api_bp = Blueprint('api', __name__)


from app.frontend import routes
