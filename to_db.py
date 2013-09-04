from save import Twitterator
from twitterizer import Twitterizer, Search, Scrape

def query_to_db(q, label=None, privilege="same_tag",**kwargs):
    """
    Saves the results of a search query to the database. See also save.Twitterator, and
    twitterizer.Search.
    :parameter q: the search query
    :type q: string
    :parameter label: the label under which to save the results, as well as the label to
    give them in the database
    :type label: string
    :parameter privilege: the privilege to give Competitors created from the search results
    in the database
    :type privilege: string
    """
	s = Search()
	t = Twitterator()
	label = label or q
	s.save_results(s.research(q, **kwargs),label)
	t.add_privileged_competitors(s.get_search_iterator(label),label=label,privilege=privilege)

def scrape_to_db(limit=20, **kwargs):
    """
    Scrapes the Public API and saves the results to the database.
    :param limit: the number of tweets to save
    :type limit: integer
    """
	s = Scrape(limit=limit, **kwargs)
	t = Twitterator()
	t.add_unprivileged_competitors(s.get_tweets())
