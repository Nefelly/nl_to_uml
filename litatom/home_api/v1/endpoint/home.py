# coding: utf-8
import logging
import json

from flask import (
    jsonify,
    request,
    render_template,
    current_app,
    Flask
)
from ....model import (
    Wording,
    UserAddressList
)
from ..form import (
    ReportForm,
    TrackChatForm,
    TrackActionForm,
    FeedbackForm
)
from ...decorator import (
    session_required,
    session_finished_required
)

from ....response import (
    fail,
    success
)
from ....const import (
    BACKUP_DNS
)
from ....service import (
    StatisticService,
    ReportService,
    TrackActionService,
    FeedbackService,
    GlobalizationService,
    UserFilterService,
    FeedService,
    UserSettingService
)


def index():
    send_file = 'index_back.html'if BACKUP_DNS in request.url else 'index.html'
    return current_app.send_static_file(send_file), 200, {'Content-Type': 'text/html; charset=utf-8'}


def favicon():
    return current_app.send_static_file('icon.png')

