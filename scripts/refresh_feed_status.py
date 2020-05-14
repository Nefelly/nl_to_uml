from litatom.const import FEED_NOT_SHOWN, FEED_NORMAL
from litatom.model import Feed


def run():
    for feed in Feed.objects(not_shown=True, status__ne=FEED_NOT_SHOWN):
            feed.status = FEED_NOT_SHOWN
            feed.save()

if __name__ == '__main__':
    run()
