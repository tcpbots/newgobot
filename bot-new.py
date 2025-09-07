#!/usr/bin/env python3
"""
GoFile Uploader Telegram Bot - Main Entry Point
"""

import asyncio
import logging
import sys
from telebot.async_telebot import AsyncTeleBot
from config import Config
from database import Database
from handlers import BotHandlers
from utils import Utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class GoFileBot:
    def __init__(self):
        self.config = Config()
        self.bot = AsyncTeleBot(self.config.BOT_TOKEN)
        self.database = Database()
        self.utils = Utils(self.config, self.database)
        self.handlers = BotHandlers(self.bot, self.database, self.utils, self.config)
        
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("Initializing GoFile Uploader Bot...")
            
            # Initialize database
            await self.database.initialize()
            logger.info("Database initialized")
            
            # Setup handlers
            self.handlers.setup_handlers()
            logger.info("Handlers set up")
            
            # Test bot
            bot_info = await self.bot.get_me()
            logger.info(f"Bot @{bot_info.username} is ready!")
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def start(self):
        """Start the bot"""
        if await self.initialize():
            logger.info("Starting bot polling...")
            try:
                await self.bot.polling(non_stop=True, interval=0)
            except Exception as e:
                logger.error(f"Polling error: {e}")
        else:
            logger.error("Failed to initialize bot")


async def main():
    bot = GoFileBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")


if __name__ == "__main__":
    asyncio.run(main())