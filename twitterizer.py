import twitter
from parsed_tweet import ParsedTweet
from tools import auth
if auth._AUTH:
    print """Success!
Your Twitter OAuth credentials have been successfully retrieved.
You can now set _auth={0}.auth._AUTH for any classes that require OAuth credentials.
			""".format("twitterizer")
from tools import filter as filter_
import re


class Twitterizer(object):
    def __init__(self, _auth=None):
        """
        Base class for Search and Scrape. Implements OAuth authorization, a generator that
        turns (text,metadata) tuples into ParsedTweet objects (see parsed_tweet.ParsedTweet
        for more information), and .filter_tweets.
        The last of these relies on a number of tests (see below) that ensure only tweets
        meeting specific requirements are allowed through.
        NB: For the purposes of this class and its children:
            A "raw tweet" object is a dictionary output by the twitter module. See
            http://mike.verdone.ca/twitter/ for more information.
            A "tweet" or "unparsed tweet" object is a tuple (text, metadata), where 'text'
            is the tweet's text (i.e. t['text'], where t is a raw tweet) and 'metadata' is
            a dictionary containing the tweet's metadata (i.e., everything else besides
            the text.)
        The class is designed to be flexible and extensible, with any number of tests being
        allowed. User-defined tests must meet the following criteria:
            1) They take a tweet object as their first (non-'self') argument. This is a
            dictionary as returned via twitter's implementation of the Twitter API.
            See http://mike.verdone.ca/twitter/ for more information.
            2) They return a boolean
            3) They include variable keyword parameters (**kwargs)
            NB: tests to be used with Scrape should probably be wrapped in try/except
            in case a tweet lacks a certain key (most commonly 'text' in case of deletions,
            etc.)
        :param _auth: Twitter OAuth authorization. See documentation under tools.auth for
        more information.
        :type _auth: function
        """
        self.__auth__ = _auth or auth._AUTH or twitter.oauth.OAuth(token="",
                                                     token_secret="",
                                                     consumer_key="",
                                                     consumer_secret="")
        self.tweets = {}
        self.saved_search_meta = {}
        self.t = twitter.Twitter(auth=self.__auth__)

    def _filter_test(self, tweet, **kwargs):
        """
        Checks if a tweet passes tools.filter._unifilter (q.v.)
        :param tweet: the tweet to filter
        :type tweet: dictionary
        """
        try:
            if filter_.unifilter(tweet['text']):
                return True
            else:
                return False
        except KeyError:
            return False

    def _censor_test(self, tweet, **kwargs):
        """
        Checks whether a tweet's text passes tools.filter.censor (q.v)
        :param tweet: the tweet to check
        :type tweet: dictionary
        """
        try:
            if filter_.curse_out(tweet['text']):
                return True
            else:
                return False
        except KeyError:
            return False

    def _hash_test(self, tweet, **kwargs):
        """
        Checks whether the tweet has hashtags, if necessary
        :param tweet: the tweet to check
        :type tweet: dictionary
        :param hash_only: whether to check if hashtags are present
        :type hash_only: boolean
        :return: boolean

        """
        try:
            if tweet['entities']['hashtags']:
                return True
            else:
                return False
        except KeyError:
            return False

    def _text_test(self,tweet, **kwargs):
        """
        Checks whether the tweet has text
        :param tweet: the tweet to check
        :type tweet: dictionary
        """
        if 'text' in tweet.keys():
            return True
        else:
            return False
    def _url_test(self, tweet, **kwargs):
        """
        Checks whether there are urls in the tweet
        :param tweet: the tweet to check
        :type tweet: dictionary
        """
        try:
            if tweet['entities']['urls']:
                return True
            else:
                return False
        except KeyError:
            return False

    def filter_tweet(self, tweet, suite=True, tests=None, **test_kwargs):
        """
        Filters a tweet using the underscored helper methods above and separates the tweet into (text,metadata) tuples
        :param tweet: the tweet to filter
        :type tweet: dict
        :param suite: whether to include the standard test suite (_censor_test, _filter_test, _hash_test, _text_test)
        :type suite: bool
        :param tests: any additional tests to use
        :type tests: list of test functions (see note on test functions above) or None
        :param test_kwargs: keyword arguments to pass to the tests
        """
        if tweet:
            tests = tests or []
            if suite:
                tests += (self._censor_test, self._filter_test, self._hash_test, self._text_test,)
            output = []
            if all([test(tweet,**test_kwargs) for test in tests]):
                text = tweet['text']
                metadata = {}
                for k in tweet.keys():
                    if k != 'text':
                        metadata[k] = tweet[k]
                return (text, metadata)
        return None

    def generator(self, tweets):
        """
        Yields ParsedTweet objects from a list of unparsed tweets.
        :param tweets: a list of unparsed tweets
        :type tweets: a list of unparsed tweet objects
        :yield: ParsedTweet object(s) (see parsed_tweet.ParsedTweet for more information)
        """
        i = 0
        while True:
            try:
                yield ParsedTweet(tweets[i][0], tweets[i][1])
                i += 1
            except IndexError:
                raise StopIteration


