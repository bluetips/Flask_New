from flask import render_template, current_app, session

from info.models import User
from . import index_blu


@index_blu.route('/')
def index():
    """
    验证是否登录，取得session的值
    :return:
    """
    try:
        user_id = session.get('user_id')
    except Exception as e:
        current_app.logger.error(e)
        return render_template('news/index.html')
    user = None
    if user_id:
        user = User.query.get(user_id)
        print(user)
    data = {'user_info': user.to_dict() if user else None}
    print(data)
    return render_template('news/index.html',data=data)


@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
