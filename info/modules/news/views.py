from flask import render_template, current_app, session, g, request, jsonify

from info import constants, db
from info.models import User, News, tb_user_collection
from info.utils.comment_utils import login_check
from info.utils.response_code import RET
from . import news_blu


@news_blu.route('/<int:news_id>')
@login_check
def detail(news_id):
    user = g.user
    news_hot = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    news_hot_list = []
    for ne in news_hot:
        news_hot_list.append(ne)

    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if news in user.collection_news:
        collec = True
    else:
        collec = False

    data = {
        'user_info': user.to_dict() if user else None,
        'news_hot_list': news_hot_list,
        'news': news.to_dict() if news else None,
        'collec': collec

    }
    return render_template('news/detail.html', data=data)


@news_blu.route('/new_collect', methods=['POST'])
@login_check
def collec():
    """
    请求参数：POST:news_id user_id
    校验参数
    返回json
    :return:
    """
    user = g.user
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    if not all([news_id, action]) and (action not in ("collect", "cancel_collect")):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库错误')

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻数据不存在")

    if action == 'collect':
        user.collection_news.append(news)

    else:
        user.collection_news.remove(news)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库错误')

    return jsonify(errno=RET.OK, errmsg='收藏成功')