class Search(Twitterizer):
    def __init__(self, _auth=None):
        """
        Child class of Twitterizer that interacts with the Search API. Several searches can
        be stored separately under different labels.
        For more information, see documentation under Twitterizer, above
        """
        self.unames_pat = re.compile(r'@[\w\d]+')
        super(Search, self).__init__(_auth=None)

    def _unames_test(self, tweet, q, **kwargs):
        """
        A test (a la Twitterizer.filter_tweets, above) to filter out tweets that only contain
        the search parameter in usernames.
        :param tweet: the tweet to check
        :type tweet: unparsed tweet object
        :param q: the search query
        :type q: string
        :return: boolean
        """
        text = re.sub(self.unames_pat, '', tweet['text'])
        if q in text:
            return True
        else:
            return False

    def get_tweets(self, label=None):
        """
        Retrieve all tweets saved under a given query or header, or all tweets if
        sort_name isn't given.
        :param sort_name: string
        :return: list of unparsed tweets
        """
        if label:
            if label in self.tweets.keys():
                return self.tweets[label]
            else:
                print "No saved tweets found for query {}".format(label)
        else:
            return self.tweets

    def __getitem__(self,label):
        """
        Custom implementation to allow for calls like S['label']
        """
        return self.get_tweets(label)

    def get_all_tweets(self):
        """
        Retrieve all tweets.
        :return: list of tweets
        """
        l = []
        for k in self.tweets.keys():
            l.append(self.tweets[k])
        return l

    def search(self, q, suite=True, ignore_unames=True, tests=None, **kwargs):
        """
        Retrieves tweets via the Twitter Search API and returns any that pass the filter
        tests (see documentation under Twitterizer.filter_tweets, above). This method
        optionally implements a new test, self._unames_test, which filters out tweets
        that only contain the search query in usernames.
        :param q: search query
        :type q: string
        :param suite: see documentation under Twitterizer.filter_tweets, above.
        :type suite: boolean
        :param ignore_unames: whether to implement _unames_test (q.v., and above)
        :type ignore_unames: boolean
        NB: In addition to the kwargs used in the .filter_tests, as documented above,
        kwargs passed to this function also get passed to the search. See
        https://dev.twitter.com/docs/api/1.1/get/search/tweets for more information.
        :return: list of unparsed tweets
        """
        results = self.t.search.tweets(q=q, **kwargs)
        tweets = results['statuses']
        search_meta = results['search_metadata']
        if ignore_unames:
            kwargs["q"] = q
            tests += self._unames_test
        return [self.filter_tweet(tweet, suite, tests, **kwargs) for tweet in results]

    def save_results(self, output, label):
        """
        Saves results of .search under a given label.
        :parameter output: results of a call to .search
        :type output: list of (str,dict) tuples, where the string is the text of the tweet,
        and the dictionary is the tweet's metadata
        :param label: the label under which to save the results
        :type label: string (or, really, anything that can serve as a dictionary key)
        """
        try:
            self.tweets[label] += output
        except KeyError:
            self.tweets[label] = output

    def text(self, tweets):
        """
        Returns the just the text of a list of tweets as produced by .search
        :parameter tweets: the tweets to extract the text from
        :type tweets: list of (str,dict) tuples, where the string is the tweet text, and
        the dictionary is the tweet metadata. See .search for more information.
        :return: list of strings
        """
        txt = [tweet[0] for tweet in tweets]
        return txt

    def metadata(self,tweets):
        """
        Returns just the metadata from a list of tweets as produced by .search
        :parameter tweets: the tweets to extract the metadata from
        :type tweets: list of (str,dict) tuples, where the string is the tweet text,
        and the dictionary is the tweet metadata. See .search for more information.
        :return: list of dictionaries
        """
        metadata = [tweet[1] for tweet in tweets]
        return metadata

    def show_labels(self):
        """
        Returns a list of labels under which tweets have been saved.
        :return: list of strings
        """
        return [k for k in self.tweets.keys()]

    def research(self, q, suite=True, tests=None, ignore_unames=True, minim=20, **kwargs):
        """
        Calls .search until a certain number of tweets have been returned
        :param q: the search query
        :type q: string
        :param minim: the minimum number of tweets to return
        :type minim: int
        :param kwargs: keyword arguments passed on to .search (and ultimately, to the
        Twitter search API itself.) See https://dev.twitter.com/docs/api/1.1/get/search/tweets
        for more information.
        :return: list of (str,dict) tuples, where the string is the tweet's text, and the
        dictionary is the tweet's metadata
        """
        tests = tests or []
        tweets = self.search(q, suite, tests, ignore_unames, **kwargs)
        while len(tweets) < minim:
            tweets = self.search(q, suite, tests, ignore_unames, **kwargs)
        return tweets

    def merge_labels(self, new_label=None, keep_old=False,*labels):
        """
        Merges the tweets saved under preexisting labels under a new label.
        :param new_label: the new label under which the tweets should be stored
        :type new_label: string (or, really, anything that can serve as a dictionary key)
        :param keep_old: whether to keep the original labels in addition to the new label
        NB: if False, the tweets themselves will still be saved, but won't be accessible
        under the old label
        :type new_label: boolean
        :param *labels: the old labels to merge
        :type *labels: strings (or anything that can serve as a dictionary key)
        NB: if a label isn't found, it'll be skipped and print an alert.
        """
        new_label = new_label or labels[0]
        new_group = []
        for label in labels:
            try:
                tweets = self.tweets[label]
                for tweet in tweets:
                    new_group.append(tweet)
                else:
                    if not keep_old:
                        del self.tweets[label]
            except KeyError:
                print "Label {0} does not exist! Skipping...".format(label)
        self.tweets[new_label] = new_group

    def get_search_generator(self,label=None):
        """
        Returns .generator for a given label.
        :param label: the label under which the tweets to be parsed are stored. If None,
        all currently saved tweets will be parsed by the generator.
        :type label: string (or valid dictionary key) or None
        :return: .generator (see documentation under Twitterizer.generator, above)
        """
        if label:
            return self.generator(self.get_tweets(label))
        else:
            return self.generator(self.tweets)

