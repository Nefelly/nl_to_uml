# coding: utf-8
from flask import Blueprint
from . import endpoint

__all__ = ['blueprint']

blueprint = b = Blueprint('api_v1', __name__)

b.add_url_rule('/nl2uml', 'nl2uml', endpoint.nl.nl2uml, methods=['POST'])
b.add_url_rule('/simple_nl2uml', 'simple_nl2uml', endpoint.nl.simple_nl2uml)
