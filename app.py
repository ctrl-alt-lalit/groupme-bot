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

    def chat(self, data):  # meant to be overwritten by children
        if ("@" + self.name in data["text"]) and (data["name"] != self.name):
            msg = "hi @{}".format(data["name"])
            self.send_message(msg)


# child classes
class LFBot(GMBot):
    def chat(self, data):
        if ("@" + self.name in data["text"]) and (data["name"] != self.name):
            msg = 'hi @{}, you said "{}"'.format(data["name"], data["text"])
            self.send_message(msg)


# test bots
test_bot = LFBot(os.getenv("TEST_BOT_ID"), os.getenv("TEST_BOT_NAME"))
@app.route('/lf', methods=["POST"])
def read_lf_group():
    data = request.get_json()
    test_bot.chat(data)
    return "done", 200


concurrent_bot = LFBot(os.getenv("BC_BOT_ID"), os.getenv("BC_BOT_NAME"))  # testing multiple bots at once, it works!
@app.route('/lf2', methods=["POST"])
def read_lf_group2():
    data = request.get_json()
    concurrent_bot.chat(data)
    return "done", 200
