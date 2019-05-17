import os

from urllib.parse import urlencode
from urllib.request import Request, urlopen
from flask import Flask, request

app = Flask(__name__)


class GMBot:  # parent class for all GroupMe bots
    def __init__(self, bot_id, bot_name, activate=True):
        self.id = bot_id
        self.name = bot_name
        self.active = activate

    def send_message(self, msg):
        url = "https://api.groupme.com/v3/bots/post"

        data = {
            "bot_id": self.id,
            "text": msg
        }

        request_msg = Request(url, urlencode(data).encode())
        urlopen(request_msg).read().decode()

    def parse(self, data):  # meant to be overwritten by children
        if ("@" + self.name in data["text"]) and (data["name"] != self.name):
            msg = "hi @{}".format(data["name"])
            self.send_message(msg)


# child classes
class LFBot(GMBot):
    def parse(self, data):
        if ("@" + self.name in data["text"]) and (data["name"] != self.name):
            msg = "hi @{}, you said {}".format(data["name"], data["text"])
            self.send_message(msg)


lf_bot = LFBot(os.getenv("LF_BOT_ID"), os.getenv("LF_BOT_NAME"))
@app.route('/', methods=["POST"])
def read_group():
    data = request.get_json()
    lf_bot.parse(data)
    return "done", 200
