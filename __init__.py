__author__ = 'samuelraker'

import sys,os
# sys.path.insert(1,os.path.abspath('tweet_stuff'))
# sys.path.insert(1,os.path.abspath('../samrakerdotcom'))
# sys.path.insert(1,os.path.abspath('../hash_to_hash'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'samrakerdotcom.settings'
#from django.conf import settings
#settings.configure()
import re
import json
import twitter
try:
    from hash_to_hash.models import Tweet, Hashtag, Competitors
    from django.db import IntegrityError
    from django.db import DatabaseError
except ImportError as e:
    errs = e.args
    for err in errs:
        print err
    print "Database-related tools will be unavailable..."
from tools import auth
from parsed_tweet import ParsedTweet

_AUTH = auth._AUTH
