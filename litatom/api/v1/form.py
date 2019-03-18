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

from ..form import (
    LitatomForm,
    PlatformField,
)
from ...const import (
    MAX_TIME
)

logger = logging.getLogger(__name__)

class SmsCodeForm(LitatomForm):
    zone = StringField(validators=[DataRequired()])
    phone = StringField(validators=[DataRequired()])

class PhoneLoginForm(LitatomForm):
    zone = StringField(validators=[DataRequired()])
    phone = StringField(validators=[DataRequired()])
    code = StringField(validators=[DataRequired()])

class PostBurnItemForm(LitatomForm):
    form_id = StringField(validators=[DataRequired()])
    item_key = StringField(validators=[DataRequired()])
    item_type = IntegerField(validators=[DataRequired(), AnyOf([1, 2])])
    item_width = IntegerField(validators=[Optional()], default=0)
    item_height = IntegerField(validators=[Optional()], default=0)

class FeedCommentForm(LitatomForm):
    content = StringField(validators=[DataRequired()])
    comment_id = StringField(validators=[Optional()])

class ReportForm(LitatomForm):
    reason = StringField(validators=[DataRequired()])
    pics = FieldList(StringField(validators=[Optional()]))
    target_user_id = StringField(validators=[Optional()])

class TrackChatForm(LitatomForm):
    content = StringField(validators=[DataRequired()])
    target_user_id = StringField(validators=[DataRequired()])