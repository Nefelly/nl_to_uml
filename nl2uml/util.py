# encoding=utf8
import base64
import datetime
import decimal
import functools
import hashlib
import logging
import os
import random
import re
import time
import urllib
import urlparse
import math
import codecs

from flask import request
from hendrix.conf import setting
from hendrix.util import get_hostname
from pyparsing import anyOpenTag, anyCloseTag

import json

logger = logging.getLogger(__name__)


class CachedProperty(object):
    """Decorator like python built-in ``property``, but it results only
    once call, set the result into decorated instance's ``__dict__`` as
    a static property.
    """

    def __init__(self, fn):
        self.fn = fn
        self.__doc__ = fn.__doc__

    def __get__(self, inst, cls):
        if inst is None:
            return self
        val = inst.__dict__[self.fn.__name__] = self.fn(inst)
        return val


cached_property = CachedProperty  # alias


class EnvvarReader(dict):
    __uninitialized = object()

    def __init__(self, *envvars):
        for ev in envvars:
            ev_norm = self._normalize(ev)
            if ev != ev_norm:
                raise ValueError('invalid envvar name: {!r}'.format(ev))
            dict.__setitem__(self, ev_norm, self.__uninitialized)

    @cached_property
    def configured(self):
        return any([self[k] for k in self])

    def _normalize(self, varname):
        return varname.strip()

    def __getitem__(self, key):
        key = self._normalize(key)
        value = dict.__getitem__(self, key)
        if value is self.__uninitialized:
            value = os.getenv(key, None)
            dict.__setitem__(self, key, value)
        return value

    __getattr__ = __getitem__

    def get(self, key, default=None):
        val = self.__getitem__(key)
        if val is not None:
            return val
        return default

    def get_int(self, key, default=None):
        value = self.__getitem__(key)
        if value is not None:
            return int(value)
        return default

    def get_float(self, key, default=None):
        value = self.__getitem__(key)
        if value is not None:
            return float(value)
        return default

    def get_bool(self, key, default=False):
        value = self.__getitem__(key)
        if value not in (None, 0):
            return True
        return default

    def get_json(self, key, default=None):
        value = self.__getitem__(key)
        if value is not None:
            return json.loads(value)
        default = default or {}
        return default

    def __setitem__(self, key, value):
        raise RuntimeError('setting envvar not supported')

    __setattr__ = __setitem__


class BaseDBManager(dict):
    @property
    def settings(self):
        raise NotImplementedError()

    def _initdb(self, name):
        raise NotImplementedError()

    def initdb(self, name):
        if not self.get(name):
            self._initdb(name)
        else:
            logger.warning('db: %r already inited', name)

    def initall(self):
        for db in self.settings:
            self.initdb(db)

    def __getitem__(self, key):
        if key not in self and key in self.settings:
            self.initdb(key)
        return super(BaseDBManager, self).__getitem__(key)

    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError:
            raise AttributeError(name)


class EnumItem(object):
    def __init__(self, name, value, display=u''):
        self.name = name
        self.value = value
        self.display = display

    def __str__(self):
        return self.display.encode('utf-8')

    def __repr__(self):
        if self.display:
            r = u'EnumItem({0.name}): <{0.value}, {0.display}>'.format(self)
        else:
            r = u'EnumItem({0.name}): <{0.value}>'.format(self)
        return r.encode('utf-8')


class Enum(object):
    def __init__(self, *items):
        self._items = {}
        values = []
        for i in items:
            display = ''
            if len(i) == 2:
                name, value = i
            elif len(i) == 3:
                name, value, display = i
            else:
                raise ValueError(i)
            if value in values:
                raise ValueError('duplicate value: {!r}'.format(value))
            values.append(value)
            i = EnumItem(name, value, display)
            self._items[name] = i

    def __repr__(self):
        return 'Enum: <{}>'.format(', '.join(self._items.keys()))

    def __getattr__(self, name):
        try:
            return self._items[name].value
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, key):
        return self._items[key].value

    def items(self):
        return self._items.values()

    def values(self):
        return set([i.value for i in self._items.values()])

    def get_by_value(self, val):
        for v in self.items():
            if v.value == val:
                return v
        raise ValueError('invalid value: {!r}'.format(val))


def memoize(f):
    _res_mapping = {}

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        key = args + tuple(sorted(kwargs.items()))
        try:
            return _res_mapping[key]
        except KeyError:
            _res_mapping[key] = value = f(*args, **kwargs)
            return value

    return wrapper


@memoize
def on_staging():
    """查看当前是否在Staging环境"""
    return True

@memoize
def in_container():
    return False
    # from hendrix.conf import setting
    # return setting.IN_CONTAINER


class ExpoBackoffDecorr(object):
    def __init__(self, base, cap):
        self.base = base
        self.cap = cap
        self.sleep = self.base

    def backoff(self, n):
        self.sleep = min(self.cap, random.uniform(self.base, self.sleep * 3))
        return self.sleep
