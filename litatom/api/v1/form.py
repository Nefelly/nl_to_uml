# coding: utf-8
import logging

from flask import request
from wtforms import (
    BooleanField,
    FloatField,
    IntegerField,
    StringField,
    FieldList
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

class FeedCommentForm(LitatomForm):
    content = StringField(validators=[DataRequired()])
    comment_id = StringField(validators=[Optional()])

class ReportForm(LitatomForm):
    reason = StringField(validators=[DataRequired()])
    pics = FieldList(validators=[Optional()])
    target_user_id = StringField(validators=[Optional()])

class FeedbackForm(LitatomForm):
    content = StringField(validators=[DataRequired()])
    pics = FieldList(StringField(), default=[])

class TrackChatForm(LitatomForm):
    content = StringField(validators=[DataRequired()])
    target_user_id = StringField(validators=[DataRequired()])

class TrackActionForm(LitatomForm):
    action = StringField(validators=[DataRequired()])
    remark = StringField(validators=[Optional()])