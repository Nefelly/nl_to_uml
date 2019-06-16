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
            'en': u'%s times left',
            'id': u'%s kali lagi'
        },
        'anoy_match_msg': {
            'vi': u'Trò chuyện 180 giây, thích nhau mở khóa giới hạn trò chuyện',
            'th': u'180 วินาที กดไลค์กันและกัน เพื่อคุยกันแบบไม่จำกัดเวลา',
            'en': u'180s chat time，Like each other unlock unlimited chats',
            'id': u'waktu mengobrol 180 detik, Sukai satu sama lain untuk mengobrol tanpa batasan waktu.'
        },
        'voice_match_msg': {
            'vi': u'7 phút trò chuyện, thích nhau mở khóa trò chuyện không giới hạn.',
            'th': u'7 นาทีแชท กดไลค์กันและกัน เพื่อคุยแบบไม่จำกัดเวลา',
            'en': u'7mins to chat，Like each other unlock unlimited chats.',
            'id': u'waktu 7 menit untuk mengobrol, Sukai satu sama lain untuk ngobrol tanpa batasan waktu'
        },
        'voice_top_wording': {
            'vi': u'Bây giờ chúng ta là bạn, thưởng thức cuộc trò chuyện không giới hạn',
            'th': u'เป็นเพื่อนกันแล้ว ขอให้สนุกไปกับการคุยแบบไม่จำกัดเวลา',
            'en': u'you are friends now, enjoy unlimited chats.',
            'id': u'kini Anda telah berteman, nikmati chat tanpa batasan waktu'
        },
        'like_feed': {
            'vi': u'Thích bài viết của bạn',
            'th': u'ถูกใจโพสของคุณ',
            'en': u'liked your feed',
            'id': u'menyukai laman Anda'
        },
        'banned_warn': {
            'vi': u'Hệ thống của chúng tôi thông báo tài khoản của bạn có hành vi không phù hợp. Bạn bị hạn chế cho đến %s. Hãy cư xử văn minh trong cuộc trò chuyện của bạn. Hãy liên hệ với nhóm dịch vụ khách hàng của chúng tôi nếu là báo cáo sai',
            'th': u'ระบบของเราสังเกตเห็นพฤติกรรมที่ไม่เหมาะสมในบัญชีของคุณ คุณถูกจำกัด จนถึง %s หรือ ติดต่อทีมบริการลูกค้าของเรา',
            'en': u'Our system has noticed inappropriate behavior on your account. You’ve been restricted until %s. In the future please keep your chats positive. If you believe you’ve been incorrectly flagged, you can contact our customer service team. ',
            'id': u'Sistem kami mendeteksi perilaku yang kurang pantas pada akun Anda. Anda tidak dapat menggunakan aplikasi s/d %s. Mohon menjaga chat Anda dengan perilaku yang positif. Jika Anda merasa tidak melakukan hal berikut, Anda dapat menghubungi tim kami.'
        },
        'reply_comment': {
            'vi': u'Trả lời bài viết của bạn',
            'th': u'ตอบกลับโพสของคุณ',
            'en': u'reply on your comment',
            'id': u'balas pada komentar Anda'
        },
        'reply_feed': {
            'vi': u'Trả lời bài viết của bạn',
            'th': u'ตอบกลับโพสของคุณ',
            'en': u'reply on your feed',
            'id': u'balas pada laman Anda'
        },
        'start_follow': {
            'vi': u'Bắt đầu theo dõi bạn',
            'th': u'เริ่มติดตามคุณ',
            'en': u'started following you',
            'id': u'mulai mengikuti Anda'
        },
        'other_ban_inform': {
            'vi': u'Báo cáo của bạn về người dùng %s đã được giải quyết. Tài khoản của %s đã bị vô hiệu hóa. Cảm ơn bạn đã ủng hộ cộng đồng Lit',
            'th': u'รายงานของคุณเกี่ยวกับผู้ใช้ %s ได้รับการพิจารณา บัญชีของ %s ถูกปิดการใช้งาน ขอบคุณสำหรับการรายงาน',
            'en': u"Your report on the user %s  has been settled. %s's account is disabled. Thank you for your support of the Lit community",
            'id': u'Laporan Anda terhadap akun %s telah selesai. Akun %s telah kami nonaktifkan. Terima kasih atas dukungan Anda terhadap Lit community.'
        },
        'app_introduce': {
            'vi': u'Litmatch là ứng dụng kết bạn.',
            'th': u'Lit Match แอพหรเพื่อนรูปแบบใหม่.',
            'en': u"Litmatch is an an app for making new friends",
            'id': u'Litmatch adalah aplikasi untuk bertemu dengan teman baru.'
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

