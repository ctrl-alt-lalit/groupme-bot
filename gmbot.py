import json
import requests
from time import sleep
from abc import ABC
from os import getenv


class GMBot(ABC):  # parent class for all GroupMe bots. Necessary bot data and functions that interact with API go here
    def __init__(self, bot_id, bot_name, group_id):
        self.id = bot_id
        self.name = bot_name
        self.group = str(group_id)

    def send_message(self, msg, attachments=()):  # post a message on GroupMe
        sleep(0.15)
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
        token = {"token": getenv("TOKEN")}
        response = requests.get(group_url, params=token)
        members_json = response.json()["response"]["members"]
        return members_json

    @staticmethod
    def create_multi_mention(member_list, bold_location):  # create mention attachment with multiple members' ids
        max_mentions_per_msg = 47  # undocumented value determined by GroupMe API, # of users you can mention at once
        loci = [bold_location] * max_mentions_per_msg
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
        mentions = self.create_multi_mention(member_list, (0, 8))
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

    def at_admin(self):
        member_list = self.get_member_list()
        admin_list = [member for member in member_list if "admin" in member["roles"]]
        mentions = self.create_multi_mention(admin_list, (0, 8))
        for mention in mentions:
            msg = "Eyyy GRL, could ya read me>"
            self.send_message(msg, [mention])