import time

from flask import render_template, request, current_app, session, redirect, url_for, g
from datetime import datetime, timedelta
from info import login_check, constants
from info.models import User, News
from . import admin_blu


@admin_blu.route('/login', methods=['GET', 'POST'])
def login():
    """
    后台登录页面，输入账户密码，验证
    GET正常渲染
    POST收到表单的账户密码 记得csrftoken
    校验账户密码成功session保存账户信息跳转到后台页面
    失败返回失败提示信息
    :return:
    """
    errmsg = None
    if request.method == 'GET':
        return render_template('admin/login.html')
    if request.method == 'POST':
        name = request.form.get('username')
        pwd = request.form.get('password')

        if not all([name, pwd]):
            return render_template('admin/login.html', errmsg='参数不全')

        try:
            user = User.query.filter(User.mobile == name).first()
            result = user.check_passowrd(pwd)
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/login.html', errmsg='数据库错误')
        if result == False:
            return render_template('admin/login.html', errmsg='密码不正确')
        if user.is_admin != True:
            return render_template('admin/login.html', errmsg='不是管理员')

        session['user_id'] = user.id
        session['is_admin'] = True

        return redirect(url_for('admin_blu.admin_index'))


@admin_blu.route('/index')
@login_check
def admin_index():
    if not g.user:
        return redirect(url_for('admin_blu.login'))
    data = {
        'user': g.user.to_dict()
    }
    return render_template('admin/index.html', data=data)


@admin_blu.route('/count')
def count():
    """
    获取用户数据，GET。
    返回：
    用户总数 月新增数 日新增数
    按天活跃列表和天的计数列表
    :return:
    """
    total_user = 0
    try:
        total_user = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
    mon_user = 0
    try:
        now = time.localtime()
        mon_begin = '%d-%02d-01' % (now.tm_year, now.tm_mon)

        mon_begin_date = datetime.strptime(mon_begin, '%Y-%m-%d')
        mon_user = User.query.filter(User.is_admin == False, User.create_time > mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)
    day_user = 0
    try:
        now = time.localtime()
        day_begin = '%d-02%d-02%d' % (now.tm_year, now.tm_mon, now.tm_mday)
        day_begin_date = datetime.strptime(day_begin, '%Y-%m-%d')
        mon_user = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    now_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
    time_li = []
    active_li = []

    for i in range(0, 30):
        begin_date = now_date - timedelta(days=i)
        end_date = now_date - timedelta(days=(i - 1))
        time_li.append(begin_date.strftime('%Y-%m-%d'))
        count = 0
        try:
            count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                      User.last_login < end_date).count()
        except Exception as e:
            current_app.logger.error(e)
        active_li.append(count)

    active_li.reverse()
    time_li.reverse()

    data = {
        "total_user": total_user,
        'mon_user': mon_user,
        'day_user': day_user,
        'time_li': time_li,
        'active_li': active_li
    }
    return render_template('admin/user_count.html', data=data)


@admin_blu.route('/news_review', methods=['POST', 'GET'])
@login_check
def news_review():
    """
    获取要审核的新闻
    GET 正常渲染要获取的新闻 参数：分页 page 返回页面携带模型对象列表
    POST 对新闻审核 参数：news_id 返回json ok
    :return:
    """
    if not g.user:
        return redirect('/')
    page = request.args.get('p', 1)

    news_li = []
    try:
        paginate = News.query.filter(News.status != 0).paginate(int(page), constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
        total = paginate.pages
        news_li = paginate.items
    except Exception as e:
        current_app.logger.error()
        total = 1

    news = []

    for ne in news_li:
        news.append(ne.to_dict())

    data = {
        'news_li': news,
        'total': total,
        'page': page
    }
    return render_template('admin/news_review.html', data=data)


@admin_blu.route('/user_list')
@login_check
def user_list():
    if not g.user:
        return redirect('/')

    page = request.args.get('p')
    if page == None:
        page = 1

    users = []
    try:
        paginate = User.query.paginate(int(page), constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
        total = paginate.pages
        users = paginate.items
    except Exception as e:
        current_app.logger.error(e)
        total = 1

    data = {
        'users_li': users,
        'total': total,
        'page': page
    }
    return render_template('admin/user_list.html', data=data)
