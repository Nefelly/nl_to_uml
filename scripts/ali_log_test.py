import os
import sys
from litatom.service import TrackActionService


def run():
    TrackActionService.create_action("5e1c12663fff225067e38989", "PH", "session.1263651703460976630", 'test')


if __name__ == "__main__":
    run()
