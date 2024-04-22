import utils
from flask import Flask
from flask_jwt_extended import JWTManager
from api.core import user_routes, common_routes


# Initialize Flask app
app = Flask(__name__)

app.register_blueprint(common_routes)
app.register_blueprint(user_routes)

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = utils.JWT_KEY
jwt = JWTManager(app)
