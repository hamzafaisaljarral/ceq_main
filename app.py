import os
from flask import Flask
from ceq_user import init_app as init_ceq_app
from flask_jwt_extended import JWTManager
from ceq_user.database.db import initialize_db as initialize_db_ceq
from flask_cors import CORS
 
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/ceq_main/static/consumer/')  # Default path
 
def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['JWT_SECRET_KEY'] = 'aSuperSecretKey'
    app.config['MONGODB_SETTINGS'] = os.environ.get('MONGO_HOST_CEQ')
    app.config['CEQ_DB_NAME'] = 'ceq'
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['UPLOAD_FOLDER'] = '/ceq_main'
    print(app.config['UPLOAD_FOLDER'])
    # Initialize JWT, database, and CORS
    jwt = JWTManager(app)
    init_ceq_app(app)
    initialize_db_ceq(app)
    cors = CORS(app, resources={r'/*': {'origins': '*'}})
    # Debugging: Print out UPLOAD_FOLDER and check if it exists
    print("UPLOAD_FOLDER:", UPLOAD_FOLDER)
    print("Does UPLOAD_FOLDER exist?", os.path.exists(UPLOAD_FOLDER))
    print("Current working DIR: ", os.getcwd())
    return app
