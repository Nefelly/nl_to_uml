# coding: utf-8
from flask import Blueprint
from . import endpoint

__all__ = ['blueprint']

blueprint = b = Blueprint('api_v1', __name__)

# lit
b.add_url_rule('/lit/test', 'lit-test', endpoint.test.test)
b.add_url_rule('/lit/hello', 'lit-hello', endpoint.test.hello)

# 验证码
b.add_url_rule('/lit/get_sms_code', 'get-sms-code', endpoint.sms_code.get_sms_code, methods=['POST'])

# user
b.add_url_rule('/lit/user/phone_login', 'user-phone-login', endpoint.user.phone_login, methods=['POST'])
b.add_url_rule('/lit/user/google_login', 'user-google-login', endpoint.user.google_login, methods=['POST'])
b.add_url_rule('/lit/user/facebook_login', 'user-facebook-login', endpoint.user.facebook_login, methods=['POST'])
b.add_url_rule('/lit/user/verify_nickname', 'user-verify-nickname', endpoint.user.verify_nickname)
b.add_url_rule('/lit/user/info', 'user-update-info', endpoint.user.update_info, methods=['POST'])
b.add_url_rule('/lit/user/<target_user_id>', 'user-get-info', endpoint.user.get_user_info)
b.add_url_rule('/lit/user/avatars', 'user-get-avatars', endpoint.user.get_avatars)
b.add_url_rule('/lit/user/info_by_huanxin', 'user-info-by-huanxin', endpoint.user.user_info_by_huanxinids, methods=['POST'])
b.add_url_rule('/lit/user/messages', 'user-messages', endpoint.user.user_messages)
b.add_url_rule('/lit/user/read_message/<message_id>', 'user-message-read', endpoint.user.read_message)
b.add_url_rule('/lit/user/firebase_token', 'user-firebase-token', endpoint.user.register_firebase, methods=['POST'])
b.add_url_rule('/lit/user/firebase_push', 'user-firebase-push', endpoint.user.firebase_push, methods=['POST'])
b.add_url_rule('/lit/user/query_online', 'user-query-online', endpoint.user.query_online, methods=['POST'])
b.add_url_rule('/lit/user/search', 'user-search', endpoint.user.search_user)

# admin
b.add_url_rule('/lit/admin/index', 'admin-index', endpoint.admin.index)
b.add_url_rule('/lit/admin/admin_feeds', 'admin-admin-feeds', endpoint.admin.feeds_square_html)
b.add_url_rule('/lit/admin/admin_hq', 'admin-admin-hq', endpoint.admin.feeds_hq_html)
b.add_url_rule('/lit/admin/login', 'admin-login', endpoint.admin.login, methods=['POST'])
b.add_url_rule('/lit/admin/hello', 'admin-hello', endpoint.admin.hello)
b.add_url_rule('/lit/admin/query_reports', 'admin-query_reports', endpoint.admin.query_reports)
b.add_url_rule('/lit/admin/ban/<report_id>', 'admin-ban', endpoint.admin.ban_user)
b.add_url_rule('/lit/admin/ban_user_by_feed/<feed_id>', 'admin-ban_by_feed', endpoint.admin.ban_user_by_feed)
b.add_url_rule('/lit/admin/unban', 'admin-unban', endpoint.admin.unban)
b.add_url_rule('/lit/admin/reject/<report_id>', 'admin-reject', endpoint.admin.reject)
b.add_url_rule('/lit/admin/feeds_square', 'admin-feed-square', endpoint.admin.feeds_square_for_admin)
b.add_url_rule('/lit/admin/add_hq/<feed_id>', 'admin-add-hq', endpoint.admin.add_hq)
b.add_url_rule('/lit/admin/remove_from_hq/<feed_id>', 'admin-remove-from-hq', endpoint.admin.remove_from_hq)
b.add_url_rule('/lit/admin/delete_feed/<feed_id>', 'admin-delete-feed', endpoint.admin.delete_feed)
b.add_url_rule('/lit/admin/change_loc', 'admin-change-loc', endpoint.admin.change_loc)
b.add_url_rule('/lit/admin/change_avatar', 'admin-change-avatar', endpoint.admin.change_avatar)
b.add_url_rule('/lit/admin/upload_apk', 'admin-upload_apk', endpoint.admin.upload_apk, methods=['POST'])
b.add_url_rule('/lit/admin/msg_to_region', 'admin-to-region', endpoint.admin.msg_to_region, methods=['POST'])
b.add_url_rule('/lit/admin/send_message', 'admin-send_message', endpoint.admin.send_message_html)
b.add_url_rule('/lit/admin/batch_insert', 'admin-batch_insert', endpoint.admin.batch_insert_html)
b.add_url_rule('/lit/admin/batch_insert_act', 'admin-batch_insert_act', endpoint.admin.batch_insert, methods=['POST'])
b.add_url_rule('/lit/admin/download_phone', 'admin-download_phone', endpoint.admin.download_phone)
b.add_url_rule('/lit/admin/mail_alert', 'admin-mail-alert', endpoint.admin.mail_alert, methods=['POST'])
b.add_url_rule('/lit/admin/stat_items', 'admin-stat_items', endpoint.admin.stat_items)

