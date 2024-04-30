from flask import Blueprint

ceq_app = Blueprint('ceq_user', __name__)

from ceq_user.resources import routes

# MongoDB settings for sub_app2
sub_app2_settings = {
    'db': 'ceq',
    'host': 'mongodb://localhost:27017'
}


def init_app(app):
    app.register_blueprint(ceq_app)

    from ceq_user.resources.routes import initialize_routes
    initialize_routes(app)