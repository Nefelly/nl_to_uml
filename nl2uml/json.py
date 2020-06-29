from __future__ import absolute_import

import json as std_json

__all__ = [
    'dumps',
    'loads',
    'dump',
    'load',
]


def dumps(obj, **kwargs):
    kwargs.setdefault('ensure_ascii', True)
    kwargs.setdefault('indent')
    kwargs.setdefault('separators', (',', ':'))
    return std_json.dumps(obj, **kwargs)

loads = std_json.loads
dump = std_json.dump
load = std_json.load