# 图片
b.add_url_rule('/lit/image/upload', 'image-upload', endpoint.oss.upload_image_from_file, methods=['POST'])
# b.add_url_rule('/lit/image/<fileid>', 'get-image', endpoint.oss.get_image)
b.add_url_rule('/lit/image/<fileid>', 'get-image', endpoint.oss.get_image)
b.add_url_rule('/lit/simage/<fileid>', 'get-simage', endpoint.oss.get_simage)
b.add_url_rule('/lit/audio/upload', 'audio-upload', endpoint.oss.upload_audio_from_file, methods=['POST'])
b.add_url_rule('/lit/audio/<fileid>', 'get-audio', endpoint.oss.get_audio)
b.add_url_rule('/lit/mp3audio/<fileid>', 'get-mp3audio', endpoint.oss.get_audio_mp3)

# home
b.add_url_rule('/lit/home/online_user_count', 'home-online-user-count', endpoint.home.online_user_count)
b.add_url_rule('/lit/home/online_users', 'home-online-users', endpoint.home.online_users)
b.add_url_rule('/lit/home/wording', 'home-wordings', endpoint.home.get_wording)
b.add_url_rule('/lit/home/report', 'home-report', endpoint.home.report, methods=['POST'])
b.add_url_rule('/lit/home/report/<report_id>', 'home-report-info', endpoint.home.report_info)
b.add_url_rule('/lit/home/feedback', 'home-feedback', endpoint.home.feedback, methods=['POST'])
b.add_url_rule('/lit/home/feedback/<feedback_id>', 'home-feedback-info', endpoint.home.feedback_info)
b.add_url_rule('/lit/home/track', 'home-track-chat', endpoint.home.track_chat, methods=['POST'])
b.add_url_rule('/lit/home/track_action', 'home-track-action', endpoint.home.track_action, methods=['POST'])
b.add_url_rule('/lit/home/track_action', 'home-action-info', endpoint.home.action_by_user_id)
b.add_url_rule('/lit/home/privacy', 'home-privacy', endpoint.home.privacy)
b.add_url_rule('/lit/home/rules', 'home-rules', endpoint.home.rules)
b.add_url_rule('/lit/home/index', 'home-index', endpoint.home.index)
b.add_url_rule('/lit/home/check_version', 'home-check-version', endpoint.home.check_version)
b.add_url_rule('/lit/home/settings', 'home-setting', endpoint.home.settings)
b.add_url_rule('/lit/home/user_filters', 'home-user-filter', endpoint.home.online_filter, methods=['POST'])
b.add_url_rule('/lit/home/first_start', 'home-first-start', endpoint.home.first_start)
b.add_url_rule('/lit/home/get_filters', 'home-get-filter', endpoint.home.get_online_filter)
b.add_url_rule('/lit/home/download', 'home-download', endpoint.home.download_app)
b.add_url_rule('/lit/home/upload_address_list', 'home-upload_address_list', endpoint.home.upload_address_list, methods=['POST'])
b.add_url_rule('/lit/home/address_list', 'home-get_address_list', endpoint.home.get_address_list)

# huanxin
b.add_url_rule('/lit/huanxin/<target_user_id>', 'huanxin-get-info', endpoint.huanxin.get_user_info)

# activity
b.add_url_rule('/lit/activity/palm/query', 'activity-palm-query', endpoint.activity.palm_query)
b.add_url_rule('/lit/activity/palm/share', 'activity-palm-share', endpoint.activity.share_info)
b.add_url_rule('/lit/activity/palm/times_left', 'activity-palm-times-left', endpoint.activity.times_left)

# anoy_match
b.add_url_rule('/lit/anoy_match/get_fakeid', 'anoy-match-create-fakeid', endpoint.anoy_match.get_fakeid)
b.add_url_rule('/lit/anoy_match/anoy_match', 'anoy-match-anoy-match', endpoint.anoy_match.anoy_match)
b.add_url_rule('/lit/anoy_match/anoy_like', 'anoy-match-anoy-like', endpoint.anoy_match.anoy_like)
b.add_url_rule('/lit/anoy_match/quit_match', 'anoy-match-quit-match', endpoint.anoy_match.quit_match)
b.add_url_rule('/lit/anoy_match/times_left', 'anoy-match-times-left', endpoint.anoy_match.match_times_left)
b.add_url_rule('/lit/anoy_match/tips', 'anoy-match-tips', endpoint.anoy_match.get_tips)
b.add_url_rule('/lit/anoy_match/judge', 'anoy-match-judge', endpoint.anoy_match.anoy_judge, methods=['POST'])
b.add_url_rule('/lit/anoy_match/video_list', 'anoy-match-video-list', endpoint.anoy_match.video_list)
b.add_url_rule('/lit/anoy_match/video_info_list', 'anoy-match-video-info-list', endpoint.anoy_match.video_info_list)
b.add_url_rule('/lit/anoy_match/video/<vid>', 'anoy-match-update-video', endpoint.anoy_match.update_video, methods=['POST'])
b.add_url_rule('/lit/anoy_match/add_time_by_ad', 'anoy-match-add-time-by-ad', endpoint.anoy_match.add_time_by_ad, methods=['POST'])
b.add_url_rule('/lit/anoy_match/accelerate_by_ad', 'anoy-match-accelerate-by-ad', endpoint.anoy_match.accelerate_by_ad, methods=['POST'])
b.add_url_rule('/lit/anoy_match/accelerate_info', 'anoy-match-accelerate-info', endpoint.anoy_match.get_accelerate_info)


