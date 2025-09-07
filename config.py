"""
Configuration settings - COMPLETE REWRITE with Pyrogram support
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Bot configuration class"""
    
    # Telegram Bot API credentials - REQUIRED
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "5066445400:AAEGWQO2Ov6SNqaW5mcPwnkr6bUFatdiKtY")
    API_ID: int = int(os.getenv("API_ID", "17760082"))
    API_HASH: str = os.getenv("API_HASH", "c3fc3cd44886967cf3c0e8585b5cad1c")
    
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required")
    if not API_ID or API_ID == 0:
        raise ValueError("API_ID is required - Get from https://my.telegram.org")
    if not API_HASH:
        raise ValueError("API_HASH is required - Get from https://my.telegram.org")
    
    # Database settings
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb+srv://usersdb:OxXu6uIVcxtLcJjr@cluster0.nn2rtsh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "gofile_bot")
    
    # Admin settings
    ADMIN_IDS: List[int] = [
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "1809710185").split(",") if x.strip()
    ]
    
    # Force subscription settings
    FORCE_SUB_CHANNEL: Optional[str] = os.getenv("FORCE_SUB_CHANNEL", "@Xtreambotz")
    FORCE_SUB_ENABLED: bool = os.getenv("FORCE_SUB_ENABLED", "true").lower() == "true"
    
    # GoFile.io API settings
    GOFILE_API_TOKEN: Optional[str] = os.getenv("GOFILE_API_TOKEN")
    GOFILE_UPLOAD_URL: str = "https://upload.gofile.io/uploadfile"
    GOFILE_API_BASE: str = "https://api.gofile.io"
    
    # File settings - FIXED: Pyrogram supports up to 4GB
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "4294967296"))  # 4GB
    ALLOWED_FILE_TYPES: List[str] = [
        'document', 'photo', 'video', 'audio', 'voice', 'video_note', 'animation'
    ]
    
    # Download settings - FIXED: 2GB limit as requested
    DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "./downloads")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "./temp")
    MAX_DOWNLOAD_SIZE: int = int(os.getenv("MAX_DOWNLOAD_SIZE", "2147483648"))  # 2GB
    
    # Performance settings
    MAX_CONCURRENT_UPLOADS: int = int(os.getenv("MAX_CONCURRENT_UPLOADS", "3"))
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1048576"))  # 1MB chunks for large files
    
    # Connection timeout settings
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
    DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "1800"))  # 30 minutes
    
    # yt-dlp settings
    YTDLP_ENABLED: bool = os.getenv("YTDLP_ENABLED", "True").lower() == "true"
    YTDLP_EXTRACT_AUDIO: bool = os.getenv("YTDLP_EXTRACT_AUDIO", "False").lower() == "true"
    YTDLP_AUDIO_FORMAT: str = os.getenv("YTDLP_AUDIO_FORMAT", "mp3")
    YTDLP_VIDEO_FORMAT: str = os.getenv("YTDLP_VIDEO_FORMAT", "best[filesize<2147483648]")  # 2GB limit
    
    # Messages
    WELCOME_MESSAGE: str = """
🤖 **Welcome to GoFile Uploader Bot!**

I can help you upload files to GoFile.io and download from URLs.

**Features:**
📁 Upload files up to **4GB** to GoFile.io
🔗 Download from URLs (including YouTube, social media)
📊 Real-time upload/download progress
🎯 Quality selection for videos/audio
📱 GoFile account management

**Supported Platforms:**
• YouTube, Instagram, TikTok, Twitter/X
• Facebook, Reddit, Vimeo, SoundCloud
• Direct file links and cloud storage

Use /help to see all commands!
"""
    
    HELP_MESSAGE: str = """
📋 **Available Commands:**

**🔹 File Operations:**
/upload - Upload file (reply to a file)
/download <url> - Download from URL and upload to GoFile

**🔹 User Commands:**
/start - Start the bot
/help - Show this help message  
/settings - User preferences
/myfiles - Your uploaded files
/account - GoFile account management
/stats - Your usage statistics

**🔹 Utility:**
/about - About this bot
/cancel - Cancel current operation

**📊 Limits:**
• Max upload: 4GB per file
• Max download: 2GB per file
• Supports all major video/audio platforms

For admin help, use /admin
"""
    
    ADMIN_HELP_MESSAGE: str = """
🔧 **Admin Commands:**

/admin - Admin panel
/users - List all users  
/ban <user_id> - Ban user
/unban <user_id> - Unban user
/broadcast <message> - Send message to all users
/stats_admin - Detailed bot statistics
/force_sub - Force subscription settings
/logs - View recent logs
/restart - Restart bot services
"""
    
    # Error messages
    ERROR_MESSAGES: dict = {
        "not_subscribed": "❌ **Access Denied**\n\nYou must join our channel first to use this bot!",
        "file_too_large": "❌ **File Too Large**\n\nMaximum size: {max_size}GB\nYour file: {file_size}",
        "invalid_url": "❌ **Invalid URL**\n\nPlease provide a valid HTTP/HTTPS URL.",
        "download_failed": "❌ **Download Failed**\n\n**Error:** {error}\n\n**Possible causes:**\n• Invalid or expired URL\n• File too large (max 2GB)\n• Server not responding\n• Geographic restrictions",
        "upload_failed": "❌ **Upload Failed**\n\n**Error:** {error}\n\nTry again or contact support if the issue persists.",
        "user_banned": "🚫 **Account Banned**\n\nYou are banned from using this bot!\n\nContact administrators if you think this is a mistake.",
        "rate_limited": "⏰ **Rate Limited**\n\nToo many requests! Please wait {seconds} seconds.",
        "admin_only": "🔒 **Admin Only**\n\nThis command is only available to administrators.",
        "invalid_command": "❌ **Unknown Command**\n\nUse /help to see available commands.",
        "subscription_check_failed": "⚠️ **Subscription Check Failed**\n\nCouldn't verify channel membership. Proceeding anyway...",
        "operation_cancelled": "⏹️ **Operation Cancelled**\n\nThe current operation has been cancelled.",
        "no_active_operation": "ℹ️ **No Active Operation**\n\nThere's no active operation to cancel.",
        "processing_error": "❌ **Processing Error**\n\nAn error occurred while processing your request. Please try again."
    }
    
    # Success messages
    SUCCESS_MESSAGES: dict = {
        "upload_complete": "✅ **Upload Successful!**\n\n📁 **File:** {filename}\n📊 **Size:** {filesize}\n🔗 **GoFile Link:** [Download Here]({url})\n\n💡 Use /myfiles to see all your uploads!",
        "download_complete": "✅ **Download & Upload Complete!**\n\n📁 **File:** {filename}\n📊 **Size:** {filesize}\n🔗 **GoFile Link:** [Download Here]({url})\n\n🎉 Successfully downloaded and uploaded to GoFile!",
        "user_banned": "✅ **User Banned**\n\nUser {user_id} has been banned successfully.",
        "user_unbanned": "✅ **User Unbanned**\n\nUser {user_id} has been unbanned successfully.",
        "broadcast_sent": "✅ **Broadcast Complete**\n\nMessage sent to {count} users successfully!"
    }
    
    # Progress messages
    PROGRESS_MESSAGES: dict = {
        "downloading": "📥 **Downloading...** {progress}%\n\n📁 **File:** {filename}\n📊 **Size:** {size}\n⏱️ **Speed:** {speed}/s\n🕒 **ETA:** {eta}",
        "uploading": "📤 **Uploading to GoFile...** {progress}%\n\n📁 **File:** {filename}\n📊 **Size:** {size}\n⏱️ **Speed:** {speed}/s",
        "processing": "🔄 **Processing...** \n\n📁 **File:** {filename}\n⚙️ **Status:** {status}",
        "extracting": "🎵 **Extracting Audio...** {progress}%\n\n📁 **From:** {source}\n🎯 **Format:** {format}",
        "converting": "🔄 **Converting...** {progress}%\n\n📁 **File:** {filename}\n🎯 **To:** {target_format}"
    }
    
    # Quality options for downloads
    VIDEO_QUALITY_OPTIONS: List[dict] = [
        {"text": "🎥 Best Quality", "format": "best", "description": "Highest available quality"},
        {"text": "🎬 1080p", "format": "best[height<=1080]", "description": "Full HD (1080p)"},
        {"text": "📺 720p", "format": "best[height<=720]", "description": "HD (720p)"},
        {"text": "📱 480p", "format": "best[height<=480]", "description": "SD (480p)"},
        {"text": "💾 Smallest", "format": "worst", "description": "Smallest file size"}
    ]
    
    AUDIO_QUALITY_OPTIONS: List[dict] = [
        {"text": "🎵 Best Quality", "format": "bestaudio", "description": "Highest audio quality"},
        {"text": "🎶 320k MP3", "format": "bestaudio[ext=mp3]/best[ext=mp3]", "description": "320 kbps MP3"},
        {"text": "🎧 256k AAC", "format": "bestaudio[ext=m4a]/best[ext=m4a]", "description": "256 kbps AAC"},
        {"text": "📻 128k", "format": "bestaudio[abr<=128]", "description": "128 kbps (smaller file)"}
    ]
    
    # Default user settings
    DEFAULT_USER_SETTINGS: dict = {
        "notifications": True,
        "auto_delete": False,
        "default_video_quality": "best[height<=720]",
        "default_audio_quality": "bestaudio",
        "extract_audio": False,
        "language": "en"
    }
    
    # Bot information
    BOT_INFO: dict = {
        "name": "GoFile Uploader Bot",
        "version": "2.0.0",
        "author": "Assistant",
        "description": "Upload files to GoFile.io with advanced download capabilities",
        "features": [
            "4GB file uploads",
            "2GB URL downloads", 
            "YouTube & social media support",
            "Quality selection",
            "Progress tracking",
            "GoFile account integration"
        ]
    }
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate configuration settings"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        if not cls.API_ID or cls.API_ID == 0:
            raise ValueError("API_ID is required")
        if not cls.API_HASH:
            raise ValueError("API_HASH is required")
        if not cls.MONGO_URI:
            raise ValueError("MONGO_URI is required")
        
        # Create directories
        os.makedirs(cls.DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user ID is an admin"""
        return user_id in cls.ADMIN_IDS
        
    @classmethod
    def get_file_size_limit_gb(cls) -> float:
        """Get file size limit in GB"""
        return cls.MAX_FILE_SIZE / (1024**3)
        
    @classmethod
    def get_download_size_limit_gb(cls) -> float:
        """Get download size limit in GB"""
        return cls.MAX_DOWNLOAD_SIZE / (1024**3)
