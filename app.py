import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json, requests
from flask import Flask, request


app = Flask(__name__)


class GMBot:  # parent class for all GroupMe bots
    def __init__(self, bot_id, bot_name, activate=True):
        self.id = bot_id
        self.name = bot_name
        self.active = activate

    def send_message(self, msg, data, mention=False):
        url = "https://api.groupme.com/v3/bots/post"
        if mention:
            packet = {
                "bot_id": self.id,
                "text": "I'm trying to help :(",
                "attachments": [
                    {
                        "type": "image",
                        "url": "https://i.groupme.com/480x325.jpeg.9e20b71dd6af4b58bbd132d4a7dec009"
                    }
                ]
            }
        else:
            packet = {
                "bot_id": self.id,
                "text": msg
            }

        #request_msg = Request(url, urlencode(packet).encode())
        #urlopen(request_msg).read().decode()
        requests.post(url, data=json.dumps(packet))


    def chat(self, data):  # meant to be overwritten by children
        if ("@" + self.name in data["text"]) and (data["name"] != self.name):
            msg = "hi @{}, my creator forgot to tell me how to talk.".format(data["name"])
            self.send_message(msg, data)


# child classes
class LFBot(GMBot):
    def chat(self, data):  # do something with message bot just read
        if data["name"] != self.name:
            if "@" + self.name in data["text"] or data["text"][0] == "!":
                self.commands(data)
            elif data["name"] == "GroupMe":
                self.group_events(data)
            elif "best house" in data["text"]:
                self.send_message("The mitochondria is the powerhouse of the cell", data)
                self.send_message("and the powerhouse of honors is House Finnell!", data)

    def commands(self, data):  # someone @s the bot
        if "help" in data["text"]:
            msg = "@{}, I know the following commands: echo, faq".format(data["name"])
            self.send_message(msg, data, True)
        elif "howdy" in str.lower(data["text"]):
            msg = "@{} HOWDY!".format(data["name"])
            self.send_message(msg, data)
        elif "echo" in data["text"]:
            msg = 'hi @{}, you said "{}"'.format(data["name"], data["text"])
            self.send_message(msg, data)
        elif "faq" in data["text"]:
            msg = "Howdy! In order to keep the group from getting cluttered, we made a FAQ for y'all. Please read this first, but feel free to ask us additional questions. {}\nbeep boop (:".format(os.getenv("FAQ_URL"))
            self.send_message(msg, data)
        else:
            msg = "Sorry, I don't recognize that command.\nbeep ): boop );"
            self.send_message(msg, data)

    def group_events(self, data):  # messages from the GroupMe client
        if "renamed" in data["text"] or "changed name" in data["text"]:  # someone changes their nickname
            new_name = data['text'][data["text"].find("to")+3:]
            msg = "nice name! @{}".format(new_name)
            self.send_message(msg, data)
        elif "has joined" in data["text"]:  # one person joins the group
            new_user = data["text"][0: data["text"].find("has joined")-1]
            msg = "Howdy! @{} Tell us your major (you can put it in your nickname) and check out this doc! {} \nThanks and Gig 'Em".format(new_user, os.getenv("FAQ_URL"))
            self.send_message(msg, data)
        elif "added" in data["text"]:  # one or more people get added to group
            new_users = data["text"][data["text"].find("added")+6: data["text"].find("to")-1]
            new_users = new_users.split(", ")
            if " and " in new_users[-1]:
                last_users = new_users[-1].split(" and ")
                new_users[-1] = last_users[0]
                new_users += [last_users[1]]
            msg = "Howdy! "
            for user in new_users:
                msg += "@{} ".format(user)
            msg += "Tell us your major (you can put it in your nickname) and check out this doc! {}\nThanks and Gig 'Em!".format(os.getenv("FAQ_URL"))
            self.send_message(msg, data)


# test bot
test_bot = LFBot(os.getenv("TEST_BOT_ID"), os.getenv("TEST_BOT_NAME"))
@app.route('/test', methods=["POST"])
def read_test_group():
    data = request.get_json()
    test_bot.chat(data)
    return "done", 200


# actual bots
lf_bot = LFBot(os.getenv("LF_BOT_ID"), os.getenv("LF_BOT_NAME"))
@app.route('/lf', methods=["POST"])
def read_test_group2():
    data = request.get_json()
    lf_bot.chat(data)
    return "done", 200
