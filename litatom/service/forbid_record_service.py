# coding=utf-8
import json
import time

from ..model import (
    Report,
    Feed,
    TrackSpamRecord,
    UserSetting,
    BlockedDevices,
    UserRecord
)
from ..service import (
    UserService,
    GlobalizationService
)
from ..util import (
    format_standard_time,
    date_from_unix_ts
)


class ForbidRecordService(object):
    @classmethod
    def mark_record(cls, user_id, from_ts=None, to_ts=None):
        TrackSpamRecordService.mark_spam_word(user_id, from_ts, to_ts)
        return ReportService.mark_report(user_id, from_ts, to_ts)

    @classmethod
    def record_sensitive_device(cls, user_id):
        user_setting = UserSetting.get_by_user_id(user_id)
        if not BlockedDevices.get_by_device(user_setting.uuid):
            BlockedDevices.add_sensitive_device(user_setting.uuid)


class ReportService(object):

    @classmethod
    def save_report(cls, user_id, reason, pics=None, target_user_id=None, related_feed_id=None, match_type=None,
                    chat_record=None, dealed=False):
        """举报内容入库"""
        report = Report()
        report.uid = user_id
        report.reason = reason
        report.pics = pics
        report.chat_record = chat_record
        report.related_feed = related_feed_id
        report.region = GlobalizationService.get_region()
        if target_user_id.startswith('love'):
            target_user_id = UserService.uid_by_huanxin_id(target_user_id)
        if dealed:
            report.dealed = dealed
        report.target_uid = target_user_id
        report.create_ts = int(time.time())
        report.save()
        return report.id

    @classmethod
    def mark_report(cls, user_id, from_time=None, to_time=None):
        """
        将一段时间举报user_id的记录标位‘已处理’，参数时间都是时间戳(int)
        :return: 一个集合，包含举报该user的举报者们
        """
        if from_time and to_time:
            objs = Report.objects(target_uid=user_id, create_ts__gte=from_time, create_ts__lte=to_time, dealed=False)
        else:
            objs = Report.objects(target_uid=user_id, create_ts__lte=int(time.time()), dealed=False)
        report_users = set()
        for obj in objs:
            obj.dealed = True
            report_users.add(obj.uid)
            obj.save()
        return report_users

    @classmethod
    def get_report_info(cls, report):
        res = {
            'reason': report.reason,
            'report_id': str(report.id),
            'user_id': report.uid,
            'pics': report.pics,
            'region': report.region,
            'deal_result': report.deal_res if report.deal_res else '',
            'target_user_id': '%s\n%s' % (
                report.target_uid, UserService.nickname_by_uid(report.target_uid)) if report.target_uid else '',
            'create_time': format_standard_time(date_from_unix_ts(report.create_ts))
        }

        res['reporter_ban_fefore'] = UserRecord.get_forbidden_times_user_id(report.uid) > 0
        if report.chat_record:
            res_record = []
            record = json.loads(report.chat_record)
            for el in record:
                uid = UserService.uid_by_huanxin_id(el['id'])
                # res_record.append({'content': el['content'], 'name': UserService.nickname_by_uid(uid)})
                res_record.append("%s: %s" % (UserService.nickname_by_uid(uid), el['content']))
            res['chat_record'] = '\n'.join(res_record)
        else:
            res['chat_record'] = ''
        res['pic_from_feed'] = False
        if report.related_feed:
            feed = Feed.get_by_id(report.related_feed)
            if feed:
                res['pic_from_feed'] = True
                res['content'] = feed.content if feed.content else ''
                if feed.audios:
                    res['audio_url'] = 'http://www.litatom.com/api/sns/v1/lit/mp3audio/%s' % feed.audios[0]
                else:
                    res['audio_url'] = ''
                res['pics'] = feed.pics
            else:
                res['content'] = ''
                res['audio_url'] = ''
        else:
            res['content'] = ''
            res['audio_url'] = ''
        return res

    @classmethod
    def info_by_id(cls, report_id):
        report = Report.get_by_id(report_id)
        if not report:
            return u'worng id', False
        return cls.get_report_info(report), True


class TrackSpamRecordService(object):

    @classmethod
    def save_record(cls, user_id, word=None, pic=None):
        if not word and not pic:
            return False
        if cls.check_spam_word_in_one_minute(user_id, int(time.time())):
            return False
        return TrackSpamRecord.create(user_id, word, pic)

    @classmethod
    def check_spam_word_in_one_minute(cls, user_id, ts):
        """检查两条spam_word之间的间隔是不是在1min之内，是的话不入库"""
        if TrackSpamRecord.count_by_time_and_uid(user_id, ts - 60, ts) > 0:
            return True
        return False

    @classmethod
    def mark_spam_word(cls, user_id, from_time=None, to_time=None):
        """将一段时间user_id的track_spam_record记录标位‘已处理’，参数时间都是时间戳(int)"""
        if from_time and to_time:
            objs = TrackSpamRecord.objects(user_id=user_id, create_time__gte=from_time, create_time__lte=to_time,
                                           dealed=False)
        else:
            objs = TrackSpamRecord.objects(user_id=user_id, create_time__lte=int(time.time()),dealed=False)
        for obj in objs:
            obj.dealed = True
            obj.save()
