import json
import requests
from time import sleep
from abc import ABC, abstractmethod
from os import environ, getenv
from json import dumps


class GroupMeBot(ABC):
    """Parent class for all GroupMe bots. Necessary bot data and functions that interact with API go here."""
    def __init__(self, bot_id, bot_name, group_id):
        self.id = bot_id
        self.name = bot_name
        self.group = str(group_id)

    @abstractmethod
    def chat(self, data):
        """Read and respond to chat messages."""
        pass

    def send_message(self, msg, attachments=(), debug = False):
        """Send a message in a GroupMe group."""
        sleep(0.3)  # wait for previous message to get shown to users
        post_url = "https://api.groupme.com/v3/bots/post"
        packet = {
            "bot_id": self.id,
            "text": str(msg),
            "attachments": attachments
        }
        r =  requests.post(post_url, data=json.dumps(packet))
        if debug:
            self.send_message(r.status_code)
            self.send_message(r.text)

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
        """Get a list of all members in a group."""
        group_url = "https://api.groupme.com/v3/groups/" + self.group
        token = {"token": getenv("TOKEN")}
        response = requests.get(group_url, params=token)
        members_json = response.json()["response"]["members"]
        return members_json

    @staticmethod
    def create_multi_mention(member_list, bold_location):
        """Create mention attachment(s) with multiple users' IDs."""
        max_mentions_per_msg = 47  # Maximum number of users you can mention in one attachment
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
        """Change an environmental variable on the Heroku server."""
        header = {
            "Authorization": "Bearer " + getenv("HEROKU_API_KEY"),
            "Accept": "application/vnd.heroku+json; version=3",
            "Content-type": "application/json"
        }
        dat = {key: value}
        url = "https://api.heroku.com/apps/" + getenv("APP_NAME") + "/config-vars"
        r = requests.patch(url, headers=header, data=json.dumps(dat))
        environ[key] = value  #if key is new, doing this can cause a memory leak

    def update_env(self):
        """UNTESTED FUNCTION!!! Get the most current environment variables from the Heroku server."""
        headers = {
            "Authorization": "Bearer {}".format(getenv("HEROKU_API_KEY")),
            "Accept": "application/vnd.heroku+json; version=3",
        }
        url = "https://api.heroku.com/apps/{}/config-vars".format(getenv("APP_NAME"))
        environ = requests.get(url, headers=headers).json() #could cause a memory leak, unsure

    def create_image_attachment(self, image_token: str):
        """Automatically make a 1-image attachment. Takes environmental key, NOT the image url, as input."""
        attachment = {
            "type": "image",
            "url": getenv(image_token)
        }
        return attachment
    
    def update_image(self, data, image_token: str):
        """Update an image url int the environment if the user attached a picture to their message.
        Return False if the user did not attach an image."""
        attachments = data["attachments"]
        for attachment in attachments:
            if attachment["type"] == "image":
                self.update_env_var(image_token, attachment["url"])
                return True
        return False
