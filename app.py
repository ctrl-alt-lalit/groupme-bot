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
            msg = "hi @{}, my creator forgot to tell me how to talk.".format(data["name"])
            self.send_message(msg)


# child classes
class LFBot(GMBot):
    def chat(self, data):  # do something with message bot just read
        if data["name"] != self.name:
            if "@" + self.name in data["text"]:
                self.commands(data)
            elif data["name"] == "GroupMe":
                self.group_events(data)
            elif "best house" in data["text"]:
                self.send_message("The mitochondria is the powerhouse of the cell")
                self.send_message("and the powerhouse of honors is House Finnell!")

    def commands(self, data):  # someone @s the bot
        if "help" in data["text"]:
            msg = "@{}, I know the following commands: echo, faq".format(data["name"])
        elif "echo" in data["text"]:
            msg = 'hi @{}, you said "{}"'.format(data["name"], data["text"])
        elif "faq" in data["text"]:
            msg = "Howdy! In order to keep the group from getting cluttered, we made a FAQ for y'all. Please read this first, but feel free to ask us additional questions. The FAQ is at the bottom is this document: {}\nbeep boop :)".format(os.getenv("FAQ_URL"))
        else:
            msg = "Sorry, I don't recognize that command.\nbeep boop :("

        self.send_message(msg)

    def group_events(self, data):  # messages from the GroupMe client
        if "renamed" in data["text"] or "changed name" in data["text"]:  # someone changes their nickname
            new_name = data['text'][data["text"].find("to")+3:]
            msg = "nice name! @{}".format(new_name)
            self.send_message(msg)
        elif "has joined" in data["text"]:  # one person joins the group
            new_user = data["text"][0: data["text"].find("has joined")-1]
            msg = "Howdy! @{}".format(new_user)
            self.send_message(msg)
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
            self.send_message(msg)



# test bots
test_bot = LFBot(os.getenv("TEST_BOT_ID"), os.getenv("TEST_BOT_NAME"))
@app.route('/test', methods=["POST"])
def read_test_group():
    data = request.get_json()
    test_bot.chat(data)
    return "done", 200


concurrent_bot = LFBot(os.getenv("BC_BOT_ID"), os.getenv("BC_BOT_NAME"))  # testing multiple bots at once, it works!
@app.route('/test2', methods=["POST"])
def read_test_group2():
    data = request.get_json()
    concurrent_bot.chat(data)
    return "done", 200
