# coding: utf-8
import logging
from flask import (
    Response,
    request,
    json,
)

logger = logging.getLogger(__name__)


class LitatomResponse(Response):
    default_mimetype = 'text/plain'

    def __init__(self, response=None, *args, **kwargs):
        if isinstance(response, dict):
            response = json.dumps(response)
            kwargs['mimetype'] = 'application/json'
        super(LitatomResponse, self).__init__(response, *args, **kwargs)

    @property
    def json(self):
        try:
            data = self.get_data(as_text=True)
            if data:
                return json.loads(data)
        except Exception:
            pass

    @property
    def success(self):
        if self.json is not None:
            if 'result' in self.json:
                return self.json['result'] == 0
            elif 'success' in self.json:
                return self.json['success']
        if str(self.status_code).startswith('2'):
            return not request.form_errors
        return False


def success(data=None, **kwargs):
    res = {'result': 0, 'success': True}
    if data is not None:
        res['data'] = data
    if kwargs:
        for k, v in kwargs.items():
            res[k] = v
    return LitatomResponse(res)


def failure(err=None):
    from .api.error import Failed
    err = err or Failed
    try:
        if 'result' not in err or err['result'] == 0:
            logger.error('invalid error response: %r', err)
    except Exception:
        logger.exception('invalid error response: %r', err)
        err = Failed
    return LitatomResponse(err)


def fail(msg=None, **kwargs):
    res = {'result': -1, 'success': False}
    if msg:
        if isinstance(res, dict) and 'result' in res:
            return LitatomResponse(msg)
        res['message'] = msg
    if kwargs:
        for k, v in kwargs.items():
            res[k] = v
    return LitatomResponse(res)


def no_content():
    return '', 204


def forbidden():
    return '', 403


def guest_forbidden():
    return '', 460
