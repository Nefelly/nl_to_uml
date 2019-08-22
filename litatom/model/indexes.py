indexes = {
    "admin_user": ["user_name"],
    "blocked": ["uid", "blocked", "create_time"],
    "feed":["user_id", "create_time"],
    "feed_like":["feed_id", "uid", "create_time"],
    "feed_comment": ["feed_id", "comment_id", "create_time"],
    "feedback": ["uid", "create_ts"],
    "firebase_info": ["user_id", "user_token", "create_time"],
    "follow": ["uid", "followed", "create_time"],
    "report": ["uid", "target_uid", "deal_user", "create_ts"],
    "track_chat": ["uid", "target_uid", "create_ts"],
    "user_message": ["uid", "related_uid", "create_time"],
    "user": ["phone", "huanxin.user_id", "google.other_id", "facebook.other_id", "nickname", "session", "create_time"],
    "user_setting": ["user_id", "create_time"],
    "user_action": ["user_id", "create_time"],
    "user_record": ["user_id", "create_time"],
    "FollowingFeed": ["user_id", "followed_user_id", "feed_create_time", "create_time"]
}

if __name__ == "__main__":
    for k, v in indexes.items():
        for ind in v:
            print "db.%s.createIndex({%s:1});" % (k, ind if "." not in ind else "\"%s\""%ind)
