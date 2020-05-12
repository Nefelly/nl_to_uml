from litatom.const import FEED_NOT_SHOWN, FEED_NORMAL
from litatom.model import Feed


def run():
    for feed in Feed.objects():
        try:
            if feed.not_shown:
                print(feed.id,1)
                feed.status = FEED_NOT_SHOWN
            else:
                print(feed.id,0)
                feed.status = FEED_NORMAL
            feed.save()
            print(feed.status)
        except AttributeError as e:
            pass


if __name__ == '__main__':
    run()
