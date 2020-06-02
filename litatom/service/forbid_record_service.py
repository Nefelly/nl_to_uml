# coding=utf-8
import json
import time

from ..const import (
    SYS_FORBID_TIME,
    OSS_AUDIO_URL,
    OSS_PIC_URL,
    FEED_NOT_FOUND_ERROR,
    SPAM_RECORD_UNKNOWN_SOURCE, ERROR_RANGE
)
from ..model import (
    Report,
    Feed,
    TrackSpamRecord,
    UserSetting,
    BlockedDevices,
    UserRecord, Blocked, User
)
from ..service import (
    UserService,
    GlobalizationService,
    ForbidCheckService,
    SpamWordCheckService
)
from ..util import (
    unix_ts_string, format_pic, format_standard_time, date_from_unix_ts
)


class ForbidRecordService(object):
    DEVICE_FORBID_THRESHOLD = 5

    @classmethod
    def mark_record(cls, user_id, from_ts=None, to_ts=None):
        TrackSpamRecordService.mark_spam_word(user_id, from_ts, to_ts)
        return ReportService.mark_report(user_id, from_ts, to_ts)

    @classmethod
    def record_sensitive_device(cls, user_id):
        user_setting = UserSetting.get_by_user_id(user_id)
        if not user_setting:
            return
        if not BlockedDevices.get_by_device(user_setting.uuid):
            BlockedDevices.add_sensitive_device(user_setting.uuid)

    @classmethod
    def get_device_forbidden_num_by_uid(cls, user_id):
        """根据 user_id，返回该设备上的各用户历史封号次数"""
        uuid = UserSetting.uuid_by_user_id(user_id)
        if not uuid:
            return 0
        uids = UserSetting.get_uids_by_uuid(uuid)

        def add(x, y):
            return x + y

        return reduce(add, map(UserRecord.get_forbidden_num_by_uid, uids))

    @classmethod
    def get_forbid_history_by_uid(cls, user_id):
        # 4个位置影响forbid_score，1.敏感用户 2.举报 3.警告 4.其他用户拉黑
        user_record = UserRecord.objects(user_id=user_id).order_by('-create_time').first()
        forbidden_from = user_record.create_time

        is_sensitive = ForbidCheckService.check_sensitive_user(user_id, forbidden_from - ERROR_RANGE)

        reports = Report.get_report_by_time_and_uid(user_id, forbidden_from - SYS_FORBID_TIME, forbidden_from,
                                                    True)
        # region = reports[0].region
        reports_res = []
        for report in reports:
            reports_res.append(ReportService.get_report_info(report))

        blocker_num = Blocked.get_blocker_num_by_time(user_id, forbidden_from - SYS_FORBID_TIME, forbidden_from)

        spam_records = TrackSpamRecord.get_records_by_uid_and_time(user_id, forbidden_from - SYS_FORBID_TIME,
                                                                   forbidden_from)
        record_res = []
        for record in spam_records:
            record_res.append(TrackSpamRecordService.get_spam_record_info(record))

        return {'sensitive': is_sensitive, 'blocker_num': blocker_num, 'illegal_records': reports_res + record_res}


