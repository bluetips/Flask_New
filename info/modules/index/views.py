from flask import render_template, current_app, session

from info import constants
from info.models import User, News
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

    news_hot = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)

    news_hot_list = []

    for news in news_hot:
        news_hot_list.append(news)

    user = None
    if user_id:
        user = User.query.get(user_id)
    data = {
        'user_info': user.to_dict() if user else None,
        'news_hot_list':news_hot_list
    }

    return render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
