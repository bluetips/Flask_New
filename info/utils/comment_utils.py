import functools

from flask import current_app, session, g

from info.models import User


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
