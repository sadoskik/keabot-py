import discord
import asyncio
import json
from datetime import datetime
import os
import logging
import logging.handlers
import argparse

class DiscordChatLogger:
    def __init__(self, bot_token, server_id, log_level=logging.INFO):
        """
        Initialize the Discord chat logger with advanced logging
        
        Args:
            bot_token (str): Discord bot token
            server_id (int): ID of the server to log
            log_level (int): Logging level (default: logging.INFO)
        """
        # Configure logging
        self.logger = self._setup_logging(log_level)
        
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        self.client = discord.Client(intents=intents)
        self.token = bot_token
        self.server_id = server_id
        
        # Setup event listeners
        @self.client.event
        async def on_ready():
            self.logger.info(f'Logged in as {self.client.user}')
            await self.log_channels()
        
        # Add error logging for discord.py events
        @self.client.event
        async def on_error(event, *args, **kwargs):
            self.logger.error(f"Error in event {event}: {args} {kwargs}")
    
    def _setup_logging(self, log_level):
        """
        Set up comprehensive logging configuration
        
        Args:
            log_level (int): Logging level to set
        
        Returns:
            logging.Logger: Configured logger
        """
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create a logger
        logger = logging.getLogger('DiscordChatLogger')
        logger.setLevel(log_level)
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        
        # Rotating File Handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename='logs/discord_chat_logger.log',
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        
        # Error File Handler (only logs errors and critical)
        error_handler = logging.FileHandler('logs/discord_chat_errors.log')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        
        return logger
    
    async def log_channels(self):
        """
        Log messages from all text channels in the specified server
        """
        # Get the server
        server = self.client.get_guild(self.server_id)
        if not server:
            self.logger.error(f"Could not find server with ID {self.server_id}")
            return
        
        # Create output directory
        output_dir = f'discord_logs_{server.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.makedirs(output_dir, exist_ok=True)
        
        # Iterate through text channels
        for channel in server.text_channels:
            try:
                await self.log_channel_messages(channel, output_dir)
            except discord.errors.Forbidden:
                self.logger.warning(f"No access to channel: {channel.name}")
            except Exception as e:
                self.logger.error(f"Error logging channel {channel.name}: {e}")
    
    async def log_channel_messages(self, channel, output_dir, limit=10000):
        """
        Log messages from a specific channel
        
        Args:
            channel (discord.TextChannel): Channel to log
            output_dir (str): Directory to save logs
            limit (int): Maximum number of messages to retrieve
        """
        # Create channel-specific log file
        log_file = os.path.join(output_dir, f'{channel.name}_messages.json')
        
        # Retrieve messages
        messages = []
        async for message in channel.history(limit=limit):
            # Extract relevant message information
            message_data = {
                'id': str(message.id),
                'author': str(message.author),
                'content': message.content,
                'timestamp': message.created_at.isoformat(),
                'channel': channel.name,
                'attachments': [att.url for att in message.attachments]
            }
            messages.append(message_data)
        
        # Save to JSON
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f'Logged {len(messages)} messages from #{channel.name}')
        except IOError as e:
            self.logger.error(f"Failed to write log file for {channel.name}: {e}")
    
    def run(self):
        """
        Run the Discord bot to collect logs
        """
        try:
            self.client.run(self.token)
        except Exception as e:
            self.logger.critical(f"Critical error running bot: {e}")

def parse_arguments():
    """
    Parse command-line arguments for the Discord chat logger
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Discord Chat Log Scraper',
        epilog='Ensure you have the necessary bot permissions before running.'
    )
    
    # Bot token argument (required)
    parser.add_argument(
        '-t', '--token', 
        type=str, 
        required=True, 
        help='Discord bot token'
    )
    
    # Server ID argument (required)
    parser.add_argument(
        '-s', '--server-id', 
        type=int, 
        required=True, 
        help='Discord server ID to log'
    )
    
    # Optional log level argument
    parser.add_argument(
        '-l', '--log-level', 
        type=str, 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    # Optional message limit argument
    parser.add_argument(
        '-m', '--message-limit', 
        type=int, 
        default=10000,
        help='Maximum number of messages to retrieve per channel (default: 10000)'
    )
    
    return parser.parse_args()

def main():
    # Parse command-line arguments
    args = parse_arguments()
    
    # Convert log level string to logging constant
    log_level = getattr(logging, args.log_level.upper())
    
    # Configure logging
    logging.basicConfig(level=log_level)
    
    # Create logger with parsed arguments
    logger = DiscordChatLogger(
        bot_token=args.token, 
        server_id=args.server_id, 
        log_level=log_level
    )
    
    # Run the logger
    logger.run()

if __name__ == "__main__":
    main()