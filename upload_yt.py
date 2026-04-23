#!/usr/bin/env python

from classes.yt_uploader import YoutubeUploader
from classes.folder import Folder
from classes.log import Log
from funcs.loaders import load_prefix
from os import getenv, path, remove, rename
from dotenv import load_dotenv
import re

load_dotenv()

PREFIX: str = load_prefix()

STATIC_PATH = getenv("STATIC", path.join(PREFIX, ".static"))
IGNORE_LIST = getenv("IGNORE", "") + " .ignore"
IGNORE_LIST = re.split("[\\s,;]+", IGNORE_LIST.strip())

folders, folder_count = Folder.init(
    PREFIX, ignore=IGNORE_LIST, mkmode=0o777
)
Folder.info(folders)

request_folders, request_count = [], 0
for f in folders:
    request_body, request_path = f.get_youtube_req()
    if request_body is None:
        Log.warn(f"Folder['{f.name[:13]}...'] has no request.")
        continue
    YoutubeUploader.time_info(request_body)
    request_folders.append(f)
    request_count += 1

if request_count == 0:
    Log.error("No videos available for upload!")
    exit(1)
else:
    Log.info(f"Found {request_count} videos to upload.")

YT = None
YT_CHANNEL = getenv("YOUTUBE") or getenv("YT")
if YT_CHANNEL is None:
    Log.error("YT_CHANNEL not defined!")
    Log.info("""
        You need to create a google console project to be able to upload
        videos. Follow the below instructions to obtain a 'client_secrets.json'
        file. Then put that file in the STATIC folder and add its file name to
        .env file as the YT key.
        For example:
        # .env file contents
        YT=client_secrets # if you didnt change the file name
    """)
    Log.info("-> developers.google.com/youtube/v3/guides/uploading_a_video")
    exit(2)

YT = YoutubeUploader.get_authenticated_service(STATIC_PATH, YT_CHANNEL)
Log.info("Youtube authenticated.")

count = 0
for f in request_folders:
    count += 1

    Log.info(f"Uploading video: {f.name} [{count}/{request_count}]")

    request_body, request_path = f.get_youtube_req()
    if request_body is None:
        Log.warn("Video has no request.")
        continue

    short_name = path.join(PREFIX, f"{f.name}.mp4")

    comment = ""
    if (comment_path := f.get_comment_path()) != "":
        with open(comment_path, "r") as f:
            comment = f.read().strip()

    YoutubeUploader.upload_video(YT, short_name, request_body, comment)

    uploaded_name = request_path.replace("youtube", "youtube-uploaded")
    if path.isfile(uploaded_name):
        remove(uploaded_name)
    rename(request_path, uploaded_name)

    Log.info("Uploaded.")

Log.end()
