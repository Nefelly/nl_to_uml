# coding: utf-8
import datetime
import time
from hendrix.conf import setting
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
    date_from_unix_ts,
)
from ..const import (
    ONE_DAY,
    SYS_FORBID,
    MANUAL_FORBID,
    BLOCK_PIC,
    SYS_FORBID_TIME,
    SPAM_RECORD_UNKNOWN_SOURCE,
    SPAM_RECORD_FEED_SOURCE,
    SPAM_RECORD_CHAT_RECORD_SOURCE
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
    COMPENSATION_PER_TEN_FOLLOWER = 2
    COMPENSATION_UPPER_THRESHOLD = 10
    RELIABLE_REPORTER_COMPENSATION = 1
    NEW_BLOCKER_DAYS = 7
    SPAM_WORD_REASON = 'spam word existence'
    ADMINISTRATOR_REPORT = 'administrator report'

    @classmethod
    def _authenticate_reporter(cls, reporter, target_user_id, ts_now=int(time.time())):
        """一日内举报不可超过五次,三日内不可重复举报一人"""
        if AppAdmin.is_admin(reporter):
            cls.forbid_user(target_user_id, SYS_FORBID_TIME, MANUAL_FORBID)
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
        alert_res = False
        print(alert_res)
        # feed, chat record不会同时在一条举报中
        if related_feed_id:
            alert_res = cls._resolve_feed_report(related_feed_id, target_user_id, user_id)
        print(alert_res)
        if chat_record:
            alert_res = cls._resolve_chat_record_report(chat_record, target_user_id, user_id)
        print(alert_res)
        if cls._is_reliable_reporter(user_id):
            reliable_reporter_compensation_score = 1
        else:
            reliable_reporter_compensation_score = 0
        res = cls._check_forbid(target_user_id, ts_now, -reliable_reporter_compensation_score)
        if res:
            cls.forbid_user(target_user_id, SYS_FORBID_TIME, SYS_FORBID, ts_now)
            return {"report_id": str(report_id), SYS_FORBID: True}, True
        if not alert_res:
            MsgService.feedback_to_reporters_unresolved(user_id)
        return {"report_id": str(report_id), SYS_FORBID: False}, True

    @classmethod
    def _resolve_feed_report(cls, feed_id, target_user_id, user_id):
        """由于举报feed中，无论文字命中还是图片命中，只入库第一个"""
        word_res, pic_res = ForbidCheckService.check_feed(feed_id)
        if not word_res and not pic_res:
            return False
        if word_res or pic_res:
            MsgService.feedback_to_reporters(target_user_id, [user_id], is_warn=True)
        if pic_res:
            for pic in pic_res:
                if pic_res[pic][1] == BLOCK_PIC:
                    TrackSpamRecordService.save_record(target_user_id, pic=pic, forbid_weight=cls.BLOCK_PIC_WEIGHTING,source=SPAM_RECORD_FEED_SOURCE)
                    MsgService.alert_feed_delete(target_user_id, pic_res[pic][0])
                    return True

        if word_res:
            TrackSpamRecordService.save_record(target_user_id, word=word_res.keys()[0],
                                               forbid_weight=cls.SPAM_WORD_WEIGHTING, source=SPAM_RECORD_FEED_SOURCE)
            MsgService.alert_feed_delete(target_user_id, cls.SPAM_WORD_REASON)
            return True
        # 只有疑似图片
        Feed.change_to_review(feed_id)
        return False

    @classmethod
    def _resolve_chat_record_report(cls, chat_record, target_user_id, user_id):
        word_res, pic_res = ForbidCheckService.check_chat_record(chat_record)
        if not word_res and not pic_res:
            return False
        if word_res or pic_res:
            MsgService.feedback_to_reporters(target_user_id, [user_id], is_warn=True)
        if pic_res:
            for pic in pic_res:
                if pic_res[pic][1] == BLOCK_PIC:
                    TrackSpamRecordService.save_record(target_user_id, pic=pic, forbid_weight=cls.BLOCK_PIC_WEIGHTING, source=SPAM_RECORD_CHAT_RECORD_SOURCE)
                    MsgService.alert_basic(target_user_id)
                    return True
        if word_res:
            TrackSpamRecordService.save_record(target_user_id, word=word_res.keys()[0],
                                               forbid_weight=cls.SPAM_WORD_WEIGHTING,source=SPAM_RECORD_CHAT_RECORD_SOURCE)
            MsgService.alert_basic(target_user_id)
            return True
        pic = pic_res.keys()[0]
        TrackSpamRecordService.save_record(target_user_id, pic=pic, forbid_weight=cls.REVIEW_PIC_WEIGHTING,source=SPAM_RECORD_CHAT_RECORD_SOURCE)
        # MsgService.alert_basic(target_user_id)
        return False

    @classmethod
    def resolve_spam_word(cls, user_id, word, source=SPAM_RECORD_UNKNOWN_SOURCE):
        """已知spam word处理"""
        TrackSpamRecordService.save_record(user_id, word=word, forbid_weight=cls.SPAM_WORD_WEIGHTING, source=source)
        return cls._basic_alert_resolution(user_id)

    @classmethod
    def resolve_review_pic(cls, record_id, res):
        """对于需要review的track spam record，人工审核结果处理"""
        record = TrackSpamRecord.get_record_by_id(record_id)
        if not record:
            return None, False
        if not res:
            record.delete()
            return 'record deleted', True
        record.forbid_weight = cls.BLOCK_PIC_WEIGHTING
        record.save()
        return cls._basic_alert_resolution(record.user_id)

    @classmethod
    def resolve_review_feed(cls, feed_id, res):
        """对于需要review的Feed，人工审核结果处理"""
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return None, False
        if not res:
            feed.change_to_normal()
            return 'normal feed', True
        feed.change_to_not_shown()
        user_id = feed.user_id
        # 理论上不可能出现
        if not feed.pics:
            return None, False
        return cls.resolve_block_pic(user_id, feed.pics[0],source=SPAM_RECORD_FEED_SOURCE)

    @classmethod
    def resolve_block_pic(cls, user_id, pic, source=SPAM_RECORD_UNKNOWN_SOURCE):
        """已鉴定过的block图片处理接口服务函数"""
        TrackSpamRecordService.save_record(user_id, pic=pic, forbid_weight=cls.BLOCK_PIC_WEIGHTING, source=source)
        return cls._basic_alert_resolution(user_id)

    @classmethod
    def _basic_alert_resolution(cls, user_id):
        """内部警告处理检查方法"""
        MsgService.alert_basic(user_id)
        res = cls._check_forbid(user_id)
        if res:
            cls.forbid_user(user_id, SYS_FORBID_TIME)
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
            time_now = date_from_unix_ts(timestamp_now)
            time_3days_ago = timestamp_now - 3 * ONE_DAY

        alert_score = TrackSpamRecord.get_alert_score_by_time_and_uid(user_id, time_3days_ago, timestamp_now)
        report_total_num = Report.count_by_time_and_uid_distinct(user_id, time_3days_ago, timestamp_now)
        report_match_num = Report.count_match_by_time_and_uid(user_id, time_3days_ago, timestamp_now)
        blocker_num = Blocked.get_blocker_num_by_time(user_id, time_now - datetime.timedelta(days=cls.NEW_BLOCKER_DAYS),
                                                      time_now)
        history_forbidden_credit = 0
        if ForbidCheckService.check_sensitive_user(user_id):
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
        if not UserService.is_forbbiden(user_id):
            UserService.forbid_action(user_id, forbid_ts)
            UserRecord.add_forbidden(user_id, forbid_type)
        reporters = ForbidRecordService.mark_record(user_id)
        MsgService.feedback_to_reporters(user_id, reporters)
        if not ForbidCheckService.check_sensitive_device(user_id):
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
    REPORT_FEEDBACK_UNRESOLVED = 'report_feedback_unresolved'
    FEED_DELETE_ALERT_WORDS = u'Your post have been deleted due to reason: %s. Please keep your feed positive.'

    @classmethod
    def alert_atom(cls, user_id, msg):
        UserService.msg_to_user(msg, user_id)
        UserModel.add_alert_num(user_id)

    @classmethod
    def alert_basic(cls, user_id):
        # cls.alert_atom(user_id, GlobalizationService.get_region_word(cls.DEFAULT_ALERT_WORDS))
        cls.alert_atom(user_id, GlobalizationService.get_cached_region_word(cls.DEFAULT_ALERT_WORDS))

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

    @classmethod
    def feedback_to_reporters_unresolved(cls, reporter):
        to_reporter_info = GlobalizationService.get_region_word(cls.REPORT_FEEDBACK_UNRESOLVED)
        UserService.msg_to_user(to_reporter_info, reporter)

