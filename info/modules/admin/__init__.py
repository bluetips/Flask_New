from flask import Blueprint, session, request, redirect, url_for

admin_blu = Blueprint('admin_blu', __name__)

from . import views


@admin_blu.before_request
def before_request():
    """
    后台的每次请求前验证是否管理员，还有如果登录了在login跳转到index
    :return:
    """
    is_admin = session.get('is_admin', None)
    if not is_admin and not request.url.endswith('login'):
        return redirect('/')
    if is_admin and request.url.endswith('login'):
        return redirect(url_for('admin_blu.admin_index'))
