import random

from info.constants import IMAGE_CODE_REDIS_EXPIRES
from info.libs.yuntongxun.sms import CCP
from info.utils.captcha.captcha import captcha
from . import passport_blu
from flask import request, abort, current_app, make_response, jsonify
from info import redis_store, constants
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
    print(param_dict)
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
    result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], '1')
    if result != 0:
        current_app.logger.error('短信服务商错误')
        return jsonify(errno=RET.THIRDERR, errmsg='发送短信失败')
    try:
        redis_store.set('SMS_CODE:' + mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='redis数据库错误')
    return jsonify(errno=RET.OK, errmsg='发送成功')
