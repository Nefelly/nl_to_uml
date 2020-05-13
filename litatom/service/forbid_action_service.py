# coding: utf-8
import datetime
import time
from hendrix.conf import setting
import json
from math import floor
from ..service import (
    ForbidCheckService,
    ReportService,
    ForbidRecordService,
    TrackSpamRecordService,
    GlobalizationService,
    UserService,
    FirebaseService,
)
from ..redis import (
    RedisClient,
)
from ..model import (
    TrackSpamRecord,
    Report,
    UserModel,
    User,
    UserRecord,
    Blocked,
    AppAdmin, Feed
)
from ..util import (
    unix_ts_local,
)
from ..const import (
    ONE_DAY,
    SYS_FORBID,
    ADMINISTRATORS,
    MANUAL_FORBID, BLOCK_PIC,
)

redis_client = RedisClient()['lit']


class ForbidActionService(object):
    REPORT_WEIGHTING = 4
    SPAM_WORD_WEIGHTING = 2
    REVIEW_PIC_WEIGHTING = 0
    BLOCK_PIC_WEIGHTING = 4
    HISTORY_FORBID_WEIGHTING = 6
    BLOCKER_WEIGHTING = 1
    REVIEW_FEED_PIC_WEIGHTING = 2
    MATCH_REPORT_WEIGHTING = 2
    FORBID_THRESHOLD = 10
    DEFAULT_SYS_FORBID_TIME = 7 * ONE_DAY
    COMPENSATION_PER_TEN_FOLLOWER = 2
    COMPENSATION_UPPER_THRESHOLD = 10
    RELIABLE_REPORTER_COMPENSATION = 1
    SPAM_WORD_REASON = 'spam word existence'
    ADMINISTRATOR_REPORT = 'administrator report'

    @classmethod
    def _authenticate_reporter(cls, reporter, target_user_id, ts_now=int(time.time())):
        """一日内举报不可超过五次,三日内不可重复举报一人"""
        if AppAdmin.is_admin(reporter):
            cls.forbid_user(target_user_id, cls.DEFAULT_SYS_FORBID_TIME, MANUAL_FORBID)
            return False, {'report_id': cls.ADMINISTRATOR_REPORT, MANUAL_FORBID: True}, True
        if setting.IS_DEV:
            return True, None, None
        if Report.is_dup_report(reporter, target_user_id, ts_now):
            return False, 'You have reported the same person in last 3 days, please try later', False
        cnt = Report.count_report_by_uid(reporter, ts_now - ONE_DAY, ts_now)
        if cnt >= 5:
            return False, 'You have reported too many times today, please try later', False
        return True, None, None

    @classmethod
    def _is_reliable_reporter(cls, reporter):
        if User.get_by_id(reporter).days <= 10:
            return False
        if Report.count_by_uid(reporter) > 0:
            return False
        if TrackSpamRecord.count_by_uid(reporter) > 0:
            return False
        return True

    @classmethod
    def resolve_report(cls, user_id, reason, pics=[], target_user_id=None, related_feed_id=None, match_type=None,
                       chat_record=None):
        """举报接口服务函数"""
        if not target_user_id:
            return None, False
        if target_user_id.startswith('love'):
            target_user_id = UserService.uid_by_huanxin_id(target_user_id)
        if AppAdmin.is_admin(target_user_id):
            return u'this is our worker, you can trust her ^_^', False
        ts_now = int(time.time())
        go_ahead, msg, res = cls._authenticate_reporter(user_id, target_user_id, ts_now)
        if not go_ahead:
            return msg, res
        # 举报不过5次，均入库存档
        Report.set_same_report_to_dealed(user_id, target_user_id)
        report_id = ReportService.save_report(user_id, reason, pics, target_user_id, related_feed_id, match_type,
                                              chat_record)
        if ForbidCheckService.check_device_sensitive(target_user_id):
            cls.forbid_user(target_user_id, cls.DEFAULT_SYS_FORBID_TIME)
            return {"report_id": str(report_id), SYS_FORBID: True}, True
        if related_feed_id:
            cls._resolve_feed_report(related_feed_id, target_user_id, user_id)

        if chat_record:
            cls._resolve_chat_record_report(chat_record, target_user_id, user_id)

        if cls._is_reliable_reporter(user_id):
            reliable_reporter_compensation_score = 1
        else:
            reliable_reporter_compensation_score = 0
        res = cls._check_forbid(target_user_id, ts_now, -reliable_reporter_compensation_score)
        if res:
            cls.forbid_user(target_user_id, cls.DEFAULT_SYS_FORBID_TIME, SYS_FORBID, ts_now)
            return {"report_id": str(report_id), SYS_FORBID: True}, True
        return {"report_id": str(report_id), SYS_FORBID: False}, True

    @classmethod
    def _resolve_feed_report(cls, feed_id, target_user_id, user_id):
        """由于举报feed中，无论文字命中还是图片命中，只入库第一个"""
        word_res, pic_res = ForbidCheckService.check_feed(feed_id)
        if not word_res and not pic_res:
            return
        if word_res or pic_res:
            MsgService.feedback_to_reporters(target_user_id, [user_id], is_warn=True)
        if pic_res:
            for pic in pic_res:
                if pic_res[pic][1] == BLOCK_PIC:
                    TrackSpamRecordService.save_record(target_user_id, pic=pic, forbid_weight=cls.BLOCK_PIC_WEIGHTING)
                    MsgService.alert_feed_delete(target_user_id, pic_res[pic][0])
                    return

        if word_res:
            TrackSpamRecordService.save_record(target_user_id, word=word_res.keys()[0],
                                               forbid_weight=cls.SPAM_WORD_WEIGHTING)
            MsgService.alert_feed_delete(target_user_id, cls.SPAM_WORD_REASON)
            return
        Feed.change_to_review(feed_id)

    @classmethod
    def _resolve_chat_record_report(cls, chat_record, target_user_id, user_id):
        word_res, pic_res = ForbidCheckService.check_chat_record(chat_record)
        if not word_res and not pic_res:
            return
        if word_res or pic_res:
            MsgService.feedback_to_reporters(target_user_id, [user_id], is_warn=True)
        if pic_res:
            for pic in pic_res:
                if pic_res[pic][1] == BLOCK_PIC:
                    TrackSpamRecordService.save_record(target_user_id, pic=pic, forbid_weight=cls.BLOCK_PIC_WEIGHTING)
                    MsgService.alert_basic(target_user_id)
                    return
        if word_res:
            TrackSpamRecordService.save_record(target_user_id, word=word_res.keys()[0],forbid_weight=cls.SPAM_WORD_WEIGHTING)
            MsgService.alert_basic(target_user_id)
            return
        pic = pic_res.keys()[0]
        TrackSpamRecordService.save_record(target_user_id, pic=pic, forbid_weight=cls.REVIEW_PIC_WEIGHTING)
        MsgService.alert_basic(target_user_id)

    @classmethod
    def resolve_spam_word(cls, user_id, word):
        """已知spam word处理"""
        TrackSpamRecordService.save_record(user_id, word=word, forbid_weight=cls.BLOCK_PIC_WEIGHTING)
        return cls._basic_alert_resolution(user_id)

    @classmethod
    def resolve_review_feed(cls, feed_id):
        """对于需要review的Feed，人工审核确认其是黄图"""
        Feed.change_to_not_shown(feed_id)
        feed = Feed.get_by_id(feed_id)
        user_id = feed.user_id
        # 理论上不可能出现
        if not feed.pics:
            return None, False
        return cls.resolve_block_pic(user_id,feed.pics[0])

    @classmethod
    def resolve_block_pic(cls, user_id, pic):
        """已鉴定过的block图片处理接口服务函数"""
        TrackSpamRecordService.save_record(user_id, pic=pic, forbid_weight=cls.BLOCK_PIC_WEIGHTING)
        return cls._basic_alert_resolution(user_id)
        # MsgService.alert_basic(user_id)
        # if ForbidCheckService.check_device_sensitive(user_id):
        #     cls.forbid_user(user_id, cls.DEFAULT_SYS_FORBID_TIME)
        #     return u"definitely sexual picture and have forbidden user", True
        # res = cls._check_forbid(user_id)
        # if not res:
        #     return u"definitely sexual picture", True
        # cls.forbid_user(user_id, cls.DEFAULT_SYS_FORBID_TIME)
        # return u"definitely sexual picture and have forbidden user", True

    @classmethod
    def resolve_review_pic(cls, record_id):
        """对于疑似的图片记录，确认其违规，作出处理"""
        record = TrackSpamRecord.get_record_by_id(record_id)
        if record.pic and record.forbid_weight == cls.REVIEW_PIC_WEIGHTING:
            record.forbid_weight = cls.BLOCK_PIC_WEIGHTING
        user_id = record.user_id
        return cls._basic_alert_resolution(user_id)

    @classmethod
    def _basic_alert_resolution(cls, user_id):
        """内部警告处理检查方法"""
        print(1.1)
        MsgService.alert_basic(user_id)
        print(1.2)
        if ForbidCheckService.check_device_sensitive(user_id):
            print(1.3)
            cls.forbid_user(user_id, cls.DEFAULT_SYS_FORBID_TIME)
            return {SYS_FORBID: True}, True
        res = cls._check_forbid(user_id)
        if res:
            cls.forbid_user(user_id, cls.DEFAULT_SYS_FORBID_TIME)
            return {SYS_FORBID: True}, True
        return {SYS_FORBID: False}, True

    @classmethod
    def _check_forbid(cls, target_user_id, ts_now=None, additional_score=0):
        """进行封号检查，应该封号返回True，未达到封号阈值返回False"""
        ts_now = int(time.time()) if not ts_now else ts_now
        # 官方账号不会被检查封号
        credit, res = cls.accum_illegal_credit(target_user_id, ts_now, additional_score)
        if not res or UserService.is_official_account(target_user_id):
            return False
        # 违规积分达到上限，非高价值用户，要被封号
        return True

    @classmethod
    def accum_illegal_credit(cls, user_id, timestamp_now=None, additional_score=0):
        """计算违规积分，查看user_id是否应该被封号"""
        if not timestamp_now:
            time_now = datetime.datetime.now()
            timestamp_now = unix_ts_local(time_now)
            time_3days_ago = unix_ts_local(time_now - datetime.timedelta(days=3))
        else:
            time_3days_ago = timestamp_now - 3 * ONE_DAY

        alert_score = TrackSpamRecord.get_alert_score_by_time_and_uid(user_id, time_3days_ago, timestamp_now)
        report_total_num = Report.count_by_time_and_uid_distinct(user_id, time_3days_ago, timestamp_now)
        report_match_num = Report.count_match_by_time_and_uid(user_id, time_3days_ago, timestamp_now)
        blocker_num = Blocked.get_blocker_num(user_id)
        history_forbidden_credit = 0
        if UserRecord.has_been_forbidden(user_id):
            history_forbidden_credit = cls.HISTORY_FORBID_WEIGHTING

        illegal_credit = alert_score + (report_total_num - report_match_num) * cls.REPORT_WEIGHTING \
                         + report_match_num * cls.MATCH_REPORT_WEIGHTING + additional_score + history_forbidden_credit \
                         + blocker_num * cls.BLOCKER_WEIGHTING - cls._get_high_value_compensation(user_id)
        if illegal_credit >= cls.FORBID_THRESHOLD:
            return illegal_credit, True
        if illegal_credit < 0:
            return 0, False
        return illegal_credit, False

    @classmethod
    def forbid_user(cls, user_id, forbid_ts, forbid_type=SYS_FORBID, ts=int(time.time())):
        """封号服务统一接口"""
        print(1.4)
        if not UserService.is_forbbiden(user_id):
            UserService.forbid_action(user_id, forbid_ts)
            UserRecord.add_forbidden(user_id, forbid_type)
        reporters = ForbidRecordService.mark_record(user_id)
        MsgService.feedback_to_reporters(user_id, reporters)
        if not ForbidCheckService.check_device_sensitive(user_id):
            ForbidRecordService.record_sensitive_device(user_id)
        return True

    @classmethod
    def _get_high_value_compensation(cls, user_id):
        """根据用户粉丝数量，获得一些补偿违规积分，避免高价值用户被举报封号"""
        followers = UserService.get_followers_by_uid(user_id)
        res = floor(followers / 10) * cls.COMPENSATION_PER_TEN_FOLLOWER
        res = res if res >= 0 else 0
        return res if res <= cls.COMPENSATION_UPPER_THRESHOLD else cls.COMPENSATION_UPPER_THRESHOLD


