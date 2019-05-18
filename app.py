import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# repeated strings
greeting = "Howdy @{}, Welcome the the {} GroupMe! Feel free to talk and ask us questions, but check out the sidebar first.\n Thanks and Gig 'Em"


class GMBot:  # parent class for all GroupMe bots
    def __init__(self, bot_id, bot_name, group_id):
        self.id = bot_id
        self.name = bot_name
        self.group = group_id

    def send_message(self, msg, attachments=()):
        post_url = "https://api.groupme.com/v3/bots/post"
        packet = {
            "bot_id": self.id,
            "text": msg,
            "attachments": attachments
        }
        requests.post(post_url, data=json.dumps(packet))

    def chat(self, data):  # meant to be overwritten by children
        if ("@" + self.name in data["text"]) and (data["name"] != self.name):
            msg = "hi @{}, my creator forgot to teach me how to talk.".format(data["name"])
            self.send_message(msg)

    @staticmethod
    def create_mention(msg, data):
        mention = {
            "type": "mentions",
            "user_ids": [data["user_id"]],
            "loci": [(msg.find("@"), len(data["name"]) + 1)]
        }
        return mention

    def at_everyone(self):
        member_url = "https://api.groupme.com/v3/groups/" + str(self.group)
        token = {
            "token": os.getenv("TOKEN")
        }
        response = requests.get(member_url, params=token)
        members_json = response.json().get("response").get("members")

        user_ids = []
        loci = []
        for member in members_json:
            user_ids += [member.get("user_id")]
            loci += [(0, 8)]
        mention = {
            "type": "mentions",
            "user_ids": user_ids,
            "loci": loci
        }

        msg = "Everyone read the GroupMe!"
        self.send_message(msg, [mention])


# child classes
class LFBot(GMBot):
    def chat(self, data):  # do something with message bot just read
        if data["name"] != self.name:
            if "@" + self.name in data["text"] or data["text"][0] == "!":
                self.commands(data)
            elif data["name"] == "GroupMe":
                self.group_events(data)
            elif "best house" in data["text"]:
                self.send_message("The mitochondria is the powerhouse of the cell")
                self.send_message("and the powerhouse of honors is House Finnell!")
            elif "@everyone" in data["text"]:
                self.at_everyone()

    def commands(self, data):  # someone prompts the bot
        if "help" in data["text"]:
            msg = "@{}, I know the following commands: echo, faq, @everyone".format(data["name"])
            self.send_message(msg, [self.create_mention(msg, data)])
        elif "howdy" in str.lower(data["text"]):
            msg = "@{} HOWDY!".format(data["name"])
            self.send_message(msg, [self.create_mention(msg, data)])
        elif "echo" in data["text"]:
            msg = '@{}, you said "{}"'.format(data["name"], data["text"][data["text"].find("echo")+5:])
            self.send_message(msg, [self.create_mention(msg, data)])
        elif "faq" in data["text"]:
            msg = "Howdy! We made a FAQ for y'all. Please read this first, but feel free to ask us additional questions. {}".format(os.getenv("FAQ_URL"))
            self.send_message(msg)
        else:
            return

    def group_events(self, data):  # messages from the GroupMe client
        if "has joined" in data["text"]:  # one person joins the group
            new_user = data["text"][0: data["text"].find("has joined")-1]
            msg = greeting.format(new_user, os.getenv("LF_GROUP_NAME"))
            self.send_message(msg, self.create_mention(msg, data))
        elif "added" in data["text"]:  # one or more people get added to group
            new_users = data["text"][data["text"].find("added")+6: data["text"].find("to")-1]
            new_users = new_users.split(", ")
            if " and " in new_users[-1]:
                last_users = new_users[-1].split(" and ")
                new_users[-1] = last_users[0]
                new_users += [last_users[1]]
            for user in new_users:
                msg = greeting.format(user, os.getenv("LF_GROUP_NAME"))
                self.send_message(msg, [self.create_mention(msg, data)])


# test bot
test_bot = LFBot(os.getenv("TEST_BOT_ID"), os.getenv("TEST_BOT_NAME"), os.getenv("TEST_GROUP_ID"))
@app.route('/test', methods=["POST"])
def read_test_group():
    data = request.get_json()
    test_bot.chat(data)
    return "done", 200


# actual bots
lf_bot = LFBot(os.getenv("LF_BOT_ID"), os.getenv("LF_BOT_NAME"), os.getenv("LF_GROUP_ID"))
@app.route('/lf', methods=["POST"])
def read_test_group2():
    data = request.get_json()
    lf_bot.chat(data)
    return "done", 200
