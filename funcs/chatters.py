from classes.log import Log
from os import getenv
import requests
import json


def chat_test_request(message) -> str:
    return """
script.txt
What if the UK just shuts down ticket scalpers forever?
Hey, quick! The government is banning anyone from selling a ticket for more \
than they paid.
No more 30% mark‑ups on shows by Viagogo or StubHub.
Touts can’t charge extra fees beyond the face value.
Even social media resale will fall under the cap.
Fans will only pay the actual price they bought it for, \
plus a small, fixed fee.
The move aims to cut £145m a year in gouged costs and stop the fraud.
Stay tuned for the full official announcement next week!

youtube.txt
{
  "snippet": {
    "title": "UK's Ticket Resale Ban 2025 #TicketScalpers #UK",
    "description": "The UK government is outlawing ticket resale for profit",
    "tags": ["ticket resale", "ticket scalping", "UK government"],
    "categoryId": "10"
  },
  "status": {
    "privacyStatus": "private",
    "publishAt": "2025-09-16T21:00:00+03:00",
    "selfDeclaredMadeForKids": false
  }
}
"""


def chat_request(message) -> str:
    api_key = getenv("OPENROUTER_API_KEY")
    if api_key is None:
        Log.error("OPENROUTER_API_KEY not found!")
        exit(10)

    model = getenv("OPENROUTER_MODEL")

    input("ARE YOU SURE REQUESTING CHAT FROM OPENROUTER::" + model + " ?")

    Log.info(f"Requesting chat from model: {model}")

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "extra_body": {"reasoning": {"enabled": True}}
        })
    )

    response = response.json()
    content = ""
    try:
        content = response['choices'][0]['message']['content']
        Log.info(f"Received content with length: {len(content)}")
    except Exception as e:
        Log.error(e)
        Log.error("Error response received: " + str(response))
        input("Continue?")

    return content
