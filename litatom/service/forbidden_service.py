# coding: utf-8
import datetime
import time
import json
from math import floor
from ..redis import (
    RedisClient,
)
from ..service import (
    GlobalizationService,
    UserService,
    FirebaseService,
)
from ..model import (
    SpamWord,
    TrackSpamRecord,
    Report,
    UserModel,
    Feed,
    UserRecord,
)
from ..util import (
    unix_ts_local,
    format_standard_time,
    date_from_unix_ts,
)
from ..const import (
    ONE_DAY,
    SYS_FORBID,
    MANUAL_FORBID,
)

redis_client = RedisClient()['lit']


class ForbiddenService(object):
    REPORT_WEIGHTING = 4
    ALERT_WEIGHTING = 2
    MATCH_REPORT_WEIGHTING = 4
    FORBID_THRESHOLD = 10
    DEFAULT_SYS_FORBID_TIME = 3 * ONE_DAY
    COMPENSATION_PER_TEN_FOLLOWER = 2

    @classmethod
    def check_spam_word(cls, word, user_id):
        if not SpamWordService.is_spam_word(word, GlobalizationService.get_region()):
            return None, False
        dealed_tag = cls.check_spam_word_in_one_minute(user_id, int(time.time()))
        TrackSpamRecord.create(user_id, word=word, dealed_tag=dealed_tag)
        cls.alert_to_user(user_id)
        res = cls.check_forbid(user_id)
        if not res:
            return GlobalizationService.get_region_word('alert_msg'), True
        return GlobalizationService.get_region_word('alert_msg'), True

    @classmethod
    def report_illegal_pic(cls, user_id, pic, reason):
        """feed 中黄色图片处理接口服务函数"""
        TrackSpamRecord.create(user_id, pic=pic)
        cls.alert_to_user(user_id,
                          msg=u'Your post have been deleted due to reason: %s. Please keep your feed positive.' % reason)
        res = cls.check_forbid(user_id)
        if not res:
            return u"spam words", True
        return u"spam words and forbidden", True

    @classmethod
    def resolve_report(cls, user_id, reason, pics=[], target_user_id=None, related_feed_id=None, match_type=None,
                       chat_record=None):
        """用户举报接口服务函数"""
        if not target_user_id:
            return None, False
        # 一日内举报不可超过五次
        ts_now = int(time.time())
        cnt = Report.count_report_by_uid(target_user_id, ts_now - ONE_DAY, ts_now)
        if cnt >= 5:
            return 'You have report too many times today, please try later', False
        # 举报不过5次，均入库存档
        report_id = ReportService.save_report(user_id, reason, pics, target_user_id, related_feed_id, match_type,
                                              chat_record)
        res = cls.check_forbid(target_user_id, ts_now)
        if res:
            return {"report_id": str(report_id), SYS_FORBID: True}, True
        return {"report_id": str(report_id), SYS_FORBID: False}, True

    @classmethod
    def report_spam(cls, user_id, word):
        """客户端举报接口服务函数"""
        TrackSpamRecord.create(user_id, word)
        cls.alert_to_user(user_id)
        res = cls.check_forbid(user_id)
        if res:
            return {SYS_FORBID: True}, True
        return {SYS_FORBID: False}, True

    @classmethod
    def check_forbid(cls, target_user_id, ts_now=None):
        """进行封号检查，封号返回Ture，未封号返回False"""
        ts_now = int(time.time()) if not ts_now else ts_now
        # 官方账号不会被检查封号
        if not cls.accum_illegal_credit(target_user_id, ts_now) or UserService.is_official_account(target_user_id):
            return False
        # 违规积分达到上限，非高价值用户，要被封号
        cls.forbid_user(target_user_id, cls.DEFAULT_SYS_FORBID_TIME, SYS_FORBID, ts_now)
        return True

    @classmethod
    def accum_illegal_credit(cls, user_id, timestamp_now=None):
        """计算违规积分，查看user_id是否应该被封号"""
        if not timestamp_now:
            time_now = datetime.datetime.now()
            timestamp_now = unix_ts_local(time_now)
            time_3days_ago = unix_ts_local(time_now - datetime.timedelta(days=3))
        else:
            time_3days_ago = timestamp_now - 3 * ONE_DAY

        alert_num = TrackSpamRecord.count_by_time_and_uid(user_id, time_3days_ago, timestamp_now)
        report_total_num = Report.count_by_time_and_uid_distinct(user_id, time_3days_ago, timestamp_now)
        report_match_num = Report.count_match_by_time_and_uid(user_id, time_3days_ago, timestamp_now)
        illegal_credit = alert_num * cls.ALERT_WEIGHTING + (report_total_num - report_match_num) * cls.REPORT_WEIGHTING \
                         + report_match_num * cls.MATCH_REPORT_WEIGHTING - cls.get_high_value_compensation(user_id)
        if illegal_credit >= cls.FORBID_THRESHOLD:
            return True
        return False

    @classmethod
    def forbid_user(cls, user_id, forbid_ts, forbid_type=SYS_FORBID, ts=int(time.time())):
        """封号服务统一接口"""
        if UserService.is_forbbiden(user_id):
            return
        UserService.forbid_action(user_id, forbid_ts)
        UserRecord.add_forbidden(user_id, forbid_type)
        reporters = ReportService.mark_report(user_id, ts - 3 * ONE_DAY, ts)
        SpamWordService.mark_spam_word(user_id, ts - 3 * ONE_DAY, ts)
        # 封号消息返回给举报者们
        cls.feedback_to_reporters(user_id, reporters)

    @classmethod
    def check_spam_word_in_one_minute(cls, user_id, ts):
        """检查两条spam_word之间的间隔是不是在1min之内，是的话不计入封号积分制度"""
        if TrackSpamRecord.count_by_time_and_uid(user_id, ts - 60, ts) > 0:
            return True
        return False

    @classmethod
    def get_high_value_compensation(cls, user_id):
        """根据用户粉丝数量，获得一些补偿违规积分，避免高价值用户被举报封号"""
        followers = UserService.get_followers_by_uid(user_id)
        res = floor(followers / 10) * cls.COMPENSATION_PER_TEN_FOLLOWER
        return res if res >= 0 else 0

    @classmethod
    def is_high_value_user(cls, user_id):
        return UserService.get_followers_by_uid(user_id) >= 20

    @classmethod
    def alert_to_user(cls, user_id, msg=None, alert_type=None):
        msg = GlobalizationService.get_region_word('alert_word') if not msg else msg
        UserService.msg_to_user(msg, user_id)
        UserModel.add_alert_num(user_id)

    @classmethod
    def feedback_to_reporters(cls, reported_uid, report_user_ids):
        target_user_nickname = UserService.nickname_by_uid(reported_uid)
        to_user_info = u"Your report on the user %s  has been settled. %s's account is disabled. Thank you for your support of the Lit community." \
                       % (target_user_nickname, target_user_nickname)
        for _ in report_user_ids:
            UserService.msg_to_user(to_user_info, _)
            FirebaseService.send_to_user(_, u'your report succeed', to_user_info)


