PyKarma
=======

PyKarma is a desktop application that uses naïve Bayes classifiers to sort links from RSS feeds by their subject and freshness for the purpose of submitting them on [reddit](http://reddit.com).

First, it crawls a user-specified list of sub-reddits, recording the titles of links on each sub-reddit and the frequency with which keywords from titles occur for a given sub-reddit. Once it has enough data (about 10,000 keywords per sub-reddit), it takes links from the loaded RSS feeds and checks whether they have already been submitted to reddit. If not, a title, found from the link's HTML \<title\> tag, is split into keywords and compared against sub-reddit keyword frequencies to find the appropriate place to submit the link.

The link's title is also compared against keywords of the most recent set of links from tracked sub-reddits. If too many keywords match these recent links, it is assumed that the content in the link has already been submitted from another source. That is, if enough keywords match, the link's staleness score will surpass a certain threshold and not be recommended for submission. Otherwise, the link is added to a list of suggested submissions.

This process happens continuously as new links are read from the RSS feed, and the application keeps crawling reddit in the background to improve sub-reddit categorization training.

A set of filters are also used to clean up RSS feed titles and to ignore or sanitize certain URLs, titles, or keywords.

**Suggested submissions list**
![Suggested submissions](http://i.imgur.com/JQP37xc.png)
*The red link above has a high staleness score because most of its keywords have shown up in a recent submission (indicated by hyphens before keywords). The selected link (about Microsoft) has a high Match Strength value for the Microsoft sub-reddit compared to PyKarma's next best guess for its suggested sub-reddit, leading to a high Relative Certainty score.*

**Dependencies**
* [Python (2.7.x)](http://python.org/download/)
* [wxPythnon (2.9.x)](http://www.wxpython.org/download.php)
* [feedparser](https://pypi.python.org/pypi/feedparser)
