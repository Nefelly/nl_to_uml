from litatom.const import FEED_NOT_SHOWN, FEED_NORMAL
from litatom.model import Feed


def run():
    for feed in Feed.objects():
        try:
            print(feed.id)
            if feed.not_shown:
                feed.status = FEED_NOT_SHOWN
            else:
                feed.status = FEED_NORMAL
            feed.save()
            print(feed.status)
        except AttributeError as e:
            pass


if __name__ == '__main__':
    run()
