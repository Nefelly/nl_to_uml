import os
import time
import sys
from litatom.mq import (
    MQProducer,
    MQConsumer
)
from litatom.model import *
from hendrix.conf import setting

def get_ages():
    m = {}
    for _ in User.objects():
        a = _.age
        if not m.has_key(a):
             m[a] = 1
        else:
            m[a] += 1
    print m


if __name__ == "__main__":
    pass