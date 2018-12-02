from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis

from config import envir
from info.modules.index import index_blu

db = SQLAlchemy()


def create_app(en):
    app = Flask(__name__)
    app.config.from_object(envir[en])
    db.init_app(app)
    Session(app)
    redis_store = StrictRedis(host=envir[en].REDIS_HOST, port=envir['development'].REDIS_PORT)

    app.register_blueprint(index_blu)
    return app
