# coding: utf-8
from flask import Blueprint
from . import endpoint

__all__ = ['blueprint']

blueprint = b = Blueprint('api_v1', __name__)

# lit
b.add_url_rule('/lit/test', 'lit-test', endpoint.test.test)

# 验证码
b.add_url_rule('/lit/get_sms_code', 'get-sms-code', endpoint.sms_code.get_sms_code, methods=['POST'])

# user
b.add_url_rule('/lit/user/phone_login', 'user-phone-login', endpoint.user.phone_login, methods=['POST'])
b.add_url_rule('/lit/image/upload', 'image-upload', endpoint.image.upload_image_from_file, methods=['POST'])
b.add_url_rule('/lit/image/<fileid>', 'get-image', endpoint.image.get_image)
# b.add_url_rule('/wx_mp/activity/emoji_2019/user_info', 'wx-mp-emoji-2019-get-user-info', endpoint.wx_mp_emoji_2019.get_user_info)
# b.add_url_rule('/wx_mp/activity/emoji_2019/user_info', 'wx-mp-emoji-2019-update-user-info', endpoint.wx_mp_emoji_2019.update_user_info, methods=['POST'])
