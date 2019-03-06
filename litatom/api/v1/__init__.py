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
b.add_url_rule('/lit/user/verify_nickname', 'user-verify-nickname', endpoint.user.verify_nickname)
b.add_url_rule('/lit/user/info', 'user-update-info', endpoint.user.update_info, methods=['POST'])
b.add_url_rule('/lit/user/<target_user_id>', 'user-get-info', endpoint.user.get_user_info)

# 图片
b.add_url_rule('/lit/image/upload', 'image-upload', endpoint.image.upload_image_from_file, methods=['POST'])
b.add_url_rule('/lit/image/<fileid>', 'get-image', endpoint.image.get_image)

# huanxin
b.add_url_rule('/lit/huanxin/<target_user_id>', 'huanxin-get-info', endpoint.huanxin.get_user_info)

