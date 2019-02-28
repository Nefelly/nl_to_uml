# flake8: noqa
from .user import (
    User
)

from ..db import DBManager

dbm = DBManager()
dbm.initall()