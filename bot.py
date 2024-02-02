import re
import discord
import logging
import logging.handlers
import json
import os
import sys
import time
import atexit
import random
import linecache
import argparse
from os.path import join, split

ROOT_DIR = split(__file__)[0]

parser = argparse.ArgumentParser("Keabot", "Run to start the discord bot Keabot. Tracks 'reddit gold', allows image upload and random reposting.")
parser.add_argument("-t", dest="tokenLoc", default=join(ROOT_DIR, "./token.json"),  required=False)
parser.add_argument("-d", dest="dataFolder", default=join(ROOT_DIR, "./Data/"), required=False)

args = parser.parse_args()
DATA_DIR = os.path.abspath(args.dataFolder)
TOKEN_LOC = os.path.abspath(args.tokenLoc)
IMAGES_DIR = join(DATA_DIR, "Images")
prefix = ".."

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s]:[%(levelname)s] %(message)s')

streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.DEBUG)
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

fileHandler = logging.handlers.RotatingFileHandler(
    join(DATA_DIR, "logs", "keabot.log"), maxBytes=(1048576*5), backupCount=7)
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

with open(TOKEN_LOC, "r") as f:
    configs = json.load(f)
    discordToken = configs["discord"]

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

#image function support
lastSentFile = ""

#database setup
score_filename = join(ROOT_DIR, "clownScore.json")
if os.access(score_filename, os.F_OK):
    with open(score_filename, "r") as read_file:
        scoreDB = json.load(read_file)
    backupName = time.strftime("clownScore_%Y_%m_%d_%H_%M.json")
    with open(
        join(DATA_DIR, "backup", backupName),
        "w") as f:
        json.dump(scoreDB, f)
    
else:
    print("No clownScore found")
    sys.exit()

clowns = {}

folders = os.listdir(IMAGES_DIR)
for f in folders:
    clowns[f] = True
with open("clowns.json", "w") as f:
    json.dump(clowns, f)


async def backup():
    with open("clowns.json", "w") as f:
        json.dump(clowns, f)
    with open("clownScore.json", "w") as f:
        json.dump(scoreDB, f)
    print("Backed up!")

