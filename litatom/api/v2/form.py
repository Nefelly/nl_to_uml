# coding: utf-8
import logging

from flask import request
from wtforms import (
    BooleanField,
    FloatField,
    IntegerField,
    StringField,
    FieldList,
)
from marshmallow import (
    Schema,
    fields,
    validates,
    ValidationError,
    post_load,
    validate,
)
from wtforms.validators import (
    DataRequired,
    Optional,
    AnyOf,
    Regexp,
)

from hendrix.util import AttributeDict

from litatom.litatom.api.v1.form import (
    LitatomForm,
    PlatformField,
)

logger = logging.getLogger(__name__)



class NoteGoodsInfoMixin(object):
    @validates('name')
    def validate_name(self, value):
        if len(value) > 60:
            raise ValidationError('invalid name: %r' % value)

    @validates('price')
    def validate_price(self, value):
        if value <= 0 or value > 99999.99:
            raise ValidationError('invalid price: %r' % value)

    @validates('shipping_rate')
    def validate_shipping_rate(self, value):
        if value < 0 or value > 999.99:
            raise ValidationError('invalid shipping rate: %r' % value)

    @post_load
    def make_object(self, data):
        if not data:
            return
        return AttributeDict(data)


class PostBurnItemForm(LitatomForm):
    form_id = StringField(validators=[DataRequired()])
    item_key = StringField(validators=[DataRequired()])
    item_type = IntegerField(validators=[DataRequired(), AnyOf([1, 2])])
    item_width = IntegerField(validators=[Optional()], default=0)
    item_height = IntegerField(validators=[Optional()], default=0)