# debug
b.add_url_rule('/lit/debug/redis_status', 'debug-redis-status', endpoint.debug.redis_status)
b.add_url_rule('/lit/debug/batch_create_login', 'debug-batch-create-login', endpoint.debug.batch_create_login)
b.add_url_rule('/lit/debug/batch_anoy_match_start', 'debug-batch-anoy-match-start', endpoint.debug.batch_anoy_match_start)
b.add_url_rule('/lit/debug/query_region', 'debug-query-region', endpoint.debug.query_region)
b.add_url_rule('/lit/debug/test_func', 'debug-test_func', endpoint.debug.test_func)
b.add_url_rule('/lit/debug/chat_msg', 'debug-chat-msg', endpoint.debug.chat_msg)
b.add_url_rule('/lit/debug/user_info', 'debug-user_info', endpoint.debug.user_info)
b.add_url_rule('/lit/debug/register_yesterday', 'debug-register_yesterday', endpoint.debug.change_register_to_yes)
b.add_url_rule('/lit/debug/delete_matched_record', 'debug-del_match_before', endpoint.debug.del_match_before)
b.add_url_rule('/lit/debug/delete_online_matched_record', 'debug-online_del_match_status', endpoint.debug.online_del_match_status)
b.add_url_rule('/lit/debug/set_times_to1', 'debug-set-times-to1', endpoint.debug.set_left_times_to_1)


# feed
b.add_url_rule('/lit/feed/create', 'feed-create-feed', endpoint.feed.create_feed, methods=['POST'])
b.add_url_rule('/lit/feed/view/<other_user_id>', 'feed-user-feeds', endpoint.feed.user_feeds)
b.add_url_rule('/lit/feed/following_feeds', 'feed-following-feeds', endpoint.feed.user_following_feeds)
b.add_url_rule('/lit/feed/square', 'feed-square-feeds', endpoint.feed.square_feeds)
b.add_url_rule('/lit/feed/hq', 'feed-hq-feeds', endpoint.feed.hq_feeds)
b.add_url_rule('/lit/feed/like/<feed_id>', 'feed-like-feed', endpoint.feed.like_feed)
b.add_url_rule('/lit/feed/delete/<feed_id>', 'feed-delete-feed', endpoint.feed.delete_feed)
b.add_url_rule('/lit/feed/comment/<feed_id>', 'feed-comment-feed', endpoint.feed.comment_feed, methods=['POST'])
b.add_url_rule('/lit/feed/del_comment/<comment_id>', 'feed-comment-delete', endpoint.feed.del_comment)
b.add_url_rule('/lit/feed/comment/<feed_id>', 'feed-feed-comments', endpoint.feed.feed_comments)
b.add_url_rule('/lit/feed/info/<feed_id>', 'feed-feed-info', endpoint.feed.feed_info)

# user_relations
b.add_url_rule('/lit/block/<other_user_id>', 'block', endpoint.user_relations.block)
b.add_url_rule('/lit/unblock/<other_user_id>', 'unblock', endpoint.user_relations.unblock)
b.add_url_rule('/lit/blocks', 'blocks', endpoint.user_relations.blocks)
b.add_url_rule('/lit/follow/<other_user_id>', 'follow', endpoint.user_relations.follow)
b.add_url_rule('/lit/unfollow/<other_user_id>', 'unfollow', endpoint.user_relations.unfollow)
b.add_url_rule('/lit/following', 'following', endpoint.user_relations.following)
b.add_url_rule('/lit/follower', 'follower', endpoint.user_relations.follower)

b.add_url_rule('/lit/ad/times_left', 'ad-times-left', endpoint.ad.times_left)

# voice_chat
# b.add_url_rule('/lit/voice_chat/invite/<target_user_id>', 'voice_chat-invite', endpoint.voice_chat.invite)
# b.add_url_rule('/lit/voice_chat/finish', 'finish_chat', endpoint.voice_chat.finish_chat)
# b.add_url_rule('/lit/voice_chat/accept/<target_user_id>', 'voice_chat-accept', endpoint.voice_chat.accept)
# b.add_url_rule('/lit/voice_chat/cancel', 'cancel_chat', endpoint.voice_chat.cancel)
# b.add_url_rule('/lit/voice_chat/reject/<target_user_id>', 'voice_chat-reject', endpoint.voice_chat.reject)