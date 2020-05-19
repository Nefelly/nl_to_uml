# encoding:utf-8
import time

from litatom.const import (
    FEED_NEED_CHECK,
    ONE_DAY,
    FORBID_PAGE_SIZE,
    SYS_FORBID,
    MANUAL_FORBID,
    SYS_FORBID_TIME,
    OSS_AUDIO_URL,
    OSS_PIC_URL, FEED_NOT_FOUND_ERROR, ERROR_RANGE,
)
from litatom.model import (
    Feed,
    UserSetting,
    TrackSpamRecord,
    Report,
    UserRecord,
    Blocked,
    User,
)
from litatom.service import (
    ForbidActionService,
    ForbidRecordService,
    ForbidCheckService,
    ReportService,
    TrackSpamRecordService, GlobalizationService
)
from litatom.util import (
    get_ts_from_str,
    time_str_by_ts,
    unix_ts_string,
)


class ForbidPlatformService(object):
    FEED_NEED_REVIEW = 'review'
    FEED_RECOMMENDED = 'recommended'
    FEED_USER_UNRELIABLE = 'score_up5'
    FORBID_LOCATIONS = {'VN', 'TH', 'ID'}
    REPORT_REGIONS = {'th', 'vi', 'id', 'en', 'us'}
    MATCH_REPORT = 'match'
    OTHER_REPORT = 'other'

    @classmethod
    def _load_spam_record(cls, temp_res, from_ts, to_ts):
        records = TrackSpamRecord.get_record_by_time(from_ts, to_ts)
        for record in records:
            user_id = record.user_id
            if user_id not in temp_res.keys():
                continue
            temp_res[user_id]['forbid_history']['records'].append(TrackSpamRecordService.get_spam_record_info(record))

    @classmethod
    def _load_report(cls, temp_res, from_ts, to_ts):
        reports = Report.get_report_by_time(from_ts, to_ts)
        for report in reports:
            user_id = report.target_uid
            if user_id not in temp_res.keys():
                continue
            temp_res[user_id]['forbid_history']['reports'].append(ReportService.get_report_info(report))

    @classmethod
    def get_forbid_record(cls, from_ts, to_ts, region=None, forbid_type=None, num=100):
        """封号记录表"""
        if region and region not in cls.FORBID_LOCATIONS:
            return 'invalid region', False
        if forbid_type and forbid_type not in {SYS_FORBID, MANUAL_FORBID}:
            return 'invalid forbid type', False

        temp_res = {}
        user_num = 0
        have_read = 0
        # 从UserRecord中加载封号用户和封号时间
        while user_num < num:
            if not forbid_type:
                users = UserRecord.get_forbid_users_by_time(from_ts, to_ts).skip(have_read).limit(num)
            else:
                users = UserRecord.get_forbid_users_by_time(from_ts, to_ts, forbid_type).skip(have_read).limit(num)
            if not users:
                break
            have_read += len(users)
            for user in users:
                user_id = user.user_id
                if region and region != UserSetting.get_loc_by_uid(user_id):
                    continue
                temp_res[user_id] = {'user_id': user_id, 'forbidden_from': time_str_by_ts(user.create_time)}
                user_num += 1
                if user_num >= num:
                    break

        # 从TrackSpamRecord中导入次数和命中历史,从Report中导入次数和命中历史
        earliest_forbidden = int(time.time())
        for uid in temp_res.keys():
            forbidden_from = get_ts_from_str(temp_res[uid]['forbidden_from'])
            if forbidden_from < earliest_forbidden:
                earliest_forbidden = forbidden_from
            print(uid)
            forbidden_until = User.get_by_id(uid).forbidden_ts
            if forbidden_until:
                forbidden_until = unix_ts_string(forbidden_until)
            temp_res[uid]['forbidden_until'] = forbidden_until
            temp_res[uid]['user_forbidden_num'] = UserRecord.get_forbidden_num_by_uid(uid)
            temp_res[uid]['device_forbidden_num'] = ForbidRecordService.get_device_forbidden_num_by_uid(uid)
            temp_res[uid]['forbid_score'] = ForbidActionService.accum_illegal_credit(uid)[0]
            temp_res[uid]['nickname'] = User.get_by_id(uid).nickname
            temp_res[uid]['forbid_history'] = ForbidRecordService.get_forbid_history_by_uid(uid)

        cls._load_spam_record(temp_res, earliest_forbidden, to_ts)
        cls._load_report(temp_res, earliest_forbidden, to_ts)
        return temp_res.values()

    @classmethod
    def get_forbid_record_atom(cls, user_id):
        """对于单个用户，如此查询"""
        nickname = User.get_by_id(user_id).nickname
        forbidden_until = User.get_by_id(user_id).forbidden_ts
        if forbidden_until:
            forbidden_until = unix_ts_string(forbidden_until)
        user_forbidden_num = UserRecord.get_forbidden_num_by_uid(user_id)
        device_forbidden_num = ForbidRecordService.get_device_forbidden_num_by_uid(user_id)
        forbid_score = ForbidActionService.accum_illegal_credit(user_id)[0]
        forbid_history = ForbidRecordService.get_forbid_history_by_uid(user_id)
        return {'user_id': user_id, 'nickname': nickname, 'forbidden_until': forbidden_until,
                'forbidden_from': UserRecord.get_forbidden_time_by_uid(user_id),
                'user_forbidden_num': user_forbidden_num, 'device_forbidden_num': device_forbidden_num,
                'forbid_score': forbid_score, 'forbid_history': forbid_history}

    @classmethod
    def get_feed(cls, from_ts, to_ts, loc=None, condition=None, num=100):
        """feed审核表"""
        if loc and loc not in cls.FORBID_LOCATIONS:
            return 'invalid location', False
        if condition and condition not in {cls.FEED_NEED_REVIEW, cls.FEED_RECOMMENDED, cls.FEED_USER_UNRELIABLE}:
            return 'invalid condition', False
        res = []
        res_length = 0
        have_read = 0
        while res_length < num:
            feeds = Feed.objects(status=FEED_NEED_CHECK, create_time__gte=from_ts, create_time__lte=to_ts).order_by(
                '-create_ts').skip(have_read).limit(num)
            if not feeds:
                break
            have_read += len(feeds)
            for feed in feeds:
                user_id = feed.user_id
                if loc and loc != UserSetting.get_loc_by_uid(user_id):
                    continue
                is_hq = feed.is_hq
                if condition == cls.FEED_RECOMMENDED and not is_hq:
                    continue
                forbid_score = ForbidActionService.accum_illegal_credit(user_id)[0]
                if condition == cls.FEED_USER_UNRELIABLE and forbid_score <= 5:
                    continue
                tmp = {'user_id': user_id, 'word': feed.content, 'pics': [OSS_PIC_URL + pic for pic in feed.pics],
                       'audio': [OSS_AUDIO_URL + audio for audio in feed.audios],
                       'comment_num': feed.comment_num, 'like_num': feed.like_num, 'hq': is_hq,
                       'forbid_score': forbid_score, 'feed_id': str(feed.id)}
                res.append(tmp)
                res_length += 1
                if res_length >= num:
                    break
        return res, True

    @classmethod
    def get_feed_atom(cls, user_id):
        feeds = Feed.objects(user_id=user_id, status=FEED_NEED_CHECK)
        forbid_score = ForbidActionService.accum_illegal_credit(user_id)[0]
        return [{'user_id': user_id, 'word': feed.content, 'pics': [OSS_PIC_URL + pic for pic in feed.pics],
                 'audio': [OSS_AUDIO_URL + audio for audio in feed.audios],
                 'comment_num': feed.comment_num, 'like_num': feed.like_num, 'hq': feed.is_hq,
                 'forbid_score': forbid_score, 'feed_id': str(feed.id)} for feed in feeds], True

    @classmethod
    def get_report(cls, from_ts, to_ts, region=None, match_type=None, num=100):
        if region and region not in cls.REPORT_REGIONS:
            return 'invalid region', False
        if match_type and match_type not in {cls.MATCH_REPORT, cls.OTHER_REPORT}:
            return 'invalid match type', False
        if not region and not match_type:
            reports = Report.objects(create_ts__gte=from_ts, create_ts__lte=to_ts, dealed=False,
                                     duplicated=False).order_by('-create_ts').limit(num)
        elif region and match_type == cls.MATCH_REPORT:
            reports = Report.objects(create_ts__gte=from_ts, create_ts__lte=to_ts, region=region, reason=match_type,
                                     dealed=False, duplicated=False).order_by('-create_ts').limit(num)
        elif region and match_type == cls.OTHER_REPORT:
            reports = Report.objects(create_ts__gte=from_ts, create_ts__lte=to_ts, region=region,
                                     reason__ne=cls.MATCH_REPORT, dealed=False, duplicated=False).order_by(
                '-create_ts').limit(num)
        elif region and not match_type:
            reports = Report.objects(create_ts__gte=from_ts, create_ts__lte=to_ts, region=region, dealed=False,
                                     duplicated=False).order_by('-create_ts').limit(num)
        elif not region and match_type == cls.MATCH_REPORT:
            reports = Report.objects(create_ts__gte=from_ts, create_ts__lte=to_ts, reason=match_type, dealed=False,
                                     duplicated=False).order_by('-create_ts').limit(num)
        else:
            reports = Report.objects(create_ts__gte=from_ts, create_ts__lte=to_ts, reason__ne=cls.MATCH_REPORT,
                                     dealed=False, duplicated=False).order_by('-create_ts').limit(num)
        return [ReportService.get_report_info(report) for report in reports], True

    @classmethod
    def get_report_atom(cls, user_id):
        reports = Report.objects(target_uid=user_id)
        return [ReportService.get_report_info(report) for report in reports], True

    @classmethod
    def get_spam_record(cls, from_ts, to_ts, region=None, num=100):
        if region and region not in cls.FORBID_LOCATIONS:
            return 'invalid region', False
        res = []
        res_len = 0
        have_read = 0
        while res_len < num:
            records = TrackSpamRecord.objects(create_time__gte=from_ts, create_time__lte=to_ts, dealed=False).order_by(
                '-create_time').skip(have_read).limit(num)
            if not records:
                break
            have_read += len(records)
            for record in records:
                user_id = record.user_id
                if region and GlobalizationService.get_region_by_user_id(user_id) != region:
                    continue
                res.append(TrackSpamRecordService.get_spam_record_info(record))
                res_len += 1
                if res_len >= num:
                    break
        return res, True

    @classmethod
    def get_spam_record_atom(cls, user_id):
        records = TrackSpamRecord.objects(user_id=user_id, dealed=False)
        return [TrackSpamRecordService.get_spam_record_info(record) for record in records], True
