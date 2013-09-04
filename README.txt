Created for my Comp Ling Master's Thesis project.
Requires the twitter package
(https://pypi.python.org/pypi/twitter/1.10.0)
NB: "The database" refers to my own database. Methods interacting with
the database will need some fairly serious tweaking to make sure they
line up with your database.

parsed_tweet.ParsedTweet is a class for representing tweets extracted
from the APIs using the twitter package.
save.Twitterator is a class presenting a number of methods for saving
ParsedTweet objects to JSON or a Django database.
to_db.query_to_db and to_db.scrape_to_db are methods for saving results
from the Search or Streaming APIs (respectively) to a Django database.
twitterizer.Twitterizer is a base class that provides authorization,
filtering, and generator methods.
twitterizer.Search inherits from twitterizer.Twitterizer, and interacts
with the Search API.
twitterizer.Scrape inherits from twitterizer.Twitterizer, and interacts
with the Streaming API.
tools presents a number of helper functions:
auth.set_AUTH is a function to set and validate Twitter OAuth
auth.auth_from_env is a function that attempts to set Twitter OAuth
from environment variables.
filter.unicheck checks if a character's ordinal value falls within
certain acceptable values, including Latin-1 and Emoji, but excluding
Latin Extended and other non-English symbols.
filter.unifilter checks whether a given string is in English by
calling filter.unicheck on each character in the string. (These two
methods were developed to filter out tweets in foreign languages,
because there's no guarantee Twitter's 'lang' parameter (see
https://dev.twitter.com/docs/platform-objects/tweets) is accurate in
any way.)
filter.curse_out filters out tweets that contain indecent or
inappropriate language
json_tools.json_to_db saves the contents of a JSON file to the
database
json_tools.json_to_parsed turns the contents of a JSON file into
ParsedTweet objects
json_tools.to_json turns ParsedTweet objects into a JSON file
longitudinal.longitudinal periodically scrapes the Streaming API
for tweets and saves the results to a JSON file
longitudinal.longitudinal_to_db periodically scrapes the Streaming
API for tweets and saves the results to the database
unshorten.lengthen uses the unshort.me API
(http://unshort.me/api.html) to turn links that have been shortened via
e.g. t.co back into the originals
unshorten.unshorten uses a regular expression to search through a
string for shortened links and calls unshorten.lengthen on all of them.
