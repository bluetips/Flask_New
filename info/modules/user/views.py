from flask import render_template, g, request, redirect, current_app, jsonify

from info import db, constants
from info.models import Category, News
from info.utils.comment_utils import login_check, qiniuyun
from info.utils.response_code import RET
from . import user_blu


@user_blu.route('/info')
@login_check
def user():
    user = g.user
    if not user:
        return redirect('/')
    data = {
        'user_info': g.user.to_dict()
    }
    return render_template('news/user.html', data=data)


@user_blu.route('/base_info', methods=['GET', 'POST'])
@login_check
def base_info():
    user = g.user
    if not user:
        return redirect('/')
    if request.method == 'POST':
        # 个人资料修改 参数 signature nike_name gender
        signature = request.json.get('signature')
        nick_name = request.json.get('nick_name')
        gender = request.json.get('gender')
        # 业务逻辑处理 添加到数据库 实例化一个模型
        user.signature = signature
        user.nick_name = nick_name
        user.gender = gender
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库错误')
        return jsonify(errno=RET.OK, errmsg='修改成功')

    data = {
        'user_info': g.user.to_dict()
    }
    return render_template('news/user_base_info.html', data=data)


@user_blu.route('/pic_info', methods=['POST', 'GET'])
@login_check
def pic_info():
    if not g.user:
        return redirect('/')
    if request.method == 'POST':
        # pic
        try:
            pic_file = request.files.get('avatar').read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="读取文件出错")
        if not pic_file:
            return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

        try:
            key = qiniuyun(pic_file)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.USERERR, errmsg='七牛云错误')

        try:
            g.user.avatar_url = key
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="保存用户数据错误")

        return jsonify(errno=RET.OK, errmsg='上传成功', data={"avatar_url": constants.QINIU_DOMIN_PREFIX + key})

    data = {
        'user_info': g.user.to_dict()
    }
    return render_template('news/user_pic_info.html', data=data)


@user_blu.route('/pass_info', methods=['POST', 'GET'])
@login_check
def pass_info():
    """
    get 常规渲染
    post json 获取旧的密码 新密码
    业务逻辑 验证旧密码 修改新的密码
    :return:json ok
    """
    if not g.user:
        return redirect('/')

    if request.method == 'POST':
        opwd = request.json.get('opwd')
        npwd = request.json.get('npwd_1')

        try:
            result = g.user.check_passowrd(opwd)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库错误')
        if result == True:
            g.user.password = npwd
        else:
            return jsonify(errno=RET.PWDERR, errmsg='密码错误')
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库错误')
        return jsonify(errno=RET.OK, errmsg='修改成功')

    return render_template('news/user_pass_info.html')


@user_blu.route('/collection', methods=['GET'])
@login_check
def collection():
    """
    显示收藏 分页显示
    get 参数：页面id 每页内容
    业务逻辑 用User模型 查询collection_news paginate显示
    :return: json :items page pages
    """
    if not g.user:
        return redirect('/')

    collection_news = g.user.collection_news
    page = 1
    p = request.args.get('p')
    if p:
        page = int(p)
    per_page = 10
    try:
        paginate = collection_news.paginate(page, per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库错误')
    page = paginate.page
    page_items = paginate.items
    pages = paginate.pages
    collection_li = []
    for item in page_items:
        collection_li.append(item.to_dict())
    data = {
        'collection_li': collection_li,
        'page': page,
        'pages': pages
    }
    return render_template('news/user_collection.html', data=data)


@user_blu.route('/news_release', methods=['POST', 'GET'])
@login_check
def news_release():
    """
    GET  正常渲染 分类
    POST json 参数：新闻 title category digest content index_image
    :return:
    """
    if not g.user:
        return redirect('/')
    if request.method == 'POST':
        title = request.form.get('title')
        source = '个人发布'
        digest = request.form.get('digest')
        content = request.form.get('content')
        image_file = request.files.get('image_file')
        category = request.form.get('category')
        category_id = Category.query.filter(Category.name == category).first().id
        user_id = g.user.id
        status = 1
        reason = ''

        if not all([title, digest, content, image_file, category]):
            return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

        try:
            image_file_byte = image_file.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.SERVERERR, errmsg='图片读取错误')

        try:
            key = qiniuyun(image_file_byte)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.UNKOWNERR, errmsg='七牛云错误')

        index_image_url = constants.QINIU_DOMIN_PREFIX + key

        news = News()
        news.title = title
        news.source = source
        news.digest = digest
        news.content = content
        news.index_image_url = index_image_url
        news.category_id = category_id
        news.user_id = g.user.id
        news.status = status
        news.reason = reason

        try:
            db.session.add(news)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='发布失败')

        return jsonify(errno=RET.OK, errmsg='OK')

    category_li = []
    try:
        category = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库错误')
    for cate in category:
        category_li.append(cate.to_dict())
    category_li.pop(0)
    data = {
        'category_li': category_li
    }

    return render_template('news/user_news_release.html', data=data)


@user_blu.route('/news_list')
@login_check
def news_list():
    """
    GET page
    业务逻辑 取到第几页 查询到符合的paginate
    :return:
    """
    if not g.user:
        return redirect('/')

    page = request.args.get('p', 1)

    try:
        news_paginate = News.query.filter(News.user_id == g.user.id).paginate(int(page), constants.USER_COLLECTION_MAX_NEWS,
                                                                              False)
        page = news_paginate.page
        pages = news_paginate.pages
        news_items = news_paginate.items
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库错误')

    news_li = []
    for item in news_items:
        news_li.append(item.to_review_dict())

    data = {
        'news_li': news_li,
        'page': page,
        'pages': pages
    }

    return render_template('news/user_news_list.html', data=data)
