from mongoengine import connect,disconnect


def initialize_db(app):
    connect(db=app.config['CEQ_DB_NAME'], host=app.config['MONGODB_SETTINGS'])