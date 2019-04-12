indexes = {
    "admin_user": ["user_name"],
    "blocked": ["uid", "blocked"],
    "feed":["user_id", "create_time"],
    "feed_like":["feed_id", "uid"],
    "feed_comment": ["feed_id", "comment_id"],
    "feedback": ["uid"],
    "firebase_info": ["user_id", "user_token"],
    "follow": ["uid", "followed"],
    "report": ["uid", "target_uid", "deal_user"],
    "track_chat": ["uid", "target_uid", "create_ts"],
    "user_message": ["uid", "related_uid", "create_time"],
    "user": ["phone", "huanxin.user_id", "google.other_id", "facebook.other_id", "nickname", "session"],
    "user_setting": ["user_id"],
    "user_action": ["user_id", "create_time"],
    "user_record": ["user_id", "create_time"]
}

if __name__ == "__main__":
    for k, v in indexes.items():
        for ind in v:
            print "db.%s.createIndex({%s:1});" % (k, ind if "." not in ind else "\"%s\""%ind)
