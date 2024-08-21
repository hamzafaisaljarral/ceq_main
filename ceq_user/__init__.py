from flask import Blueprint
from flask_jwt_extended import JWTManager, get_jwt
 
# Create a global JWTManager instance
jwt = JWTManager()
blacklist = set()  # Global set to keep track of blacklisted tokens
 
# Define your Blueprint
ceq_app = Blueprint('ceq_user', __name__)
 
def initialize_jwt(app):
    """Initialize JWTManager with Flask app."""
    jwt.init_app(app)
 
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    """Check if the token is in the blacklist."""
    jti = jwt_payload.get("jti")
    print("Checking jti in blacklist:", jti)
    return jti in blacklist
 
def setup_jwt_handlers(app):
    """Setup JWT token handlers."""
    @jwt.token_in_blocklist_loader
    def token_in_blacklist(jwt_header, jwt_payload):
        return check_if_token_in_blacklist(jwt_header, jwt_payload)
 
def init_app(app):
    """Initialize application with blueprints and JWT handlers."""
    app.register_blueprint(ceq_app)
    from ceq_user.resources.routes import initialize_routes
    initialize_routes(app)
    initialize_jwt(app)  # Initialize JWTManager with the app
    setup_jwt_handlers(app)  # Setup JWT handlers