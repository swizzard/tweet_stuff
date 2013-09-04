from ..save.twitterator import Twitterator
from ..parsed_tweet import ParsedTweet
import json
def json_to_db(infile):
	"""
	Creates a Twitterator object from a JSON file and saves the ParsedTweet objects, hashtags,
	and competitor pairs to the database.
	:param infile: the path to the JSON file.
	:type infile: string
	"""
	t = Twitterator(infile)
	t.tweets_to_db()
	t.competitors_to_db()


def json_to_parsed(infile, maximum=None):
	"""
	Reads a JSON file and creates ParsedTweet objects from the data.
	:param infile: the name of the file containing the JSON data.
	:type infile: string.
	:param maximum: the maximum number of tweets to be processed. If None, all the tweets in the file
	will be read.
	:type maximum: integer.
	:return: list of ParsedTweet objects.
	"""
	with open(infile) as f:
		l = f.readlines()
	limit = maximum or len(l)
	tweets = []
	for x in l[:limit]:
		try:
			ParsedTweet(json.loads(x)[0], json.loads(x)[1])
		except ValueError:
			continue
	return tweets


def to_json(tweets, outfile):
	"""
	Turns ParsedTweet objects into a JSON file, with one ParsedTweet object per line.
	:param tweets: the ParsedTweet objects to be encoded.
	:type tweets: list of ParsedTweet objects.
	:param outfile: the file to which to write the JSON-encoded objects.
	:type outfile: string.
	"""
	s = "{}\n".format("\n".join((tweet.to_json() for tweet in tweets)))
	with open(outfile, "a") as f:
		f.write(s)
	print "{} tweets written to {}".format(len(tweets), outfile)
