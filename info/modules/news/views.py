from flask import render_template, current_app, session, g, request, jsonify, abort

from info import constants, db
from info.models import User, News, tb_user_collection, Comment, CommentLike
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

    author = None
    if news.user_id:
        try:
            author = User.query.get(news.user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库错误')

    if user:

        if news in user.collection_news:
            collec = True
        else:
            collec = False

        try:
            comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库错误')

        comment_ids = [comment.id for comment in comments]

        comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                 CommentLike.user_id == g.user.id)

        comment_like_cds = [commentLike.comment_id for commentLike in comment_likes]

        comment_li = []

        for comm in comments:
            comm_dict = comm.to_dict()
            if comm.id in comment_like_cds:
                comm_dict['is_like'] = True
            else:
                comm_dict['is_like'] = False
            comment_li.append(comm_dict)

    else:
        try:
            comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库错误')
        comment_li = []
        for comm in comments:
            comm_dict = comm.to_dict()
            comm_dict['is_like'] = False
            comment_li.append(comm_dict)
        collec = False

    # 添加查询comment点赞
    is_follow = None
    if author:
        is_follow = False
        if user in author.followers:
            is_follow = True

    data = {
        'user_info': user.to_dict() if user else None,
        'news_hot_list': news_hot_list,
        'news': news.to_dict() if news else None,
        'collec': collec,
        'comment_li': comment_li,
        'author': author.to_dict() if author else None,
        'is_follow': is_follow

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


@news_blu.route('/news_comment', methods=['POST'])
@login_check
def news_comment():
    """
    json:news_id user_id content parant_id
    查询评论情况
    :return:json
    """
    user = g.user
    news_id = request.json.get('news_id')
    content_str = request.json.get('comment')
    parent_id = request.json.get('parent_id')
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='未登录')
    if not all([news_id, content_str]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = content_str
    if parent_id:
        comment.parent_id = parent_id
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存评论数据失败")
    return jsonify(errno=RET.OK, errmsg="评论成功", data=comment.to_dict())


@news_blu.route('/comment_like', methods=['POST'])
@login_check
def comment_like():
    """
    POST接收json
    参数：comment_id user_id action:点赞还是取消
    业务逻辑 实例化一个模型，添加数据进去
    :return: json ok
    """
    comment_id = request.json.get('comment_id')
    user = g.user
    action = request.json.get('action')
    if not all([comment_id, user, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    if not action in ('add', 'remove'):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论数据不存在")

    if action == 'add':
        comment_like = Comment.query.filter(CommentLike.comment_id == comment_id,
                                            CommentLike.user_id == user.id).first()
        if not comment_like:
            comment_like = CommentLike()
            comment_like.comment_id = comment_id
            comment_like.user_id = user.id
            db.session.add(comment_like)
            comment.like_count += 1
    if action == 'remove':
        comment_like = Comment.query.filter(CommentLike.comment_id == comment_id,
                                            CommentLike.user_id == user.id).first()
        if comment_like:
            db.session.delete(comment_like)
            comment.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库错误')
    return jsonify(errno=RET.OK, errmsg='Like成功')


@news_blu.route('/followed_user', methods=['POST', 'GET'])
@login_check
def followed_user():
    """关注/取消关注用户"""
    if not g.user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    user_id = request.json.get("user_id")
    action = request.json.get("action")

    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("follow", "unfollow"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询到关注的用户信息
    try:
        target_user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")

    if not target_user:
        return jsonify(errno=RET.NODATA, errmsg="未查询到用户数据")

    # 根据不同操作做不同逻辑
    if action == "follow":
        if target_user.followers.filter(User.id == g.user.id).count() > 0:
            return jsonify(errno=RET.DATAEXIST, errmsg="当前已关注")
        target_user.followers.append(g.user)
    else:
        if target_user.followers.filter(User.id == g.user.id).count() > 0:
            target_user.followers.remove(g.user)

    # 保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据保存错误")

    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_blu.route('/other')
@login_check
def other():
    user = g.user

    # 获取其他用户id
    user_id = request.args.get("id")
    if not user_id:
        abort(404)
    # 查询用户模型
    other = None
    try:
        other = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
    if not other:
        abort(404)

    # 判断当前登录用户是否关注过该用户
    is_followed = False
    if g.user:
        if other.followers.filter(User.id == user.id).count() > 0:
            is_followed = True

    # 组织数据，并返回
    data = {
        "user_info": user.to_dict(),
        "other_info": other.to_dict(),
        "is_followed": is_followed
    }
    return render_template('news/other.html', data=data)


@news_blu.route('/other_news_list')
def other_news_list():
    # 获取页数
    p = request.args.get("p", 1)
    user_id = request.args.get("user_id")
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if not all([p, user_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")

    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(p, constants.OTHER_NEWS_PAGE_MAX_COUNT, False)
        # 获取当前页数据
        news_li = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    news_dict_li = []

    for news_item in news_li:
        news_dict_li.append(news_item.to_review_dict())
    data = {"news_list": news_dict_li, "total_page": total_page, "current_page": current_page}
    return jsonify(errno=RET.OK, errmsg="OK", data=data)
