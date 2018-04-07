import os
import sys
import logging
from datetime import timedelta

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stderr))

# Time in seconds after last use of token to invalidate it.
TokenInactivityTimeout = timedelta(seconds=300)

userkey = "user"
passwordkey = "password"
tokenkey = "token"

ResponseJSONTimeFormat = '%H:%M:%S' # i.e. 13:00:00
ResponseJSONDateTimeFormat = '%Y-%m-%d_%H:%M:%S' # i.e. 2018-01-01_13:00:00
DBHost = os.environ.get('DBHost')
