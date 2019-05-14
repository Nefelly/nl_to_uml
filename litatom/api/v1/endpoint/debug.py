import logging

from flask import (
    jsonify,
    request
)

from hendrix.conf import setting
from ...decorator import (
    session_required,
    session_finished_required
)

from ....response import (
    fail,
    success
)
from ....service import (
    DebugHelperService,
    AnoyMatchService,
    GlobalizationService
)

logger = logging.getLogger(__name__)



def redis_status():
    if not setting.IS_DEV:
        return success()
    key = request.args.get('key')
    return success(AnoyMatchService.debug_all_keys(key))

def batch_create_login():
    return success(DebugHelperService.batch_create_login())

def batch_anoy_match_start():
    return success(DebugHelperService.batch_anoy_match_start())

@session_required
def query_region():
    return success({"region": GlobalizationService.get_region()})