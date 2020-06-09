# coding: utf-8
import time
from ..model import Feedback
from ..const import (
    MAX_TIME
)
from flask import (
    request
)
from ..service import (
    GlobalizationService
)

class FeedbackService(object):

    @classmethod
    def feedback(cls, user_id, content, pics=[], phone=None):
        feedback = Feedback()
        feedback.uid = user_id
        feedback.content = content
        feedback.pics = pics
        feedback.phone = phone
        feedback.region = GlobalizationService.get_region()
        feedback.request_args = request.url.split('?')[1]
        feedback.create_ts = int(time.time())
        feedback.save()
        return {'feedback_id': str(feedback.id)}, True

    @classmethod
    def deal_feedback(cls, feedback_id):
        obj = Feedback.get_by_id(feedback_id)
        if obj:
            obj.dealed = True
            obj.save()
            return None, True
        return u'deal fail', False

    @classmethod
    def info_by_id(cls, feedback_id):
        feedback = Feedback.get_by_id(feedback_id)
        if not feedback:
            return u'worng id', False
        return feedback.to_json(), True

    @classmethod
    def feed_back_list(cls, start_ts=MAX_TIME, num=10):
        if start_ts < 0:
            return u'wrong start_ts', False
        next_start = -1
        feedbacks = Feedback.objects(create_ts__lte=start_ts, region=GlobalizationService.get_region(), dealed=False).order_by(
            '-create_ts').limit(num + 1)
        feedbacks = list(feedbacks)
        # feedbacks.reverse()   # 时间顺序错误
        has_next = False
        if len(feedbacks) == num + 1:
            has_next = True
            next_start = feedbacks[-1].create_ts
            feedbacks = feedbacks[:-1]
        feedbacks = [el.to_json() for el in feedbacks]
        return {
                   'feedbacks': feedbacks,
                   'has_next': has_next,
                   'next_start': next_start
               }, True