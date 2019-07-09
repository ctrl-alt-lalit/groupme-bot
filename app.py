import os
import json
import requests
from flask import Flask, request
from abc import ABC
from time import sleep
from random import randrange


app = Flask(__name__)


class GMBot(ABC):  # parent class for all GroupMe bots. Necessary bot data and functions that interact with API go here
    def __init__(self, bot_id, bot_name, group_id):
        self.id = bot_id
        self.name = bot_name
        self.group = str(group_id)

    def send_message(self, msg, attachments=()):  # post a message on GroupMe
        sleep(0.1)
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

    def get_member_list(self):  # get list of all members of a group from GroupMe API
        group_url = "https://api.groupme.com/v3/groups/" + self.group
        token = {"token": os.getenv("TOKEN")}
        response = requests.get(group_url, params=token)
        members_json = response.json()["response"]["members"]
        return members_json

    @staticmethod
    def create_multi_mention(member_list):  # create mention attachment with multiple members' ids
        max_mentions_per_msg = 47  # undocumented value determined by GroupMe API, # of users you can mention at once
        loci = [(0, 8)] * max_mentions_per_msg
        user_ids = [member["user_id"] for member in member_list]
        mention_list = []
        while len(user_ids) > max_mentions_per_msg:
            mention_list += [{"type": "mentions", "user_ids": user_ids[:max_mentions_per_msg], "loci": loci}]
            del user_ids[:max_mentions_per_msg]
        if user_ids:
            mention_list += [{"type": "mentions", "user_ids": user_ids, "loci": loci[:len(user_ids)]}]
        return mention_list

    def at_everyone(self):  # mention every member of a group
        member_list = self.get_member_list()
        mentions = self.create_multi_mention(member_list)
        for mention in mentions:
            msg = "Everyone read the GroupMe!"
            self.send_message(msg, [mention])

    def get_user_dict(self, names=()):  # returns dictionary with format {"name" : "user_id"} for given names
        members_list = self.get_member_list()
        user_dict = {}
        for member in members_list:
            if member["nickname"] in names:
                user_dict[member["nickname"]] = member["user_id"]
        return user_dict


# child classes
class LFBot(GMBot):
    def chat(self, data):  # potentially respond to most recent message
        if data["name"] != self.name:
            if data["text"][0] == "!" or "@" + self.name in data["text"]:
                self.commands(data)
            elif data["name"] == "GroupMe":
                self.groupme_events(data)
            elif "@everyone" in data["text"] and self.check_privilege(data):
                self.at_everyone()
            elif "@fish" in data["text"] and self.check_privilege(data):
                self.at_freshmen()
            elif "best house" in str.lower(data["text"]):
                self.cheerlead_finnell()

    def commands(self, data):  # someone directly prompts the bot
        chat_input = str.lower(data["text"])
        if "help" in chat_input:
            msg = "@{}, I know the following commands: !faq, !movein, !RAs, !launch," \
                  " !code, @fish, @everyone".format(data["name"])
            self.send_message(msg, [self.create_mention(msg, data)])
        elif "faq" in chat_input:
            msg = os.getenv("FAQ_URL")
            self.send_message(msg)
        elif "movein" in chat_input:
            msg = os.getenv("MOVEIN_URL")
            self.send_message(msg)
        elif "launch" in chat_input:
            msg = os.getenv("LAUNCH_URL")
            self.send_message(msg)
        elif "code" in chat_input:
            msg = "@{} my github repository (source code) can be found at " \
                  "https://github.com/lbauskar/GroupmeDormBot".format(data["name"])
            self.send_message(msg, [self.create_mention(msg, data)])
        elif "ras" in chat_input:
            msg = os.getenv("RA_STR")
            self.send_message(msg)

    def groupme_events(self, data):  # parse messages from the GroupMe client
        greeting = os.getenv("LF_GROUP_NAME")
        if "has joined" in data["text"]:
            new_name = data["text"][0: data["text"].find("has joined")-1]
            msg = greeting.format(new_name, os.getenv("LF_GROUP_NAME"))
            new_user = self.get_user_dict([new_name])
            if new_user:
                mention = {"type": "mentions", "user_ids": [new_user[new_name]],
                           "loci": [(msg.find("@"), len(new_name) + 1)]}
                self.send_message(msg, [mention])
            else:
                self.send_message(msg)
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
                msg = greeting.format(user, os.getenv("LF_GROUP_NAME"))
                mention = {"type": "mentions", "user_ids": [user_id], "loci": [(msg.find("@"), len(user) + 1)]}
                self.send_message(msg, [mention])
                new_names.remove(user)
            for name in new_names:  # plain text for those who can't be mentioned
                msg = greeting.format(name)
                self.send_message(msg)

    def at_freshmen(self):  # mention all the freshmen only
        member_list = self.get_member_list()
        for member in member_list:
            if "SA" in member["nickname"] or "RA" in member["nickname"] or "JA" in member["nickname"]:
                member_list.remove(member)
        msg = "Freshmen, read the GroupMe pls"
        if member_list:
            fish_mentions = self.create_multi_mention(member_list)
            for fish_mention in fish_mentions:
                self.send_message(msg, [fish_mention])
        else:
            self.send_message(msg)

    def check_privilege(self, data):  # see if user is authorized to issue command
        name = data["name"]
        if "SA" in name or "JA" in name or "RA" in name:
            return True
        else:
            msg = "I'm sorry @{}, I'm afraid I can't do that".format(name)
            self.send_message(msg, [self.create_mention(msg, data)])
            return False

    def cheerlead_finnell(self):
        rng = randrange(4)
        if rng == 0:
            self.send_message("The mitochondria is the powerhouse of the cell,"
                              " and the powerhouse of Honors is House Finnell!")
        elif rng == 1:
            self.send_message("The best ice cream from Texas is Blue Bell. The greatest house in Honors is Finnell.")
        elif rng == 2:
            self.send_message("If you ain't getting Finnell, you're getting finessed.")
        elif rng == 3:
            self.send_message("The only thing mightier than the Heldenfelds stairwell"
                              " is the power and pride of House Finnell!")


class SABot(GMBot):
    def chat(self, data):
        if data["name"] != self.name and data["name"] != "GroupMe":
            if "@everyone" in data["text"]:
                self.at_everyone()
            if "!!!test" in data["text"]:
                self.send_message("I'm working")


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


sa_bot = SABot(os.getenv("SA_BOT_ID"), os.getenv("SA_BOT_NAME"), os.getenv("SA_GROUP_ID"))
@app.route("/sa", methods=["POST"])
def read_sa_group():
    data = request.get_json()
    sa_bot.chat(data)
    return "OK", 200
