import json
import re
import requests
from urllib2 import URLError


class Parsed(object):
    def __init__(self, js):
        """
        Base class for ParsedTweet and ParsedUser classes.
        :param js: JSON dict as returned by Twitter API
        :type js: JSON
        """
        self.metadata = self.__get_meta_keys__(js)
        self.meta_keys = self.metadata.keys()
        self.entities = self.get_meta("entities")
        self.urls = []
        urls = self.get_meta('urls')
        if urls:
                for url in urls:
                    expanded = url.get('expanded_url')
                    if expanded:
                        self.urls.append(expanded)
                    else:
                        tco = url.get('url')
                        if tco:
                            self.urls.append(tco)
        self.unshortened_urls = self.get_unshortened_urls()
        self.url_domains = self.get_url_domains()
        self.id = self.get_meta("id_str")

    def __get_meta_keys__(self, js):
        """
        The metadata dictionary returned by the Twitter API is heavily nested. This function
        flattens that dictionary and makes it easier to retrieve various parts of the metadata
        (see also .get_meta, below.)
        :param metadata: the twitter metadata.
        :type metadata: dictionary.
        :return: dictionary.
        """
        d = {}
        for k in js.keys():
            d[k] = js[k]
            if isinstance(js[k], dict):
                d.update(self.__get_meta_keys__(js[k]))
        return d

    def get_meta(self, value=None, verbose=False):
        """
        This function can be used to retrieve any of the various parts of the twitter
        metadata.
        :param value: the metadata value to be retrieved.
        :type value: string.
        :param verbose: if True, print an alert when the metadata retrieval fails.
        :type verbose: boolean.
        :return: string, list, or dictionary, depending on the metadata in question.
        """
        if self.get('meta_keys', None):
            if value:
                try:
                    return self.metadata[value]
                except KeyError:
                    if verbose:
                        print "No value found for {}".format(value)
                    return None
            else:
                return self.meta_keys
        else:
            return None

    def get(self, value, default=None):
        """
        An implementation of the standard dictionary.get() method.
        :param value: the value to be gotten.
        :type value: string.
        :param default: the default value, to be returned if the getting fails.
        :return: string, list, or dictionary, depending on the metadata, or None.
        """
        if hasattr(self, value):
            return self.__getattribute__(value)
        else:
            if hasattr(self, 'meta_key'):
                if hasattr(self.meta_keys, 'get'):
                    return self.meta_keys.get(value, default)
            else:
                return default

    def get_unshortened_urls(self):
        unshortened = []
        for url in self.urls:
            try:
                r = requests.get(url)
                unshortened.append(r.url)
            except (requests.exceptions.RequestException, URLError) as e:
                print e.args[0]
                unshortened.append(url)
        return unshortened

    def get_url_domains(self):
        domains = []
        p = re.compile(r'https?://([\w\d\.\-]+\.\w{2,3})')
        for url in self.unshortened_urls:
            domains.append(p.match(url).group(1))
        return domains

    def to_json(self, verbose=True):
        """
        Serializes the object to JSON.
        NB: The way I've implemented it, each Parsed object is serialized to a separate line of JSON.
        This allows one file to be appended with new Parsed JSON representations, but also means that
        one needs to decode said file line-by-line.
        :param verbose: whether to print a notice that the object is being serialized.
        :type verbose: boolean.
        :return: string representation of the JSON serialization of the object.
        """
        if verbose:
            print "serializing {}".format(self.__repr__())
        return json.dumps(self.metadata)


