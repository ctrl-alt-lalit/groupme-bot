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

    @staticmethod
    def create_multi_mention(members_json):  # create mention attachment with every member's id
        user_ids = []
        loci = []
        for member in members_json:
            user_ids += [member["user_id"]]
            loci += [(0, 8)]
        mention = {"type": "mentions", "user_ids": user_ids, "loci": loci}
        return mention

    def at_everyone(self):  # mention every member of the GroupMe
        member_json = self.get_member_json()
        mentions = self.create_multi_mention(member_json)
        msg = "Everyone read the GroupMe!"
        self.send_message(msg, [mentions])

    def get_user_dict(self, names=()):  # returns dictionary with format {"name" : "user_id"} for given names
        members_json = self.get_member_json()
        user_dict = {}
        for member in members_json:
            if member["nickname"] in names:
                user_dict[member["nickname"]] = member["user_id"]
        return user_dict


# child classes
class LFBot(GMBot):
    greeting = "Howdy @{}, Welcome to the {} GroupMe! Feel free to talk and ask us questions, " \
               "but check out the sidebar first.\nThanks and Gig 'Em"

    def chat(self, data):  # potentially respond to most recent message
        if data["name"] != self.name:
            if "@" + self.name in data["text"] or data["text"][0] == "!":
                self.commands(data)
            elif data["name"] == "GroupMe":
                self.group_events(data)
            elif "@everyone" in data["text"]:
                self.at_everyone()
            elif "@fish" in data["text"]:
                self.at_freshmen()
            elif "best house" in data["text"]:
                self.send_message("The mitochondria is the powerhouse of the cell")
                sleep(0.1)
                self.send_message("and the powerhouse of honors is House Finnell!")

    def commands(self, data):  # someone directly prompts the bot
        if "help" in data["text"]:
            msg = "@{}, I know the following commands: faq, movein, RAs, launch," \
                  " code, @fish, @everyone".format(data["name"])
            self.send_message(msg, [self.create_mention(msg, data)])
        elif "faq" in data["text"]:
            msg = "Howdy! We made a FAQ for y'all. Please read this first," \
                  " but feel free to ask us additional questions. {}".format(os.getenv("FAQ_URL"))
            self.send_message(msg)
        elif "movein" in data["text"]:
            msg = "Howdy! This web page will answer most of your move in questions. {}".format(os.getenv("MOVEIN_URL"))
            self.send_message(msg)
        elif "launch" in data["text"]:
            msg = "Check out the LAUNCH website for more info about Honors. {}".format(os.getenv("LAUNCH_URL"))
            self.send_message(msg)
        elif "code" in data["text"]:
            msg = "@{} my github repository (source code) can be found at " \
                  "https://github.com/lbauskar/GroupmeDormBot".format(data["name"])
            self.send_message(msg, [self.create_mention(msg, data)])
        elif "ras" in str.lower(data["text"]):
            msg = os.getenv("RA_STR")
            self.send_message(msg)

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

            new_names = list_added_users()
            new_users = self.get_user_dict(new_names)
            for user, user_id in new_users.items():  # @ users who can be mentioned
                msg = self.greeting.format(user, os.getenv("LF_GROUP_NAME"))
                mention = {"type": "mentions", "user_ids": [user_id], "loci": [(msg.find("@"), len(user) + 1)]}
                self.send_message(msg, [mention])
                new_names.remove(user)
            for name in new_names:  # plain text for those who can't be mentioned
                msg = self.greeting.format(name, os.getenv("LF_GROUP_NAME"))
                self.send_message(msg)

    def at_freshmen(self):  # mention all the freshmen only
        member_json = self.get_member_json()
        for member in member_json:
            if "SA" in member["nickname"] or "RA" in member["nickname"] or "JA" in member["nickname"]:
                member_json.remove(member)
        msg = "Freshmen, read the GroupMe pls"
        if member_json:
            fish_mention = self.create_multi_mention(member_json)
            self.send_message(msg, [fish_mention])
        else:
            self.send_message(msg)


# BOTS
test_bot = LFBot(os.getenv("TEST_BOT_ID"), os.getenv("TEST_BOT_NAME"), os.getenv("TEST_GROUP_ID"))
@app.route("/test", methods=["POST"])
def read_test_group():
    data = request.get_json()
    test_bot.chat(data)
    return "OK", 200


lf_bot = LFBot(os.getenv("LF_BOT_ID"), os.getenv("LF_BOT_NAME"), os.getenv("LF_GROUP_ID"))
@app.route("/lf", methods=["POST"])
def read_lf_group():
    data = request.get_json()
    lf_bot.chat(data)
    return "OK", 200
