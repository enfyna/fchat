from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from classes.log import Log
from os import path

# import google.auth.transport.requests
# from google.oauth2.credentials import Credentials


class YoutubeUploader:
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.force-ssl"
    ]
    MAX_TITLE_LENGTH = 100

    @staticmethod
    def get_authenticated_service(dir, secret_file_name):
        # creds = None

        secret_file = path.join(dir, secret_file_name + ".json")

        # token_file = secret_file + ".token"
        # if os.path.exists(token_file):
        # creds = Credentials.from_authorized_user_file(
        # token_file, YoutubeUploader.SCOPES)

        # if not creds or not creds.valid:
        # if creds and creds.expired and creds.refresh_token:
        # creds.refresh(google.auth.transport.requests.Request())
        # else:

        flow = InstalledAppFlow.from_client_secrets_file(
            secret_file, YoutubeUploader.SCOPES)
        creds = flow.run_local_server(open_browser=False)

        # with open(token_file, "w") as token:
        # token.write(creds.to_json())
        # else:
        # print("Using existing credentials from token file.")

        return build("youtube", "v3", credentials=creds)

    @staticmethod
    def time_info(req):
        if "snippet" not in req:
            Log.warn("No snippet provided in request body.")
            return
        if "status" not in req:
            Log.warn("No status provided in request body.")
            return

        snippet = req["snippet"]
        status = req["status"]

        title = snippet["title"] + " #shorts #viral"
        if len(title) > YoutubeUploader.MAX_TITLE_LENGTH:
            Log.warn(f"{title[0:20]}... => Title too long. "
                     f"Will truncate to {YoutubeUploader.MAX_TITLE_LENGTH}"
                     "characters.")

        Log.info(f"{title[0:20]}... => {status['publishAt']}")

    @staticmethod
    def upload_video(youtube, file_path, request_body, comment=""):

        if "snippet" not in request_body:
            request_body["snippet"] = {}

        if "title" not in request_body["snippet"]:
            request_body["snippet"]["title"] = "Untitled"
            Log.warn("No title provided. Using 'Untitled'.")

        if "description" not in request_body["snippet"]:
            request_body["snippet"]["description"] = ""
            Log.warn("No description provided. Using empty description.")

        request_body["snippet"]["description"] += " #shorts #viral"
        title = request_body["snippet"]["title"] + " #shorts #viral"
        if len(title) > YoutubeUploader.MAX_TITLE_LENGTH:
            title = title[:YoutubeUploader.MAX_TITLE_LENGTH]
            title = " ".join(title.split()[:-1])
            Log.warn(f"Truncating to {YoutubeUploader.MAX_TITLE_LENGTH}"
                     "characters.")
            Log.warn(f"New Title: {title}")
        request_body["snippet"]["title"] = title

        if "categoryId" not in request_body["snippet"]:
            request_body["snippet"]["categoryId"] = "22"
            Log.warn("No categoryId provided. Using '22' (People & Blogs).")

        if "tags" not in request_body["snippet"]:
            request_body["snippet"]["tags"] = ["shorts"]
            Log.warn("No tags provided. Using default tag 'shorts'.")
        if "shorts" not in request_body["snippet"]["tags"]:
            request_body["snippet"]["tags"].append("shorts")

        if "status" not in request_body:
            request_body["status"] = {}
        if "privacyStatus" not in request_body["status"]:
            request_body["status"]["privacyStatus"] = "private"
            Log.warn("No privacyStatus provided. Using 'private'.")
        if "publishAt" not in request_body["status"]:
            Log.warn("No publishAt provided. Video will not be scheduled.")

        media = MediaFileUpload(
            file_path,
            chunksize=1024*1024*1,  # 1MB
            resumable=True,
            mimetype="video/*"
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                value = int(status.progress() * 100)
                print(f"Upload progress: {value}%", end="\r")

        Log.info(f"Upload complete. Video ID: {response['id']}")

        if len(comment) > 0:
            Log.info(f"Writing comment: {comment}")
            youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": response['id'],
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": comment
                            }
                        }
                    }
                }
            ).execute()

        return response
