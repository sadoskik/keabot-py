import discord
import logging
import json
import os
import sys
import time
import atexit
import random
import linecache
import logging

client = discord.Client()
with open("token.json", "r") as f:
    configs = json.load(f)
    discordToken = configs["discord"]



#image function support
lastSentFile = ""
CURR_DIR = os.getcwd()

#
#database setup
if os.access("clownScore.json", os.F_OK):
    with open("clownScore.json", "r") as read_file:
        scoreDB = json.load(read_file)
    backupName = time.strftime("backup/clownScore_%Y_%m_%d_%H_%M.json")
    with open(backupName, "w") as f:
        json.dump(scoreDB, f)
    
else:
    print("No clownScore found")
    sys.exit()

clowns = {}

files = os.listdir(CURR_DIR + "/Images/")
for f in files:
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
    print('We have logged in as {0.user}'.format(client))
    print(CURR_DIR)

@client.event
async def on_message(message):
    
    if message.author == client.user or message.author.bot:
        print("Sender was me or bot")
        return
    if not message.content.startswith(prefix):
        print("Sender did not use ..")
        return
    
    args = message.content.lower().strip()[len(prefix):].split(' ')
    command = args.pop(0)
    server = str(message.guild.id) 
    user = str(message.author.id) 


    #new server handler
    if server not in scoreDB:
        scoreDB[server] = {}
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
async def on_message_delete(message):
    await message.channel.send(":eyes:")

@client.event
async def on_reaction_add(reaction, user):
    if reaction.custom_emoji and reaction.emoji.name != "gold":
        print("Not gold emoji")
        return
    receiver = str(reaction.message.author.id) 
    server = str(reaction.message.guild.id) 
    gifter = str(user.id) 
    
    
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
        print("%s gave themself gold" % gifter)
        print("gave self gold")
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
    print("%s gave %s gold" % (gifter, receiver))

@client.event
async def on_reaction_remove(reaction, user):
    if reaction.custom_emoji and reaction.emoji.name != "gold":
        print("Not gold emoji")
        return
    receiver = str(reaction.message.author.id )
    server = str(reaction.message.guild.id )
    taker = str(user.id )
    
    
    #new user handling
    if taker not in scoreDB[server]:
        scoreDB[server][taker]["score"] = 0
        scoreDB[server][taker]["given"] = 0
        scoreDB[server][taker]["self"] = 0
    if receiver not in scoreDB[server]:
        scoreDB[server][receiver]["score"] = 0
        scoreDB[server][receiver]["given"] = 0
        scoreDB[server][receiver]["self"] = 0
    #

    #check for selfish
    if taker == receiver:
        print("%s took gold from themself" % taker)
        scoreDB[server][taker]["self"] -= 1
        await backup()
        return 
    #
    
    #increment relevant values
    scoreDB[server][receiver]["score"] -= 1
    scoreDB[server][taker]["given"] -= 1
    #
    await backup()
    print("%s took gold from %s" % (taker, receiver))  


async def leaderboard(message):
    print()
    print("python leaderboard called")
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
    await message.channel.send("Your score is: " + str(score))
    return

async def addimage(message, args):
    server = str(message.guild.id) 
    if len(args) == 0:
        await message.channel.send("No clown given, bozo")
        return
    clownName = args[0]
    print(clownName)
    print(clowns)
    if clownName not in clowns:
        print("Tried to add an image to a clown that doesn't exist")
        await message.channel.send("That clown doesn't exist")
        return
    fileNonce = time.strftime("_%Y_%m_%d_%H_%M_%S_")
    i = 0
    for image in message.attachments:
        extension = image.filename[-4:]
        path = CURR_DIR + "/Images/" + clownName + "/" + clownName + fileNonce + str(i) + extension
        await image.save(path)
        await message.channel.send("Image saved")
        i += 1

    return

async def delete(message, args):
    server = str(message.guild.id)
    os.remove(lastSentFile)

    return

async def postImage(message, name):
    server = str(message.guild.id) 
    
    path = CURR_DIR + "/Images/" + name
    if os.access(path, os.F_OK):
        files = os.listdir(path)
        print(files)
        n = random.randint(0, len(files)-1)
        fileToSend = files[n]
        fileToSend = path + "/" + fileToSend
        with open(fileToSend, "rb") as f:
            fpVar = discord.File(f)
            await message.channel.send(file=fpVar)
        print("Sent file: " + fileToSend)
        lastSentFile = fileToSend
    else:
        await message.channel.send("This clown doesn't exist")
    return

async def addClown(message, args):
    server = str(message.guild.id) 
    if os.access("Images/" + args[0], os.F_OK):
        await message.channel.send("This clown already exists")
    else:
        os.mkdir(CURR_DIR + "/Images/" + args[0])
        print("Created directory for clown " + args[0])
        await message.channel.send("Clown created: " + args[0])
        clowns[args[0]] = True
    await backup()
    return

async def listClowns(message):
    server = str(message.guild.id) 
    print("..clowns called")
    scoreboard = discord.Embed(title="Scoreboard", color=discord.Color.from_rgb(255, 0, 0))
    
    path = CURR_DIR + "/Images"
    files = os.listdir(path)
    i = 1
    for f in files:
        scoreboard.add_field(name = str(i)+".", value = f, inline=False)
        i += 1
    await message.channel.send(embed = scoreboard)

    return

async def removeClown(message, args):
    server = str(message.guild.id) 
    return




client.run(discordToken)