class MsgService(object):
    WARN_FEEDBACK_WORDS = 'other_warn_inform'
    BAN_FEEDBACK_WORDS = 'other_ban_inform'
    FIREBASE_FEEDBACK_WORDS = u'your report succeed'
    DEFAULT_ALERT_WORDS = 'alert_word'
    FEED_DELETE_ALERT_WORDS = u'Your post have been deleted due to reason: %s. Please keep your feed positive.'

    @classmethod
    def alert_atom(cls, user_id, msg):
        UserService.msg_to_user(msg, user_id)
        UserModel.add_alert_num(user_id)

    @classmethod
    def alert_basic(cls, user_id):
        cls.alert_atom(user_id, GlobalizationService.get_region_word(cls.DEFAULT_ALERT_WORDS))

    @classmethod
    def alert_feed_delete(cls, user_id, reason):
        cls.alert_atom(user_id, cls.FEED_DELETE_ALERT_WORDS % reason)

    @classmethod
    def feedback_to_reporters(cls, reported_uid, report_user_ids, is_warn=False):
        target_user_nickname = UserService.nickname_by_uid(reported_uid)
        if is_warn:
            to_user_info = GlobalizationService.get_region_word(cls.WARN_FEEDBACK_WORDS) % (
                target_user_nickname, target_user_nickname)
        else:
            to_user_info = GlobalizationService.get_region_word(cls.BAN_FEEDBACK_WORDS) % (
                target_user_nickname, target_user_nickname)
        for reporter in report_user_ids:
            UserService.msg_to_user(to_user_info, reporter)
            FirebaseService.send_to_user(reporter, cls.FIREBASE_FEEDBACK_WORDS, to_user_info)
