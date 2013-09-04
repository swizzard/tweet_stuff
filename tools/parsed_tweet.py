import json
class ParsedTweet(object):
	def __init__(self, text, metadata, tokenize=None):
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
		self.tokenize = tokenize or self.__split__
		self.text = text or metadata.get('text', '')
		self.text = self.text.encode('utf8', 'replace').decode('ascii', 'replace')
		self.tokenized_text = self.tokenize(text)
		self.munge_p = re.compile(r'@[\w\d_]+')
		self.munged_text = re.sub(self.munge_p, '@xxxxxxxx', self.text)
		self.metadata = metadata
		self.hashtags = None
		if self.metadata:
			self.meta_key = self.__get_meta_key__(self.metadata)
			self.meta_keys = self.meta_key.keys()
			try:
				hts = metadata['entities']['hashtags']
				if hts:
					self.hashtags = [ht['text'] for ht in hts]
			except KeyError:
				self.hashtags = None
		self.hashtags = self.hashtags or re.findall(r'#[\w_\d]+', text)
		self.uid = self.get_meta('user')['id']

	def __get_meta_key__(self, metadata):
		"""
		The metadata dictionary returned by the Twitter API is heavily nested. This function
		flattens that dictionary and makes it easier to retrieve various parts of the metadata
		(see also .get_meta, below.)
		:param metadata: the twitter metadata.
		:type metadata: dictionary.
		:return: dictionary.
		"""
		d = {}
		for k in metadata.keys():
			d[k] = metadata[k]
			if isinstance(metadata[k], dict):
				d.update(self.__get_meta_key__(metadata[k]))
		return d

	def __split__(self, s):
		"""
		The default tokenization function. Splits a string by whitespace.
		:param s: the string to be tokenized.
		:type s: string.
		:return: list of strings.
		"""
		return re.split(r'\s+', s)

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
		if self.get('meta_key', None):
			if value:
				try:
					return self.meta_key[value]
				except KeyError:
					if verbose:
						print "No value found for {}".format(value)
					return None
			else:
				return self.meta_key
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
				if hasattr(self.meta_key, 'get'):
					return self.meta_key.get(value, default)
			else:
				return default

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

	def get_uid(self):
		return self.uid

	def to_json(self, verbose=True):
		"""
		Serializes the object to JSON.
		NB: The way I've implemented it, each ParsedTweet object is serialized to a separate line of JSON.
		This allows one file to be appended with new ParsedTweet JSON representations, but also means that
		one needs to decode said file line-by-line. See json_to_parsed, below.
		:param verbose: whether to print a notice that the object is being serialized.
		:type verbose: boolean.
		:return: string representation of the JSON serialization of the object.
		"""
		if verbose:
			print "serializing {}".format(self.__repr__())
		return json.dumps([self.get_text(), self.get_meta()])
