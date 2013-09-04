import auth
from ..get_tweets.twitterizer import Scrape
from ..save.twitterator import Twitterator
def longitudinal(outfile="tweets6-23.json", interval=3600, limit=1000):
	"""
	Periodically retrieves a certain number of tweets from the Twitter stream.
	:param outfile: the name of the file to which to write the retrieved tweets.
	:type outfile: string.
	:param interval: how long to wait (in seconds) between scraping the stream for more tweets.
	:type interval: integer.
	:param limit: the number of tweets to retrieve at a go.
	:type limit: integer.
	"""
	while True:
		s = Scrape(_auth=auth._AUTH)
		print "getting tweets..."
		tweets = s.get_tweets(limit=limit)
		print "saving tweets"
		to_json(tweets, outfile)
		print "sleeping for {} seconds".format(interval)
		time.sleep(interval)


def longitudinal_to_db(_auth=auth._AUTH, interval=3600, limit=1000):
    """
    Periodically saves a number of tweets from the Streaming API to the database
    :param _auth: see tools.auth for more information
    :type _auth: OAuth object
    :param interval: how long to wait (in seconds) in between scraping for more tweets.
    :type interval: integer
    :param limit: how many tweets to retrieve at one time
    :type limit: integer
    """
	t = Twitterator()
	s = Scrape(_auth)
	while True:
		print "getting tweets..."
		tweets = s.get_scrape_iterator(sample=s.get_sample(s.get_stream()), limit=limit)
		print "saving tweets"
		for tweet in tweets:
			t.add_new_competitor(tweet)
		print "done"
