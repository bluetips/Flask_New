from flask import render_template, current_app, session, request, jsonify

from info import constants
from info.models import User, News
from info.utils.response_code import RET
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
        'news_hot_list': news_hot_list
    }

    return render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


@index_blu.route('/new_list')
def new_list():
    """
    GET request.arg
    1.参数：分类cid 页面page 每页多少content_num
    2.参数校验
    3.数据库查询
    4.返回json
    :return:
    """
    args_dict = request.args
    cid = args_dict.get('cid', '1')
    page = args_dict.get('page', '1')
    per_page = args_dict.get('per_page', constants.HOME_PAGE_MAX_NEWS)

    try:
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数格式错误')

    # 如果分类id不为1，那么添加分类id的过滤
    filters = []

    if cid != '1':
        filters.append(News.category_id == cid)
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
        items = paginate.items
        tottal_page = paginate.pages
        current_page = paginate.page
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库错误')

    new_list = []

    for new in items:
        new_list.append(new.to_dict())
    data = {
        'tottal_page': tottal_page,
        'current_page': current_page,
        'new_list': new_list,
        'cid': cid

    }

    return jsonify(errno=RET.OK, errmsg='成功', data=data)
