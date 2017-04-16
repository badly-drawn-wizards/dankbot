from yowsup.common.tools import Jid

from traceback import print_exc
from urllib.request import urlopen, urlretrieve, HTTPError, Request
from urllib.parse import urlparse
from datetime import datetime
from random import choice
from tempfile import NamedTemporaryFile
from os.path import expanduser
import re
import json


def fetchJson(url):
    print("Fetching json from {}".format(url))
    with urlopen(Request(url, headers={'User-Agent':"DankBot"})) as response:
        return json.loads(response.read().decode())

class DankCommandProcessor:
    def process(self, ctxt, cmd, body):
        return False

class DankMemeBank:
    ALL_TYPES = ["image", "youtube", "selfpost"]
    DEFAULT_TYPES = ["image", "youtube"]
    DANK_FRESHNESS = 1800 # 15 minutes
    def __init__(self, subreddit, submission_types=None):
        if submission_types is None:
            submission_types = self.DEFAULT_TYPES
        self.submission_types = submission_types
        self.subreddit = subreddit
        self.memes = []
        self.last_updated = None

    def doMeme(self, ctxt, location):
        now = datetime.utcnow()
        if len(self.memes) == 0 or (now - self.last_updated).total_seconds() > self.DANK_FRESHNESS:
            self.fetchMemes()
            self.last_updated = now
        meme = choice(self.memes)
        (submission_type, title, data) = meme
        if submission_type == "image":
            url = data
            ext = url[-4:]
            location += ext
            urlretrieve(url, location) # Ultra mega terrible, I know. Just wait until you see the eval command.
            promise = ctxt.reply(image=location)
        if submission_type == "youtube":
            url = data
            promise = ctxt.reply("{}\n{}".format(title, url))
        if submission_type == "selfpost":
            selftext = data
            promise = ctxt.reply("*{}*\n{}".format(title, selftext))
        self.memes.remove(meme)
        return promise


    def fetchMemes(self):
        print("Fetching memes")
        self.memes.clear()
        submissions = fetchJson("https://reddit.com/r/{}.json".format(self.subreddit))["data"]["children"]
        for submission in submissions:
            submission = submission["data"]
            url = submission["url"]
            title = submission["title"]
            selftext = submission["selftext"]
            probably_image = url.endswith(".jpg") or url.endswith(".png")
            probably_youtube = urlparse(url).hostname in ["youtube.com", "youtu.be"]
            probably_self_post = submission["is_self"]
            if probably_image:
                meme = ("image", title, url)
            elif probably_youtube:
                meme = ("youtube", title, url)
            elif probably_self_post:
                meme = ("selfpost", title, selftext)
            else:
                meme = (None, None, None)
            (submission_type, _, _) = meme
            if submission_type is not None and submission_type in self.submission_types:
                self.memes.append(meme)

        print("Got {} memes".format(len(self.memes)))

class DankGroups(DankCommandProcessor):
    MEME_COMMAND = re.compile("group (?P<subcommand>\\w+)(\s+(?P<group>\\w+))?")
    def __init__(self, groups):
        self.groups = groups
    def process(self, ctxt, cmd):
        match = self.MEME_COMMAND.match(cmd)
        if match:
            subcommand = match.group("subcommand")
            group = match.group("group")
            print("Group is {}".format(group))
            if subcommand == "list":
                ctxt.reply("THE LIST OF GROUPS YOU CAN JOIN ARE:\n{}".format("\n".join(self.groups.keys())))
            elif subcommand == "add":
                if group in self.groups:
                    ctxt.addToGroup(self.groups[group]['jid'])
                else:
                    ctxt.reply("THAT IS NOT A GROUP, HUMAN")
            else:
                ctxt.reply("I DO NOT RECOGNIZE THE '{}' GROUP SUBCOMMAND.".format(subcommand))
        return bool(match)



