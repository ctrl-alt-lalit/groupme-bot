import requests
from gmbot import GroupMeBot
from os import getenv
from time import sleep
from random import choice

class LFBot(GroupMeBot):
    """This bot is intended for use in the main dorm-wide chat."""

    def chat(self, data):
        if data["name"] == "GroupMe":
                self.respond_to_groupme_events(data)

        if data["name"] != self.name:
            text = str.lower(data["text"])
            if "!help" in text:
                msg = getenv("LF_HELP_STR").format(data["name"])
                self.send_message(msg, [self.create_mention(msg, data)])
            if "!faq" in text:
                self.send_message(getenv("FAQ_URL"))
            if "!movein" in text:
                self.send_message(getenv("MOVEIN_URL"))
            if "!launch" in text:
                self.send_message(getenv("LAUNCH_URL"))
            if "!howdy" in text:
                msg = "Howdy Week Schedule:"
                self.send_message(msg, [self.create_image_attachment("HOWDY_IMG")])
            if "!code" in text:
                msg = "@{} my github repository (source code) can be found at " \
                      "https://github.com/lbauskar/GroupmeDormBot".format(data["name"])
                self.send_message(msg, [self.create_mention(msg, data)])
            if "!ras" in text:
                self.send_message(getenv("RA_STR"))
            if "!core" in text:
                self.send_message("core.tamu.edu\nicd.tamu.edu")
            if "!registration" in text or "shut up" in text:
                msg = "Yes, more seats will open for your classes. No we don't know when. " \
                      "Check your major's catalog for what classes to take."
                self.send_message(msg)
            if "!google " in text:
                self.use_google(text, command_used="!google ")
            elif "!g " in text:
                self.use_google(text, command_used="!g ")
            if "!stats" in text:
                self.chat_stats()
            if self.not_a_freshman(data): #non-freshmen exclusive commands
                if "@everyone" in text:
                    self.at_everyone()
                if "@freshmen" in text:
                    self.at_freshmen()
                if "!update_howdy" in text and not self.update_image(data, "HOWDY_IMG"):
                    self.send_message("Please attach an image.")
                
    def respond_to_groupme_events(self, data):
        """Parse messages from GroupMe client."""
        greeting = getenv("LF_GREETING")

        def send_greeting_message(name, user_id = None):
            """Send a greeting to a user who just joined the chat."""
            msg = greeting.format(name)
            if user_id:
                mention = {
                    "type": "mentions",
                    "user_ids": [user_id],
                    "loci": [(msg.find("@"), len(name) + 1)]
                }
                self.send_message(msg, [mention])
            else:
                self.send_message(msg)

        def greet_joined_user():
            """Greet the one user added to the chat."""
            new_name = data["text"][0: data["text"].find("has joined") - 1]
            new_user = self.get_user_dict([new_name])
            if new_user:
                send_greeting_message(new_name, new_user[new_name])
            else:
                self.send_message(new_name)

        def greet_added_users():
            """Greet multiple users who were added to the chat."""
            def list_added_users():  # create list of new user names from "added" message
                names = data["text"][data["text"].find("added") + 6: data["text"].find("to the group") - 1].split(", ")
                if " and " in names[-1]:
                    last_users = names[-1].split(" and ")
                    names[-1] = last_users[0]
                    names += [last_users[1]]
                return names

            new_names = list_added_users()
            new_users = self.get_user_dict(new_names)
            for name, user_id in new_users:  # @ users who can be mentioned
                send_greeting_message(name, user_id)
                new_names.remove(name)
            for name in new_names:  # plain text for those who can't be mentioned
                send_greeting_message(name)
        
        def say_goodbye():
            """Send randomized farewell in response to a user leaving the chat."""
            goodbye = choice(getenv("LF_GOODBYES").split(", "))
            if "{}" in goodbye:
                name = data["text"][:data["text"].find(" has left")]
                goodbye = goodbye.format(name)
            self.send_message(goodbye)
        

        if "has joined" in data["text"]:
            greet_joined_user()
        elif "added" in data["text"]:
            greet_added_users()
        elif "has left" in data["text"]:
            say_goodbye()

    def at_everyone(self):
        """Mention every member of a group."""
        for mention in self.create_multi_mention(self.get_member_list(), bold_location=(0, 8)):
            self.send_message("Everyone read the GroupMe!", [mention])

    def at_freshmen(self):
        """Mention every freshman in the group."""
        member_list = [member for member in self.get_member_list() if member["user_id"] not in self.get_a_team_ids()]
        if member_list:
            for mention in self.create_multi_mention(member_list, bold_location=(0, 8)):
                self.send_message("Freshmen, read the GroupMe pls", [mention])

    def get_a_team_ids(self):
        """Get the user ids of every non-freshman."""
        a_name_list = getenv("A_TEAM_LIST").split(", ")
        return [member["user_id"] for member in self.get_member_list() if member["name"] in a_name_list]

    def not_a_freshman(self, data):
        """See if user is not a freshman."""
        return data["user_id"] in self.get_a_team_ids()

    def use_google(self, text, command_used):
        """Create snide Google search from a message."""
        search_terms = text[text.find(command_used) + len(command_used):].split()
        if search_terms:
            if search_terms[0][0] == '"':
                for i, term in enumerate(search_terms):
                    if term[-1] == '"':
                        search_terms = search_terms[0:i+1]
                        break
            url = "http://letmegooglethat.com/?q="
            for term in search_terms:
                url += ''.join(ch for ch in term if ch.isalnum()) + "+"  # make term alphanumeric and add it to url
            url = url[:-1]
            if url[-1] != '=' and url[-1] != '+':  # if usable search terms were inputted
                self.send_message("use Google\n"+url)

    def chat_stats(self):
        """Display number and percentage of users who have this chat muted."""
        # Can't send % sign to GroupMe. Results in response code 500: Internal Server Error.
        def num_muted():
            muted_members = 0
            members = self.get_member_list()
            for member in members:
                if member["muted"]:
                    muted_members += 1
            percent_muted = round(muted_members / len(members) * 100)
            self.send_message("{} users of {}, ({} percent), have this chat muted.".format(muted_members, len(members), percent_muted))

        def a_team_muted():
            a_team = [member for member in self.get_member_list() if member["user_id"] in getenv("A_TEAM_LIST")]
            if (len(a_team) == 0):
                return
            muted_members = 0
            for member in a_team:
                if member["muted"]:
                    muted_members += 1
            percent_muted = str(round(muted_members / len(a_team) * 100))
            self.send_message("{} SAs/JAs/RAs of {}, ({} percent), have this chat muted".format(muted_members, len(a_team), percent_muted))

        num_muted()
        a_team_muted()

