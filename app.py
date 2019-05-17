import os
import json

from urllib.parse import urlencode
from urllib.request import Request, urlopen
from flask import Flask, request

app = Flask(__name__)
@app.route('/', methods=["POST"])
def echo():
    data = request.get_json()

    # only reply to other people
    if data["name"] != os.getenv("GM_BOT_NAME"):
        msg = '{} sent "{}"'.format(data["name"], data["text"])
        send_message(msg)

    return "done", 200


def send_message(msg):
    url = "https://api.groupme.com/v3/bots/post"

    data = {
        "bot_id": os.getenv("GM_BOT_ID"),
        "text": msg
    }

    request = Request(url, urlencode(data).encode())
    json = urlopen(request).read().decode()
