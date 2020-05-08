# coding: utf-8
from flask import Blueprint
from . import endpoint

__all__ = ['blueprint']

blueprint = b = Blueprint('api_home', __name__)

# lit
b.add_url_rule('/', 'lit-home', endpoint.home.index)
b.add_url_rule('/favicon.ico', 'lit-home-favicon', endpoint.home.favicon)
