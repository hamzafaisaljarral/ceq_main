from flask_jwt_extended import JWTManager, get_jwt
 
jwt = JWTManager()  # Create a global JWTManager instance
blacklist = set()  # This set should be accessible globally
 
def initialize_jwt(app):
    jwt.init_app(app)  # Initialize JWTManager with Flask app
 
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload.get("jti")
    print("Checking jti in blacklist:", jti)
    return jti in blacklist
 
def setup_jwt_handlers(app):
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blacklist(jwt_header, jwt_payload):
        return check_if_token_in_blacklist(jwt_header, jwt_payload)    
    