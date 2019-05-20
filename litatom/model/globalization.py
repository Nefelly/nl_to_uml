# coding: utf-8
import datetime
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)


class RegionWord(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    region = StringField(required=True)
    tag = StringField(required=True)
    word = StringField(required=True)
    add_user = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    TAG_REGION_WORD = {
        'time_left': {
            'vi': u'Còn lại %s lần',
            'th': u'เหลือ %s ครั้ง',
            'en': u'%s times left'
        },
        'anoy_match_msg': {
            'vi': u'Trò chuyện 180 giây, thích nhau mở khóa giới hạn trò chuyện',
            'th': u'180 วินาที กดไลค์กันและกัน เพื่อคุยกันแบบไม่จำกัดเวลา',
            'en': u'180s chat time，Like each other unlock unlimited chats'
        },
        'voice_match_msg': {
            'vi': u'Trò chuyện 180 giây, thích nhau mở khóa giới hạn trò chuyện',
            'th': u'180 วินาที กดไลค์กันและกัน เพื่อคุยกันแบบไม่จำกัดเวลา',
            'en': u'180s chat time，Like each other unlock unlimited chats'
        },
        'like_feed': {
            'vi': u'Thích bài viết của bạn',
            'th': u'ถูกใจโพสของคุณ',
            'en': u'liked your feed'
        },
        'banned_warn': {
            'vi': u'Hệ thống của chúng tôi thông báo tài khoản của bạn có hành vi không phù hợp. Bạn bị hạn chế cho đến %s. Hãy cư xử văn minh trong cuộc trò chuyện của bạn. Hãy liên hệ với nhóm dịch vụ khách hàng của chúng tôi nếu là báo cáo sai',
            'th': u'ระบบของเราสังเกตเห็นพฤติกรรมที่ไม่เหมาะสมในบัญชีของคุณ คุณถูกจำกัด จนถึง %s หรือ ติดต่อทีมบริการลูกค้าของเรา',
            'en': u'Our system has noticed inappropriate behavior on your account. You’ve been restricted until %s. In the future please keep your chats positive. If you believe you’ve been incorrectly flagged, you can contact our customer service team. '
        },
        'reply_comment': {
            'vi': u'Trả lời bài viết của bạn',
            'th': u'ตอบกลับโพสของคุณ',
            'en': u'reply on your comment'
        },
        'reply_feed': {
            'vi': u'Trả lời bài viết của bạn',
            'th': u'ตอบกลับโพสของคุณ',
            'en': u'reply on your feed'
        },
        'start_follow': {
            'vi': u'Bắt đầu theo dõi bạn',
            'th': u'เริ่มติดตามคุณ',
            'en': u'started following you'
        },
        'other_ban_inform': {
            'vi': u'Báo cáo của bạn về người dùng %s đã được giải quyết. Tài khoản của %s đã bị vô hiệu hóa. Cảm ơn bạn đã ủng hộ cộng đồng Lit',
            'th': u'รายงานของคุณเกี่ยวกับผู้ใช้ %s ได้รับการพิจารณา บัญชีของ %s ถูกปิดการใช้งาน ขอบคุณสำหรับการรายงาน',
            'en': u"Your report on the user xxx  has been settled. %s's account is disabled. Thank you for your support of the Lit community"
        }
    }

    @classmethod
    def add_or_mod(cls, region, tag, word):
        obj = cls.objects(region=region, tag=tag).first()
        if not obj:
            obj = cls()
        obj.region = region
        obj.tag = tag
        obj.word = word
        obj.save()
        return True

    @classmethod
    def word_by_region_tag(cls, region, tag):
        return cls.TAG_REGION_WORD.get(tag, {}).get(region, '')
        obj = cls.objects(region=region, tag=tag).first()
        if obj:
            return obj.word
        return ''

