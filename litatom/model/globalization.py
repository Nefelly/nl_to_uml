# coding: utf-8
import datetime
import json
from mongoengine import (
    BooleanField, 
    DateTimeField, 
    Document, 
    IntField, 
    ListField, 
    StringField, 
)
from ..util import is_json


class RegionWord(Document):
    meta = {
        'strict': False, 
        'alias': 'db_alias'
    }

    region = StringField(required=True)
    tag = StringField(required=True)
    word = StringField(required=True)
    add_user = StringField(required=False)
    create_time = DateTimeField(required=True,  default=datetime.datetime.now)

    TAG_REGION_WORD = {
        'time_left': {
            'vi': u'Còn lại %s lần', 
            'th': u'เหลือ %s ครั้ง', 
            'en': u'%s times left', 
            'id': u'%s kali lagi', 
            'india': u'%s times left',
            'ko': u'%s회 남았습니다',
            'ja': u'%s回残り',
        },
        'unlimited_time': {
            'vi': u'Không giới hạn số lần',
            'th': u'ไม่จำกัดจำนวนครั้ง',
            'en': u'unlimited times',
        },
        'anoy_match_msg': {
            'vi': u'Trò chuyện 180 giây,  thích nhau mở khóa giới hạn trò chuyện', 
            'th': u'180 วินาที กดไลค์กันและกัน เพื่อคุยกันแบบไม่จำกัดเวลา', 
            'en': u'180s chat time，Like each other unlock unlimited chats', 
            'india': u'180s chat time，Like each other unlock unlimited chats', 
            'id': u'waktu mengobrol 180 detik,  Sukai satu sama lain untuk mengobrol tanpa batasan waktu.',
            'ko': u'180초의 채팅시간,서로”좋아요” 누르면 무제한 대화 할 수 있다.',
            'ja': u'180秒間のチャット。相手にいいねして制限なしチャットを始める',
        }, 
        'voice_match_msg': {
            'vi': u'7 phút trò chuyện,  thích nhau mở khóa trò chuyện không giới hạn.', 
            'th': u'7 นาทีแชท กดไลค์กันและกัน เพื่อคุยแบบไม่จำกัดเวลา', 
            'en': u'7mins to chat，Like each other unlock unlimited chats.', 
            'india': u'7mins to chat，Like each other unlock unlimited chats.', 
            'id': u'waktu 7 menit untuk mengobrol,  Sukai satu sama lain untuk ngobrol tanpa batasan waktu',
            'ko': u'7분동안대화하고,서로 “좋아요” 하면 무제한 채팅잠금해제',
            'ja': u'7分間のボイスチャット。お互いに「いいね」して制限なしのチャットへ',
            #   'vi': u'It’s more easier for you to have a voice match at night (9.pm~12.pm)', 
            #   'th': u'ช่วงเวลาสุดสนุกของการสุ่มโทร ระหว่างเวลา 21.00 - 00.00 น. ทุกวัน', 
            #   'en': u'It’s more easier for you to have a voice match at night (9.pm~12.pm)', 
            #   'id': u'pada jam 9-12 malam akan lebih mudah bagi Anda untuk melakukan voice match'
        }, 
        'voice_top_wording': {
            'vi': u'Bây giờ chúng ta là bạn,  thưởng thức cuộc trò chuyện không giới hạn', 
            'th': u'เป็นเพื่อนกันแล้ว ขอให้สนุกไปกับการคุยแบบไม่จำกัดเวลา', 
            'en': u'you are friends now,  enjoy unlimited chats.', 
            'india': u'you are friends now,  enjoy unlimited chats.', 
            'id': u'kini Anda telah berteman,  nikmati chat tanpa batasan waktu',
            'ko': u'친구 추가되었습니다. 무제한 채팅 즐기세요',
            'ja': u'今は友達です。制限なしのチャットを楽しんで！	',
        }, 
        'like_feed': {
            'vi': u'Thích bài viết của bạn', 
            'th': u'ถูกใจโพสของคุณ', 
            'en': u'liked your feed', 
            'india': u'liked your feed', 
            'id': u'menyukai laman Anda',
            'ko': u'당신의 feed를 좋아했다',
            'ja': u'あなたのフィードにいいね',
        }, 
        'banned_warn': {
            'vi': u'Hệ thống của chúng tôi thông báo tài khoản của bạn có hành vi không phù hợp. Bạn bị hạn chế cho đến %s. Hãy cư xử văn minh trong cuộc trò chuyện của bạn. Hãy liên hệ với nhóm dịch vụ khách hàng của chúng tôi nếu là báo cáo sai', 
            'th': u'ระบบของเราสังเกตเห็นพฤติกรรมที่ไม่เหมาะสมในบัญชีของคุณ คุณถูกจำกัด จนถึง %s หรือ ติดต่อทีมบริการลูกค้าของเรา', 
            'en': u'Our system has noticed inappropriate behavior on your account. You’ve been restricted until %s. In the future please keep your chats positive. If you believe you’ve been incorrectly flagged,  you can contact our customer service team. ', 
            'india': u'Our system has noticed inappropriate behavior on your account. You’ve been restricted until %s. In the future please keep your chats positive. If you believe you’ve been incorrectly flagged,  you can contact our customer service team. ', 
            'id': u'Sistem kami mendeteksi perilaku yang kurang pantas pada akun Anda. Anda tidak dapat menggunakan aplikasi s/d %s. Mohon menjaga chat Anda dengan perilaku yang positif. Jika Anda merasa tidak melakukan hal berikut,  Anda dapat menghubungi tim kami.',
            'ko': u'나의 계좌에서 부적절한 행동을 알아챘습니다. %s까지 계좌 제한되셨습니다. 앞으로는 대화 내용을 긍정적으로 유지하세요. 플래그가 잘못 표시되었다고 생각하면고객 서비스 팀에 문의하십시오.',
            'ja': u'あなたのアカウントに不適切な行為を発見した。%sまでに制限する。今後は不正行為がないようにご注意ください。攻撃的な報告と思う場合、litatomwang@gmail.comまでご連絡ください。',
        },
        'reply_comment': {
            'vi': u'Trả lời bài viết của bạn', 
            'th': u'ตอบกลับโพสของคุณ', 
            'en': u'reply on your comment', 
            'india': u'reply on your comment', 
            'id': u'balas pada komentar Anda',
            'ko': u'나의 댓글에 답하기',
            'ja': u'コメントに返事',
        }, 
        'reply_feed': {
            'vi': u'Trả lời bài viết của bạn', 
            'th': u'ตอบกลับโพสของคุณ', 
            'en': u'reply on your feed', 
            'india': u'reply on your feed', 
            'id': u'balas pada laman Anda',
            'ko': u'나의 Feed에 답하기',
            'ja': u'投稿に返事',
        }, 
        'start_follow': {
            'vi': u'Bắt đầu theo dõi bạn', 
            'th': u'เริ่มติดตามคุณ', 
            'en': u'started following you', 
            'india': u'started following you', 
            'id': u'mulai mengikuti Anda',
            'ko': u'나를 팔로우하기 시작했습니다.',
            'ja': u'フォローを始めた',
        }, 
        'other_ban_inform': {
            'vi': u'Báo cáo của bạn về người dùng %s đã được giải quyết. Tài khoản của %s đã bị vô hiệu hóa. Cảm ơn bạn đã ủng hộ cộng đồng Lit', 
            'th': u'รายงานของคุณเกี่ยวกับผู้ใช้ %s ได้รับการพิจารณา บัญชีของ %s ถูกปิดการใช้งาน ขอบคุณสำหรับการรายงาน', 
            'en': u"Your report on the user %s  has been settled. %s's account is disabled. Thank you for your support of the Lit community", 
            'india': u"Your report on the user %s  has been settled. %s's account is disabled. Thank you for your support of the Lit community", 
            'id': u'Laporan Anda terhadap akun %s telah selesai. Akun %s telah kami nonaktifkan. Terima kasih atas dukungan Anda terhadap Lit community.',
            'ko': u'사용자 %s에 대한 신고가 해결되었습니다. %s의 계정이 비활성화되었습니다.. 항상 lit 커뮤니티를 이용해주셔서 감사합니다. .',
            'ja': u'ユーザー%sに対するご報告は解決済みです。%sのアカウントを禁止しました。Litコミュニティーの維持にご協力いただきありがとうございます。',
        },
        'other_warn_inform':{
            'en': u"Your report on the user %s  has been settled. %s's account is warned. Thank you for your support of the Lit community",
            'id':u"Laporan Anda pada pengguna% s telah diselesaikan. % telah kami peringatkan. Terima kasih atas dukungan Anda terhadap komunitas Litmatch.",
            'vi':u"Báo cáo của bạn về tài khoản %s đã được xử lý. %s đã bị khoá. Cám ơn bạn đã báo cáo đến Litmatch",
            'th':u"การรายงานผู้ใช้%sจากคุณได้รับการจัดการแล้ว s%ได้รับการเตือนแล้ว ขอบคุณสำหรับการรายงานและสนับสนุน litmatch ",

        },
        'app_introduce': {
            'vi': u'Litmatch là ứng dụng kết bạn.', 
            'th': u'Litmatch แอพหรเพื่อนรูปแบบใหม่.', 
            'en': u"Litmatch is an an app for making new friends", 
            'india': u"Litmatch is an an app for making new friends", 
            'id': u'Litmatch adalah aplikasi untuk bertemu dengan teman baru.',
            'ko': u'새 친구를 사귀고 싶으면 Litmatch를 열어주세요.',
            'ja': u'Litmatchは新しい友達を作るアプリです。',
        }, 
        'video_list': {
            'vi': ['5QfXwgkJITA', 'GQ4F9k4USfA', 'xyNNLWSnNPk', 'U4P3djsPU94', 'JbJ5AdZeR14', 'Nk-isYXzUsg', 'XTVWGjWJAdI', 'AiD1a2fFFLw', 'JbJ5AdZeR14', '5QfXwgkJITA'],
            'th': ['ZwcmNkzm7m0', 'fhbxpm8yZWA', 'ReXNvQUURdI', 'ZJNI3vBZvqc', 'ILU9NbWn4t0', 'B8Hu35Qyw5w', 'tBGHuRhU_yk', 'SecLbWBvDP8', 'oHSlO4UQ16o', 'n32PxBLrut4'], 
            'en': ['b-7qGd5jM2s', 'pWAP7fIwGnI', 'XOBGHAQB-wI', 'kJQP7kiw5Fk', 'cBVGlBWQzuc', 'PMhWCD6u4fA', 'lBiRs4wzIhI', 'SecLbWBvDP8', '250rS-RvwlU', 'Y0viP67wNqk'],
            'india': ['b-7qGd5jM2s', 'pWAP7fIwGnI', 'XOBGHAQB-wI', 'kJQP7kiw5Fk', 'cBVGlBWQzuc', 'PMhWCD6u4fA', 'lBiRs4wzIhI', 'SecLbWBvDP8', '250rS-RvwlU', 'Y0viP67wNqk'],
            'id': ['wVH2iWZ1oyU', '9We3pS6aqvA', 'HTj2n52jz94', 'cwrCz2Yl5bw', '_khNMobLZns', 'HBWC9wTk4tQ', 'nQpYHiB0k6k', 'WhVyGGenmQw', 'RHgVhC8ow00', 'PWA5w0Yxco', 'VWH3GDikM9M', 'bo_efYhYU2A']
        },
        'bio': {
            'en': {'newcomer': ['He is a newcomer', 'She is a newcomer'], 'mystierious': ['He is mysterious', 'She is mysterious']},
            'vi': {'newcomer': [u'Anh ấy là thành viên mới', u'Cô ấy là thành viên mới'], 'mystierious': [u'Anh ấy là người bí ẩn', u'Cô ấy là người bí ẩn']},
            'th': {'newcomer': [u'เขาเป็นผู้ใช้งานใหม่', u'เธอเป็นผู้ใช้งานใหม่'], 'mystierious': [u'เขาคือบุคคลลึกลับ', u'เธอคือบุคคลลึกลับ']},
            'ja': {'newcomer': [u'彼は新規ユーザー', u'彼女は新規ユーザー'], 'mystierious': [u'ミステリアスな男子', u'ミステリアスな女子']},
            'id': {'newcomer': [u'Dia pendatang baru', u'Dia pendatang baru'], 'mystierious': [u'Dia misterius', u'Dia misterius']},
        },
        'alert_word': {
            'en': u'Warning,Our system has noticed inappropriate behavior on your account. Please keep positive. If you are warned three times,you will be banned. If you believe you’ve been incorrectly flagged, please send your litmatch name in your email to litatomwang@gmail.com',
            'vi': u'Hệ thống chúng tôi thông báo tài khoản của bạn có hành vi không phù hợp. Hãy cư xử văn minh trong cuộc trò chuyện của bạn. Nếu báo cáo này sai bạn có thể liên lạc với chúng tôi qua email litatomwang@gmail.com',
            'th': u'ระบบของเราสังเกตเห็นพฤติกรรมที่ไม่เหมาะสมในบัญชีของคุณโปรดประพฤติตามความเหมาะสมหากคุณคิดว่าคุณถูกตั้งค่าสถานะไม่ถูกต้อง คุณสามารถติดต่อเราอยู่ที่litatomwang@gmail.com',
        },
        'alert_msg':{
            'en': u'Contains inappropriate information, please modify，If you continue to behave badly, you may be banned',
            'id': u'Memuat informasi yang kurang pantas, mohon perbaiki, jika Anda terus berperilaku demikian, Anda mungkin akan di blokir',
            'vi': u'Nội dung không phù hợp, hãy sữa đổi. Nếu vẫn tiếp tục , tài khoản của bạn có thể bị khoá.',
            'th': u'รวมข้อความที่ไม่เหมาะสม กรุณาแก้ไข ถ้าคุณทำแบบนี้อีก เราจะแบนบัญชีของคุณ',
        },
        'sms_could_not_register': {
            'en': u'Registration of mobile phone is temporarily unavailable. Please register in other ways.',
            'vi': u'Số điện thoại đăng nhập tạm thời không sử dụng được. Vui lòng sử dụng các hình thức đăng nhập khác',
            'th': u'ไม่สามารถลงทะเบียนโทรศัพท์มือถือได้ชั่วคราว กรุณาลงทะเบียนด้วยวิธีอื่น',
        },
        'visit_home': {
            'en': u'visited your profile👣',
            'vi': u'đã ghé thăm tường nhà bạn 👣',
            'th': u'เข้าเยี่ยมชมโปรไฟล์ของคุณ👣',
            'ja': u'があなたのプロフィールを訪問した👣'
        },
        'queue_inform': {
            'en': u'Queuing number %d，Wait about %d minute(s)',
            'vi': u'Đang xếp hàng đợi ở thứ tự %d, vui lòng đợi khoảng %d phút',
            'th': u'กำลังรอ %d คิว ประมาณ %d นาที',
            'ja': u'今は%d番です。%d分間お待ちください。'
        },
        'filter_inform': {
            'en': u'filtering will result in matching and user recommendations',
            'vi': u'Lọc chọn ở mục kết đôi match sẽ có hiệu lực với danh sách người dùng gợi ý ',
            'th': u'การเลือกตัวกรองมีผลต่อการจับคู่และรายชื่อผู้ใช้แนะนำ',
            'ja': u'フィルターはマッチングとおすすめのユーザーリストにある',
            'id': u'Pemfilteran dapat berefek pada rekomendasi user yang diberikan dan match'
        },
        'rate_conversation_diamonds': {
            'en': u'You initiate the conversation too much，Use diamonds to unlock',
            'vi': u'Bạn gửi tin nhắn cho quá nhiều người, dùng kim cương mở',
            'th': u'คุณเริ่มสนทนามากเกินไป ใช้เพชรเพื่อปลดล็อก',
            'id': u'Anda terlalu banyak memulai pembicaraan, gunakan diamond untuk membuka kunci'
        },
        'rate_conversation_stop': {
            'en': u'You initiate the conversation too much today',
            'vi': u'Bạn đã trò chuyện quá nhiều lần trong hôm nay',
            'th': u'วันนี้คุณเริ่มสนทนามากเกินไป',
            'id': u'Anda terlalu banyak memulai pembicaraan hari ini'
        },
        'rate_follow_diamonds': {
            'en': u'You follow too many people，Use diamonds to unlock',
            'vi': u'Bạn đã theo dõi quá nhiều người, dùng kim cương mở khoá',
            'th': u'คุณติดตามคนเยอะเกินไป ใช้เพชรเพื่อปลดล็อก',
            'id': u'Anda mengikuti terlalu banyak orang， gunakan diamond untuk membuka kunci'
        },
        'rate_follow_stop': {
            'en': u'You follow too many people today',
            'vi': u'Bạn theo dõi quá nhiều người trong hôm nay',
            'th': u'วันนี้คุณติดตามคนเยอะเกินไป',
            'id': u'Anda mengikuti terlalu banyak orang hari ini'
        },
        'rate_comment_diamonds': {
            'en': u'You comment too many people，Use diamonds to unlock',
            'vi': u'Bạn bình luận quá nhiều lần, dùng kim cương mở khoá',
            'th': u'คุณคอมเม้นต์ให้คนอื่นมากเกินไป ใช้เพชรเพื่อปลดล็อก',
            'id': u'Anda berkomentar terlalu banyak, gunakan diamond untuk membuka kunci'
        },
        'rate_comment_stop': {
            'en': u'You comment too many people today',
            'vi': u'Bạn bình luận quá nhiều lần trong hôm nay',
            'th': u'ววันนี้คุณคอมเม้นต์ให้คนอื่นมากเกินไป',
            'id': u'Anda berkomentar terlalu banyak hari ini'
        },
        'protected_conversation_diamonds': {
            'en': u'Too many people have chatted with her today. To avoid disturbing her, please use diamond to unlock.',
            'vi': u'Hôm nay có rất nhiều người đến tìm cô ấy nói chuyện, để không ai làm phiền, hãy dùng kim cương để mở cuộc trò chuyện !',
            'th': u'วันนี้มีคนทักเขาหลายคนแล้ว เพื่อไม่ให้เป็นการรบกวนเขามากเกินไป โปรดใช้เพชรเพื่อปลดล็อกการแชท',
            'id': u'Banyak orang yang chat dengannya hari ini, Agar tidak terlalu menganggu, silakan gunakan diamond untuk membuka kunci obrolan.'
        },
        'coummunity_rule': {
            'en': u'"As in any community，there are rules to protect everyone and make sure to have the coolest and safest experience\n\n'
                  u'• Be kind with your new friends 💛\n\n'
                  u'• You can report any inappropriate profile or behavior: our review team will check 😮\n\n• Only use your personal pictures ✌️\n\n'
                  u'• Pictures in underwear or shirtless are not allowed 👮"',
            'vi': u'"Như trong bất kì các cộng đồng nào, các qui tắc này nhằm để người dùng có những trải nghiệm tuyệt vời và an toàn nhất '
                  u'\n\n• Hãy trò chuyện lịch sự với người bạn mới 💛'
                  u'\n\n• Bạn có thể báo cáo bất kỳ tài khoản nào có hành vi không phù hợp: Bộ phận đánh giá của chúng tôi sẽ kiểm tra 😮'
                  u'\n\n• Chỉ có thể dùng hình ảnh của chính mình ✌️'
                  u'\n\n• Hình ảnh trang phục bikini hoặc khoả thân đều không được chấp nhận 👮"',
            'th': u'เช่นเดียวกับในชุมชนต่าง ๆ ที่มีกฎเพื่อคุ้มครองทุกคนและเพื่อให้แน่ใจว่าจะได้รับประสบการณ์ที่สะดวกสบายและปลอดภัยที่สุด •เป็นมิตรกับเพื่อนใหม่ของคุณ💛 '
                  u'\n\n•คุณสามารถรายงานโปรไฟล์หรือพฤติกรรมใด ๆ ที่ไม่เหมาะสมได้ : ทีมตรวจสอบของเราจะทำการตรวจสอบ😮 '
                  u'\n\n•โปรดใช้ภาพจริงของตัวคุณเท่านั้น ️ '
                  u'\n\n•ไม่อนุญาตให้ใช้รูปที่สวมชุดชั้นในหรือโป๊เปลือย',
            'id': u'"Seperti di komunitas mana pun, terdapat aturan-aturan untuk melindungi semua pengguna untuk memastikan pengguna memiliki pengalaman yang menyenangkan dan nyaman'
                  u'\n\n• Bersikap baik pada teman baru Anda 💛'
                  u'\n\n• Anda dapat melaporkan profil atau perilaku yang tidak pantas: tim peninjau kami akan memeriksa 😮'
                  u'\n\n• Hanya gunakan gambar pribadi Anda ✌'
                  u'\n\n• Gambar dengan pakaian dalam atau tanpa pakaian tidak diperbolehkan 👮 "'
        }


    }

    REGION_BENCHMARK = 'en'

    @classmethod
    def is_valid_word(cls, region, tag, word):
        if region == cls.REGION_BENCHMARK:
            return None
        obj = cls.objects(region=cls.REGION_BENCHMARK, tag=tag).first()
        if not obj:
            return u'tag not vailid, please retry later'
        en_word = obj.word
        is_json_en = is_json(en_word)
        is_json_local = is_json(word)
        if is_json_en != is_json_local:
            return u'word json format not meet, please check if your word is json'
        if not is_json_local:
            place_holders = en_word.count('%s')
            if place_holders != word.count('%s'):
                return u'%%s number dismatch, please check'
        return None

    @classmethod
    def add_or_mod(cls,  region,  tag,  word):
        obj = cls.objects(region=region,  tag=tag).first()
        if not obj:
            obj = cls()
        obj.region = region
        obj.tag = tag
        obj.word = word
        obj.save()
        return True

    @classmethod
    def word_by_region_tag(cls,  region,  tag):
        tag_words = cls.TAG_REGION_WORD.get(tag,  {})
        res = tag_words.get(region,  '')
        if not res:
            res = tag_words.get('en', '')
        return res
        # return cls.TAG_REGION_WORD.get(tag,  {}).get(region,  '')
        # obj = cls.objects(region=region,  tag=tag).first()
        # if obj:
        #     return obj.word
        # return ''

    @classmethod
    def get_content(cls, word):
        if is_json(word):
            return json.loads(word)
        return word

    @classmethod
    def adding(cls):
        for tag in cls.TAG_REGION_WORD:
            for region in cls.TAG_REGION_WORD[tag]:
                word = cls.TAG_REGION_WORD[tag][region]
                if not isinstance(word, str):
                    word = json.dumps(word)
                cls.add_or_mod(region, tag, word)

    @classmethod
    def load(cls):
        tag_region_word = {}
        tags = ['time_left', 'anoy_match_msg', 'voice_match_msg', 'voice_top_wording', 'like_feed', 'banned_warn',
                'reply_comment', 'reply_feed', 'start_follow', 'other_ban_inform', 'app_introduce', 'video_list',
                'bio', 'alert_word', 'alert_msg', 'sms_could_not_register']
        for obj in cls.objects():
            region = obj.region
            tag = obj.tag
            word = cls.get_content(obj.word)
            if not tag_region_word.get(tag):
                tag_region_word[tag] = {}
            tag_region_word[tag][region] = word
        cls.TAG_REGION_WORD = tag_region_word

# RegionWord.load()
