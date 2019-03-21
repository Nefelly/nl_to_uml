# coding: utf-8
from flask import Blueprint
from . import endpoint

__all__ = ['blueprint']

blueprint = b = Blueprint('api_v1', __name__)

# lit
b.add_url_rule('/lit/test', 'lit-test', endpoint.test.test)

# 验证码
b.add_url_rule('/lit/get_sms_code', 'get-sms-code', endpoint.sms_code.get_sms_code, methods=['POST'])

# user
b.add_url_rule('/lit/user/phone_login', 'user-phone-login', endpoint.user.phone_login, methods=['POST'])
b.add_url_rule('/lit/user/verify_nickname', 'user-verify-nickname', endpoint.user.verify_nickname)
b.add_url_rule('/lit/user/info', 'user-update-info', endpoint.user.update_info, methods=['POST'])
b.add_url_rule('/lit/user/<target_user_id>', 'user-get-info', endpoint.user.get_user_info)
b.add_url_rule('/lit/user/avatars', 'user-get-avatars', endpoint.user.get_avatars)
b.add_url_rule('/lit/user/info_by_huanxin', 'user-info-by-huanxin', endpoint.user.user_info_by_huanxinids, methods=['POST'])


# 图片
b.add_url_rule('/lit/image/upload', 'image-upload', endpoint.image.upload_image_from_file, methods=['POST'])
b.add_url_rule('/lit/image/<fileid>', 'get-image', endpoint.image.get_image)

# home
b.add_url_rule('/lit/home/online_user_count', 'home-online-user-count', endpoint.home.online_user_count)
b.add_url_rule('/lit/home/online_users', 'home-online-users', endpoint.home.online_users)
b.add_url_rule('/lit/home/wording', 'home-wordings', endpoint.home.get_wording)
b.add_url_rule('/lit/home/report', 'home-report', endpoint.home.report, methods=['POST'])
b.add_url_rule('/lit/home/report/<report_id>', 'home-report-info', endpoint.home.report_info)
b.add_url_rule('/lit/home/track', 'home-track-chat', endpoint.home.track_chat, methods=['POST'])
b.add_url_rule('/lit/home/track_action', 'home-track-action', endpoint.home.track_action, methods=['POST'])
b.add_url_rule('/lit/home/track_action', 'home-action-info', endpoint.home.action_by_user_id)

# huanxin
b.add_url_rule('/lit/huanxin/<target_user_id>', 'huanxin-get-info', endpoint.huanxin.get_user_info)

# anoy_match
b.add_url_rule('/lit/anoy_match/get_fakeid', 'anoy-match-create-fakeid', endpoint.anoy_match.get_fakeid)
b.add_url_rule('/lit/anoy_match/anoy_match', 'anoy-match-anoy-match', endpoint.anoy_match.anoy_match)
b.add_url_rule('/lit/anoy_match/anoy_like', 'anoy-match-anoy-like', endpoint.anoy_match.anoy_like)
b.add_url_rule('/lit/anoy_match/quit_match', 'anoy-match-quit-match', endpoint.anoy_match.quit_match)
b.add_url_rule('/lit/anoy_match/times_left', 'anoy-match-times-left', endpoint.anoy_match.match_times_left)
b.add_url_rule('/lit/anoy_match/judge', 'anoy-match-judge', endpoint.anoy_match.anoy_judge, methods=['POST'])


# debug
b.add_url_rule('/lit/debug/redis_status', 'debug-redis-status', endpoint.debug.redis_status)
b.add_url_rule('/lit/debug/batch_create_login', 'debug-batch-create-login', endpoint.debug.batch_create_login)
b.add_url_rule('/lit/debug/batch_anoy_match_start', 'debug-batch-anoy-match-start', endpoint.debug.batch_anoy_match_start)

# feed
b.add_url_rule('/lit/feed/create', 'feed-create-feed', endpoint.feed.create_feed, methods=['POST'])
b.add_url_rule('/lit/feed/view/<other_user_id>', 'feed-user-feeds', endpoint.feed.user_feeds)
b.add_url_rule('/lit/feed/square', 'feed-square-feeds', endpoint.feed.square_feeds)
b.add_url_rule('/lit/feed/like/<feed_id>', 'feed-like-feed', endpoint.feed.like_feed)
b.add_url_rule('/lit/feed/comment/<feed_id>', 'feed-comment-feed', endpoint.feed.comment_feed, methods=['POST'])
b.add_url_rule('/lit/feed/comment/<feed_id>', 'feed-feed-comments', endpoint.feed.feed_comments)

# user_relations
b.add_url_rule('/lit/block/<other_user_id>', 'block', endpoint.user_relations.block)
b.add_url_rule('/lit/unblock/<other_user_id>', 'unblock', endpoint.user_relations.unblock)
b.add_url_rule('/lit/blocks', 'blocks', endpoint.user_relations.blocks)

b.add_url_rule('/lit/follow/<other_user_id>', 'follow', endpoint.user_relations.follow)
b.add_url_rule('/lit/unfollow/<other_user_id>', 'unfollow', endpoint.user_relations.unfollow)
b.add_url_rule('/lit/follows', 'follows', endpoint.user_relations.follows)