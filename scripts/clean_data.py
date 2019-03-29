from litatom.model import *

def clear_objs():
    for cls in [Blocked, Feed, FeedLike, FeedComment, Follow, Report, Feedback,
                UserAction, UserRecord, UserMessage]:
        cls.objects().delete()

if __name__ == '__main__':
    clear_objs()