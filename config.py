from redis import StrictRedis
import logging


class Config(object):
    SECRET_KEY = 'zhengzhi'
    PERMANENT_SESSION_LIFETIME = 86400 * 2
    SQLALCHEMY_DATABASE_URI = 'mysql://root:12345678@localhost:3306/info27'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    SESSION_TYPE = 'redis'
    SESSION_USE_SIGNER = True
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_PERMANENT = False


class Development(Config):
    DEBUG = True


class Product(Config):
    pass


envir = {
    'development': Development,
    'product': Product
}
