import functools

from flask import current_app, session, g

from info.models import User

from qiniu import Auth, put_data

access_key = 'NskHf9-OnAGrZjUK-HsIpnmcSeZ4FdNpk2eUngdE'
secret_key = 'AXh3b-_5tgiNcw0L7IZ3bNgVP1f1pu40THPl1wNW'
bucket_name = 'information'


def index_loop(data):
    if data == 0:
        data = 'first'
    if data == 1:
        data = 'second'
    if data == 2:
        data = 'third'
    return data


def login_check(f):
    @functools.wraps(f)
    def wapper(*args, **kwargs):
        try:
            user_id = session.get('user_id')
        except Exception as e:
            current_app.logger.error(e)
        user = None
        if user_id:
            user = User.query.get(user_id)
        g.user = user
        return f(*args, **kwargs)

    return wapper


def qiniuyun(data):
    if not data:
        return None
    try:
        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)
        ret, info = put_data(token, None, data)
    except Exception as e:
        current_app.logger.error(e)
        raise e
    if info and info.status_code != 200:
        raise Exception('上传文件到七牛云失败')
    return ret['key']
