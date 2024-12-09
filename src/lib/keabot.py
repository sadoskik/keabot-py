import discord
from discord import Member, Guild, User
import discord.ext
from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional, Union, Literal

import logging
from sqlite3 import Row, Connection
from pathlib import Path
import tempfile
import hashlib


from .score_helper import *
from .image_helper import *


logger = logging.getLogger(__name__)



class Keabot(commands.Bot):
    
    def __init__(self, *args, db_conn: Connection, root_dir: Path, data_dir: Path, **kwargs):
        super().__init__(*args, **kwargs)
        self.ROOT_DIR = root_dir
        self.DATA_DIR = data_dir
        self.db_conn = db_conn
        @self.event
        async def on_ready():
            logger.info('We have logged in as %s', self.user)
            logger.info("ROOT_DIR: %s", self.ROOT_DIR)
            logger.info("DATA_DIR: %s", self.DATA_DIR)   
            await self.tree.sync() 
            logger.info("Ready")
        @self.command(name="leaderboard")
        async def leaderboard(ctx:Context, number:Optional[int]=5):
            logger.info("leaderboard called")
            
            scoreboard = discord.Embed(title="Scoreboard", color=discord.Color.from_rgb(255, 0, 0))
            i = 0
            for user in get_top_scores(self.db_conn, ctx.guild.id):
                i += 1
                if i == number:
                    break
                user: Row
                members = await ctx.guild.query_members(user_ids=[user["user_id"]], limit=1)
                if members:
                    member = members[0]
                    scoreboard.add_field(name = f"{i}.", value = f"{member.display_name}: {user['score']}")
                
            await ctx.reply(embed = scoreboard)
            return
        @self.command(name="score")
        async def score(ctx:Context, member:Optional[Member]):
            if not member:
                member = ctx.author
            
            score = get_score(self.db_conn, ctx.guild.id, member.id)
            await ctx.reply(f"Your score is: {score}")
        @self.command(name="addimage")
        async def addImage(ctx: Context, *tags, attachments:commands.Greedy[discord.Attachment]):
            VALID_FILE_EXTENSIONS = ["audio", "image", "video"]
            tags = list(tags)
            for attachment in attachments:
                if not attachment.content_type:
                    await ctx.reply(f"{attachment.filename} does not have a content type. Skipping for safety")
                file_extension = None
                for valid_type in VALID_FILE_EXTENSIONS:
                    if valid_type in attachment.content_type:
                        file_extension = valid_type
                        break
                else:
                    await ctx.reply(f"{attachment.filename} does not appear to be a supported type ({attachment.content_type}). Skipping")
                    continue
                logger.info("Attachment %s is valid type %s", attachment.filename, file_extension)
                
                attachment_content = await attachment.read()
                file_hash = hashlib.sha256(attachment_content).hexdigest()
                ext = attachment.filename.split('.')[-1]
                new_filename = f"{file_hash}.{ext}"
                file_path = self.DATA_DIR / "images" / new_filename
                if file_path.exists():
                    logger.warning("File already exists")

                file_path.write_bytes(attachment_content)
                logger.info("Wrote file to disk: %s", file_path)
                add_image(self.db_conn, ctx.guild.id, tags, new_filename)
                await ctx.reply(f"{attachment.filename} added to {", ".join(tags)}")
        @self.command(name="tags")
        async def tags(ctx: Context):
            tags = get_tags(self.db_conn, ctx.guild.id)
            if not tags:
                await ctx.reply("There are no tags registered in this server")
                return
            tags_embed = discord.Embed(title="Tags", color=discord.Color.from_rgb(255, 0, 0))
            for tag in tags:
                tags_embed.add_field(name=tag, value="")
                i += 1
            await ctx.reply(embed=tags_embed)
        @self.command(name="deletetag")
        async def deleteTag(ctx: Context, tag:str):
            await ctx.reply("Not implemented yet")
        @self.command(name="deleteimage")
        async def deleteImage(ctx: Context, message:discord.Message):
            await ctx.reply("Not implemented yet")
        @self.command(name="postimage")
        async def postImage(ctx: Context, tag:str):
            logger.info("Images requested for tag '%s'", tag)
            image_filename = get_random_image(self.db_conn, ctx.guild.id, tag)
            if not image_filename:
                await ctx.reply("An image could not be found for that tag.")
                return
            image_filepath = self.DATA_DIR / "images" / image_filename
            await ctx.reply(file=discord.File(image_filepath))
            return

        @self.event
        async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
            if not reaction.is_custom_emoji() or reaction.emoji.name != "gold":
                return
            receiver = reaction.message.author
            server_id = reaction.message.guild.id
            gifter = user
            
            logger.info("Gold add reaction event. Gifter: %s, Receiver: %s, Server: %d", gifter.display_name, receiver.display_name, server_id)
            
            increment_score(self.db_conn, server_id, receiver.id)

            #check for selfish
            if gifter == receiver:
                logger.info("%s gave themself gold", gifter)
                increment_self(self.db_conn, server_id, gifter.id)
            else:
                increment_given(self.db_conn, server_id, gifter.id)

        @self.event
        async def on_reaction_remove(reaction, user):
            if not reaction.is_custom_emoji() or reaction.emoji.name != "gold":
                return
            receiver = reaction.message.author
            server_id = reaction.message.guild.id
            gifter = user
            
            logger.info("Gold remove reaction event. Gifter: %s, Receiver: %s, Server: %d", gifter.display_name, receiver.display_name, server_id)
            
            decrement_score(self.db_conn, server_id, receiver.id)

            #check for selfish
            if gifter == receiver:
                logger.info("%s took gold from themself", gifter)
                decrement_self(self.db_conn, server_id, gifter.id)
            else:
                decrement_given(self.db_conn, server_id, gifter.id) 

