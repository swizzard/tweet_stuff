import twitter
from parsed_tweet import ParsedTweet
from django.conf import settings
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from hash_to_hash.models import Hashtag,Tweet,Competitors, WhichTag
from _mysql import Warning

class Twitterator(object):
	def __init__(self, infile=None, outfile=None, verbosity=True):
		"""
		A class to create Django-compliant fixtures from JSON-encoded ParsedTweet objects,
		or save ParsedTweet objects directly to the database. Also includes methods for
		generating and serializing/saving competitors.
		NB: The fixture-generating methods below are VERY memory-intensive!
		:param infile: the name of the file containing the JSON-encoded ParsedTweet objects.
		:type infile: string.
		:param outfile: the name of the file to which to write the fixtures. NB: only one fixture
		will be written, containing data for all three models.
		type outfile: string.
		:param verbosity: whether a message will be printed after each tweet, hashtag, and competitor set
		is created, and after the fixtures are written to the outfile.
		:type verbosity: string.
		NB: As with the ParsedTweet class above, I've tailored the fixtures produced by these classes to
		my own needs. Feel free to change .tweet_fixture, .hash_fixture, and .competitor_fixture to suit
		your own purposes!
		"""
		self.infile = infile
		self.outfile = outfile
		self.fixtures = []
		self.competitors = []
		try:
			self.tweet_i = Tweet.objects.latest('id').id + 1
		except ObjectDoesNotExist:
			self.tweet_i = 1
		try:
			self.hash_i = Hashtag.objects.latest('id').id + 1
		except ObjectDoesNotExist:
			self.hash_i = 1
		try:
			self.competitors_i = Competitors.objects.latest('id').id + 1
		except ObjectDoesNotExist:
			self.competitors_i = 1
		try:
			self.whichtag_i = WhichTag.objects.latest('id').id + 1
		except ObjectDoesNotExist:
			self.whichtag_i = 1
		self.verbosity = verbosity
		self.competitors = Competitors.objects.all()
		self.hashtags = Hashtag.objects.all()

	def tweet_generator(self):
		"""
		A generator that turns the JSON in the infile to ParsedTweet objects, one line/object at a time.
		:return: ParsedTweet objects.
		"""
		with open(self.infile) as f:
			lines = f.readlines()
		i = 0
		while i < len(lines):
			try:
				yield ParsedTweet(json.loads(lines[i])[0], json.loads(lines[i])[1])
				i += 1
			except StopIteration:
				break
				print "{0} tweets processed".format(i)

	def tweet_to_db(self, tweet, label, verbose):
		"""
		Creates a Tweet object from a ParsedTweet object and saves it to the database.
		"""
		try:
			lat = tweet.get_coordinates()[1]
			lon = tweet.get_coordinates()[0]
		except TypeError:
			lat = None
			lon = None
		t = Tweet(id=self.tweet_i,
		          text=tweet.text,
		          munged_text=tweet.munged_text,
		          uid=tweet.get_uid(),
		          time_zone=tweet.get_meta('time_zone'),
		          lat=lat,
		          lon=lon)
		try:
			if verbose:
				print "Saving tweet {0}".format(t.id)
			try:
				t.save()
				for hashtag in tweet.get_hashes():
					self.hashtag_to_db(hashtag, t, label, verbose)
			except Warning:
				return None
		except IntegrityError:
			if verbose:
				print "Error encountered...trying again"
			self.tweet_i += 1
			self.tweet_to_db(tweet, label, verbose)
		else:
			self.tweet_i += 1

	def hashtag_to_db(self, hashtag, tweet, label, verbose):
		"""
		Creates and saves Hashtag objects to the database.
		:param hashtag: the text of the hashtag
		:type hashtag: string
		:param tweet: the Tweet object associated with the hashtag
		:type tweet: Tweet object (see tweet_to_db, above)
		NB: While you probably could call this method directly, it's much less messy
		to let tweet_to_db call it instead.
		"""
		try:
			H = Hashtag.objects.get(text=hashtag)
			H.tweet.add(tweet)
			if verbose:
				print "hashtag text already in db...skipping..."
			if H.label != label and label != "none":
				if verbose:
					print "relabeling hashtag as {0}".format(label)
				H.label = label
		except ObjectDoesNotExist:
			h = Hashtag(id=self.hash_i, text=hashtag, label=label)
			try:
				if verbose:
					print "Saving hashtag {0}".format(h.id)
				h.save()
				h.tweet.add(tweet)
			except IntegrityError:
				if verbose:
					print "error encountered...trying again"
				self.hash_i += 1
				self.hashtag_to_db(hashtag, tweet, label, verbose)
			else:
				self.hash_i += 1

	def tags_to_comps(self, label, privilege):
		H = Hashtag.objects.filter(label=label)
		for h in H:
			other_tags = H.filter(id__gt=h.id)
			for tag in other_tags:
				self.create_comps(privilege, h, tag)


	def create_comps(self, privilege, tag1, tag2):
		try:
			c = Competitors.objects.create(id=self.competitors_i,yes=0,no=0,privilege=privilege)
			print "saving competitor pair {0}".format(self.competitors_i)
			self.competitors_i += 1
			self.create_whichtag(tag=tag1, competitors=c, tag_no=1)
			self.create_whichtag(tag=tag2, competitors=c, tag_no=2)
		except IntegrityError:
			self.competitors_i += 1
			self.create_comps(privilege, tag1, tag2)

	def create_whichtag(self, tag, competitors, tag_no):
		try:
			w = WhichTag(tag=tag, competitors=competitors, tag_no=tag_no, id=self.whichtag_i)
			w.save()
			print "saved whichtag {0}".format(self.whichtag_i)
			self.whichtag_i += 1
		except IntegrityError:
			self.whichtag_i += 1
			self.create_whichtag(tag, competitors, tag_no)

	def tweets_to_db(self, label):
		"""
		Iterates through .tweet_generator and saves all tweets to the database.
		"""
		for tweet in self.tweet_generator():
			self.tweet_to_db(tweet, label)

	def __save_comps__(self, tag1, tag2, privilege, verbose=True):
		"""
		Creates and saves a Competitors object to the database. Helper method for
		competitors_to_db to prevent IntegrityErrors caused by duplicate
		primary keys.
		:param tag1: the first hashtag in the pair
		:type tag1: Hashtag object (see hashtag_to_db, above)
		:param tag2: the second hashtag
		:type tag2: Hashtag object
		"""
		if not self.competitors.filter(tag1__id=tag1.pk).filter(tag2__id=tag2.pk):
			try:
				comps = Competitors(id=self.competitors_i,
				                    tag1=tag1,
				                    tag2=tag2,
				                    yes=0,
				                    no=0,
				                    privilege=privilege)
				if verbose:
					print "saving competitor pair {0}".format(comps.id)
				comps.save()
			except IntegrityError as e:
				if verbose:
					print "error encountered ({0})...trying again".format(e)
				self.competitors_i += 1
				self.__save_comps__(tag1, tag2, privilege, verbose)
			else:
				self.competitors_i += 1

	def competitors_to_db(self, start=1):
		i = start
		while True:
			try:
				tag1 = self.hashtags.get(pk=i)
				j = i + 1
				while True:
					try:
						tag2 = self.hashtags.get(pk=j)
						self.__save_comps__(tag1, tag2)
						j += 1
					except Hashtag.DoesNotExist:
						break
				i += 1
			except Hashtag.DoesNotExist:
				break

	def add_new_competitor(self, tweet, verbose=True):
		self.tweet_to_db(tweet, verbose)
		tags = Hashtag.objects.filter(tweet__pk=self.tweet_i)
		for tag in tags:
			j  = 1
			while True:
				try:
					tag2 = self.hashtags.get(pk=j)
					self.__save_comps__(tag, tag2, verbose)
					j += 1
				except Hashtag.DoesNotExist:
					break

	def add_privileged_competitors(self, tweet_iterator, label=None, privilege=None, verbose=True):
		for tweet in tweet_iterator:
			self.tweet_to_db(tweet, label, verbose)
		else:
			self.tags_to_comps(label,privilege)

	def add_unprivileged_competitors(self, tweet_iterator, label="none", privilege="random", verbose=True):
		self.add_privileged_competitors(tweet_iterator, label, privilege, verbose)
