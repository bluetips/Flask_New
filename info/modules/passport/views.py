from info.constants import IMAGE_CODE_REDIS_EXPIRES
from info.utils.captcha.captcha import captcha
from . import passport_blu
from flask import request, abort, current_app, make_response
from info import redis_store


@passport_blu.route('/image_code')
def get_img_code():
    """
    取得前台传入得参数，调动工具得生成图片，数字内容，存入redis，传到前台
    """
    img_code_uuid = request.args.get('code_id', None)
    if not img_code_uuid:
        return abort(403)

    name, text, image = captcha.generate_captcha()

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
