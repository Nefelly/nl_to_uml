import logging

from flask import (
    jsonify,
    request
)

from ...decorator import (
    admin_session_required
)

from ...error import (
    Success,
    FailedLackOfField
)
from ....response import (
    failure,
    fail,
    success
)
from ..form import (
    PhoneLoginForm
)
from ....service import (
    AdminService,
    UserMessageService,
    FirebaseService
)
from  ....const import (
    MAX_TIME
)
logger = logging.getLogger(__name__)
# handler = logging.FileHandler("/data/log/litatom.log")
# logger.addHandler(handler)

def login():
    data = request.json
    user_name = data.get('username', '')
    pwd = data.get('password', '')
    data, status = AdminService.login(user_name, pwd)
    if not status:
        return fail(data)
    return success(data)

@admin_session_required
def hello():
    return jsonify('hello')
