from flask import render_template, request, current_app, session, redirect, url_for, g

from info import login_check
from info.models import User
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

        if not all([name,pwd]):
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
    return render_template('admin/index.html')
