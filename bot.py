#!/usr/bin/env python3
"""
GoFile Uploader Bot - Main Entry Point (COMPLETE REWRITE with Pyrogram)
"""

import asyncio
import logging
import sys
import signal
import os
from pathlib import Path

from pyrogram import Client
from pyrogram.errors import ApiIdInvalid, ApiIdPublishedFlood, AccessTokenInvalid

from config import Config
from database import Database
from handlers import BotHandlers
from utils import Utils
from downloader import MediaDownloader

# Create required directories first
Path("logs").mkdir(exist_ok=True)
Path("session").mkdir(exist_ok=True)
Path("downloads").mkdir(exist_ok=True)
Path("temp").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class GoFileBot:
    """Main bot class using Pyrogram"""
    
    def __init__(self):
        self.config = Config()
        
        # Initialize Pyrogram client
        self.app = Client(
            "gofile_bot",
            api_id=self.config.API_ID,
            api_hash=self.config.API_HASH,
            bot_token=self.config.BOT_TOKEN,
            workdir="./session"
        )
        
        # Initialize components
        self.database = Database()
        self.utils = Utils(self.config, self.database)
        self.downloader = MediaDownloader(self.config, self.utils)
        self.handlers = BotHandlers(self.app, self.database, self.utils, self.downloader, self.config)
        
        self.is_running = False
        
    async def initialize(self) -> bool:
        """Initialize all bot components"""
        try:
            logger.info("🚀 Starting GoFile Uploader Bot...")
            
            # Validate configuration
            self.config.validate_config()
            logger.info("✅ Configuration validated")
            
            # Initialize database
            await self.database.initialize()
            logger.info("✅ Database connected")
            
            # Test bot credentials
            await self.app.start()
            bot_info = await self.app.get_me()
            logger.info(f"✅ Bot authenticated: @{bot_info.username} ({bot_info.first_name})")
            
            # Setup handlers
            await self.handlers.setup_handlers()
            logger.info("✅ Handlers configured")
            
            self.is_running = True
            logger.info(f"🎉 Bot {bot_info.first_name} is ready!")
            
            return True
            
        except ApiIdInvalid:
            logger.error("❌ Invalid API_ID provided. Get it from https://my.telegram.org")
            return False
        except AccessTokenInvalid:
            logger.error("❌ Invalid BOT_TOKEN provided. Get it from @BotFather")
            return False
        except ValueError as e:
            logger.error(f"❌ Configuration error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def start(self):
        """Start the bot"""
        if not await self.initialize():
            logger.error("❌ Failed to initialize bot")
            return
            
        try:
            logger.info("🔄 Bot is now running...")
            
            # Setup signal handlers for graceful shutdown
            def signal_handler(signum, frame):
                logger.info(f"📡 Received signal {signum}, shutting down...")
                asyncio.create_task(self.stop())
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Keep the bot running
            await self.app.idle()
            
        except KeyboardInterrupt:
            logger.info("⌨️ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Runtime error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the bot gracefully"""
        if self.is_running:
            logger.info("🛑 Stopping bot...")
            self.is_running = False
            
            try:
                # Stop pyrogram client
                if self.app.is_connected:
                    await self.app.stop()
                    
                # Close database connection
                await self.database.close()
                
                # Cleanup temporary files
                await self.utils.cleanup_temp_files()
                
                logger.info("✅ Bot stopped successfully")
                
            except Exception as e:
                logger.error(f"❌ Error during shutdown: {e}")


async def main():
    """Main entry point"""
    # Show startup banner
    print("🤖 GoFile Uploader Bot v2.0")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required")
        sys.exit(1)
    
    bot = GoFileBot()
    
    try:
        await bot.start()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        sys.exit(1)
