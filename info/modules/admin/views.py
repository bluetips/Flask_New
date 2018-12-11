import time

from flask import render_template, request, current_app, session, redirect, url_for, g, jsonify
from datetime import datetime, timedelta
from info import login_check, constants, db
from info.models import User, News, Category
from info.utils.comment_utils import qiniuyun
from info.utils.response_code import RET
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


@admin_blu.route('/news_review')
@login_check
def news_review():
    """
    获取要审核的新闻
    GET 正常渲染要获取的新闻 参数：分页 page 返回页面携带模型对象列表
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


@admin_blu.route('news_review_detail', methods=['GET', 'POST'])
def news_review_detail():
    """
    如果是ajax请求post 取到status 如果是不通过给出reason
    :return:json
    """

    if request.method == 'POST':
        action = request.json.get('action')
        reason = request.json.get('reason')
        news_id = request.json.get('news_id')

        if not all([action, news_id]):
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库错误')
        if action == 'accept':
            news.status = 0
        if action == 'reject':
            if not reason:
                return jsonify(errno=RET.PARAMERR, errmsg='请输入理由')
            news.status = -1
            news.reason = reason

        try:
            db.session.add(news)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库错误')

        return jsonify(errno=RET.OK, errmsg='通过')

    news_id = request.args.get('news_id')
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    data = {
        'news': news.to_review_dict() if news else None
    }
    return render_template('admin/news_review_detail.html', data=data)


@admin_blu.route('/news_edit', methods=['POST', 'GET'])
def news_edit():
    """
    获取要审核的新闻
    GET 正常渲染要获取的新闻 参数：分页 page 返回页面携带模型对象列表
    :return:
    """
    page = request.args.get('p', 1)

    news_li = []
    try:
        paginate = News.query.filter(News.status == 0).paginate(int(page), constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
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
    return render_template('admin/news_edit.html', data=data)


@admin_blu.route('/news_edit_detail', methods=['GET', 'POST'])
def news_edit_detail():
    """
    如果是ajax请求post 取到status 如果是不通过给出reason
    :return:json
    """

    if request.method == 'POST':
        news_id = request.form.get("news_id")
        title = request.form.get("title")
        digest = request.form.get("digest")
        content = request.form.get("content")
        index_image = request.files.get("index_image")
        category_id = request.form.get("category_id")
        # 1.1 判断数据是否有值
        if not all([title, digest, content, category_id]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

        news = None
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
        if not news:
            return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

        # 1.2 尝试读取图片
        if index_image:
            try:
                index_image = index_image.read()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

            # 2. 将标题图片上传到七牛
            try:
                key = qiniuyun(index_image)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
            news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
        # 3. 设置相关数据
        news.title = title
        news.digest = digest
        news.content = content
        news.category_id = category_id

        # 4. 保存到数据库
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
        # 5. 返回结果
        return jsonify(errno=RET.OK, errmsg="编辑成功")

    news_id = request.args.get('news_id')
    try:
        news = News.query.get(news_id)
        category = Category.query.get(news.category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库错误·')

    category_li = []

    categ = Category.query.all()
    for cate in categ:
        category_li.append(cate)

    category_li.pop(0)

    data = {
        'news': news if news else None,
        'category': category,
        'category_li': category_li

    }
    return render_template('admin/news_edit_detail.html', data=data)


@admin_blu.route('/news_type', methods=['GET', 'POST'])
def news_type():
    if request.method == 'GET':
        try:
            category = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库错误')
        category_li = []
        for cate in category:
            category_li.append(cate.to_dict())

        data = {
            'category_li': category_li
        }
        return render_template('admin/news_type.html', data=data)
    if request.method == 'POST':
        """
        post category_id name
        """
        category_id = request.json.get('id', None)
        name = request.json.get('name')

        if not name:
            return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

        if category_id:
            cate = Category.query.get(category_id)
            cate.name = name
            db.session.commit()
            return jsonify(errno=RET.OK, errmsg='成功')
        else:
            cate = Category()
            cate.name = name
            db.session.add(cate)
            db.session.commit()
            return jsonify(errno=RET.OK, errmsg='OK')
