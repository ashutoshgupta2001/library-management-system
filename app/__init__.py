from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import pymysql
pymysql.install_as_MySQLdb()

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:ashutosh@localhost/ashu_library'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = '2a063d1d-3dc8-47fe-8a29-19af9fc49b4e'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

from app import admin_routes
from app import user_routes


def create_tables():
    with app.app_context():
        db.create_all()
    print("Tables created!")