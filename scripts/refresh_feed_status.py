from litatom.const import FEED_NOT_SHOWN, FEED_NORMAL
from litatom.model import Feed


def run():
    for feed in Feed.objects():
        try:
            if feed.not_shown:
                feed.status = FEED_NOT_SHOWN
            else:
                feed.status = FEED_NORMAL
            feed.save()
        except AttributeError as e:
            pass


if __name__ == '__main__':
    run()
