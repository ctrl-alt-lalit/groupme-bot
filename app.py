import os
import json
import requests
from flask import Flask, request
from time import sleep
from abc import ABC

app = Flask(__name__)


class GMBot(ABC):  # parent class for all GroupMe bots. Necessary bot data and functions that interact with API go here
    def __init__(self, bot_id, bot_name, group_id):
        self.id = bot_id
        self.name = bot_name
        self.group = group_id

    def send_message(self, msg, attachments=()):  # post a message on GroupMe
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
    def create_mention(msg, data):  # create a simple, 1-person mention attachment
        mention = {
            "type": "mentions",
            "user_ids": [data["user_id"]],
            "loci": [(msg.find("@"), len(data["name"]) + 1)]
        }
        return mention

    def get_member_json(self):  # get json of all members from GroupMe API
        member_url = "https://api.groupme.com/v3/groups/" + str(self.group)
        token = {
            "token": os.getenv("TOKEN")
        }
        response = requests.get(member_url, params=token)
        members_json = response.json()["response"]["members"]
        return members_json

    def at_everyone(self):  # mention every member of the GroupMe
        def create_everyone_mention(members_json):  # create mention attachment with every member's id
            user_ids = []
            loci = []
            for member in members_json:
                user_ids += [member["user_id"]]
                loci += [(0, 8)]
            mention = {
                "type": "mentions",
                "user_ids": user_ids,
                "loci": loci
            }
            return mention

        member_json = self.get_member_json()
        mentions = create_everyone_mention(member_json)
        msg = "Everyone read the GroupMe!"
        self.send_message(msg, [mentions])

    def get_user_dict(self, names=()):  # returns dictionary with format {"name" : "user_id"} for given names
        members_json = self.get_member_json()
        user_dict = {}
        for member in members_json:
            if member.get("nickname") in names:
                user_dict[member.get("nickname")] = member.get("user_id")
        return user_dict


# child classes
class LFBot(GMBot):
    greeting = "Howdy @{}, Welcome the {} GroupMe! Feel free to talk and ask us questions, " \
               "but check out the sidebar first.\nThanks and Gig 'Em"

    def chat(self, data):  # potentially respond to most recent message
        if data["name"] != self.name:
            if "@" + self.name in data["text"] or data["text"][0] == "!":
                self.commands(data)
            elif data["name"] == "GroupMe":
                self.group_events(data)
            elif "best house" in data["text"]:
                self.send_message("The mitochondria is the powerhouse of the cell")
                sleep(0.1)
                self.send_message("and the powerhouse of honors is House Finnell!")
            elif "@everyone" in data["text"]:
                self.at_everyone()

    def commands(self, data):  # someone prompts the bot
        if "help" in data["text"]:
            msg = "@{}, I know the following commands: faq, @everyone".format(data["name"])
            self.send_message(msg, [self.create_mention(msg, data)])
        elif "faq" in data["text"]:
            msg = "Howdy! We made a FAQ for y'all. Please read this first," \
                  " but feel free to ask us additional questions. {}".format(os.getenv("FAQ_URL"))
            self.send_message(msg)
        elif "howdy" in str.lower(data["text"]):
            msg = "@{} HOWDY!".format(data["name"])
            self.send_message(msg, [self.create_mention(msg, data)])
        else:
            return

    def group_events(self, data):  # parse messages from the GroupMe client
        if "has joined" in data["text"]:
            new_name = data["text"][0: data["text"].find("has joined")-1]
            msg = self.greeting.format(new_name, os.getenv("LF_GROUP_NAME"))
            new_user = self.get_user_dict([new_name])
            if new_user == {}:
                self.send_message(msg)
            else:
                mention = {"type": "mentions", "user_ids": [new_user[new_name]], "loci": [(msg.find("@"), len(new_name)+1)]}
                self.send_message(msg, [mention])
        elif "added" in data["text"]:
            def list_added_users():  # create list of new user names from "added" message
                new_usernames = data["text"][data["text"].find("added")+6: data["text"].find("to the group")-1]
                new_usernames = new_usernames.split(", ")
                if " and " in new_usernames[-1]:
                    last_users = new_usernames[-1].split(" and ")
                    new_usernames[-1] = last_users[0]
                    new_usernames += [last_users[1]]
                return new_usernames

            new_users = self.get_user_dict(list_added_users())
            for user, user_id in new_users.items():
                msg = self.greeting.format(user, os.getenv("LF_GROUP_NAME"))
                mention = {"type": "mentions", "user_ids": [user_id], "loci": [(msg.find("@"), len(user) + 1)]}
                self.send_message(msg, [mention])


# test bot
test_bot = LFBot(os.getenv("TEST_BOT_ID"), os.getenv("TEST_BOT_NAME"), os.getenv("TEST_GROUP_ID"))
@app.route('/test', methods=["POST"])
def read_test_group():
    data = request.get_json()
    test_bot.chat(data)
    return "ok", 200  # 200 is the ok code for the GroupMe API


# actual bots
lf_bot = LFBot(os.getenv("LF_BOT_ID"), os.getenv("LF_BOT_NAME"), os.getenv("LF_GROUP_ID"))
<<<<<<< HEAD
@app.route('/lf', methods=["POST"])
=======
@app.route("/lf", methods=["POST"])
>>>>>>> 5961012... join failsafe
def read_lf_group():
    data = request.get_json()
    lf_bot.chat(data)
    return "ok", 200