class DankMeme(DankCommandProcessor):
    MEME_COMMAND = re.compile("(?P<cmd>\\w+)")
    LOCATION = "/tmp/memes"

    def __init__(self, defaultBlacklist, groups, memeInfo):
        self.defaultBlacklist = defaultBlacklist
        self.groups = groups
        self.memeInfo = memeInfo
        self.memeBanks = {meme: DankMemeBank(**config) for meme, config in memeInfo.items()}

    def process(self, ctxt, cmd):
        match = self.MEME_COMMAND.match(cmd)
        if match:
            cmd = match.group("cmd")
            memeInfo = self.memeInfo.get(cmd.lower())
            print("Meme is {}".format(cmd))
            if memeInfo:
                shouldDoMeme = True
                if ctxt.isGroupMessage():
                    for group, config in self.groups.items():
                        jid = config.get('jid')
                        if 'blacklist' in config:
                            blacklist = config['blacklist']
                        else:
                            blacklist = self.defaultBlacklist
                        if jid == ctxt.getFrom():
                            break
                    else:
                        group = None
                        blacklist = DEFAULT_BLACKLIST
                    print("Meme is {} and blacklist is {}".format(cmd, blacklist))
                    if cmd in blacklist:
                        shouldDoMeme = False

                if shouldDoMeme:
                    self.memeBanks[cmd].doMeme(ctxt,self.LOCATION)
                else:
                    ctxt.reply("THE COMMAND /{} IS BLACKLISTED".format(cmd, ("FOR THE GROUP '{}'".format(group) if group else "")))
                return True
        return False

class DankAdmin(DankCommandProcessor):
    DENIED_MESSAGES = [
        "USERNAME IS NOT IN THE SUDOERS FILE. THIS INCIDENT WILL BE REPORTED TO SANTA.",
        "YOU ARE NOT WORTHY.",
        "I DO NOT LIKE YOU ENOUGH TO DO THAT.",
        "YOUR MOTHER WAS A HAMSTER AND YOUR FATHER SMELT OF ELDERBERRIES."
    ]
    ADMIN_COMMAND = re.compile("^admin (?P<subcommand>\\w+)\\s*(?P<body>.+)?$")

    def __init__(self, groups, admins):
        self.groups = groups
        self.admins = admins

    def process(self, ctxt, cmd):
        match = self.ADMIN_COMMAND.match(cmd)
        if match:
            subcommand = match.group("subcommand")
            body = match.group("body")
            if ctxt.getAuthor() not in self.admins:
                ctxt.reply(choice(self.DENIED_MESSAGES))
            elif subcommand == "setname":
                if body:
                    ctxt.setName(body)
                else:
                    ctxt.reply("Expected name")
            elif subcommand == "setstatus":
                if body:
                    ctxt.setStatus(body)
                else:
                    ctxt.reply("Expected name")
            elif subcommand == "eval":
                result = eval(body)
                ctxt.reply("=> {}".format(result))
            elif subcommand == "kill":
                ctxt.kill()
            elif subcommand == "introduction":
                ctxt.reply("HELLO FELLOW HUMANS.\nI COME IN PEACE WITH DANK MEMES.\nJUST SAY /meme.")
            elif subcommand == "promote":
                if ctxt.isGroupMessage():
                    ctxt.promote()
                else:
                    ctxt.reply("YOU CAN ONLY USE THAT COMMAND IN A GROUP")
            elif subcommand == "saygroup":
                [group, text] = body.split(" ", 1)
                if group in self.groups:
                    ctxt.send(self.groups[group]['jid'], text)
                else:
                    ctxt.reply("THAT IS NOT A GROUP, HUMAN")
            else:
                ctxt.reply("I DO NOT RECOGNIZE THE '{}' ADMIN SUBCOMMAND.".format(subcommand))
        return bool(match)


class DankChain(DankCommandProcessor):
    def __init__(self, chain):
        self.chain = chain
    def process(self, ctxt, cmd):
        for processor in self.chain:
            if processor.process(ctxt, cmd):
                return True
        return False

class DankBot(DankCommandProcessor):
    NAME = "DankBot"
    STATUS = "I AM TOTALLY NOT A ROBOT."
    def __init__(self, chain=None, config=None):
        if config is None:
            config = self.readConfig()
        self.config = config
        if chain is None:
            chain = self.getDefaultChain()
        self.chain = chain

    def readConfig(self):
        with open(expanduser("~/.config/dankbot.json")) as f:
            return json.load(f)

    def getDefaultChain(self):
        defaultBlacklist = self.config['default_blacklist']
        groups = self.config['groups']
        memeInfo = self.config['meme_info']
        admins = self.config['admins']
        return DankChain([DankAdmin(groups, [Jid.normalize(jid) for jid in admins]), DankMeme(defaultBlacklist, groups, memeInfo), DankGroups(groups)])

    def process(self, ctxt, cmd):
        try:
            result = self.chain.process(ctxt, cmd)
            if not result:
                ctxt.reply("I DO NOT UNDERSTAND WHAT HUMAN IS SAYING.")
        except Exception as e:
            print(print_exc())
            print(e)
            ctxt.reply("SOMETHING SHORT-CIRCUITED")
        return True
