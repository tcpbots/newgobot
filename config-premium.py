"""
Premium GoFile Bot Configuration v3.0
Based on: TheHamkerCat/WilliamButcherBot architecture
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Premium Configuration Management"""
    
    # ================================
    # CORE TELEGRAM CREDENTIALS
    # ================================
    
    # REQUIRED: Get from https://my.telegram.org
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    
    # REQUIRED: Get from @BotFather
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # REQUIRED: Admin user IDs (comma-separated)
    ADMINS_RAW: str = os.getenv("ADMIN_IDS", "")
    ADMIN_IDS: List[int] = [
        int(admin_id.strip()) for admin_id in ADMINS_RAW.split(",") 
        if admin_id.strip().isdigit()
    ] if ADMINS_RAW else []
    
    # ================================
    # DATABASE CONFIGURATION
    # ================================
    
    # MongoDB Connection (No size limits!)
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "premium_gofile_bot")
    
    # ================================
    # PREMIUM FEATURES (NO LIMITS!)
    # ================================
    
    # File upload limits (4GB Pyrogram support)
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "4294967296"))  # 4GB
    MAX_DOWNLOAD_SIZE: int = int(os.getenv("MAX_DOWNLOAD_SIZE", "10737418240"))  # 10GB (Premium!)
    
    # No concurrent operation limits (Premium!)
    MAX_CONCURRENT_UPLOADS: int = int(os.getenv("MAX_CONCURRENT_UPLOADS", "10"))
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "10"))
    
    # ================================
    # DIRECTORIES
    # ================================
    
    DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "./downloads")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "./temp")
    COOKIES_DIR: str = os.getenv("COOKIES_DIR", "./cookies")
    SESSIONS_DIR: str = os.getenv("SESSIONS_DIR", "./sessions")
    
    # ================================
    # GOFILE.IO PREMIUM CONFIGURATION
    # ================================
    
    # GoFile API endpoints
    GOFILE_API_BASE: str = "https://api.gofile.io"
    GOFILE_UPLOAD_ENDPOINT: str = f"{GOFILE_API_BASE}/uploadFile"
    GOFILE_ACCOUNT_ENDPOINT: str = f"{GOFILE_API_BASE}/getAccountDetails"
    GOFILE_CREATE_FOLDER_ENDPOINT: str = f"{GOFILE_API_BASE}/createFolder"
    
    # Optional GoFile account token
    GOFILE_API_TOKEN: Optional[str] = os.getenv("GOFILE_API_TOKEN")
    
    # ================================
    # YT-DLP PREMIUM CONFIGURATION
    # ================================
    
    # Enable premium yt-dlp features
    YTDLP_ENABLED: bool = os.getenv("YTDLP_ENABLED", "true").lower() == "true"
    YTDLP_COOKIES_ENABLED: bool = os.getenv("YTDLP_COOKIES_ENABLED", "true").lower() == "true"
    
    # Premium quality options
    YTDLP_VIDEO_FORMAT: str = os.getenv("YTDLP_VIDEO_FORMAT", "best[height<=2160]")  # 4K support!
    YTDLP_AUDIO_FORMAT: str = os.getenv("YTDLP_AUDIO_FORMAT", "best")
    YTDLP_EXTRACT_AUDIO: bool = os.getenv("YTDLP_EXTRACT_AUDIO", "false").lower() == "true"
    
    # Premium user agents and headers
    YTDLP_USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    # ================================
    # FORCE SUBSCRIPTION (OPTIONAL)
    # ================================
    
    FORCE_SUB_ENABLED: bool = os.getenv("FORCE_SUB_ENABLED", "false").lower() == "true"
    FORCE_SUB_CHANNEL: Optional[str] = os.getenv("FORCE_SUB_CHANNEL")
    
    # ================================
    # PREMIUM PERFORMANCE SETTINGS
    # ================================
    
    # Chunk sizes for optimal performance
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1048576"))  # 1MB chunks
    UPLOAD_CHUNK_SIZE: int = int(os.getenv("UPLOAD_CHUNK_SIZE", "8388608"))  # 8MB upload chunks (Premium!)
    
    # Timeout settings
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "120"))  # 2 minutes
    DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "3600"))  # 1 hour (Premium!)
    UPLOAD_TIMEOUT: int = int(os.getenv("UPLOAD_TIMEOUT", "7200"))  # 2 hours (Premium!)
    
    # Retry settings (Premium resilience!)
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "5"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "2"))
    
    # ================================
    # PREMIUM BOT MESSAGES
    # ================================
    
    BOT_INFO: Dict[str, Any] = {
        "name": "Premium GoFile Uploader Bot",
        "version": "3.0.0",
        "description": "Premium Telegram bot for uploading files to GoFile.io with advanced yt-dlp integration",
        "author": "Premium Bot Development Team",
        "features": [
            "🚀 4GB file uploads (Full Telegram support)",
            "📥 10GB media downloads from 1000+ sites",
            "🎥 4K video quality support",
            "⚡ Real-time progress tracking",
            "🎯 Smart quality selection",
            "🔗 GoFile account integration", 
            "📊 Advanced statistics",
            "🛡️ Premium error handling",
            "🎵 Audio extraction",
            "📱 Multi-platform support",
            "🔄 Auto-retry mechanisms",
            "💾 Unlimited storage via GoFile"
        ]
    }
    
    WELCOME_MESSAGE: str = """
🎉 **Welcome to Premium GoFile Bot v3.0!**

🚀 **Premium Features:**
• Upload files up to **4GB** to GoFile.io
• Download from **1000+ platforms** (YouTube, Instagram, TikTok, etc.)
• **4K video quality** support
• **Real-time progress** tracking
• **Smart quality selection**
• **GoFile account** integration

📱 **How to use:**
• Send any file to upload instantly
• Send any URL to download and upload
• Use /help for all commands

⚡ **Premium Performance:**
• No artificial limits
• Advanced retry mechanisms
• Multi-threaded operations
• Smart error recovery

🎯 **Get Started:** Choose an option below!
"""
    
    HELP_MESSAGE: str = """
📚 **Premium GoFile Bot - Help Guide**

🎯 **Main Commands:**
• `/start` - Welcome message
• `/help` - Show this help
• `/upload` - Upload file (reply to file)
• `/download <url>` - Download from URL
• `/cancel` - Cancel current operation
• `/settings` - User preferences
• `/myfiles` - View uploaded files
• `/account` - GoFile account management
• `/stats` - Usage statistics
• `/about` - Bot information

🎥 **Media Download:**
• Support for 1000+ platforms
• 4K video quality support
• Audio extraction available
• Smart format selection
• Real-time progress tracking

📊 **Premium Features:**
• No file size limits (up to 4GB)
• Advanced retry mechanisms
• Multi-threaded operations
• GoFile account integration
• Detailed statistics

💡 **Pro Tips:**
• Link your GoFile account for better management
• Use quality selection for optimal downloads
• Check /stats for usage analytics
"""
    
    # ================================
    # ERROR MESSAGES (PREMIUM QUALITY)
    # ================================
    
    ERROR_MESSAGES: Dict[str, str] = {
        "invalid_url": "❌ **Invalid URL**\n\nPlease provide a valid HTTP/HTTPS URL.",
        "file_too_large": "❌ **File Too Large**\n\nFile size: {file_size}\nMaximum allowed: {max_size}GB\n\n💡 **Tip:** Try a smaller file or use premium features.",
        "download_failed": "❌ **Download Failed**\n\nError: {error}\n\n**Possible solutions:**\n• Try again in a few minutes\n• Check if the URL is still valid\n• Some platforms may require cookies",
        "upload_failed": "❌ **Upload Failed**\n\nError: {error}\n\n**Possible solutions:**\n• Check your internet connection\n• Try again in a few minutes\n• Contact support if issue persists",
        "processing_error": "❌ **Processing Error**\n\nSomething went wrong while processing your request.\n\n**Try:**\n• Using /cancel to stop current operation\n• Trying again in a few minutes\n• Contact support if issue persists",
        "user_banned": "🚫 **Access Denied**\n\nYour account has been suspended.\n\nContact an administrator for assistance.",
        "not_subscribed": "⚠️ **Subscription Required**\n\nYou must join our channel to use this bot.\n\nClick the button below to join, then try again.",
        "operation_cancelled": "🛑 **Operation Cancelled**\n\nThe current operation has been stopped.",
        "no_active_operation": "ℹ️ **No Active Operation**\n\nThere's nothing to cancel right now.",
        "admin_only": "🔒 **Admin Only**\n\nThis command is restricted to bot administrators.",
        "invalid_format": "❌ **Invalid Format**\n\nPlease check your input and try again.",
        "rate_limited": "⏱️ **Rate Limited**\n\nToo many requests. Please wait a moment and try again.",
        "maintenance_mode": "🔧 **Maintenance Mode**\n\nThe bot is currently under maintenance. Please try again later.",
        "feature_disabled": "🚫 **Feature Disabled**\n\nThis feature is currently disabled by administrators."
    }
    
    # ================================
    # SUCCESS MESSAGES (PREMIUM QUALITY)
    # ================================
    
    SUCCESS_MESSAGES: Dict[str, str] = {
        "upload_complete": """
✅ **Upload Complete!**

📁 **File:** {filename}
📊 **Size:** {filesize}
🔗 **Link:** {url}

📈 **Stats:** File uploaded successfully to GoFile.io!
⏱️ **Time:** Upload completed in record time!

💡 **Tip:** Your file is now permanently stored and ready to share!
""",
        "download_complete": """
✅ **Download & Upload Complete!**

📁 **File:** {filename}
📊 **Size:** {filesize}  
🔗 **Link:** {url}
🌐 **Source:** Downloaded and uploaded successfully!

📈 **Premium Quality:** Your media has been processed with the best quality available!

💡 **Tip:** File is now permanently hosted on GoFile.io!
""",
        "account_linked": "✅ **GoFile Account Linked!**\n\nYour GoFile account has been successfully connected.\nYou now have access to premium features!",
        "settings_updated": "✅ **Settings Updated!**\n\nYour preferences have been saved successfully."
    }
    
    # ================================
    # ADMIN MESSAGES
    # ================================
    
    ADMIN_HELP_MESSAGE: str = """

🛡️ **Admin Commands:**
• `/admin` - Admin panel
• `/broadcast <message>` - Send message to all users
• `/users` - List users
• `/ban <user_id>` - Ban user
• `/unban <user_id>` - Unban user
• `/stats_admin` - Detailed statistics
• `/force_sub` - Force subscription settings
• `/maintenance` - Toggle maintenance mode
"""
    
    # ================================
    # DEFAULT USER SETTINGS (PREMIUM)
    # ================================
    
    DEFAULT_USER_SETTINGS: Dict[str, Any] = {
        "default_video_quality": "best[height<=1080]",
        "default_audio_quality": "best",
        "extract_audio": False,
        "notifications": True,
        "delete_after_upload": False,
        "auto_retry": True,
        "preferred_format": "mp4",
        "premium_features": True,
        "smart_quality_selection": True,
        "progress_notifications": True
    }
    
    # ================================
    # SUPPORTED PLATFORMS (PREMIUM LIST)
    # ================================
    
    SUPPORTED_PLATFORMS: List[str] = [
        "youtube.com", "youtu.be", "youtube-nocookie.com",
        "instagram.com", "instagr.am", 
        "tiktok.com", "vm.tiktok.com",
        "twitter.com", "x.com", "t.co",
        "facebook.com", "fb.watch", "fb.com",
        "reddit.com", "redd.it", "v.redd.it",
        "vimeo.com",
        "dailymotion.com", "dai.ly", 
        "soundcloud.com",
        "twitch.tv", "clips.twitch.tv",
        "streamable.com",
        "imgur.com", "i.imgur.com",
        "pinterest.com", "pin.it",
        "linkedin.com",
        "tumblr.com",
        "spotify.com", "open.spotify.com",
        "bandcamp.com",
        "mixcloud.com", 
        "archive.org",
        "mediafire.com",
        "mega.nz",
        "dropbox.com",
        "drive.google.com",
        "onedrive.live.com",
        "wetransfer.com"
    ]
    
    # ================================
    # VALIDATION METHODS
    # ================================
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate configuration and raise errors for missing required values"""
        
        missing_configs = []
        
        # Check required configs
        if not cls.API_ID or cls.API_ID == 0:
            missing_configs.append("API_ID (get from https://my.telegram.org)")
            
        if not cls.API_HASH:
            missing_configs.append("API_HASH (get from https://my.telegram.org)")
            
        if not cls.BOT_TOKEN:
            missing_configs.append("BOT_TOKEN (get from @BotFather)")
            
        if not cls.ADMIN_IDS:
            missing_configs.append("ADMIN_IDS (your Telegram user ID)")
            
        if missing_configs:
            error_msg = "❌ Missing required configuration:\n\n"
            for config in missing_configs:
                error_msg += f"• {config}\n"
            error_msg += "\n💡 Create a .env file with these values!"
            raise ValueError(error_msg)
            
        logger.info("✅ Configuration validation passed!")
    
    @classmethod  
    def is_admin(cls, user_id: int) -> bool:
        """Check if user is an admin"""
        return user_id in cls.ADMIN_IDS
    
    @classmethod
    def get_file_size_limit_gb(cls) -> float:
        """Get file size limit in GB"""
        return cls.MAX_FILE_SIZE / (1024**3)
    
    @classmethod
    def get_download_size_limit_gb(cls) -> float:
        """Get download size limit in GB"""
        return cls.MAX_DOWNLOAD_SIZE / (1024**3)
    
    @classmethod
    def get_platform_name(cls, url: str) -> str:
        """Get platform name from URL"""
        url_lower = url.lower()
        
        platform_map = {
            "youtube.com": "YouTube",
            "youtu.be": "YouTube", 
            "instagram.com": "Instagram",
            "tiktok.com": "TikTok",
            "twitter.com": "Twitter/X",
            "x.com": "Twitter/X",
            "facebook.com": "Facebook",
            "reddit.com": "Reddit",
            "vimeo.com": "Vimeo",
            "dailymotion.com": "Dailymotion",
            "soundcloud.com": "SoundCloud",
            "twitch.tv": "Twitch",
            "streamable.com": "Streamable",
            "spotify.com": "Spotify"
        }
        
        for domain, name in platform_map.items():
            if domain in url_lower:
                return name
                
        return "Direct Link"
    
    @classmethod
    def get_random_user_agent(cls) -> str:
        """Get random user agent for requests"""
        import random
        return random.choice(cls.YTDLP_USER_AGENTS)
    
    @classmethod
    def create_directories(cls) -> None:
        """Create required directories"""
        import pathlib
        
        directories = [
            cls.DOWNLOAD_DIR,
            cls.TEMP_DIR, 
            cls.COOKIES_DIR,
            cls.SESSIONS_DIR,
            "logs"
        ]
        
        for directory in directories:
            pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
            
        logger.info("✅ Required directories created!")


# Create directories on import
Config.create_directories()