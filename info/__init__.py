from logging.handlers import RotatingFileHandler
import logging
from flask import Flask, render_template, g
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from redis import StrictRedis
from config import envir

redis_store = None  # type:StrictRedis
db= SQLAlchemy()

from info.utils.comment_utils import index_loop, login_check


def setup_log(en):
    # 设置日志的记录等级
    logging.basicConfig(level=envir[en].LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(en):
    app = Flask(__name__)
    app.config.from_object(envir[en])
    db.init_app(app)
    Session(app)
    global redis_store
    redis_store = StrictRedis(host=envir[en].REDIS_HOST, port=envir['development'].REDIS_PORT)

    from info.modules.index import index_blu
    app.register_blueprint(index_blu)

    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)

    from info.modules.news import news_blu
    app.register_blueprint(news_blu)

    from info.modules.user import user_blu
    app.register_blueprint(user_blu)

    from info.modules.admin import admin_blu
    app.register_blueprint(admin_blu, url_prefix='/admin')

    CSRFProtect(app)

    setup_log(en)

    @app.after_request
    def after_request(response):
        csrf_token = generate_csrf()
        response.set_cookie("csrf_token", csrf_token)
        return response

    @app.errorhandler(404)
    @login_check
    def not_found(resp):
        user = g.user
        data = {
            'user_info': user.to_dict() if user else None
        }
        return render_template('news/404.html', data=data)

    app.add_template_filter(index_loop, 'index_loop')

    return app
