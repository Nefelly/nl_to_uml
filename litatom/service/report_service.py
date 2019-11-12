# coding: utf-8
import time
import json
from ..redis import RedisClient
from ..model import (
    Report,
    Feed
)
from ..const import (
    ONE_DAY
)
from ..service import (
    UserService,
    GlobalizationService
)
from ..util import (
    date_from_unix_ts,
    format_standard_time
)
redis_client = RedisClient()['lit']

class ReportService(object):

    @classmethod
    def report(cls, user_id, reason, pics=[], target_user_id=None, related_feed_id=None, match_type=None, chat_record=None):
        report = Report()
        report.uid = user_id
        report.reason = reason
        report.pics = pics
        report.chat_record = chat_record
        report.related_feed = related_feed_id
        report.region = GlobalizationService.get_region()
        if target_user_id:
            ts_now = int(time.time())
            cnt = Report.objects(uid=user_id, create_ts__gte=ts_now - ONE_DAY).count()
            if cnt >= 5:
                return 'You have report too many times today, please try later', False
            if target_user_id.startswith('love'):
                target_user_id = UserService.uid_by_huanxin_id(target_user_id)
            report.target_uid = target_user_id
            if UserService.is_official_account(target_user_id):
                return 'This is our official account, please don\'t be naughty', False
            if cls._should_block(target_user_id, user_id, reason):
                UserService.auto_forbid(target_user_id, 3 * ONE_DAY)
                objs = Report.objects(target_uid=target_user_id, create_ts__gte=(ts_now - 3 * ONE_DAY))
                send_uids = []
                for _ in objs:
                    if not _.dealed:
                        _.dealed = True
                        _.save()
                        send_uids.append(_.uid)
                UserService.block_actions(target_user_id, list(set(send_uids)))
        ts_now = int(time.time())
        report.create_ts = ts_now
        report.save()
        return {'report_id': str(report.id)}, True

    @classmethod
    def _should_block(cls, target_user_id, user_id, reason=None):
        match_reason = 'match'
        match_cnt = 0.7
        ts_now = int(time.time())
        objs = Report.objects(target_uid=target_user_id, create_ts__gte=(ts_now - 3 * ONE_DAY), dealed=False)
        judge_num = 2
        cnt = match_cnt if reason == match_reason else 1
        uids = {user_id}
        if objs:
            for _ in objs:
                if _.uid not in uids:
                    uids.add(_.uid)
                    if _.reason == match_reason:
                        cnt += match_cnt
                    else:
                        cnt += 1
                    if cnt >= judge_num:
                        return True
        return False
    
    @classmethod
    def get_report_info(cls, report):
        res = {
            'reason': report.reason,
            'report_id': str(report.id),
            'user_id': report.uid,
            'pics': report.pics,
            'region': report.region,
            'deal_result': report.deal_res if report.deal_res else '',
            'target_user_id': '%s\n%s' % (report.target_uid, UserService.nickname_by_uid(report.target_uid)) if report.target_uid else '',
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