class ParsedTweet(Parsed):
    def __init__(self, js, tokenize=None):
        """
        A class that turns some salient parts of the twitter metadata into attributes,
        and also tokenizes and munges the text of the tweet.
        The class also flattens metadata dictionary (see .__get_meta_key, below.)
        The various parts of the metadata that I have implemented get methods for are those relevant
        to my research. Feel free to add to/replace these methods for your own purposes!
        NB: Twitter metadata is frequently in unicode. You have been warned.
        NB: See .to_json, below, for information on serialization.
        :param text: the text of the tweet. If None, an attempt will be made to retrieve the text from the
        metadata.
        :type text: string
        :param metadata: the rest of the twitter metadata (although it doesn't really matter if text is
        included here also.)
        :type metadata: dictionary
        :param tokenize: a tokenization function, e.g. one that takes a string and returns a list of tokens.
        The default is a simple whitespace-based tokenizer (see .__split__, below.)
        :type tokenize: function
        """
        super(ParsedTweet, self).__init__(js)
        self.tokenize = tokenize or self.__split__
        self.text = self.metadata.get('text', '')
        self.text = self.text.encode('utf8', 'replace').decode('ascii', 'replace')
        self.tokenized_text = self.tokenize(self.text)
        self.munge_p = re.compile(r'(@|http://(www\.)?)[\w\d\.\-\?/]+')
        self.munged_text = re.sub(self.munge_p, '\g<1>xxxxxxxx', self.text)
        self.hashtags = None
        try:
            hts = self.metadata['entities']['hashtags']
            if hts:
                self.hashtags = [ht['text'] for ht in hts]
        except KeyError:
            self.hashtags = None
        self.hashtags = self.hashtags or re.findall(r'#[\w_\d]+', text)
        self.user = ParsedUser(self.get_meta("user"))
        self.created_at = self.get_meta("created_at")
        self.mentions = self.get_mentions()

    def get_mentions(self):
        mentions = self.get_meta("entities")["user_mentions"]
        mention_ids = []
        for mention in mentions:
            mention_ids.append(mention["id_str"])
        return mention_ids

    def __split__(self, s):
        """
        The default tokenization function. Splits a string by whitespace.
        :param s: the string to be tokenized.
        :type s: string.
        :return: list of strings.
        """
        return re.split(r'\s+', s)

    def get_hashes(self):
        """
        :return: list of strings
        """
        return self.hashtags

    def get_text(self):
        return self.text

    def get_munged_text(self):
        """
        Returns the text of the tweet with all usernames replaced with '@xxxxxxxx'
        :return: string
        """
        return self.munged_text

    def get_tokenized(self, decode=True):
        """
        A (shorter) alias of .get_tokenized_text, below.
        """
        return self.get_tokenized_text(decode)

    def get_tokenized_text(self, decode=True):
        """
        Returns the text as tokenized by the function passed in .__init__, or by .__split__, above.
        :param decode: if True, the text will be decoded from unicode.
        :type decode: boolean.
        :return: list of strings.
        """
        if decode:
            return [word.decode('utf8') for word in self.tokenized_text]
        else:
            return self.tokenized_text

    def get_coordinates(self):
        """
        Gets the geolocation coordinates from the metadata.
        NB: not all tweets have such data.
        NB: the geolocation data provided by Twitter is, IMHO, a bit of a mess. There are
        sometimes multiple lists of coordinates--I'm not sure what they all represent.
        In these cases, I've made the (arbitrary) choice to use the first set.
        :return: list of strings (longitude, latitude)
        """
        if self.get_meta('coordinates'):
            coordinates = self.get_meta('coordinates')
            while isinstance(coordinates[0], list):
                coordinates = coordinates[0]
            else:
                return coordinates

    def get_user(self):
        return self.user


class ParsedUser(Parsed):
    def __init__(self, js):
        super(ParsedUser, self).__init__(js)
        self.created_at = self.get_meta("created_at")
        self.description = self.get_meta("description")
        self.followers_count = self.get_meta("followers_count")
        self.following_count = self.get_meta("friends_count")
        self.lang = self.get_meta("lang")
        self.location = self.get_meta("location")
        self.name = self.get_meta("name")
        self.screen_name = self.get_meta("screen_name")
        self.statuses_count = self.get_meta("statuses_count")
        self.tz = self.get_meta("time_zone")
        self.utc_offset = self.get_utc_offset()
        self.utc_tz = self.get_utc_tz()
        self.verified = self.get_meta("verified")

    def get_utc_offset(self):
        """
        If the User supplies utc_offset, return it. Otherwise, try and guess the offset
        from the created_at attribute.
        """
        offset = self.get_meta("utc_offset")
        if offset:
            return int(offset)
        else:
            m = re.search(r'\d{2}:\d{2}:\d{2} ((\+|-)\d{4}) \d{4}', self.created_at)
            if m:
                offset = int(m.group(1))
        return offset

    def get_utc_tz(self):
        if self.utc_offset:
            return self.utc_offset / 3600
        else:
            return None

def tweets_from_json(fname):
    with open(fname) as f:
        for x in f.readlines():
            js = json.loads(x)
            if len(js) == 2:
                return ParsedTweet(js[0],js[1])
            else:
                return ParsedTweet(js=js[0])

def users_from_json(fname):
    with open(fname) as f:
        return [ParsedUser(json.loads(x)) for x in f.readlines()]
