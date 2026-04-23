from newspaper import Article
from classes.log import Log
import requests


def get_article_from_url(url: str) -> Article:
    article = Article(url)
    article.download()
    article.parse()
    return article


def request_article_from_reddit(
        reddit_url, sub, sort, req_count, blacklist_words):

    article = None

    reddit = f"{reddit_url}/{sub}/{sort}"
    req_url = f"{reddit}/.json?limit={req_count}&t=day"
    Log.info(f"Requesting: {req_url}")
    res = requests.get(
        req_url,
        headers={
            "User-Agent": "script:my_reddit_scraper:1.0 "}
    )
    Log.info(f"Result from reddit: {res.status_code}")
    if res.status_code != 200:
        return None

    res = res.json()

    title = None
    url = None
    for i in range(req_count):
        post = res["data"]["children"][i]["data"]

        title: str = post["title"].lower()
        url: str = post["url"]

        blacklist = False
        for w in blacklist_words:
            if title.find(w) >= 0:
                print(f"Found blacklisted word: {w} @ {title}")
                blacklist = True
                break

        if blacklist:
            continue

        try:
            article = get_article_from_url(url)
            break
        except Exception as e:
            Log.error(f"Couldnt get article from: {url}")
            Log.error(f"Reason: {e}")
            continue

    return article