class Scrape(Twitterizer):
    def __init__(self, _auth=None, stream=None, sample=None):
        """
        Child class of Twitterizer that interacts with the Streaming API. Note that unlike
        the Search class, this class lacks any storage functionality, and so the data scraped
        from the Streaming API must be used immediately. This class allows for multiple
        streams and multiple samples.
        :param _auth: your twitter authentication. See the documentation under Twitterizer,
        above.
        :type _auth: function
        :param stream: a twitter.TwitterStream object to pull the tweets from.
        :type stream: twitter.TwitterStream object.
        :param sample: a twitter.stream.statuses.sample object.
        :type sample: twitter.stream.statuses.sample object.
        """
        super(Scrape, self).__init__(_auth=None)
        self._stream = stream or self.get_stream()
        self._sample = sample or self.get_sample(self.stream)

    @property
    def sample(self):
        return self.get_sample(self.stream)

    @property
    def stream(self):
        return self.get_stream()

    def get_stream(self):
        """
        Get a new TwitterStream stream.
        :return: twitter.TwitterStream object.
        """
        return twitter.TwitterStream(auth=self.__auth__)

    def get_sample(self, stream):
        """
        Get a new sample from a stream.
        :param stream: the stream to sample from.
        :type stream: twitter.TwitterStream object.
        :return: twitter.stream.statuses.sample object.
        """
        return stream.statuses.sample()

    def get_tweets(self, sample=None, limit=20, suite=True, tests=None, as_gen=True, verbose=True,  percolate=False, **kwargs):
        """
        Retrieve tweets from a sample.
        :param sample: a pre-existing twitter.stream.statuses.sample object
        :type sample: twitter.stream.statuses.sample object
        :param limit: the maximum number of tweets to return at once
        :type limit: integer
        :param suite: See documentation under Twitterizer, above
        :type suite: boolean
        :param tests: additional tests to pass to filter_tweet
        :type tests: list of test functions (see documentation for Twitterizer)
        :param as_gen: whether to return a list of unparsed tweets (False) or a
        Twitterizer.generator created therefrom
        :type as_gen: boolean
        :param verbose: whether to print the number of tweets returned
        :type verbose: boolean
        :param percolate: if True, re-raises StopIteration error caused by exhaustion of the sample
        :type percolate: boolean
        :return: list of unparsed tweets, or .generator
        """
        sample = sample or self.sample
        tests = tests or []
        i = 0
        tweets = []
        while i < limit:
            try:
                tw = self.filter_tweet(next(sample,None), suite, tests, **kwargs)
                if tw:
                    tweets.append(tw)
                    i += 1
            except StopIteration:
                if i > 0:
                    more = "more "
                else:
                    more = ""
                print "sample seems not to have any {}tweets".format(more)
                if percolate:
                    raise StopIteration
                break
        if verbose:
            print "{} tweets returned".format(i)
        if as_gen:
            return self.get_scrape_generator(tweets)
        else:
            return tweets

    def rescrape(self, sample=None, limit=1000, suite=True, tests=None, as_gen=True, verbose=True, **kwargs):
        """
        Calls get_tweets multiple times, while also refreshing the sample as needed.
        :param sample: a pre-existing twitter.stream.statuses.sample object
        :type sample: twitter.stream.statuses.sample object
        :param limit: the maximum number of tweets to return
        :type limit: int
        :param suite: See documentation above
        :type suite: boolean
        :param tests: additional tests to pass to filter_tweet
        :type tests: list of test functions (see documentation for Twitterizer)
        :param as_gen: whether to return a list of unparsed tweets (False) or a
        Twitterizer.generator created therefrom
        :type as_gen: boolean
        :param verbose: whether to print the number of twets returned
        :type verbose: boolean
        """
        i = 0
        tw = []
        while i <= limit:
            try:
                tw += self.get_tweets(sample,suite,tests,as_gen=False, percolate=True, **kwargs)
            except StopIteration:
                _sample=self.get_sample(self.get_stream())
                tw += self.get_tweets(_sample, suite, tests, as_gen=False, percolate=True)
        else:
            if as_gen:
                return self.get_scrape_generator(tw)
            else:
                return tw

    def get_scrape_generator(self,tweets):
        """
        Returns .generator for scraped tweets.
        """
        return self.generator(tweets)
