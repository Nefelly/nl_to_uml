# coding: utf-8
from collections import namedtuple

from flask import request
from hendrix.context import g as hen_g
from hendrix.context import Context

_LitatomAPIContext = namedtuple('_LitatomAPIContext', ['client_host', 'req_id'])


def get_ctx():
    ctx = hen_g.get_current_ctx()
    if ctx is None:
        set_ctx()
        ctx = hen_g.get_current_ctx()
    return ctx


def set_ctx():
    ctx = Context(
        api_name=request.endpoint,
        api_ctx=_LitatomAPIContext(request.ip, request.id),
        api_args=tuple(request.values.lists()),
    )
    hen_g.set_ctx(ctx)


def clear_ctx():
    hen_g.remove_ctx()
