import requests
import re

def lengthen(link):
    """
    Lengthens a link using the unshort.me API. See http://unshort.me/api.html for more
    information.
    :parameter link: the link to unshorten
    :type link: string
    :return: string
    """
	r = requests.get('http://api.unshort.me/unshorten?r={link}&format=json'.format(link=link))
	if r.ok:
		j = r.json()
		requested = j['requestedURL']
		resolved = j['resolvedURL']
		if requested == resolved:
			return resolved
		else:
			return lengthen(resolved)
	else:
		if r.status_code == 400:
			return link
		else:
			print "Error code {0}: {1}".format(r.status_code, r.json().get("error",None))

def unshorten(text):
    """
    Searches a text for shortened links and calls lengthen() on them
    :param text: the text to search through
    :type text: string
    :return: dictionary of strings: {shortened_link:unshortened_link}
    """
	p = re.compile(r'http://[\w\./\d]+')
	links = re.findall(p,text)
	if not links:
		return None
	long_links = {}
	for link in links:
		long_links[link] = lengthen(link)
	return long_links
