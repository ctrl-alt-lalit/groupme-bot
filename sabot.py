from gmbot import GMBot
from os import getenv


class SABot(GMBot):
    def chat(self, data):
        if data["name"] != self.name and data["name"] != "GroupMe":
            text = data["text"].lower()
            if "!help" in text:
                msg = "I can do these things: @everyone, @JAs, @JAbies, !timesheet, " \
                      "and one secret command!"
            if "@everyone" in text:
                self.at_everyone()
            if "@jas" in text:
                self.at_admin()
            if "@jabies" in text:
                self.at_jabies()
            if "@failures" in text:
                self.at_failures()
            if "!timesheet" in text:
                img_attachment = {
                    "type": "image",
                    "url": getenv("TIMESHEET_URL")
                }
                self.send_message("Work Schedule:", [img_attachment])

    def at_jabies(self):
        member_list = self.get_member_list()
        jaby_list = getenv("JABY_LIST").split(", ")
        mention_list = [member for member in member_list if member["name"] in jaby_list]
        mentions = self.create_multi_mention(mention_list, bold_location=(12, 9))
        for mention in mentions:
            msg = "UwU rawr x3 *nuzzles* notice me senpai"
            self.send_message(msg, [mention])

    def at_failures(self):
        member_list = self.get_member_list()
        failure_list = getenv("FAILURE_LIST").split(", ")
        mention_list = [member for member in member_list if member["name"] in failure_list]
        mentions = self.create_multi_mention(mention_list, bold_location=(8, 2))
        for mention in mentions:
            msg = "It's ok bb at least u tried"
            self.send_message(msg, [mention])
