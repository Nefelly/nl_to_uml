# coding: utf-8
"""
本文件为各api接口查询阿里云日志服务litatom:litatomstore提供查询条件翻译服务
"""

# lit
ALILOG_TEST = 'request_uri:/api/sns/v1/lit/test AND request_method:GET'
ALILOG_HELLO = 'request_uri:/api/sns/v1/lit/hello AND request_method:GET'

# 验证码
ALILOG_GETSMSCODE = 'request_uri:/api/sns/v1/lit/get_sms_code AND request_method:POST'

# user
ALILOG_USER_PHLOGIN = 'request_uri:/api/sns/v1/lit/user/phone_login AND request_method:POST'
ALILOG_USER_GOLOGIN = 'request_uri:/api/sns/v1/lit/user/google_login AND request_method:POST'
ALILOG_USER_FBLOGIN = 'request_uri:/api/sns/v1/lit/user/facebook_login AND request_method:POST'
ALILOG_USER_VERIFYNNAME = 'request_uri:/api/sns/v1/lit/user/verify_nickname AND request_method:GET'
ALILOG_USER_INFO = 'request_uri:/api/sns/v1/lit/user/info AND request_method:POST'
ALILOG_USER = 'request_uri:/api/sns/v1/lit/user/<target_user_id> AND request_method:GET'
ALILOG_USER_AVATERS = 'request_uri:/api/sns/v1/lit/user/avatars AND request_method:GET'
ALILOG_USER_INFOBYHX = 'request_uri:/api/sns/v1/lit/user/info_by_huanxin AND request_method:POST'
ALILOG_USER_MESSAGES = 'request_uri:/api/sns/v1/lit/user/messages AND request_method:GET'
ALILOG_USER_READMES = 'request_uri:/api/sns/v1/lit/user/read_message/ AND request_method:GET'
ALILOG_USER_FIREBASETK = 'request_uri:/api/sns/v1/lit/user/firebase_token AND request_method:POST'
ALILOG_USER_FIREBASEPS = 'request_uri:/api/sns/v1/lit/user/firebase_push AND request_method:POST'
ALILOG_USER_QUERYOL = 'request_uri:/api/sns/v1/lit/user/query_online AND request_method:POST'
ALILOG_USER_SEARCH = 'request_uri:/api/sns/v1/lit/user/search AND request_method:GET'
ALILOG_USER_ACCOST = 'request_uri:/api/sns/v1/lit/user/accost AND request_method:GET'
ALILOG_USER_CONVERSATION = 'request_uri:/api/sns/v1/lit/user/conversation AND request_method:POST'
ALILOG_USER_CONVERSATIONS = 'request_uri:/api/sns/v1/lit/user/conversations AND request_method:GET'
ALILOG_USER_DELCONVERSATION = 'request_uri:/api/sns/v1/lit/user/del_conversation/ AND request_method:GET'

# account
ALILOG_ACCOUNT_INFO = 'request_uri:/api/sns/v1/lit/account/account_info AND request_method:GET'
ALILOG_ACCOUNT_PRODINFO = 'request_uri:/api/sns/v1/lit/account/products AND request_method:GET'
ALILOG_ACCOUNT_PAYINFORM = 'request_uri:/api/sns/v1/lit/account/pay_inform AND request_method:POST'
ALILOG_ACCOUNT_DEPBYACT = 'request_uri:/api/sns/v1/lit/account/deposit_by_activity AND request_method:POST'
ALILOG_ACCOUNT_BUYPROD = 'request_uri:/api/sns/v1/lit/account/buy_product AND request_method:POST'
ALILOG_ACCOUNT_DIAMONDPROD = 'request_uri:/api/sns/v1/lit/account/diamond_products AND request_method:GET'
ALILOG_ACCOUNT_UNBANBYDIAMOND = 'request_uri:/api/sns/v1/lit/account/unban_by_diamonds/ AND request_method:GET'

