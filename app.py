from os import getenv
from flask import Flask, request
from gmbot import GroupMeBot
from lfbot import LFBot
from sabot import SABot
from rabot import RABot


app = Flask(__name__)


test_bot = RABot(getenv("TEST_BOT_ID"), getenv("TEST_BOT_NAME"), getenv("TEST_GROUP_ID"))
@app.route("/test", methods=["POST"])
def read_test_group():
    data = request.get_json()
    test_bot.chat(data)
    return "OK", 200


lf_bot = LFBot(getenv("LF_BOT_ID"), getenv("LF_BOT_NAME"), getenv("LF_GROUP_ID"))
@app.route("/lf", methods=["POST"])
def read_lf_group():
    data = request.get_json()
    lf_bot.chat(data)
    return "OK", 200


sa_bot = SABot(getenv("SA_BOT_ID"), getenv("SA_BOT_NAME"), getenv("SA_GROUP_ID"))
@app.route("/sa", methods=["POST"])
def read_sa_group():
    data = request.get_json()
    sa_bot.chat(data)
    return "OK", 200


ra_bot = RABot(getenv("RA_BOT_ID"), getenv("RA_BOT_NAME"), getenv("RA_GROUP_ID"))
@app.route("/ra", methods=["POST"])
def read_ra_group():
    data = request.get_json()
    ra_bot.chat(data)
    return "OK", 200
