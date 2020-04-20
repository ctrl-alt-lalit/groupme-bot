import json
import requests
from time import sleep
from abc import ABC, abstractmethod
from os import environ


class GMBot(ABC):
    env = environ

    """Parent class for all GroupMe bots. Necessary bot data and functions that interact with API go here."""
    def __init__(self, bot_id, bot_name, group_id):
        self.id = bot_id
        self.name = bot_name
        self.group = str(group_id)

    @abstractmethod
    def chat(self, data):
        """Read and respond to chat messages."""
        pass

    def send_message(self, msg, attachments=()):
        """Send a message in a GroupMe group."""
        sleep(0.3)  # wait for previous message to get processed by GroupMe
        post_url = "https://api.groupme.com/v3/bots/post"
        packet = {
            "bot_id": self.id,
            "text": str(msg),
            "attachments": attachments
        }
        requests.post(post_url, data=json.dumps(packet))

    @staticmethod
    def create_mention(msg, data):
        """Automatically create a 1-person mention attachment."""
        mention = {
            "type": "mentions",
            "user_ids": [data["user_id"]],
            "loci": [(msg.find("@"), len(data["name"]) + 1)]
        }
        return mention

    def get_member_list(self):
        """Get list of all members in a group."""
        group_url = "https://api.groupme.com/v3/groups/" + self.group
        token = {"token": self.env["TOKEN"]}
        response = requests.get(group_url, params=token)
        members_json = response.json()["response"]["members"]
        return members_json

    @staticmethod
    def create_multi_mention(member_list, bold_location):
        """Create mention attachment(s) with multiple users' IDs."""
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

    def get_user_dict(self, nicknames=()):
        """Return a dictionary with the format {nickname : user_id} for given nicknames."""
        user_dict = {member["nickname"]: member["user_id"] for member in self.get_member_list()
                     if member["nickname"] in nicknames}
        return user_dict
    
    def update_env_var(self, key, value):
        header = {
            "Authorization": "Bearer " + self.env["HEROKU_API_KEY"],
            "Accept": "application/vnd.heroku+json; version=3",
            "Content-type": "application/json"
        }
        dat = "{" + key + ": " + value + "}" 
        url = "https://api.heroku.com/apps/" + self.env["APP_NAME"] + "/config-vars"
        requests.patch(url, headers=header, data=dat)
        self.env[key] = value

    def update_env(self):
            headers = {
                "Authorization": "Bearer {}".format(self.env["HEROKU_API_KEY"]),
                "Accept": "application/vnd.heroku+json; version=3",
            }
            url = "https://api.heroku.com/apps/{}/config-vars".format(self.env["APP_NAME"])
            self.env = requests.get(url, headers=headers).json()

    