# admin
ALILOG_ADMIN_INDEX = 'request_uri:/api/sns/v1/lit/admin/index AND request_method:GET'
ALILOG_ADMIN_ADFEEDS = 'request_uri:/api/sns/v1/lit/admin/admin_feeds AND request_method:GET'
ALILOG_ADMIN_ADHQ = 'request_uri:/api/sns/v1/lit/admin/admin_hq AND request_method:GET'
ALILOG_ADMIN_LOGIN = 'request_uri:/api/sns/v1/lit/admin/login AND request_method:POST'
ALILOG_ADMIN_HELLO = 'request_uri:/api/sns/v1/lit/admin/hello AND request_method:GET'
ALILOG_ADMIN_QUERYREPORTS = 'request_uri:/api/sns/v1/lit/admin/query_reports AND request_method:GET'
ALILOG_ADMIN_BAN = 'request_uri:/api/sns/v1/lit/admin/ban AND request_method:GET'
ALILOG_ADMIN_BANUSERBYFEED = 'request_uri:/api/sns/v1/lit/admin/ban_user_by_feed AND request_method:GET'
ALILOG_ADMIN_UNBAN = 'request_uri:/api/sns/v1/lit/admin/unban AND request_method:GET'
ALILOG_ADMIN_REJECT = 'request_uri:/api/sns/v1/lit/admin/reject/ AND request_method:GET'
ALILOG_ADMIN_FEEDSQUARE = 'request_uri:/api/sns/v1/lit/admin/feeds_square AND request_method:GET'
ALILOG_ADMIN_ADDHQ = 'request_uri:/api/sns/v1/lit/admin/add_hq/ AND request_method:GET'
ALILOG_ADMIN_RMFROMHQ = 'request_uri:/api/sns/v1/lit/admin/remove_from_hq AND request_method:GET'
ALILOG_ADMIN_DELFEED = 'request_uri:/api/sns/v1/lit/admin/delete_feed AND request_method:GET'
ALILOG_ADMIN_CHANGELOC = 'request_uri:/api/sns/v1/lit/admin/change_loc AND request_method:GET'
ALILOG_ADMIN_ADDDIAMOND = 'request_uri:/api/sns/v1/lit/admin/add_diamonds AND request_method:GET'
ALILOG_ADMIN_SETDIAMOND = 'request_uri:/api/sns/v1/lit/admin/set_diamonds AND request_method:GET'
ALILOG_ADMIN_CHANGEAVATER = 'request_uri:/api/sns/v1/lit/admin/change_avatar AND request_method:GET'
ALILOG_ADMIN_UPLOADAPK = 'request_uri:/api/sns/v1/lit/admin/upload_apk AND request_method:POST'
ALILOG_ADMIN_MSGTOREGION = 'request_uri:/api/sns/v1/lit/admin/msg_to_region AND request_method:POST'
ALILOG_ADMIN_SENDMESSAGE = 'request_uri:/api/sns/v1/lit/admin/send_message AND request_method:GET'
ALILOG_ADMIN_BATCHINSERT = 'request_uri:/api/sns/v1/lit/admin/batch_insert AND request_method:GET'
ALILOG_ADMIN_BATCHINSERTACT = 'request_uri:/api/sns/v1/lit/admin/batch_insert_act AND request_method:POST'
ALILOG_ADMIN_DOWNLOADPHONE = 'request_uri:/api/sns/v1/lit/admin/download_phone AND request_method:GET'
ALILOG_ADMIN_MAILALERT = 'request_uri:/api/sns/v1/lit/admin/mail_alert AND request_method:POST'
ALILOG_ADMIN_STATITEMS = 'request_uri:/api/sns/v1/lit/admin/stat_items AND request_method:GET'
ALILOG_ADMIN_JOURNAL = 'request_uri:/api/sns/v1/lit/admin/journal AND request_method:GET'
ALILOG_ADMIN_ADDSTATITEM = 'request_uri:/api/sns/v1/lit/admin/add_stat_item AND request_method:POST'
ALILOG_ADMIN_DELSTATITEM = 'request_uri:/api/sns/v1/lit/admin/delete_stat_item/ AND request_method:GET'
ALILOG_ADMIN_GETOFFICIALFEED = 'request_uri:/api/sns/v1/lit/admin/get_official_feed AND request_method:GET'
ALILOG_ADMIN_ADDTOTOP = 'request_uri:/api/sns/v1/lit/admin/add_to_top AND request_method:GET'
ALILOG_ADMIN_RMFROMTOP = 'request_uri:/api/sns/v1/lit/admin/remove_from_top AND request_method:GET'
ALILOG_ADMIN_OFFICIALFEED = 'request_uri:/api/sns/v1/lit/admin/official_feed AND request_method:GET'
ALILOG_ADMIN_JOURNALCAL = 'request_uri:/api/sns/v1/lit/admin/journal_cal AND request_method:GET'
ALILOG_ADMIN_GETLOG = 'request_uri:/api/sns/v1/lit/admin/get_log AND request_method:GET'
ALILOG_ADMIN_REGIONWORDS = 'request_uri:/api/sns/v1/lit/admin/region_words AND request_method:GET'
ALILOG_ADMIN_ADMINWORDS = 'request_uri:/api/sns/v1/lit/admin/admin_words AND request_method:GET'
ALILOG_ADMIN_BANBYUID = 'request_uri:/api/sns/v1/lit/admin/ban_by_uid AND request_method:GET'
ALILOG_ADMIN_BANREPORTER = 'request_uri:/api/sns/v1/lit/admin/ban_reporter/ AND request_method:GET'
ALILOG_ADMIN_CHANGESETTING = 'request_uri:/api/sns/v1/lit/admin/change_setting AND request_method:POST'
ALILOG_ADMIN_MODSETTING = 'request_uri:/api/sns/v1/lit/admin/mod_setting AND request_method:GET'
ALILOG_ADMIN_MONGOGENCSV = 'request_uri:/api/sns/v1/lit/admin/mongo_gen_csv AND request_method:GET'
ALILOG_ADMIN_MONGOGENCSVPAGE = 'request_uri:/api/sns/v1/lit/admin/mongo_gen_csv_page AND request_method:GET'