atexit.register(backup)
###


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print ('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))



@client.event
async def on_ready():
    logger.info('We have logged in as %s', client.user)
    logger.info("ROOT_DIR: %s", ROOT_DIR)

@client.event
async def on_message(message: discord.Message):
    
    if message.author == client.user or message.author.bot:
        logger.debug("Sender was me or bot")
        return
    if not message.content.startswith(prefix):
        logger.debug("Sender did not use ..")
        return
    
    args = message.content.lower().strip()[len(prefix):].split(' ')
    command = args.pop(0)
    server = str(message.guild.id) 
    user = str(message.author.id) 

    logger.info("Message: %s", message)
    logger.info("Message content: %s", message.content)
    #new server handler
    if server not in scoreDB:
        scoreDB[server] = {}
        logger.info("New server created in DB: %s", server)
    #

    #reddit gold commands
    if(command == "leaderboard"):
        await leaderboard(message)
        return
    if(command == "score"):
        await getScore(message)
        return
    #

    

    #random image commands
    if(command == "addimage"):
        await addimage(message, args)
        return
    if(command == "delete"):
        await delete(message, args)
        return
    if(command in clowns):
        await postImage(message, command)
        return
    if(command == "addclown"):
        await addClown(message, args)
        return
    if(command == "clowns"):
        await listClowns(message)
        return
    if(command == "removeClown"):
        await removeClown(message, args)
        return
    #
    


@client.event
async def on_reaction_add(reaction, user):
    if reaction.is_custom_emoji() and reaction.emoji.name != "gold":
        logger.debug("Not gold emoji")
        return
    receiver = str(reaction.message.author.id) 
    server = str(reaction.message.guild.id) 
    gifter = str(user.id) 
    
    logger.info("Gold reaction event. Gifter: %s, Receiver: %s, Server: %s", gifter, receiver, server)
    if server not in scoreDB:
        scoreDB[server] = {}
        logger.info("Created server object in scoreDB for %s", server)
    #new user handling
    if gifter not in scoreDB[server]:
        scoreDB[server][gifter] = {}
        scoreDB[server][gifter]["score"] = 0
        scoreDB[server][gifter]["given"] = 0
        scoreDB[server][gifter]["self"] = 0

    if receiver not in scoreDB[server]:
        scoreDB[server][receiver] = {}
        scoreDB[server][receiver]["score"] = 0
        scoreDB[server][receiver]["given"] = 0
        scoreDB[server][receiver]["self"] = 0
    #

    #check for selfish
    if gifter == receiver:
        logger.info("%s gave themself gold", gifter)
        scoreDB[server][gifter]["self"] += 1
        await backup()
        return 
    #

    #increment relevant values
    scoreDB[server][receiver]["score"] += 1
    scoreDB[server][gifter]["given"] += 1
    #
    #update name
    scoreDB[server][gifter]["name"] = user.display_name

    await backup()
    logger.info("%s gave %s gold", gifter, receiver)

@client.event
async def on_reaction_remove(reaction, user):
    if reaction.is_custom_emoji() and reaction.emoji.name != "gold":
        logger.debug("Not gold emoji")
        return
    receiver = str(reaction.message.author.id )
    server = str(reaction.message.guild.id )
    taker = str(user.id )
    
    if server not in scoreDB:
        scoreDB[server] = {}
        logger.info("Add new server to scoreDB for %s", server)
    
    #new user handling
    if taker not in scoreDB[server]:
        scoreDB[server][taker]["score"] = 0
        scoreDB[server][taker]["given"] = 0
        scoreDB[server][taker]["self"] = 0
        return
    if receiver not in scoreDB[server]:
        scoreDB[server][receiver]["score"] = 0
        scoreDB[server][receiver]["given"] = 0
        scoreDB[server][receiver]["self"] = 0
        return
    #

    #check for selfish
    if taker == receiver:
        logger.info("%s took gold from themself", taker)
        scoreDB[server][taker]["self"] -= 1
        await backup()
        return 
    #
    
    #increment relevant values
    scoreDB[server][receiver]["score"] -= 1
    scoreDB[server][taker]["given"] -= 1
    #
    await backup()
    logger.info("%s took gold from %s", taker, receiver)  


async def leaderboard(message):
    logger.info("leaderboard called")
    server = str(message.guild.id) 
    scoreboard = discord.Embed(title="Scoreboard", color=discord.Color.from_rgb(255, 0, 0))
    i = 1

    #address this when bot permissions are updated
    def sortFunc(userObj):
        return scoreDB[server][userObj]["score"]
    for userID in sorted(scoreDB[server], key=sortFunc, reverse=True):
        print(userID)
        print(scoreDB[server][userID]["score"])
    for userID in sorted(scoreDB[server], key=sortFunc, reverse=True):
        if "name" in scoreDB[server][userID]:
            output = scoreDB[server][userID]["name"] + ": " + str(scoreDB[server][userID]["score"])
            scoreboard.add_field(name = str(i)+".", value = output, inline=False)
            i += 1
        if i == 5:
            break
    await message.channel.send(embed = scoreboard)
    return

async def getScore(message):
    server = str(message.guild.id) 
    score = scoreDB[server][str(message.author.id)]["score"]
    await message.reply("Your score is: " + str(score))
    return

async def addimage(message: discord.Message, args):
    server = str(message.guild.id) 
    if len(args) == 0:
        logger.info("No argument was given")
        await message.reply("No clown given, bozo")
        return
    clownName = args[0]
    logger.info("Adding image for %s", clownName)
    if clownName not in clowns:
        logger.warning("Tried to add an image to a clown that doesn't exist")
        await message.reply("That clown doesn't exist")
        return
    fileNonce = time.strftime("_%Y_%m_%d_%H_%M_%S_")
    if len(message.attachments) > 30:
        logger.warning("User attempted to upload more than 30 (%s)", str(len(message.attachments)))
        await message.reply("Woah! Don't upload so many at once!")
        return
    i = 0
    for image in message.attachments:
        if image.size > pow(10, 8): # 100MB
            logger.warning("User attempted to upload a more than 100MB file (%s)", str(image.size/1000) + "KB")
            await message.reply("One of these files was way too big. Stopping. (%s)" % str(image.size/1000) + "KB")
            return
        extension = image.filename[-4:]
        path = join(
            IMAGES_DIR,
            clownName,
            clownName + fileNonce + str(i) + extension)
        await image.save(path)
        await message.reply("Image(s) saved")
        i += 1

    return

async def delete(message: discord.Message, args):
    server = str(message.guild.id)
    if not lastSentFile:
        logger.info("Attempt to delete with no previous post")
        await message.reply("No previous image post found")
        return
    try:
        os.remove(lastSentFile)
    except:
        logger.error("Delete image error.")
        await message.reply("Failed to delete")
        return
    logger.info("Deleted %s", lastSentFile)
    await message.reply("Image deleted")
    return

async def postImage(message, name):
    global lastSentFile
    server = str(message.guild.id) 
    
    path = join(IMAGES_DIR, name)
    if os.access(path, os.F_OK):
        files = os.listdir(path)
        if len(files) < 1:
            logger.warning("Attempt to post for user with no images")
            await message.reply("No images for this clown exist")
            return
        n = random.randint(0, len(files)-1)
        fileToSend = files[n]
        fileToSend = join(path, fileToSend)
        with open(fileToSend, "rb") as f:
            fpVar = discord.File(f)
            await message.channel.send(file=fpVar)
        logger.info("Sent file: %s", fileToSend)
        lastSentFile = fileToSend
    else:
        await message.reply("This clown doesn't exist")
    return

async def addClown(message, args):
    server = str(message.guild.id) 
    if os.access(join(IMAGES_DIR, args[0]), os.F_OK):
        await message.reply("This clown already exists")
    else:
        os.mkdir(join(IMAGES_DIR, args[0]))
        logger.info("Created directory for clown %s", args[0])
        await message.reply("Clown created: " + args[0])
        clowns[args[0]] = True
    await backup()
    return

async def listClowns(message):
    server = str(message.guild.id) 
    logger.info("listClowns called")
    scoreboard = discord.Embed(title="Scoreboard", color=discord.Color.from_rgb(255, 0, 0))
    files = os.listdir(IMAGES_DIR)
    i = 1
    for f in files:
        scoreboard.add_field(name = str(i)+".", value = f, inline=False)
        i += 1
    await message.channel.send(embed = scoreboard)

    return

async def removeClown(message, args):
    server = str(message.guild.id) 
    logger.warning("Attempt to use unfinished removeClown function")
    await message.reply("This is not implemented yet.")
    return



client.run(discordToken)
