import random
from datetime import datetime
from . import passport_blu
from info.constants import IMAGE_CODE_REDIS_EXPIRES
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha

from flask import request, abort, current_app, make_response, jsonify, session
from info import redis_store, constants, db
from info.utils.response_code import RET


@passport_blu.route('/image_code')
def get_img_code():
    """
    取得前台传入得参数，调动工具得生成图片，数字内容，存入redis，传到前台
    """
    img_code_uuid = request.args.get('code_id', None)
    if not img_code_uuid:
        return abort(403)

    name, text, image = captcha.generate_captcha()
    print(text)

    # 与数据库有关的都要try
    try:
        redis_store.set('imgCodeUuid=' + img_code_uuid, text, ex=IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)

    # 设置返回响应
    response = make_response(image)
    response.headers["Content-Type:"] = 'image/jpg'
    return response


# URL：/passport/sms_code
@passport_blu.route('/sms_code', methods=['POST'])
def sms_code():
    """
    1.取得参数
    2.校验图片验证码
    3.生成随机短信验证码
    4.调用短信接口发送短信
    5.发送成功，将随机验证码保存到redis，给出发送成功响应
    :return:
    """
    param_dict = request.json
    mobile = param_dict.get('mobile')
    image_code = param_dict.get('image_code')
    image_code_id = param_dict.get('image_code_id')
    # 校验参数
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.DATAEXIST, errmsg='参数不全')
    try:
        real_image_code = redis_store.get('imgCodeUuid=' + image_code_id).decode()

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='Redis数九错误')
    if not real_image_code:
        return jsonify(RET.NODATA, errmsg='验证码已过期')
    if real_image_code != image_code:
        return jsonify(errno=RET.DBERR, errmsg='输入验证码错误')
    sms_code = random.randint(0, 999999)
    # result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], '1')

    print(sms_code)
    # if result != 0:
    #     current_app.logger.error('短信服务商错误')
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送短信失败')
    try:
        redis_store.set('SMS_CODE:' + mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='redis数据库错误')
    return jsonify(errno=RET.OK, errmsg='发送成功')


@passport_blu.route('/register', methods=['POST'])
def register():
    """取参数用户名 密码 短信验证码 校验是否齐全 校验验证码 存入用户信息数据库模型 信息保存 返回响应"""
    dict_param = request.json
    mobile = dict_param.get('mobile')
    pwd = dict_param.get('pwd')
    sms_code = dict_param.get('sms_code')
    if not all([mobile, pwd, sms_code]):
        current_app.logger.error('参数不齐全')
        return jsonify(errno=RET.PARAMERR, errmsg='参数不齐全')
    try:
        real_sms_code = redis_store.get('SMS_CODE:' + mobile).decode()
    except Exception as e:
        current_app.logger.error('Redis数据库错误')
        return jsonify(errno=RET.DBERR, errmsg='Redis数据库错误')
    if not real_sms_code:
        return jsonify(errno=RET.NODATA, errmsg='验证码过期')
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='验证码错误')
    try:
        redis_store.delete("SMS_" + mobile)
    except Exception as e:
        current_app.logger.error(e)

    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    user.password = pwd

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('mysql数据库错误')
        return jsonify(errno=RET.DBERR, errmsg='Mysql数据库错误')

    session['user_id'] = user.id
    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile

    return jsonify(errno=RET.OK, errmasg='注册成功')


# 登录页面实现
@passport_blu.route('/login', methods=['POST'])
def login():
    """
    获取参数：mobile pwd
    校验参数完整，
    是否存在mobile
    校验密码是否正确
    设置session，保持状态
    返回响应
    :return:
    """
    dict_param = request.json
    print(dict_param)
    mobile = dict_param.get('mobile')
    pwd = dict_param.get('pwd')
    if not all([mobile, pwd]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据错误")

    if not user:
        return jsonify(errno=RET.DATAEXIST, errmsg='用户不存在')

    result = user.check_passowrd(pwd)

    if not result:
        return jsonify(errno=RET.DBERR, errmsg='密码错误')

    session['user_id'] = user.id
    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile

    user.last_login = datetime.now()
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库写入错误 ')

    return jsonify(errno=RET.OK, errmsg='登录成功')


@passport_blu.route('/login_out')
def login_out():
    """删除session,flask中以及集成好了，不用获取sessionid"""
    session.pop('user_id', None)
    session.pop('nick_name', None)
    session.pop('mobile', None)

    return jsonify(errno=RET.OK, errmsg='登出成功')
