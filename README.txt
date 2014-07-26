tweet_stuff v 0.3.0

Created for my Comp Ling Master's Thesis project.
Requires the twitter package
(https://pypi.python.org/pypi/twitter/1.10.0)

A collection of tools to collect, parse, and extract features from tweets.

auth.py : functions to create and validate twitter.oauth.OAuth objects. Keys can be input
    directly via auth.set_AUTH, or automatically from environment variables (which I
    prefer, since you don't have to keep them on-hand or store them anywhere obvious.)
    Either way, the resulting OAuth object is validated by creating a new twitter instance
    (see the Python twitter documentation cited above for more information) and checking
    its home timeline. Used in basically everything else here.

parsed.py : 3 classes to parse tweets and users:
    Parsed: a superclass from which ParsedTweet and ParsedUser inherit. It has methods
        to process the JSON data provided by the Twitter API, turn some of them into
        attributes, and also unshorten any available URLS using the requests library
        (http://www.python-requests.org/) and extract their domains.
    ParsedTweet: a class that represents a parsed tweet. Extends the Parsed class with
        methods and attributes that deal with tweet-specific issues, like text munging
        (anonymizing usernames and URLs), geolocation coordinates, text tokenization,
        mentions, and hashtags.  Also creates a ParsedUser instance (see below) based on
        the user information provided as part of the tweet JSON.
    ParsedUser: a class that represents a parsed user. Extends the Parsed class with
        methods and attributes that deal with user-specific issues, such as
        followers/following counts, username, and timezone (which is calculated from UTC
        offset if not provided.)
    parsed.py also includes functions to save ParsedTweet and ParsedUser instances to
        JSON files.

twitterizer.py : 3 classes to extract, filter, and process tweets from the stream:
    Twitterizer: a superclass from which Search and Scrape inherit. It implements
        authorization via tools/auth.py (q.v.) and a filtering system that includes a
        'suite' of standard tests (presence of text, presence of hashtags, absence of
        'bad words', absence of "non-English" characters), and an additional test for
        presence of URLs. The filtering system is designed to be easily extensible--any
        function that returns boolean values can be added via the tests keyword argument
        of Twitterizer.filter_tweet. See the code for more specifics of the implementations
        of the included tests. Twitterizer also includes a method to create a generator
        that converts JSON obtained via the Twitter API into ParsedTweet objects.
    Search : a class that interacts with the search functionality of the Twitter API, and
        inherits from Twitterizer. Includes a method to search Twitter for a given term and
        return a minimum number of results (using cursoring--see 
        https://dev.twitter.com/docs/working-with-timelines for more information on
        cursoring.)
    Scrape : a class that interacts with the 'firehose' funcitonality of the Twitter API,
        and inherits from Twitterizer. Includes methods to obtain streams and samples of
        streams, as well as methods to extract tweets from a sample and continue to scrape
        the sample until a certain number of tweets have been extracted.

feature_extraction/
    basic_features.py : two functions to extract basic/easy-to-process features from
        ParsedTweets (get_tweet_features) and ParsedUsers (get_user_features). Both 
        use dictionaries to identify which features to extract and how to process them,
        in the format {feature1: [function, arg1, arg2], feature2: [function],
        feature3: None,...}, where feature1 is the feature to pull out of the 
        ParsedTweet/-User object, function is a function to apply to it, and 
        arg1, arg2... are additional arguments to pass to that function. 
        (NB: it's assumed that the extracted feature is the first argument to pass 
        to the function; you'll have to lambda-ize/wrap any functions that don't 
        follow this call signature.) Values of None in these dictionaries result in 
        the feature being appended to final_features as-is. Any features that are lists
        and have a function value will have that function applied to every member of that
        list. As it stands, the 'defaults' are to hash unshortened_urls and url_domains, and
        apply get_user_features to the ParsedUser object created as part of ParsedTweet creation. get_tweet_features and get_user_features are designed to be extensible,
        similar to Twitterizer.filter_tweet--pass your own {feature:[function,arg,arg...]}
        dictionary with the other_features parameter and go to town.
        NB: While the general outline/call signature of these functions is unlikely to change
        significantly, the features/functions in the default to_extract dictionaries
        is subject to revision as I figure out which features I want to use/how to
        pre-process them.
    freq_splitter.py : implements an algorithm to split a string (e.g., a hashtag) into
        words using a Dynamic Programming technique that makes use of the relative
        frequencies of words in a wordlist.
    tweet_idf.py : a class (Tweet_idf) that implements methods to calculate Term Frequency-
        Inverse Document Frequency (TF-IDF, see http://en.wikipedia.org/wiki/Tf%E2%80%93idf
        for more information) based on tweets, using ParsedTweet.words (i.e., excluding
        hashtags, usernames, and links.) Includes methods to create a TF-IDF corpus from
        supplied tweets, calculate the IDF of a given word based on that corpus, and
        return a list of the words in a given tweet sorted in decreasing TF-IDF order.
        Based on a Python TF-IDF implementation by Niniane Wang (https://code.google.com/p/tfidf/).
    corpora_used.txt : a list of NLTK corpora used to create the wordlists.
    words.txt : a wordlist extracted from the corpora cited in corpora_used.txt
    lowered_words.txt : the same words as in words.txt, but lowercased via .lower().
    freqs.json : a JSON dump of a dictionary of the frequencies of the words in words.txt
        calculated using nltk.FreqDist.
    lowered_freqs.json : the same as freqs.json, but for lowered_freqs.txt.


Questions/comments: file an issue or pull request, or email me at sam.raker@gmail.com
Use in good health!
