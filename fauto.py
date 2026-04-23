#!/usr/bin/env python

from newspaper import Article
from os import getenv, mkdir, path, remove
from PIL import Image
from funcs.loaders import load_prefix
from funcs.chatters import chat_request, chat_test_request
from funcs.article import request_article_from_reddit, get_article_from_url
from funcs.bing_image import bing_images_browser
from classes.log import Log
from dotenv import load_dotenv
import requests

load_dotenv()

PREFIX: str = load_prefix()

REDDIT_URL: str = "https://www.reddit.com/r"
SUB_URL: str = getenv("SUB_URL", "worldnews")
TOPIC_TYPE: str = getenv("TOPIC_TYPE", "top")
REQ_COUNT: int = getenv("REQ_COUNT", 3)
IMG_RES_THRESHOLD: int = getenv("IMG_RES_THRESHOLD", 400)
URL: str = getenv("URL")
NOIMG: bool = getenv("NOIMG") is not None
PROMPT_FILE: str = getenv("PROMPT_FILE", "prompt.txt")
TESTING: bool = getenv("TESTING")

if URL is not None:
    Log.info(f"URL = {URL}")
else:
    Log.info(f"REDDIT = {(SUB_URL, TOPIC_TYPE, REQ_COUNT)}")
Log.info(f"PROMPT_FILE = {PROMPT_FILE}")

BLACLIST_WORDS: list[str] = [
    "/",
    "school",
    "shooting",
    "kill",
    "die",
    "death",
    "murder",
    "child",
]

chatter = None

if TESTING is not None:
    Log.info("=== TESTING MODE! ===")
    chatter = chat_test_request
else:
    chatter = chat_request
    api_key = getenv("OPENROUTER_API_KEY")
    if api_key is None:
        Log.info("OPENROUTER_API_KEY not found!")
        exit(1)
    Log.info("OPENROUTER_API_KEY = OK!")


def main() -> None:

    prompt = None
    with open(path.join(PREFIX, PROMPT_FILE), "r") as f:
        prompt = f.read()

    article: Article = request_article_from_reddit(
        REDDIT_URL,
        SUB_URL,
        TOPIC_TYPE,
        REQ_COUNT,
        BLACLIST_WORDS
    ) if URL is None else get_article_from_url(URL)

    if article is None:
        Log.info("Article not found")
        return 0

    Log.info("ARTICLE FOUND")
    Log.info(article.title)
    Log.info(article.url)

    folder_path = path.join(PREFIX, article.title)
    if path.exists(folder_path):
        Log.info(f"Using folder:{folder_path}")
    else:
        mkdir(folder_path)
        Log.info(f"Created: {folder_path}")

    article_file = path.join(folder_path, "article.txt")
    if path.exists(article_file):
        Log.info(f"Overwriting article file: {article_file}")

    chat_prompt = prompt + article.text

    with open(article_file, "w") as f:
        f.write(chat_prompt)

    Log.info("REQUESTING CHAT")
    chat_result = chatter(chat_prompt).strip()
    chat_file = path.join(folder_path, "chat.txt")
    with open(chat_file, "w") as f:
        f.write(chat_result)

    if NOIMG:
        return 0

    Log.info(f"Requesting images for: {article.title}")
    downloaded = 0

    urls = []
    if article.has_top_image():
        Log.info(f"Article has top image: {article.top_image}")
        urls.append(article.top_image)

    try:
        urls.extend(bing_images_browser(article.title))
    except Exception as e:
        Log.info("Couldnt find images disabling headless mode.")
        Log.info(f"Reason: {e}")
        urls.extend(bing_images_browser(article.title, headless_mode=False))

    for url in urls:
        data = requests.get(url).content
        name: str = url\
            .removeprefix("http://")\
            .removeprefix("https://")\
            .removeprefix("www.")\
            .split("?")[0]\
            .replace("/", "-")

        downloaded += 1
        name = path.join(folder_path, f'img-{downloaded}-{name}')
        with open(name, "wb") as f:
            f.write(data)

        try:
            img = Image.open(name).convert("RGBA")
            new_file = name + ".png"
            if img.width * img.height < IMG_RES_THRESHOLD:
                Log.error(f"Image too low-res: {name}")
                new_file = new_file + '.lowres'
                Log.info("Marked image with '.lowres' suffix.")
            img.save(new_file, "PNG")
            remove(name)
            Log.info(f"Converted image: {url}")
        except Exception as e:
            Log.info(f"Failed to convert {url}: {e}")

    return


if __name__ == "__main__":
    main()
    Log.end()
