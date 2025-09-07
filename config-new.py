"""
Configuration settings and environment variables
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Bot configuration class"""
    
    # Bot settings
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is required")
    
    # Database settings
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "gofile_bot")
    
    # Admin settings
    ADMIN_IDS: List[int] = [
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
    ]
    
    # Force subscription settings
    FORCE_SUB_CHANNEL: Optional[str] = os.getenv("FORCE_SUB_CHANNEL")
    FORCE_SUB_ENABLED: bool = os.getenv("FORCE_SUB_ENABLED", "False").lower() == "true"
    
    # GoFile.io API settings
    GOFILE_API_TOKEN: Optional[str] = os.getenv("GOFILE_API_TOKEN")
    GOFILE_UPLOAD_URL: str = "https://upload.gofile.io/uploadfile"
    GOFILE_API_BASE: str = "https://api.gofile.io"
    
    # File settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "2147483648"))  # 2GB
    ALLOWED_FILE_TYPES: List[str] = [
        'document', 'photo', 'video', 'audio', 'voice', 'video_note', 'animation'
    ]
    
    # Download settings
    DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "./downloads")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "./temp")
    MAX_DOWNLOAD_SIZE: int = int(os.getenv("MAX_DOWNLOAD_SIZE", "5368709120"))  # 5GB
    
    # Performance settings
    MAX_CONCURRENT_UPLOADS: int = int(os.getenv("MAX_CONCURRENT_UPLOADS", "3"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "8192"))
    
    # Messages
    WELCOME_MESSAGE: str = """
🤖 **Welcome to GoFile Uploader Bot!**

I can help you upload files to GoFile.io and download from URLs.

**Features:**
📁 Upload any file to GoFile.io
🔗 Download from URLs and upload to GoFile
📊 Track upload/download progress
⚙️ Quality selection for videos
📱 Account management

Use /help to see all commands!
"""
    
    HELP_MESSAGE: str = """
📋 **Available Commands:**

**File Operations:**
/upload - Upload file (reply to a file)
/download <url> - Download and upload to GoFile

**User Commands:**
/start - Start the bot
/help - Show this help message
/settings - User preferences
/myfiles - Your uploaded files
/account - GoFile account management
/stats - Your usage statistics

**Utility:**
/about - About this bot

For more help, contact administrators.
"""
    
    ADMIN_HELP_MESSAGE: str = """
🔧 **Admin Commands:**

/admin - Admin panel
/users - List all users
/ban <user_id> - Ban user
/unban <user_id> - Unban user
/broadcast <message> - Send message to all users
/stats_admin - Bot statistics
/force_sub - Force subscription settings
"""
    
    # Error messages
    ERROR_MESSAGES: dict = {
        "not_subscribed": "❌ You must join our channel first to use this bot!",
        "file_too_large": "❌ File is too large! Maximum size: {max_size}MB",
        "invalid_url": "❌ Invalid URL provided!",
        "download_failed": "❌ Failed to download from URL: {error}",
        "upload_failed": "❌ Failed to upload to GoFile: {error}",
        "user_banned": "❌ You are banned from using this bot!",
        "rate_limited": "❌ Too many requests! Please wait.",
        "admin_only": "❌ This command is only available to administrators!",
        "invalid_command": "❌ Invalid command! Use /help to see available commands."
    }
    
    # Success messages
    SUCCESS_MESSAGES: dict = {
        "upload_complete": "✅ File uploaded successfully!\n🔗 **Download Link:** {url}",
        "download_complete": "✅ Download and upload completed!\n🔗 **GoFile Link:** {url}",
        "user_banned": "✅ User {user_id} has been banned",
        "user_unbanned": "✅ User {user_id} has been unbanned",
        "broadcast_sent": "✅ Broadcast message sent to {count} users"
    }
    
    # Default user settings
    DEFAULT_USER_SETTINGS: dict = {
        "notifications": True,
        "auto_delete": False,
        "default_quality": "best",
        "language": "en"
    }
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate configuration settings"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        
        if not cls.MONGO_URI:
            raise ValueError("MONGO_URI is required")
        
        # Create directories if they don't exist
        os.makedirs(cls.DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user ID is an admin"""
        return user_id in cls.ADMIN_IDS