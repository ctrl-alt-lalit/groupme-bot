from gmbot import GroupMeBot
from os import getenv

class SABot(GroupMeBot):
    """This bot is intended for use in the SA chat."""
    def chat(self, data):
        if data["name"] != self.name and data["name"] != "GroupMe":
            text = data["text"].lower()
            if "!help" in text:
                msg = "I can do these things: @everyone, @JAs, @JAbies, !timesheet, !update_timesheet"
                self.send_message(msg)
            if "@everyone" in text:
                self.at_everyone()
            if "@jas" in text:
                self.at_jas()
            if "@jabies" in text:
                self.at_jabies()
            if "@failures" in text:
                self.at_failures()
            if "!timesheet" in text:
                self.send_message("Work Schedule:", [self.create_image_attachment("TIMESHEET_IMG")])
            if "!update_timesheet" in text and not self.update_image(data, "TIMESHEET_IMG"):
                    self.send_message("Please attach the image you want to replace the timesheet with.")

    def at_everyone(self):
        """Mention every member of a group."""
        for mention in self.create_multi_mention(self.get_member_list(), bold_location=(8, 8)):
            self.send_message(msg="Read me bitches!", attachments=[mention])

    def at_jas(self):
        """Mention every JA."""
        admin_list = [member for member in self.get_member_list() if "admin" in member["roles"]]
        for mention in self.create_multi_mention(admin_list, bold_location=(5, 3)):
            self.send_message(msg="Eyyy GRL, could ya read me?", attachments=[mention])

    def at_jabies(self):
        """Mention every upcoming JA."""
        jaby_list = getenv("JABY_LIST").split(", ")
        mention_list = [member for member in self.get_member_list() if member["name"] in jaby_list]
        for mention in self.create_multi_mention(mention_list, bold_location=(12, 9)):
            self.send_message(msg="UwU rawr x3 *nuzzles* notice me senpai.", attachments=[mention])

    def at_failures(self):
        """Mention everyone who applied to be a JA but didn't get accepted."""
        failure_list = getenv("FAILURE_LIST").split(", ")
        mention_list = [member for member in self.get_member_list() if member["name"] in failure_list]
        for mention in self.create_multi_mention(mention_list, bold_location=(8, 2)):
            self.send_message(msg="It's ok bb at least u tried.", attachments=[mention])