class SpamWordService(object):
    KEYWORD_CHAINS = {}
    DEFAULT_KEYWORD_CHAIN = {}
    DELIMIT = '\x00'
    NOT_REGION = False

    @classmethod
    def add(cls, keyword, region=None):
        """以字典嵌套格式，将keyword的每个字母存入KEYWORD_CHAINS"""
        keyword = keyword.lower()
        chars = keyword.strip()
        if not chars:
            return
        if cls.NOT_REGION:
            level = cls.DEFAULT_KEYWORD_CHAIN
        else:
            if not cls.KEYWORD_CHAINS.get(region):
                cls.KEYWORD_CHAINS[region] = {}
            level = cls.KEYWORD_CHAINS[region]
        for i in range(len(chars)):
            if chars[i] in level:
                level = level[chars[i]]
            else:
                if not isinstance(level, dict):
                    break
                for j in range(i, len(chars)):
                    level[chars[j]] = {}
                    last_level, last_char = level, chars[j]
                    level = level[chars[j]]
                last_level[last_char] = {cls.DELIMIT: 0}
                break
        if i == len(chars) - 1:
            level[cls.DELIMIT] = 0

    @classmethod
    def load(cls):
        for region in GlobalizationService.REGIONS:
            for _ in SpamWord.get_by_region(region):
                cls.add(_.word, region)

    @classmethod
    def mark_spam_word(cls, user_id, from_time, to_time):
        """将一段时间user_id的track_spam_record记录标位‘已处理’，参数时间都是时间戳(int)"""
        objs = TrackSpamRecord.objects(user_id=user_id, create_time__gte=from_time, create_time__lte=to_time,
                                       dealed=False)
        for obj in objs:
            obj.dealed = True
            obj.save()

    @classmethod
    def is_spam_word(cls, word, region=None):
        """从word的某个位置开始连续匹配到了一个keyword，则判定为spam_word"""
        if not word:
            return False
        word = word.lower()
        ret = []
        start = 0
        while start < len(word):
            level = cls.KEYWORD_CHAINS.get(region, {}) if not cls.NOT_REGION else cls.DEFAULT_KEYWORD_CHAIN
            step_ins = 0
            for char in word[start:]:
                if char in level:
                    step_ins += 1
                    if cls.DELIMIT not in level[char]:
                        level = level[char]
                    else:
                        return True
                else:
                    ret.append(word[start])
                    break
            else:
                ret.append(word[start])
            start += 1
        return False

    @classmethod
    def get_spam_words(cls, region):
        lst = SpamWord.get_spam_words(region.lower())
        if not lst:
            return 'not spam words', False
        return {'spam_words': lst}, True


class ReportService(object):

    @classmethod
    def save_report(cls, user_id, reason, pics=None, target_user_id=None, related_feed_id=None, match_type=None,
                    chat_record=None):
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
        report.target_uid = target_user_id
        report.create_ts = int(time.time())
        report.save()
        return report.id

    @classmethod
    def mark_report(cls, user_id, from_time, to_time):
        """
        将一段时间举报user_id的记录标位‘已处理’，参数时间都是时间戳(int)
        :return: 一个列表，包含举报该user的举报者们
        """
        objs = Report.objects(target_uid=user_id, create_ts__gte=from_time, create_ts__lte=to_time, dealed=False)
        report_users = []
        for obj in objs:
            obj.dealed = True
            report_users.append(obj.uid)
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
        if report.related_feed:
            feed = Feed.get_by_id(report.related_feed)
            if feed:
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


SpamWordService.load()