# # 图片
# ALILOG_ADMIN_INDEX = 'request_uri:/api/sns/v1/lit/admin/index AND request_method:GET'
# b.add_url_rule('/lit/image/upload', 'image-upload', endpoint.oss.upload_image_from_file, methods=['POST'])
# b.add_url_rule('/lit/image/chat_upload', 'image-upload', endpoint.oss.upload_image_from_file, methods=['POST'])
# # b.add_url_rule('/lit/image/<fileid>', 'get-image', endpoint.oss.get_image)
# b.add_url_rule('/lit/image/<fileid>', 'get-image', endpoint.oss.get_image)
# b.add_url_rule('/lit/simage/<fileid>', 'get-simage', endpoint.oss.get_simage)
# b.add_url_rule('/lit/audio/upload', 'audio-upload', endpoint.oss.upload_audio_from_file, methods=['POST'])
# b.add_url_rule('/lit/audio/<fileid>', 'get-audio', endpoint.oss.get_audio)
# b.add_url_rule('/lit/log/upload', 'log-upload', endpoint.oss.upload_log_from_file, methods=['POST'])
# b.add_url_rule('/lit/log/<fileid>', 'get-log', endpoint.oss.get_log)
# b.add_url_rule('/lit/mp3audio/<fileid>', 'get-mp3audio', endpoint.oss.get_audio_mp3)
#
# # home
# b.add_url_rule('/lit/home/online_user_count', 'home-online-user-count', endpoint.home.online_user_count)
# b.add_url_rule('/lit/home/online_users', 'home-online-users', endpoint.home.online_users)
# b.add_url_rule('/lit/home/wording', 'home-wordings', endpoint.home.get_wording)
# b.add_url_rule('/lit/home/report', 'home-report', endpoint.home.report, methods=['POST'])
# b.add_url_rule('/lit/home/report/<report_id>', 'home-report-info', endpoint.home.report_info)
# b.add_url_rule('/lit/home/feedback', 'home-feedback', endpoint.home.feedback, methods=['POST'])
# b.add_url_rule('/lit/home/feedback/<feedback_id>', 'home-feedback-info', endpoint.home.feedback_info)
# b.add_url_rule('/lit/home/track', 'home-track-chat', endpoint.home.track_chat, methods=['POST'])
# b.add_url_rule('/lit/home/track_action', 'home-track-action', endpoint.home.track_action, methods=['POST'])
# b.add_url_rule('/lit/home/track_action', 'home-action-info', endpoint.home.action_by_user_id)
# b.add_url_rule('/lit/home/privacy', 'home-privacy', endpoint.home.privacy)
# b.add_url_rule('/lit/home/rules', 'home-rules', endpoint.home.rules)
# b.add_url_rule('/lit/home/index', 'home-index', endpoint.home.index)
# b.add_url_rule('/lit/home/check_version', 'home-check-version', endpoint.home.check_version)
# b.add_url_rule('/lit/home/settings', 'home-setting', endpoint.home.settings)
# b.add_url_rule('/lit/home/user_filters', 'home-user-filter', endpoint.home.online_filter, methods=['POST'])
# b.add_url_rule('/lit/home/first_start', 'home-first-start', endpoint.home.first_start)
# b.add_url_rule('/lit/home/get_filters', 'home-get-filter', endpoint.home.get_online_filter)
# b.add_url_rule('/lit/home/download', 'home-download', endpoint.home.download_app)
# b.add_url_rule('/lit/home/upload_address_list', 'home-upload_address_list', endpoint.home.upload_address_list, methods=['POST'])
# b.add_url_rule('/lit/home/address_list', 'home-get_address_list', endpoint.home.get_address_list)
# b.add_url_rule('/lit/home/spam_words', 'home-spam_words', endpoint.home.get_spam_word)
# b.add_url_rule('/lit/home/report_spam', 'home-report_spam', endpoint.home.report_spam, methods=['POST'])
# b.add_url_rule('/lit/home/check_pic', 'home-check_pic', endpoint.home.check_pic, methods=['POST'])
#
# # huanxin
# b.add_url_rule('/lit/huanxin/<target_user_id>', 'huanxin-get-info', endpoint.huanxin.get_user_info)
#
# # activity
# b.add_url_rule('/lit/activity/palm/query', 'activity-palm-query', endpoint.activity.palm_query)
# b.add_url_rule('/lit/activity/palm/share', 'activity-palm-share', endpoint.activity.share_info)
# b.add_url_rule('/lit/activity/palm/times_left', 'activity-palm-times-left', endpoint.activity.times_left)
# b.add_url_rule('/lit/activity/user_share/<share_user_id>', 'activity-user-share', endpoint.activity.user_share)
# b.add_url_rule('/lit/activity/share_static', 'activity-share-static', endpoint.activity.share_static)
#
# # anoy_match
# b.add_url_rule('/lit/anoy_match/get_fakeid', 'anoy-match-create-fakeid', endpoint.anoy_match.get_fakeid)
# b.add_url_rule('/lit/anoy_match/anoy_match', 'anoy-match-anoy-match', endpoint.anoy_match.anoy_match)
# b.add_url_rule('/lit/anoy_match/anoy_like', 'anoy-match-anoy-like', endpoint.anoy_match.anoy_like)
# b.add_url_rule('/lit/anoy_match/quit_match', 'anoy-match-quit-match', endpoint.anoy_match.quit_match)
# b.add_url_rule('/lit/anoy_match/times_left', 'anoy-match-times-left', endpoint.anoy_match.match_times_left)
# b.add_url_rule('/lit/anoy_match/tips', 'anoy-match-tips', endpoint.anoy_match.get_tips)
# b.add_url_rule('/lit/anoy_match/judge', 'anoy-match-judge', endpoint.anoy_match.anoy_judge, methods=['POST'])
# b.add_url_rule('/lit/anoy_match/video_list', 'anoy-match-video-list', endpoint.anoy_match.video_list)
# b.add_url_rule('/lit/anoy_match/video_info_list', 'anoy-match-video-info-list', endpoint.anoy_match.video_info_list)
# b.add_url_rule('/lit/anoy_match/video/<vid>', 'anoy-match-update-video', endpoint.anoy_match.update_video, methods=['POST'])
# b.add_url_rule('/lit/anoy_match/add_time_by_ad', 'anoy-match-add-time-by-ad', endpoint.anoy_match.add_time_by_ad, methods=['POST'])
# b.add_url_rule('/lit/anoy_match/accelerate_by_ad', 'anoy-match-accelerate-by-ad', endpoint.anoy_match.accelerate_by_ad, methods=['POST'])
# b.add_url_rule('/lit/anoy_match/accelerate_info', 'anoy-match-accelerate-info', endpoint.anoy_match.get_accelerate_info)
#
#
# # debug
# b.add_url_rule('/lit/debug/redis_status', 'debug-redis-status', endpoint.debug.redis_status)
# b.add_url_rule('/lit/debug/batch_create_login', 'debug-batch-create-login', endpoint.debug.batch_create_login)
# b.add_url_rule('/lit/debug/batch_anoy_match_start', 'debug-batch-anoy-match-start', endpoint.debug.batch_anoy_match_start)
# b.add_url_rule('/lit/debug/query_region', 'debug-query-region', endpoint.debug.query_region)
# b.add_url_rule('/lit/debug/test_func', 'debug-test_func', endpoint.debug.test_func)
# b.add_url_rule('/lit/debug/chat_msg', 'debug-chat-msg', endpoint.debug.chat_msg)
# b.add_url_rule('/lit/debug/user_info', 'debug-user_info', endpoint.debug.user_info)
# b.add_url_rule('/lit/debug/register_yesterday', 'debug-register_yesterday', endpoint.debug.change_register_to_yes)
# b.add_url_rule('/lit/debug/delete_matched_record', 'debug-del_match_before', endpoint.debug.del_match_before)
# b.add_url_rule('/lit/debug/delete_online_matched_record', 'debug-online_del_match_status', endpoint.debug.online_del_match_status)
# b.add_url_rule('/lit/debug/set_times_to1', 'debug-set-times-to1', endpoint.debug.set_left_times_to_1)
#
#
# # feed
# b.add_url_rule('/lit/feed/create', 'feed-create-feed', endpoint.feed.create_feed, methods=['POST'])
# b.add_url_rule('/lit/feed/view/<other_user_id>', 'feed-user-feeds', endpoint.feed.user_feeds)
# b.add_url_rule('/lit/feed/following_feeds', 'feed-following-feeds', endpoint.feed.user_following_feeds)
# b.add_url_rule('/lit/feed/square', 'feed-square-feeds', endpoint.feed.square_feeds)
# b.add_url_rule('/lit/feed/hq', 'feed-hq-feeds', endpoint.feed.hq_feeds)
# b.add_url_rule('/lit/feed/like/<feed_id>', 'feed-like-feed', endpoint.feed.like_feed)
# b.add_url_rule('/lit/feed/delete/<feed_id>', 'feed-delete-feed', endpoint.feed.delete_feed)
# b.add_url_rule('/lit/feed/comment/<feed_id>', 'feed-comment-feed', endpoint.feed.comment_feed, methods=['POST'])
# b.add_url_rule('/lit/feed/del_comment/<comment_id>', 'feed-comment-delete', endpoint.feed.del_comment)
# b.add_url_rule('/lit/feed/comment/<feed_id>', 'feed-feed-comments', endpoint.feed.feed_comments)
# b.add_url_rule('/lit/feed/info/<feed_id>', 'feed-feed-info', endpoint.feed.feed_info)
#
# # user_relations
# b.add_url_rule('/lit/block/<other_user_id>', 'block', endpoint.user_relations.block)
# b.add_url_rule('/lit/unblock/<other_user_id>', 'unblock', endpoint.user_relations.unblock)
# b.add_url_rule('/lit/blocks', 'blocks', endpoint.user_relations.blocks)
# b.add_url_rule('/lit/follow/<other_user_id>', 'follow', endpoint.user_relations.follow)
# b.add_url_rule('/lit/unfollow/<other_user_id>', 'unfollow', endpoint.user_relations.unfollow)
# b.add_url_rule('/lit/following', 'following', endpoint.user_relations.following)
# b.add_url_rule('/lit/follower', 'follower', endpoint.user_relations.follower)
#
# b.add_url_rule('/lit/ad/times_left', 'ad-times-left', endpoint.ad.times_left)
# b.add_url_rule('/lit/ad/reset_accost', 'ad-reset_accost', endpoint.ad.reset_accost, methods=['POST'])
#
# # voice_chat
# # b.add_url_rule('/lit/voice_chat/invite/<target_user_id>', 'voice_chat-invite', endpoint.voice_chat.invite)
# # b.add_url_rule('/lit/voice_chat/finish', 'finish_chat', endpoint.voice_chat.finish_chat)
# # b.add_url_rule('/lit/voice_chat/accept/<target_user_id>', 'voice_chat-accept', endpoint.voice_chat.accept)
# # b.add_url_rule('/lit/voice_chat/cancel', 'cancel_chat', endpoint.voice_chat.cancel)
# # b.add_url_rule('/lit/voice_chat/reject/<target_user_id>', 'voice_chat-reject', endpoint.voice_chat.reject)
# b.add_url_rule('/lit/voice_chat/room_id', 'voice_get_roomid', endpoint.voice_chat.get_roomid, methods=['POST'])