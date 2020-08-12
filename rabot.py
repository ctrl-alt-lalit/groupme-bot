from gmbot import GroupMeBot

class RABot(GroupMeBot):
    """Meant for the RA chat"""
    def chat(self, data):
        if data["name"] != self.name and data["name"] != "GroupMe":
            text = data["text"].lower()
            if "@everyone" in text:
                self.at_everyone()
            if "!!!test" in text:
                self.send_message("posts")

    def at_everyone(self):
        """Mention every member of a group."""
        for mention in self.create_multi_mention(self.get_member_list(), bold_location=(0, 8)):
            self.send_message(msg="Everyone read the chat please", attachments=[mention])