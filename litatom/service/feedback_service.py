# coding: utf-8
import time
from ..model import Feedback

class FeedbackService(object):

    @classmethod
    def feedback(cls, user_id, content, pics=[], phone=None):
        feedback = Feedback()
        feedback.uid = user_id
        feedback.content = content
        feedback.pics = pics
        feedback.phone = phone
        feedback.create_ts = int(time.time())
        feedback.save()
        return {'feedback_id': str(feedback.id)}, True

    @classmethod
    def info_by_id(cls, feedback_id):
        feedback = Feedback.get_by_id(feedback_id)
        if not feedback:
            return u'worng id', False
        return feedback.to_json(), True