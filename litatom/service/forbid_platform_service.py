import time

from litatom.const import FEED_NEED_CHECK, ONE_DAY
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
    ForbidActionService, ForbidCheckService
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
    FEED_LOCATIONS = {'VN', 'TH', 'ID'}

    PIC_URL = 'http://www.litatom.com/api/sns/v1/lit/simage/'
    AUDIO_URL = 'http://www.litatom.com/api/sns/v1/lit/audio/'

    @classmethod
    def _load_spam_record(cls, temp_res, from_ts, to_ts):
        records = TrackSpamRecord.get_record_by_time(from_ts, to_ts)
        for record in records:
            if record.user_id in temp_res.keys():
                # temp_num表示目前已录入的警告次数
                temp_num = temp_res[record.user_id][1]
                if temp_num == temp_res[record.user_id][u'警告次数']:
                    continue
                temp_res[record.user_id][1] += 1
                if record.word:
                    temp_res[record.user_id][u'警告' + str(temp_num + 1)] = {u'敏感词': record.word,
                                                                           u'命中词':SpamWordCheckService.get_spam_word(record.word,GlobalizationService.get_region_by_user_id(record.user_id)),
                                                                           u'警告时间': time_str_by_ts(record.create_time)}
                elif record.pic:
                    temp_res[record.user_id][u'警告' + str(temp_num + 1)] = {u'色情图片': record.pic,
                                                                           u'警告时间': time_str_by_ts(record.create_time)}

    @classmethod
    def _load_report(cls, temp_res, from_ts, to_ts):
        reports = Report.get_report_by_time(from_ts, to_ts)
        for report in reports:
            if report.target_uid in temp_res.keys():
                temp_num = temp_res[report.target_uid][2]
                if temp_num == temp_res[report.target_uid][u'举报次数']:
                    continue
                if not temp_num:
                    temp_res[report.target_uid][u'地区'] = report.region
                temp_res[report.target_uid][2] += 1
                temp_res[report.target_uid][u'举报' + str(temp_num + 1)] = {u'举报者': report.uid, u'举报原因': report.reason,
                                                                          u'举报时间': time_str_by_ts(report.create_ts)}
                if report.pics:
                    pics = [cls.PIC_URL + pic for pic in report.pics]
                    temp_res[report.target_uid][u'举报' + str(temp_num + 1)][u'举报图片'] = pics
                elif report.related_feed:
                    feed = Feed.objects(id=report.related_feed).first()
                    temp_res[report.target_uid][u'举报' + str(temp_num + 1)][u'举报feed'] = {}
                    if not feed:
                        temp_res[report.target_uid][u'举报' + str(temp_num + 1)][u'举报feed'][
                            'ERROR'] = 'FEED CAN NOT BE FOUND'
                    else:
                        if feed.content:
                            temp_res[report.target_uid][u'举报' + str(temp_num + 1)][u'举报feed']['content'] = feed.content
                        if feed.pics:
                            pics = [cls.PIC_URL + pic for pic in feed.pics]
                            temp_res[report.target_uid][u'举报' + str(temp_num + 1)][u'举报feed']['pictures'] = pics
                        if feed.audios:
                            audios = [cls.AUDIO_URL + audio for audio in feed.audios]
                            temp_res[report.target_uid][u'举报' + str(temp_num + 1)][u'举报feed']['audios'] = audios

    @classmethod
    def get_forbid_history(cls, from_ts=int(time.time() - ONE_DAY), to_ts=int(time.time())):
        # 从UserRecord中加载封号用户和封号时间
        users = UserRecord.get_forbid_users_by_time(from_ts, to_ts, 'sysForbid')
        temp_res = {}
        for user in users:
            temp_res[user.user_id] = {u'user_id': user.user_id, u'封号时间': time_str_by_ts(user.create_time)}

        # 从TrackSpamRecord中导入次数和命中历史,从Report中导入次数和命中历史
        earlist_illegal_action_ts = int(time.time())
        total_forbid_num = len(temp_res)
        report_forbid_num = 0.0
        for uid in temp_res.keys():
            temp_ts = get_ts_from_str(temp_res[uid][u'封号时间']) - 7 * ONE_DAY
            if temp_ts < earlist_illegal_action_ts:
                earlist_illegal_action_ts = temp_ts
            temp_res[uid][u'警告次数'] = TrackSpamRecord.count_by_time_and_uid(uid, temp_ts, temp_ts + 3 * ONE_DAY, True)
            temp_res[uid][u'举报次数'] = Report.count_by_time_and_uid(uid, temp_ts, temp_ts + 3 * ONE_DAY, True)
            temp_res[uid][u'历史被封次数'] = UserRecord.get_forbidden_times_user_id(uid)
            temp_res[uid][u'被多少人拉黑'] = Blocked.get_blocker_num_by_time(uid)
            temp_res[uid][1] = 0
            temp_res[uid][2] = 0
            # if temp_res[uid][u'警告次数'] != 0:
            #     temp_res.pop(uid)
            # report_forbid_num += 1
            if temp_res[uid][u'警告次数'] == 0:
                report_forbid_num += 1

        cls._load_spam_record(temp_res, earlist_illegal_action_ts, to_ts)
        cls._load_report(temp_res, earlist_illegal_action_ts, to_ts)
        print('总封号人数',total_forbid_num)
        print('仅因举报封号人数',report_forbid_num)
        print('仅因举报封号率',report_forbid_num/total_forbid_num)
        # write_to_json(file, [item for item in temp_res.values() if (item.pop(1) or 1) and (item.pop(2) or 1)])

    @classmethod
    def get_forbid_history_by_uid(cls, user_id):
        has_forbidden_num = UserRecord.get_forbidden_times_user_id(user_id)
        forbidden_ts = User.get_by_id(user_id).forbidden_ts
        if forbidden_ts:
            forbidden_ts = unix_ts_string(forbidden_ts)
        forbid_score = ForbidActionService.accum_illegal_credit(user_id)
        is_sensitive = ForbidCheckService.check_sensitive_user(user_id)
        ts_now = int(time.time())
        report_times = Report.count_by_time_and_uid(user_id, temp_ts, temp_ts + 3 * ONE_DAY, True)


    @classmethod
    def get_feed(cls, loc, condition):
        if loc not in cls.FEED_LOCATIONS:
            return 'invalid location', False
        if condition not in {cls.FEED_NEED_REVIEW, cls.FEED_RECOMMENDED, cls.FEED_USER_UNRELIABLE}:
            return 'invalid condition', False
        feeds = Feed.objects(status=FEED_NEED_CHECK).limit(100)
        res = []
        for feed in feeds:
            user_id = feed.user_id
            if loc and loc != UserSetting.get_loc_by_uid(user_id):
                continue
            is_hq = feed.is_hq
            if condition == cls.FEED_RECOMMENDED and not is_hq:
                continue
            forbid_score = ForbidActionService.accum_illegal_credit(user_id)
            if condition == cls.FEED_USER_UNRELIABLE and forbid_score <= 5:
                continue
            tmp = {'user_id': user_id, 'word': feed.content, 'pics': feed.pics, 'audio': feed.audios,
                   'comment_num': feed.comment_num, 'like_num': feed.like_num, 'hq': is_hq,
                   'forbid_score': forbid_score}
            res.append(tmp)
        return res, True


