import twitter
import os
_AUTH = None
def set_AUTH(token, token_secret, consumer_key, consumer_secret):
	"""
	:param token: your token
	:type token: string
	:param token_secret: your token secret
	:type token_secret: string
	:param consumer_key: your consumer key
	:type consumer_key: string
	:param consumer_secret: your consumer secret
	:type consumer_secret: string
	See https://dev.twitter.com/ for more information.
	"""
	_auth = twitter.oauth.OAuth(token, token_secret, consumer_key, consumer_secret)
	t = twitter.Twitter(auth=_auth)
	try:
		test = t.statuses.home_timeline()
		del t # only needed to check that _auth is working.
		del test
		global _AUTH
		_AUTH = _auth
		print """Success!
Your Twitter OAuth credentials have been successfully retrieved.
You can now set _auth=auth._AUTH for any classes that require OAuth credentials.
			"""
	except twitter.api.TwitterHTTPError as e:
		errors = json.loads(e.response_data)
		print errors["errors"][0]["message"]

def auth_from_env():
    TOKEN = os.environ.get("TWITTER_TOKEN", -1)
    if TOKEN == -1:
        print """TWITTER_TOKEN environment variable not found.
        Please supply it manually, or set it via the command line"""
    TOKEN_SECRET = os.environ.get("TWITTER_TOKEN_SECRET", -1)
    if TOKEN_SECRET == -1:
        print """TWITTER_TOKEN_SECRET environment variable not found.
        Please supply it manually, or set it via the command line"""
    CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY", -1)
    if CONSUMER_KEY == -1:
        print """TWITTER_CONSUMER_KEY environment variable not found.
        Please supply it manually, or set it via the command line."""
    CONSUMER_SECRET = os.environ.get("TWITTER_CONSUMER_SECRET", -1)
    if CONSUMER_SECRET == -1:
        print """TWITTER_CONSUMER_SECRET environment variable not found.
        Please supply it manually, or set it via the command line."""
    if TOKEN != -1 and TOKEN_SECRET != -1 and CONSUMER_KEY != -1 and CONSUMER_SECRET != -1:
        set_AUTH(TOKEN, TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)

auth_from_env()
