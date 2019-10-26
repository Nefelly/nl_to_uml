# coding: utf-8
import logging
import json

from flask import (
    jsonify,
    request,
    render_template,
    current_app
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
    APP_PATH
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

logger = logging.getLogger(__name__)

def index():
    return current_app.send_static_file('index.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}

