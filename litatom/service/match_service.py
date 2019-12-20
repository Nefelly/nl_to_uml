# coding=utf-8
import time
import datetime
import random
import cPickle
from hendrix.conf import setting
from ..redis import RedisClient
from ..key import (
    REDIS_USER_MATCH_LEFT,
    REDIS_FAKE_ID_UID,
    REDIS_UID_FAKE_ID,
    REDIS_FAKE_START,
    REDIS_ANOY_CHECK_POOL,
    REDIS_MATCH_BEFORE,
    REDIS_MATCHED,
    REDIS_FAKE_LIKE,
    REDIS_JUDGE_LOCK,
    REDIS_MATCH_PAIR,
    REDIS_ACCELERATE_CACHE
)
from ..util import (
    now_date_key,
    low_high_pair
)
from ..const import (
    CREATE_HUANXIN_ERROR,
    ONE_DAY,
    FIVE_MINS,
    GENDERS,
    BOY,
    GIRL,
    MAX_TIME,
    USER_NOT_EXISTS,
    PROFILE_NOT_COMPLETE,
    NOT_IN_MATCH,
    ONE_MIN,
    CAN_MATCH_ONLINE,
    USER_MODEL_EXCHANGE
)
from ..service import (
    UserService,
    FollowService,
    BlockService,
    GlobalizationService,
    StatisticService,
    StatisticService,
    MqService
)
from ..model import (
    User,
    MatchRecord,
    UserModel
)
redis_client = RedisClient()['lit']