class ReportService(object):

    @classmethod
    def save_report(cls, user_id, reason, pics=None, target_user_id=None, related_feed_id=None, match_type=None,
                    chat_record=None, dealed=False, forbid_weight=4):
        """举报内容入库"""
        report = Report()
        report.uid = user_id
        report.reason = reason
        report.pics = pics
        report.chat_record = chat_record
        report.related_feed = related_feed_id
        report.region = GlobalizationService.get_region()
        # if target_user_id.startswith('love'):
        #     target_user_id = UserService.uid_by_huanxin_id(target_user_id)
        if dealed:
            report.dealed = dealed
        report.target_uid = target_user_id
        report.create_ts = int(time.time())
        report.forbid_weight = forbid_weight
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
        if not report:
            return None
        target_uid = report.target_uid
        reportee = User.get_by_id(target_uid)
        tmp = {'report_id': str(report.id), 'forbid_weight': 2 if report.reason == 'match' else 4,
               'reporter': report.uid, 'pics': [OSS_PIC_URL + pic for pic in report.pics],
               'region': report.region, 'chat_record': None, 'reason': report.reason, 'feed': None,
               'user_id': target_uid, 'reporter_nickname': UserService.nickname_by_uid(report.uid),
               'reporter_ban_before': UserRecord.get_forbidden_num_by_uid(report.uid) > 0,
               'reportee_nickname': reportee.nickname if reportee else None,
               'reportee_create_time': format_standard_time(reportee.create_time) if reportee else None,
               'report_weight':report.forbid_weight}

        if report.related_feed:
            feed = Feed.objects(id=report.related_feed).first()
            if not feed:
                tmp['feed'] = FEED_NOT_FOUND_ERROR
            else:
                tmp['feed'] = {'content': feed.content, 'pics': [OSS_PIC_URL + pic for pic in feed.pics],
                               'audios': [OSS_AUDIO_URL + audio for audio in feed.audios]}

        if report.chat_record:
            res_record = []
            chat_records = json.loads(report.chat_record)
            for chat_record in chat_records:
                uid = UserService.uid_by_huanxin_id(chat_record['id'])
                res_record.append("%s: %s" % (UserService.nickname_by_uid(uid), chat_record['content']))
            tmp['chat_record'] = '\n'.join(res_record)
        return tmp

    @classmethod
    def info_by_id(cls, report_id):
        report = Report.get_by_id(report_id)
        if not report:
            return u'worng id', False
        return cls.get_report_info(report), True

    @classmethod
    def get_report_info_tmp(cls, report):
        res = {'reason': report.reason, 'report_id': str(report.id), 'user_id': report.uid, 'pics': report.pics,
               'region': report.region, 'deal_result': report.deal_res if report.deal_res else '',
               'target_user_id': '%s\n%s' % (
                   report.target_uid, UserService.nickname_by_uid(report.target_uid)) if report.target_uid else '',
               'create_time': format_standard_time(date_from_unix_ts(report.create_ts)),
               'reporter_ban_fefore': UserRecord.has_been_forbidden(report.uid)}

        if report.chat_record:
            res_record = []
            record = json.loads(report.chat_record)
            record = record[-20:]
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


class TrackSpamRecordService(object):

    @classmethod
    def save_record(cls, user_id, word=None, pic=None, forbid_weight=0, source=SPAM_RECORD_UNKNOWN_SOURCE):
        if not word and not pic:
            return False
        if cls.check_spam_word_in_one_minute(user_id, int(time.time())):
            return False
        return TrackSpamRecord.create(user_id, word, pic, forbid_weight=forbid_weight, source=source)

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
            objs = TrackSpamRecord.objects(user_id=user_id, create_time__lte=int(time.time()), dealed=False)
        for obj in objs:
            obj.dealed = True
            obj.save()

    @classmethod
    def get_review_pic(cls, num=10000):
        """按时间倒序，返回需要review的spam record, [{'pic':'','record_id':''},{'pic':'','record_id':''}]"""
        records = TrackSpamRecord.get_review_pic(num)
        res = []
        for record in records:
            temp = {'pic': format_pic(record.pic), 'record_id': str(record.id)}
            res.append(temp)
        return res

    @classmethod
    def get_spam_record_info(cls, record):
        tmp = {'forbid_weight': record.forbid_weight, 'user_id': record.user_id,
               'nickname': UserService.nickname_by_uid(record.user_id), 'record_id': str(record.id),
               'create_time': unix_ts_string(record.create_time), 'source': record.source}
        if record.word:
            tmp['word'] = {'word': record.word, 'hit_word': SpamWordCheckService.get_spam_word(record.word,
                                                                                               GlobalizationService.get_region_by_user_id(
                                                                                                   record.user_id))}
        elif record.pic:
            tmp['pic'] = format_pic(record.pic)
        return tmp
