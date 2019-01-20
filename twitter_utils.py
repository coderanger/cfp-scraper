import os

import requests
import tweepy

auth = tweepy.OAuthHandler(os.environ['TWITTER_CONSUMER_KEY'], os.environ['TWITTER_CONSUMER_SECRET'])
auth.set_access_token(os.environ['TWITTER_ACCESS_KEY'], os.environ['TWITTER_ACCESS_SECRET'])

api = tweepy.API(auth)

_expand_cache = {}

def expand_url(url):
    expanded = _expand_cache.get(url)
    if expanded is not None:
        return expanded
    expanded = requests.head(url, allow_redirects=True).url
    _expand_cache[url] = expanded
    return expanded


def search_for_url(query, total=1000):
    max_id = None
    last_max_id = None
    count = 0
    while count < total:
        for tweet in api.search(q=query, count=100, max_id=max_id, result_type='recent'):
            count += 1
            if max_id:
                max_id = min(max_id, tweet.id)
            else:
                max_id = tweet.id
            for url in tweet.entities['urls']:
                # Twitter only expands their own shortener so get event more.
                truly_expanded_url = url['expanded_url']
                if query not in truly_expanded_url:
                    truly_expanded_url = expand_url(truly_expanded_url)
                if query in truly_expanded_url:
                    yield truly_expanded_url
        # Did we run of Tweets?
        if last_max_id == max_id:
            break
        last_max_id = max_id


if __name__ == '__main__':
    for url in search_for_url('sessionize.com'):
        print(url)