class MatchService(object):
    MATCH_WAIT = 60 * 3 + 1
    MATCH_INT = 60 * 3  # talking time
    TOTAL_WAIT = MATCH_INT + MATCH_WAIT + FIVE_MINS
    MAX_CHOOSE_NUM = 40
    MATCH_TMS = 20 if not setting.IS_DEV else 1000
    OTHER_GENDER_M = {BOY: GIRL, GIRL: BOY}
    MAX_TIMES = 99999
    FAKE_MAX_TIME = -100

    TYPE_ANOY_CHECK_POOL = REDIS_ANOY_CHECK_POOL
    TYPE_FAKE_ID_UID = REDIS_FAKE_ID_UID
    TYPE_UID_FAKE_ID = REDIS_UID_FAKE_ID
    TYPE_FAKE_START = REDIS_FAKE_START
    TYPE_MATCHED = REDIS_MATCHED
    TYPE_MATCH_BEFORE = REDIS_MATCH_BEFORE
    TYPE_USER_MATCH_LEFT = REDIS_USER_MATCH_LEFT
    TYPE_FAKE_LIKE = REDIS_FAKE_LIKE
    TYPE_MATCH_PAIR = REDIS_MATCH_PAIR
    TYPE_JUDGE_LOCK = REDIS_JUDGE_LOCK
    MATCH_KEY_BY_REGION_GENDER = GlobalizationService.anoy_match_key_by_region_gender
    MATCH_TYPE = 'soul'
    ACCELERATE_KEY_BY_TYPE_REGION_GENDER = GlobalizationService.accelerate_match_key_by_region_type_gender

    @classmethod
    def get_judge_time(cls):
        return int(time.time()) - cls.MATCH_WAIT

    @classmethod
    def get_anoy_count(cls, gender):
        judge_time = cls.get_judge_time()
        return redis_client.zcount(cls.MATCH_KEY_BY_REGION_GENDER(gender), judge_time, MAX_TIME) + \
               redis_client.zcount(cls.ACCELERATE_KEY_BY_TYPE_REGION_GENDER(cls.MATCH_TYPE, gender), judge_time, MAX_TIME)

    @classmethod
    def _get_anoy_id(cls, user):
        huanxin = user.huanxin
        return huanxin.user_id, huanxin.password
        # return HuanxinService.gen_id_pwd()

    @classmethod
    def cal_match_score(cls, uid1, uid2, uid1_alone=False, uid2_alone=False):
        return 1

    @classmethod
    def get_tips(cls):
        assert False, NotImplementedError

    @classmethod
    def _add_to_match_pool(cls, gender, fake_id, user_id):
        # 进入匹配id池子
        if not gender or not fake_id:
            return
        int_time = int(time.time())
        is_accelerate = cls._is_accelerate(user_id)
        if not is_accelerate:
            anoy_gender_key = cls.MATCH_KEY_BY_REGION_GENDER(gender)
        else:
            anoy_gender_key = cls.ACCELERATE_KEY_BY_TYPE_REGION_GENDER(cls.MATCH_TYPE, gender)
        redis_client.zadd(anoy_gender_key, {fake_id: int_time})

    @classmethod
    def _remove_from_match_pool(cls, gender, fake_id):
        if not gender or not fake_id:
            return
        # uid = cls._uid_by_fake_id(fake_id)
        # redis_client.delete(REDIS_ACCELERATE_CACHE.format(user_id=uid))
        return redis_client.zrem(cls.MATCH_KEY_BY_REGION_GENDER(gender), fake_id) or redis_client.zrem(cls.ACCELERATE_KEY_BY_TYPE_REGION_GENDER(cls.MATCH_TYPE, gender), fake_id)

    @classmethod
    def _add_to_check_pool(cls, fake_id):
        if not fake_id:
            return
        int_time = int(time.time())
        redis_client.zadd(cls.TYPE_ANOY_CHECK_POOL, {fake_id: int_time})

    @classmethod
    def _clear_match_pair(cls, fake_id, other_fakeid, leave_fake_id=None):
        pair = low_high_pair(fake_id, other_fakeid)
        key = cls.TYPE_MATCH_PAIR.format(low_high_fakeid=pair)
        match_time = redis_client.get(key)
        if not match_time:
            return
        match_time = int(match_time)
        user_id1 = cls._uid_by_fake_id(fake_id)
        user_id2 = cls._uid_by_fake_id(other_fakeid)
        if not leave_fake_id:
            quit_user = None
        else:
            quit_user = user_id1 if leave_fake_id == fake_id else user_id2
        obj = MatchRecord.create(user_id1, user_id2, cls.MATCH_TYPE, quit_user, match_time, int(time.time()) - match_time)
        MqService.push(USER_MODEL_EXCHANGE, {'model_type': 'match', 'data': str(cPickle.dumps(obj))})
        redis_client.delete(key)

    @classmethod
    def _destroy_fake_id(cls, fake_id, need_remove_from_pool=True):
        if not fake_id:
            return
        #HuanxinService.delete_user(fake_id)
        user_id = redis_client.get(cls.TYPE_FAKE_ID_UID.format(fake_id=fake_id))

        if user_id:
            # could not be clear now, because should be used to judge
            # redis_client.delete(cls.TYPE_FAKE_ID_UID.format(fake_id=fake_id))
            redis_client.delete(cls.TYPE_JUDGE_LOCK.format(fake_id=fake_id))
            redis_client.delete(cls.TYPE_UID_FAKE_ID.format(user_id=user_id))

        # delete match infos
        if need_remove_from_pool:
            redis_client.delete(cls.TYPE_FAKE_START.format(fake_id=fake_id))
            other_fakeid = redis_client.get(cls.TYPE_MATCHED.format(fake_id=fake_id))
            if other_fakeid:
                redis_client.delete(cls.TYPE_FAKE_START.format(fake_id=other_fakeid))
                redis_client.delete(cls.TYPE_MATCHED.format(fake_id=fake_id))
                redis_client.delete(cls.TYPE_MATCHED.format(fake_id=other_fakeid))
                cls._clear_match_pair(fake_id, other_fakeid)
                # pair = low_high_pair(fake_id, other_fakeid)
                # redis_client.delete(cls.TYPE_MATCH_PAIR.format(low_high_fakeid=pair))
                # redis_client.delete(REDIS_FAKE_LIKE.format(fake_id=fake_id))
                # redis_client.delete(REDIS_FAKE_LIKE.format(fake_id=other_fakeid))
            if not cls._remove_from_match_pool(BOY, fake_id):
                cls._remove_from_match_pool(GIRL, fake_id)
        redis_client.zrem(cls.TYPE_ANOY_CHECK_POOL, fake_id)

    @classmethod
    def _in_match(cls, fake_id1, fake_id2):
        pair = low_high_pair(fake_id1, fake_id2)
        in_match = redis_client.get(cls.TYPE_MATCH_PAIR.format(low_high_fakeid=pair))
        return True if in_match else False

    @classmethod
    def _create_match(cls, fake_id1, fake_id2, gender1, user_id, user_id2):
        time_now = int(time.time())
        pair = low_high_pair(fake_id1, fake_id2)
        redis_client.set(cls.TYPE_MATCHED.format(fake_id=fake_id2), fake_id1, cls.MATCH_INT)
        redis_client.set(cls.TYPE_MATCHED.format(fake_id=fake_id1), fake_id2, cls.MATCH_INT)
        redis_client.set(cls.TYPE_MATCH_PAIR.format(low_high_fakeid=pair), time_now, cls.MATCH_INT)
        redis_client.set(cls.TYPE_MATCH_BEFORE.format(low_high_fakeid=pair), 1, ONE_DAY)
        # 将其从正在匹配队列中删除
        cls._remove_from_match_pool(gender1, fake_id1)
        cls._remove_from_match_pool(cls.OTHER_GENDER_M.get(gender1), fake_id2)
        redis_client.delete(REDIS_ACCELERATE_CACHE.format(user_id=user_id))
        redis_client.delete(REDIS_ACCELERATE_CACHE.format(user_id=user_id2))
        cls._add_to_check_pool(fake_id1)
        cls._add_to_check_pool(fake_id2)
        return True

    @classmethod
    def _delete_match(cls, fake_id):
        fake_id2 = redis_client.get(cls.TYPE_MATCHED.format(fake_id=fake_id))
        if not fake_id2:
            cls._destroy_fake_id(fake_id, True)
            return True
        cls._clear_match_pair(fake_id, fake_id2, fake_id)
        # pair = low_high_pair(fake_id, fake_id2)
        # redis_client.delete(cls.TYPE_MATCH_PAIR.format(low_high_fakeid=pair))
        cls._destroy_fake_id(fake_id, True)
        cls._destroy_fake_id(fake_id2, True)
        # map(cls._destroy_fake_id, [fake_id, fake_id2])
        return True

    @classmethod
    def get_match_user_info(cls, fake_id):
        user_id = cls._uid_by_fake_id(fake_id)
        age = UserService.uid_age(user_id)
        return {
            "user_id": user_id,
            "age": age,
            "login_day": User.get_by_id(user_id).days,
            "matched_times": cls._get_matched_times(user_id)
        }

    @classmethod
    def _is_out_wait_time(cls, fake_id, gender):
        return True
        score = redis_client.zscore(cls.MATCH_KEY_BY_REGION_GENDER(gender), fake_id)
        time_now = int(time.time())
        if not score:
            return False
        wait = 7
        if time_now - score > wait:
            return True
        return False

    @classmethod
    def _match(cls, fake_id, gender):
        '''
        return matched fake_id, if this match info has been set up
        '''
        matched_key = cls.TYPE_MATCHED.format(fake_id=fake_id)
        fake_id2 = redis_client.get(matched_key)
        if fake_id2:
            if cls._in_match(fake_id, fake_id2):
                # redis_client.delete(cls.TYPE_FAKE_START.format(fake_id=fake_id))
                return fake_id2, True
            redis_client.delete(matched_key)
        int_time = int(time.time())
        judge_time = int_time - cls.MATCH_WAIT
        other_gender = cls.OTHER_GENDER_M.get(gender)
        other_cnt = cls.get_anoy_count(other_gender)
        if other_cnt == 0:
            return None, False
        my_cnt = cls.get_anoy_count(gender)
        if other_cnt == 1:
            if my_cnt > 1:
                return None, False

        accelerate_fakeids = redis_client.zrangebyscore(cls.ACCELERATE_KEY_BY_TYPE_REGION_GENDER(cls.MATCH_TYPE, other_gender), judge_time + 3, MAX_TIME, 0, cls.MAX_CHOOSE_NUM)
        other_fakeids = redis_client.zrangebyscore(cls.MATCH_KEY_BY_REGION_GENDER(other_gender), judge_time + 3, MAX_TIME, 0, cls.MAX_CHOOSE_NUM)
        if not accelerate_fakeids and not other_fakeids:
            return None, False

        user_id = cls._uid_by_fake_id(fake_id)
        user_age = UserService.uid_age(user_id)

        cnt = 0
        matched_fakeid = None
        for fake_id2 in accelerate_fakeids:  # 应该使用随机策略，因为排队诅咒会导致排队最久最先排到导致平均等待时间最长，且驱逐耐心较小的用户
            user_id2 = cls._uid_by_fake_id(fake_id2)
            if not redis_client.get(cls.TYPE_MATCH_BEFORE.format(low_high_fakeid=low_high_pair(fake_id, fake_id2))) and not BlockService.get_block_msg(user_id, user_id2):
                matched_fakeid = fake_id2
                break

        try_tms = 20
        #TODO first select all, then choose
        if not matched_fakeid:
            near_new = []
            near_old = []
            far_new = []
            far_old = []
            for el_fake_id in other_fakeids:
                m = cls.get_match_user_info(el_fake_id)
                age = m["age"]
                login_day = m["login_day"]
                matched_times = m["matched_times"]
                if abs(user_age - age) > 3:
                    if login_day < 1 and matched_times < 1:
                        far_new.append(el_fake_id)
                    else:
                        far_old.append(el_fake_id)
                else:
                    if login_day < 1 and matched_times < 1:
                        near_new.append(el_fake_id)
                    else:
                        near_old.append(el_fake_id)
            user1_out_wait = cls._is_out_wait_time(fake_id, gender)
            to_scan = near_new + near_old
            near_num = len(to_scan)
            if user1_out_wait:
                to_scan = to_scan + far_new + far_old

            m = cls.get_match_user_info(fake_id)
            login_day = m["login_day"]
            matched_times = m["matched_times"]
            if login_day < 1 and matched_times < 1:
                uids = cls._batch_uids_by_fake_id(to_scan)
                uid_scores = UserModel.batch_get_score(uids)
                fakeid_scores = []
                inds = min(len(uids), len(uid_scores))
                for i in range(inds):
                    fakeid_scores.append([to_scan[i], uid_scores[i][1]])
                fake_ids = [el[0] for el in sorted(fakeid_scores, key=lambda x: -x[1])]
                to_scan = fake_ids
            for i in range(len(to_scan)):
                # fake_id2 = random.choice(other_fakeids)
                fake_id2 = to_scan[i]
                if i >= near_num:
                    if not cls._is_out_wait_time(fake_id2, other_gender):
                        continue
                user_id2 = cls._uid_by_fake_id(fake_id2)
                # user2_age = UserService.uid_age(user_id2)
                # if cnt < try_tms - 1 and abs(user_age - user2_age) > 3:
                #     continue
                if not redis_client.get(cls.TYPE_MATCH_BEFORE.format(low_high_fakeid=low_high_pair(fake_id, fake_id2))) and not BlockService.get_block_msg(user_id, user_id2):
                    matched_fakeid = fake_id2
                    break
                elif cnt == try_tms - 1:
                    return None, False
                # if not UserFilterService.filter_by_age_gender(user_id, user_id2) or not UserFilterService.filter_by_age_gender(user_id2, user_id):
                #     if i == try_tms - 1:
                #         return None, False
                #     continue
            #redis_client.zadd(matched_key, {fake_id2: int_time})
        if not matched_fakeid:
            return None, False
        fake_id2_matched = redis_client.get(cls.TYPE_MATCHED.format(fake_id=matched_fakeid))
        if not fake_id2_matched or fake_id2_matched == fake_id:
            cls._create_match(fake_id, matched_fakeid, gender, user_id, user_id2)
            return matched_fakeid, False
        return None, False

    @classmethod
    def _is_member(cls, user_id):
        from ..service import AccountService
        return AccountService.is_member(user_id)

    @classmethod
    def _match_left_verify(cls, user_id):
        # 匹配次数验证
        # if AccountService.is_member(user_id):
        #     return cls.MAX_TIMES, True
        now_date = now_date_key()
        match_left_key = cls.TYPE_USER_MATCH_LEFT.format(user_date=user_id + now_date)
        default_match_times = cls.MATCH_TMS if not cls._is_member(user_id) else cls.MATCH_TMS
        redis_client.setnx(match_left_key, default_match_times)
        redis_client.expire(match_left_key, ONE_DAY)
        times_left = int(redis_client.get(match_left_key))
        if times_left <= 0:
            return u'Your match opportunity has run out, please try again tomorrow', False
        return times_left, True

    @classmethod
    def _get_matched_times(cls, user_id):
        times, status = cls._match_left_verify(user_id)
        if not status:
            return cls.MATCH_TMS
        return max(cls.MATCH_TMS - times, 0)

    @classmethod
    def _decr_match_left(cls, user_id):
        # if AccountService.is_member(user_id):
        #     return
        now_date = now_date_key()
        match_left_key = cls.TYPE_USER_MATCH_LEFT.format(user_date=user_id + now_date)
        if not redis_client.get(match_left_key):
            default_match_times = cls.MATCH_TMS if not cls._is_member(user_id) else cls.MATCH_TMS
            redis_client.setnx(match_left_key, default_match_times)
            # redis_client.setnx(match_left_key, cls.MATCH_TMS)
            redis_client.expire(match_left_key, ONE_DAY)
        redis_client.decr(match_left_key)

    @classmethod
    def set_member_match_left(cls, user_id):
        '''
        需要更改保存以获取用户已经匹配的次数
        :param user_id:
        :return:
        '''
        now_date = now_date_key()
        match_left_key = cls.TYPE_USER_MATCH_LEFT.format(user_date=user_id + now_date)
        redis_client.delete(match_left_key)
        # if not left_tms:
        #     return
        # left_tms = int(left_tms)
        # if left_tms < cls.MATCH_TMS:
        #     new_tms = cls.MATCH_TMS -

    @classmethod
    def _incr_match_left(cls, user_id, num=1):
        now_date = now_date_key()
        match_left_key = cls.TYPE_USER_MATCH_LEFT.format(user_date=user_id + now_date)
        if not redis_client.get(match_left_key):
            default_match_times = cls.MATCH_TMS if not cls._is_member(user_id) else cls.MATCH_TMS
            redis_client.setnx(match_left_key, default_match_times)
            # redis_client.setnx(match_left_key, cls.MATCH_TMS)
            redis_client.expire(match_left_key, ONE_DAY)
        redis_client.incrby(match_left_key, num)

    @classmethod
    def pure_get_fake_id(cls, user_id):
        user = User.get_by_id(user_id)
        if not user:
            return USER_NOT_EXISTS, False
        gender = UserService.get_gender(user_id)
        if not gender:
            return PROFILE_NOT_COMPLETE, False
        fake_id, pwd = cls._get_anoy_id(user)
        return fake_id

    @classmethod
    def create_fakeid(cls, user_id):
        user = User.get_by_id(user_id)
        if not user:
            return USER_NOT_EXISTS, False

        gender = UserService.get_gender(user_id)
        if not gender:
            return PROFILE_NOT_COMPLETE, False
        user_id = str(user.id)
        msg, status = cls._match_left_verify(user_id)
        if not status:
            return msg, False
        old_fake_id = redis_client.get(cls.TYPE_UID_FAKE_ID.format(user_id=user_id))
        if old_fake_id:
            cls._destroy_fake_id(old_fake_id)

        fake_id, pwd = cls._get_anoy_id(user)
        if not fake_id:
            return CREATE_HUANXIN_ERROR, False
        res = {
            'fake_id': fake_id,
            'password': pwd,
            'can_match_online': CAN_MATCH_ONLINE
        }
        # cls._add_to_check_pool(fake_id)
        # 建立fakeid:uid索引
        redis_client.set(cls.TYPE_FAKE_ID_UID.format(fake_id=fake_id), user_id, ex=cls.TOTAL_WAIT)

        # 建立uid:fakeid索引
        redis_client.set(cls.TYPE_UID_FAKE_ID.format(user_id=user_id), fake_id, ex=cls.TOTAL_WAIT)

        cls._add_to_match_pool(gender, fake_id, user_id)

        # 进入匹配过期
        redis_client.set(cls.TYPE_FAKE_START.format(fake_id=fake_id), int(time.time()), cls.MATCH_WAIT)
        return res, True

    @classmethod
    def anoy_user_info(cls, fake_id):
        res = {}
        user_id = cls._uid_by_fake_id(fake_id)
        user = User.get_by_id(user_id)
        if not user_id:
            return res
        res['avatar'] = user.avatar
        return res


    @classmethod
    def _in_match_out(cls, user_id, fake_id, gender, out_uid):
        '''
        匹配中用户匹配非匹配中用户
        :param user_id:
        :param fake_id:
        :param gender:
        :param out_uid:
        :return:
        '''
        matched_key = cls.TYPE_MATCHED.format(fake_id=fake_id)
        fake_id2 = redis_client.get(matched_key)
        if fake_id2:
            if cls._in_match(fake_id, fake_id2):
                return fake_id2, True
            redis_client.delete(matched_key)
        fake_id2 = cls.pure_get_fake_id(out_uid)
        if redis_client.get(cls.TYPE_MATCH_BEFORE.format(low_high_fakeid=low_high_pair(fake_id, fake_id2))):
            return None, False
        if BlockService.get_block_msg(user_id, out_uid):
            return None, False
        fake_id2_matched = redis_client.get(cls.TYPE_MATCHED.format(fake_id=fake_id2))
        if not fake_id2_matched or fake_id2_matched == fake_id:
            cls._create_match(fake_id, fake_id2, gender)
            cls._delete_match(fake_id)
            return fake_id2, False
        return None, False

    @classmethod
    def _match_online(cls, fake_id, gender):
        other_gender = cls.OTHER_GENDER_M.get(gender)
        user_id = cls._uid_by_fake_id(fake_id)
        user_ids = StatisticService.online_users_by_interval(other_gender, 3 * ONE_MIN)
        nearest_uid = UserService.nearest_age_uid(user_id, user_ids)
        if not nearest_uid:
            return None, False
        return cls._in_match_out(user_id, fake_id, gender, nearest_uid)

    @classmethod
    def _match_yesterday(cls, fake_id, gender):
        other_gender = cls.OTHER_GENDER_M.get(gender)
        user_id = cls._uid_by_fake_id(fake_id)
        user = User.get_by_id(user_id)
        users = User.user_register_yesterday(other_gender, user.country)
        user_ids = [str(el.id) for el in users]
        nearest_uid = UserService.nearest_age_uid(user_id, user_ids)
        if not nearest_uid:
            return None, False
        return cls._in_match_out(user_id, fake_id, gender, nearest_uid)


    @classmethod
    def anoy_match(cls, user_id):
        fake_id = cls._fakeid_by_uid(user_id)
        # 匹配已过期
        fake_expire_key = cls.TYPE_FAKE_START.format(fake_id=fake_id)
        start_tm = redis_client.get(fake_expire_key) if fake_id else None
        if not fake_id or not start_tm:
            return u'fakeid: %s time out, please try another one' % fake_expire_key, False

        gender = UserService.get_gender(user_id)
        if not gender:
            return PROFILE_NOT_COMPLETE, False

        matched_id = None
        if CAN_MATCH_ONLINE:
            times_left, status = cls._match_left_verify(user_id)
            if status and (cls.MATCH_TMS - times_left) % 5 == 0 and cls.MATCH_TMS != times_left:
                matched_id, has_matched = cls._match_yesterday(fake_id, gender)
        if not matched_id:
            matched_id, has_matched = cls._match(fake_id, gender)

            if CAN_MATCH_ONLINE and not matched_id:
                time_now = int(time.time())
                if time_now - int(start_tm) >= 10:
                    matched_id, has_matched = cls._match_online(fake_id, gender)
        if not matched_id:
            return u'please try again', False

        if not has_matched:  # has_matched 上次已经匹配过 重复调用接口
            # 减少今日剩余次数
            cls._decr_match_left(user_id)

            other_user_id = cls._uid_by_fake_id(matched_id)
            if other_user_id and not CAN_MATCH_ONLINE:
                cls._decr_match_left(other_user_id)
        tips, status = cls.get_tips()
        res = {
            'matched_fake_id': matched_id,
            'tips': tips
        }
        res.update(cls.anoy_user_info(matched_id))
        return res, True

    @classmethod
    def get_times_left(cls, user_id):
        msg, status = cls._match_left_verify(user_id)
        times = 0
        if status:
            times = msg
        return {
            'wording': GlobalizationService.get_region_word('time_left') % times,
            'times': times if times < cls.MAX_TIMES/2 else cls.FAKE_MAX_TIME
            }

    @classmethod
    def _uid_by_fake_id(cls, fake_id):
        return redis_client.get(cls.TYPE_FAKE_ID_UID.format(fake_id=fake_id))

    @classmethod
    def _batch_uids_by_fake_id(cls, fake_ids):
        return redis_client.mget([cls.TYPE_FAKE_ID_UID.format(fake_id=_) for _ in fake_ids])

    @classmethod
    def _fakeid_by_uid(cls, user_id):
        return redis_client.get(cls.TYPE_UID_FAKE_ID.format(user_id=user_id))

    @classmethod
    def _other_fakeid_byfake_id(cls, fake_id):
        return redis_client.get(cls.TYPE_MATCHED.format(fake_id=fake_id))

    @classmethod
    def anoy_like(cls, user_id):
        fake_id = cls._fakeid_by_uid(user_id)
        if not fake_id:
            return u'you have no match to quit', False
        other_fake_id = cls._other_fakeid_byfake_id(fake_id)
        if not other_fake_id or not cls._in_match(fake_id, other_fake_id):
            return u'your are not in match', False
        redis_client.set(cls.TYPE_FAKE_LIKE.format(fake_id=fake_id), other_fake_id, cls.MATCH_INT)
        like_eachother = False
        if redis_client.get(cls.TYPE_FAKE_LIKE.format(fake_id=other_fake_id)) == fake_id:
            like_eachother = True
            FollowService.follow_eachother(cls._uid_by_fake_id(fake_id), cls._uid_by_fake_id(other_fake_id))
        return {'like_eachother': like_eachother}, True

    @classmethod
    def clean_pools(cls):
        wait_buff = 2
        for g in GENDERS:
            from ..key import REDIS_ANOY_GENDER_ONLINE_REGION
            int_time = time.time()
            judge_time = int_time - cls.MATCH_WAIT
            for region in GlobalizationService.LOC_REGION.values():
                from flask import current_app, request, Flask
                app = Flask(__name__)
                from werkzeug.test import EnvironBuilder
                ctx = app.request_context(EnvironBuilder('/', 'http://localhost/').get_environ())
                ctx.push()
                request.region = region
                to_rem = redis_client.zrangebyscore(cls.MATCH_KEY_BY_REGION_GENDER(g), 0, judge_time - wait_buff, 0, cls.MAX_CHOOSE_NUM)
                to_rem += redis_client.zrangebyscore(cls.ACCELERATE_KEY_BY_TYPE_REGION_GENDER(cls.MATCH_TYPE, g), 0, judge_time - wait_buff, 0, cls.MAX_CHOOSE_NUM)
                for el in to_rem:
                    cls._destroy_fake_id(el)
                    print "match pool fake_id: %s destoryed" % el
                to_rem_check = redis_client.zrangebyscore(cls.TYPE_ANOY_CHECK_POOL.format(gender=g), 0,  int_time - cls.MATCH_INT - wait_buff, 0, cls.MAX_CHOOSE_NUM)
                for el in to_rem + to_rem_check:
                    cls._destroy_fake_id(el, False)
                    print "check pool fake_id: %s destoryed" % el

    @classmethod
    def judge(cls, user_id, judge):
        fake_id = cls._fakeid_by_uid(user_id)
        other_fakeid = redis_client.get(cls.TYPE_MATCHED.format(fake_id=fake_id))
        if not other_fakeid:
            return NOT_IN_MATCH, False
        redis_key = cls.TYPE_JUDGE_LOCK.format(fake_id=fake_id)
        lock = redis_client.setnx(redis_key, 1)
        redis_client.expire(redis_key, cls.MATCH_INT)
        if not lock:
            return u'you have judged', False
        if not judge in User.JUDGES:
            return u'judge must be one of %s' % ','.join(User.JUDGES)
        other_user_id = cls._uid_by_fake_id(other_fakeid)
        user = User.get_by_id(other_user_id)
        user.add_judge(judge)
        return None, True


    @classmethod
    def quit_match(cls, user_id):   # should delete match pair
        fake_id = cls._fakeid_by_uid(user_id)
        if not fake_id:
            return None, True
            # return u'you have no match to quit', False
        # if cls._uid_by_fake_id(fake_id) != user_id:
        #     return u'you are not authorized to quit', False
        cls._delete_match(fake_id)
        return None, True
        # if possible to reset pwd

    @classmethod
    def add_time(cls, user_id):
        cls._incr_match_left(user_id)
        return None, True

    @classmethod
    def _is_accelerate(cls, user_id):
        key = REDIS_ACCELERATE_CACHE.format(user_id=user_id)
        if not redis_client.get(key):
            return False
        return True

    @classmethod
    def get_queue_num(cls, user_id, is_accelerated=False):
        MAX_QUEUE_NUM = 100
        # is_accelerated = cls._is_accelerate(user_id)
        fake_id = cls._fakeid_by_uid(user_id)
        judge_time = cls.get_judge_time()
        if not fake_id:
            return MAX_QUEUE_NUM
        gender = UserService.get_gender(user_id)
        if is_accelerated:
            rank = redis_client.zrank(cls.ACCELERATE_KEY_BY_TYPE_REGION_GENDER(cls.MATCH_TYPE, gender), fake_id)
            return rank if rank is not None else redis_client.zcount(cls.ACCELERATE_KEY_BY_TYPE_REGION_GENDER(cls.MATCH_TYPE, gender), judge_time, MAX_TIME)
        rank = redis_client.zrank(cls.MATCH_KEY_BY_REGION_GENDER(gender), fake_id)
        if rank is None:
            rank = cls.get_anoy_count(gender)
        return redis_client.zcount(cls.ACCELERATE_KEY_BY_TYPE_REGION_GENDER(cls.MATCH_TYPE, gender), judge_time, MAX_TIME) + rank

    @classmethod
    def accelerate_info(cls, user_id):
        is_accelerate = cls._is_accelerate(user_id)
        queue_num = cls.get_queue_num(user_id, is_accelerate)
        # if cls._is_accelerate(user_id):
        #     queue_num = 1
        if queue_num < 3:
            wait_time = 1
        elif queue_num < 8:
            wait_time = 2
        else:
            wait_time = 3
        return {
            "is_accelerate": is_accelerate,
            "queue_number": queue_num,
            "wait_time": wait_time,
            "queue_info": GlobalizationService.get_region_word('queue_inform') % (queue_num, wait_time)
        }, True

    @classmethod
    def accelerate(cls, user_id):
        key = REDIS_ACCELERATE_CACHE.format(user_id=user_id)
        redis_client.set(key, 1, ONE_DAY)
        fake_id = cls._fakeid_by_uid(user_id)
        gender = UserService.get_gender(user_id)
        old_time = redis_client.zscore(cls.MATCH_KEY_BY_REGION_GENDER(gender), fake_id)
        if old_time:
            redis_client.zrem(cls.MATCH_KEY_BY_REGION_GENDER(gender), fake_id)
        else:
            old_time = int(time.time())
        redis_client.zadd(cls.ACCELERATE_KEY_BY_TYPE_REGION_GENDER(cls.MATCH_TYPE, gender), {fake_id: old_time})
        return cls.accelerate_info(user_id), True
