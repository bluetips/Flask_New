from flask import render_template, g, request, redirect, url_for, current_app, jsonify

from info import db, constants
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


@user_blu.route('/pass_info')
@login_check
def pass_info():
    """
    get 常规渲染
    post 密码
    :return:
    """
    if not g.user:
        return redirect('/')
    data = {
        'user_info': g.user.to_dict()
    }
    return render_template('news/user_pass_info.html')
