import asyncio
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
import sqlite3
from pathlib import Path
from os.path import join, split
from lib.keabot import Keabot

async def main():
    ROOT_DIR = Path("/app")
    parser = argparse.ArgumentParser("Keabot", "Run to start the discord bot Keabot. Tracks 'reddit gold', allows image upload and random reposting.")
    parser.add_argument(
            "-t",
            dest="token_file",
            default="/secret/discord_token",
            required=False,
            type=Path
            )

    parser.add_argument(
            "-d",
            dest="data_folder",
            default=ROOT_DIR / "data", 
            type=Path,
            required=False
            )
    parser.add_argument(
            "-c",
            dest="config_loc",
            default= ROOT_DIR/ "config.json",
            type=Path,
            required=False
            )

    args = parser.parse_args()
    TOKEN_FILE = args.token_file
    DATA_DIR:Path = args.data_folder
    CONFIG_LOC:Path = args.config_loc
    TOKEN = None

    h = logging.handlers.RotatingFileHandler(
        filename=DATA_DIR / "logs" / "keabot.log",
        maxBytes=1000*1000*50,
        backupCount=7
    )
    logging.basicConfig(
            handlers=[h],
            level=logging.DEBUG
            )
    logger = logging.getLogger(__name__)
    config = json.loads(CONFIG_LOC.read_text())
    prefix = config["prefix"]
    
    if TOKEN_FILE:
        logger.info("Opening token file %s", TOKEN_FILE)
        try:
            TOKEN = TOKEN_FILE.read_text()
        except:
            logger.critical("Failed to open file: %s", TOKEN_FILE)

    if not TOKEN:
        TOKEN = os.environ.get("DISCORD_TOKEN")

    if not TOKEN:
        logger.error("No token specified. Provide on command line or in environment")
        sys.exit(1)

    #database setup
    db_conn = sqlite3.connect(DATA_DIR / "db" / "keabot.sqlite3")
    db_conn.row_factory = sqlite3.Row
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guild_reactions = True
    intents.presences = True
    description = """Keaton's chatbot to handle random image posting and score tracking."""

    keabot = Keabot(
        db_conn=db_conn,
        root_dir=ROOT_DIR,
        data_dir=DATA_DIR,
        intents=intents,
        description=description,
        command_prefix=prefix
        )
    await keabot.start(TOKEN)
if __name__ == "__main__":
    asyncio.run(main())
    