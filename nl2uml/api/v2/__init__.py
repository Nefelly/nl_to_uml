# coding: utf-8
from flask import Blueprint
from . import endpoint

__all__ = ['blueprint']

blueprint = b = Blueprint('api_v2', __name__)

# lit
b.add_url_rule('/lit/test', 'lit-test', endpoint.test.test)
