import os
from flask import Flask
from ceq_user import init_app as init_ceq_app
from ceq_user.database.db import initialize_db as initialize_db_ceq
from flask_cors import CORS
# Removed import of JWTManager and setup_jwt_handlers
 
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/ceq_main/static/consumer/')  # Default path
 
def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['JWT_SECRET_KEY'] = 'aSuperSecretKey'
    app.config['MONGODB_SETTINGS'] = os.environ.get('MONGO_HOST_CEQ')
    app.config['CEQ_DB_NAME'] = 'ceq'
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['UPLOAD_FOLDER'] = '/ceq_main'
    # Initialize application components
    init_ceq_app(app)  # This handles JWT setup now
    initialize_db_ceq(app)
 
    # CORS configuration
    cors = CORS(app, resources={r'/*': {'origins': '*'}})
 
    return app