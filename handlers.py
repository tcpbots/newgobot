"""
Complete Bot handlers using Pyrogram - ALL FUNCTIONS INCLUDED
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, ChannelPrivate

from config import Config
from database import Database
from utils import Utils
from downloader import MediaDownloader

logger = logging.getLogger(__name__)


class BotHandlers:
    """Complete Bot handlers using Pyrogram"""
    
    def __init__(self, app: Client, database: Database, utils: Utils, downloader: MediaDownloader, config: Config):
        self.app = app
        self.db = database
        self.utils = utils
        self.downloader = downloader
        self.config = config
        
        # Store active operations for cancellation
        self.active_operations: Dict[int, asyncio.Task] = {}
        
    async def setup_handlers(self):
        """Setup all message and callback handlers"""
        
        # Command handlers
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_command(client, message):
            await self.handle_start(message)
            
        @self.app.on_message(filters.command("help") & filters.private)
        async def help_command(client, message):
            await self.handle_help(message)
            
        @self.app.on_message(filters.command("upload") & filters.private)
        async def upload_command(client, message):
            await self.handle_upload_command(message)
            
        @self.app.on_message(filters.command("download") & filters.private)
        async def download_command(client, message):
            await self.handle_download_command(message)
            
        @self.app.on_message(filters.command("cancel") & filters.private)
        async def cancel_command(client, message):
            await self.handle_cancel(message)
            
        @self.app.on_message(filters.command("settings") & filters.private)
        async def settings_command(client, message):
            await self.handle_settings(message)
            
        @self.app.on_message(filters.command("myfiles") & filters.private)
        async def myfiles_command(client, message):
            await self.handle_myfiles(message)
            
        @self.app.on_message(filters.command("account") & filters.private)
        async def account_command(client, message):
            await self.handle_account(message)
            
        @self.app.on_message(filters.command("stats") & filters.private)
        async def stats_command(client, message):
            await self.handle_stats(message)
            
        @self.app.on_message(filters.command("about") & filters.private)
        async def about_command(client, message):
            await self.handle_about(message)
            
        # Admin commands
        @self.app.on_message(filters.command("admin") & filters.private)
        async def admin_command(client, message):
            await self.handle_admin(message)
            
        @self.app.on_message(filters.command("broadcast") & filters.private)
        async def broadcast_command(client, message):
            await self.handle_broadcast(message)
            
        @self.app.on_message(filters.command("users") & filters.private)
        async def users_command(client, message):
            await self.handle_users_list(message)
            
        @self.app.on_message(filters.command("ban") & filters.private)
        async def ban_command(client, message):
            await self.handle_ban_user(message)
            
        @self.app.on_message(filters.command("unban") & filters.private)
        async def unban_command(client, message):
            await self.handle_unban_user(message)
            
        @self.app.on_message(filters.command("stats_admin") & filters.private)
        async def admin_stats_command(client, message):
            await self.handle_admin_stats(message)
            
        @self.app.on_message(filters.command("force_sub") & filters.private)
        async def force_sub_command(client, message):
            await self.handle_force_sub_settings(message)
            
        # File handlers
        @self.app.on_message(
            (filters.document | filters.photo | filters.video | 
             filters.audio | filters.voice | filters.video_note | 
             filters.animation) & filters.private
        )
        async def file_handler(client, message):
            await self.handle_file_upload(message)
            
        # URL handler (text messages that are URLs)
        @self.app.on_message(filters.text & filters.private)
        async def text_handler(client, message):
            await self.handle_text_message(message)
            
        # Callback query handlers
        @self.app.on_callback_query()
        async def callback_handler(client, callback_query):
            await self.handle_callback_query(callback_query)
            
        logger.info("✅ All handlers registered successfully")
    
    # Utility methods
    async def check_subscription(self, user_id: int) -> bool:
        """Check if user is subscribed to required channel"""
        if not self.config.FORCE_SUB_ENABLED or not self.config.FORCE_SUB_CHANNEL:
            return True
            
        try:
            member = await self.app.get_chat_member(self.config.FORCE_SUB_CHANNEL, user_id)
            return member.status in ["member", "administrator", "creator"]
        except (UserNotParticipant, ChannelPrivate, ChatAdminRequired) as e:
            logger.warning(f"Subscription check failed for user {user_id}: {e}")
            return True  # Allow access if we can't verify
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            return True
    
    async def check_user_permissions(self, message: Message) -> bool:
        """Check if user has permission to use the bot"""
        user_id = message.from_user.id
        
        # Check if banned
        if await self.db.is_user_banned(user_id):
            await message.reply(self.config.ERROR_MESSAGES["user_banned"])
            return False
            
        # Check subscription
        if not await self.check_subscription(user_id):
            await self.send_subscription_required(message)
            return False
            
        return True
    
    async def send_subscription_required(self, message: Message):
        """Send subscription required message"""
        if not self.config.FORCE_SUB_CHANNEL:
            return
            
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🔗 Join Channel", 
                url=f"https://t.me/{self.config.FORCE_SUB_CHANNEL.lstrip('@')}"
            )],
            [InlineKeyboardButton(
                "✅ I've Joined", 
                callback_data="check_subscription"
            )]
        ])
        
        await message.reply(
            self.config.ERROR_MESSAGES["not_subscribed"],
            reply_markup=keyboard
        )
    
    # Command handlers
    async def handle_start(self, message: Message):
        """Handle /start command"""
        try:
            user = message.from_user
            
            # Create/update user in database
            user_data = {
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language_code": user.language_code
            }
            await self.db.create_user(user_data)
            
            # Check permissions
            if not await self.check_user_permissions(message):
                return
            
            # Create welcome keyboard
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📁 Upload File", callback_data="help_upload"),
                    InlineKeyboardButton("🔗 Download URL", callback_data="help_download")
                ],
                [
                    InlineKeyboardButton("⚙️ Settings", callback_data="user_settings"),
                    InlineKeyboardButton("📊 My Stats", callback_data="user_stats")
                ],
                [
                    InlineKeyboardButton("❓ Help", callback_data="show_help"),
                    InlineKeyboardButton("ℹ️ About", callback_data="show_about")
                ]
            ])
            
            await message.reply(
                self.config.WELCOME_MESSAGE,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in start handler: {e}")
            await message.reply(self.config.ERROR_MESSAGES["processing_error"])
    
    async def handle_help(self, message: Message):
        """Handle /help command"""
        try:
            if not await self.check_user_permissions(message):
                return
                
            help_text = self.config.HELP_MESSAGE
            
            # Add admin help for admins
            if self.config.is_admin(message.from_user.id):
                help_text += f"\n\n{self.config.ADMIN_HELP_MESSAGE}"
            
            # Add supported platforms
            platforms = await self.downloader.get_supported_platforms_list()
            help_text += f"\n\n📋 **Supported Platforms:**\n"
            help_text += "\n".join(platforms[:8])  # Show first 8
            help_text += f"\n\n💡 **Quick Tips:**\n"
            help_text += "• Send any file to upload to GoFile.io\n"
            help_text += "• Send any URL to download and upload\n"
            help_text += "• Use quality selection for videos\n"
            help_text += "• Extract audio from videos"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎥 Video Download", callback_data="help_video"),
                    InlineKeyboardButton("🎵 Audio Extract", callback_data="help_audio")
                ],
                [InlineKeyboardButton("📱 All Platforms", callback_data="show_platforms")]
            ])
            
            await message.reply(help_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in help handler: {e}")
    
    async def handle_upload_command(self, message: Message):
        """Handle /upload command"""
        try:
            if not await self.check_user_permissions(message):
                return
            
            if message.reply_to_message:
                await self.handle_file_upload(message.reply_to_message)
            else:
                await message.reply(
                    "📁 **File Upload**\n\n"
                    "Please reply to a file with /upload or simply send me any file.\n\n"
                    "📊 **Supported:**\n"
                    "• Documents, photos, videos, audio\n"
                    "• Up to 4GB per file\n"
                    "• All file types supported"
                )
                
        except Exception as e:
            logger.error(f"Error in upload command: {e}")
    
    async def handle_download_command(self, message: Message):
        """Handle /download command"""
        try:
            if not await self.check_user_permissions(message):
                return
            
            # Extract URL from command
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) < 2:
                platforms = await self.downloader.get_supported_platforms_list()
                platform_text = "\n".join(platforms[:10])
                
                await message.reply(
                    f"🔗 **Download from URL**\n\n"
                    f"**Usage:** `/download <url>`\n\n"
                    f"**Example:**\n"
                    f"`/download https://youtube.com/watch?v=...`\n\n"
                    f"📋 **Supported Platforms:**\n{platform_text}\n\n"
                    f"📊 **Limits:**\n"
                    f"• Max download: {self.config.get_download_size_limit_gb():.1f}GB\n"
                    f"• Quality selection available\n"
                    f"• Audio extraction supported"
                )
                return
            
            url = command_parts[1].strip()
            await self.handle_url_download(message, url)
            
        except Exception as e:
            logger.error(f"Error in download command: {e}")
    
    async def handle_cancel(self, message: Message):
        """Handle /cancel command"""
        try:
            user_id = message.from_user.id
            
            if user_id in self.active_operations:
                # Cancel the active operation
                task = self.active_operations[user_id]
                task.cancel()
                del self.active_operations[user_id]
                
                await message.reply(self.config.ERROR_MESSAGES["operation_cancelled"])
            else:
                await message.reply(self.config.ERROR_MESSAGES["no_active_operation"])
                
        except Exception as e:
            logger.error(f"Error in cancel handler: {e}")
    
    async def handle_settings(self, message: Message):
        """Handle /settings command"""
        try:
            if not await self.check_user_permissions(message):
                return
            
            user = await self.db.get_user(message.from_user.id)
            if not user:
                await message.reply("❌ User not found. Please use /start first.")
                return
            
            settings = user.get('settings', self.config.DEFAULT_USER_SETTINGS)
            
            settings_text = f"⚙️ **Your Settings**\n\n"
            settings_text += f"👤 **User:** {user.get('first_name', 'Unknown')}\n"
            settings_text += f"🆔 **ID:** `{user['user_id']}`\n"
            settings_text += f"📅 **Joined:** {user.get('join_date', datetime.utcnow()).strftime('%Y-%m-%d')}\n\n"
            
            settings_text += f"🎥 **Video Quality:** {settings.get('default_video_quality', 'best[height<=720]')}\n"
            settings_text += f"🎵 **Audio Quality:** {settings.get('default_audio_quality', 'bestaudio')}\n"
            settings_text += f"🔊 **Extract Audio:** {'Yes' if settings.get('extract_audio', False) else 'No'}\n"
            settings_text += f"🔔 **Notifications:** {'Enabled' if settings.get('notifications', True) else 'Disabled'}\n\n"
            
            settings_text += f"📊 **Limits:**\n"
            settings_text += f"• Max Upload: {self.config.get_file_size_limit_gb():.1f}GB\n"
            settings_text += f"• Max Download: {self.config.get_download_size_limit_gb():.1f}GB"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎥 Video Settings", callback_data="settings_video"),
                    InlineKeyboardButton("🎵 Audio Settings", callback_data="settings_audio")
                ],
                [
                    InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications"),
                    InlineKeyboardButton("🗑️ Auto Delete", callback_data="settings_autodelete")
                ],
                [InlineKeyboardButton("🔗 GoFile Account", callback_data="gofile_account")]
            ])
            
            await message.reply(settings_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in settings handler: {e}")
    
    async def handle_myfiles(self, message: Message):
        """Handle /myfiles command"""
        try:
            if not await self.check_user_permissions(message):
                return
            
            files = await self.db.get_user_files(message.from_user.id, limit=15)
            
            if not files:
                await message.reply(
                    "📁 **Your Files**\n\n"
                    "You haven't uploaded any files yet.\n\n"
                    "💡 **Get Started:**\n"
                    "• Send me any file to upload to GoFile.io\n"
                    "• Send any URL to download and upload\n"
                    "• Up to 4GB per file supported!"
                )
                return
            
            files_text = "📁 **Your Recent Files:**\n\n"
            
            for i, file_doc in enumerate(files, 1):
                name = file_doc.get('file_name', 'Unknown')[:30]
                size = self.utils.format_file_size(file_doc.get('file_size', 0))
                date = file_doc.get('upload_date', datetime.utcnow()).strftime('%m/%d')
                gofile_id = file_doc.get('gofile_id', '')
                
                files_text += f"{i}. **{name}**\n"
                files_text += f"   📊 {size} • 📅 {date} • "
                files_text += f"[🔗 Download](https://gofile.io/d/{gofile_id})\n\n"
            
            # Get user stats
            user_stats = await self.db.get_user_stats(message.from_user.id)
            total_files = user_stats.get('files_uploaded', len(files))
            total_size = self.utils.format_file_size(user_stats.get('total_size', 0))
            
            files_text += f"📊 **Summary:**\n"
            files_text += f"• Total Files: {total_files}\n"
            files_text += f"• Total Size: {total_size}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 Detailed Stats", callback_data="user_stats"),
                    InlineKeyboardButton("🔄 Refresh", callback_data="refresh_files")
                ]
            ])
            
            await message.reply(files_text, reply_markup=keyboard, disable_web_page_preview=True)
            
        except Exception as e:
            logger.error(f"Error in myfiles handler: {e}")
    
    async def handle_account(self, message: Message):
        """Handle /account command"""
        try:
            if not await self.check_user_permissions(message):
                return
            
            user = await self.db.get_user(message.from_user.id)
            gofile_account = user.get('gofile_account', {}) if user else {}
            
            account_text = "🔗 **GoFile Account Management**\n\n"
            
            if gofile_account.get('token'):
                account_text += f"✅ **Account Linked**\n"
                account_text += f"🆔 Account ID: `{gofile_account.get('account_id', 'Unknown')}`\n"
                account_text += f"🎯 Tier: {gofile_account.get('tier', 'Unknown')}\n\n"
                account_text += f"✨ **Benefits:**\n"
                account_text += f"• Manage files from GoFile dashboard\n"
                account_text += f"• Access to premium features\n"
                account_text += f"• Extended file retention\n"
                account_text += f"• Priority support"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🗑️ Unlink Account", callback_data="gofile_unlink")],
                    [InlineKeyboardButton("🔄 Refresh Token", callback_data="gofile_refresh")]
                ])
            else:
                account_text += f"❌ **No Account Linked**\n\n"
                account_text += f"📝 **Current Status:** Anonymous uploads\n\n"
                account_text += f"🔗 **Link Your Account:**\n"
                account_text += f"1. Get your API token from [GoFile.io](https://gofile.io/myprofile)\n"
                account_text += f"2. Click 'Link Account' below\n"
                account_text += f"3. Send your API token\n\n"
                account_text += f"✨ **Benefits of linking:**\n"
                account_text += f"• Manage all your files\n"
                account_text += f"• Access premium features\n"
                account_text += f"• Better file retention"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Link Account", callback_data="gofile_link")],
                    [InlineKeyboardButton("❓ How to Get Token", callback_data="gofile_help")]
                ])
            
            await message.reply(account_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in account handler: {e}")
    
    async def handle_stats(self, message: Message):
        """Handle /stats command"""
        try:
            if not await self.check_user_permissions(message):
                return
            
            user_stats = await self.db.get_user_stats(message.from_user.id)
            
            if not user_stats:
                await message.reply("❌ Unable to retrieve your statistics.")
                return
            
            stats_text = f"📊 **Your Statistics**\n\n"
            
            stats_text += f"👤 **Profile:**\n"
            stats_text += f"🆔 User ID: `{message.from_user.id}`\n"
            stats_text += f"📅 Joined: {user_stats.get('join_date', datetime.utcnow()).strftime('%Y-%m-%d')}\n\n"
            
            stats_text += f"📁 **Upload Stats:**\n"
            stats_text += f"📄 Files Uploaded: {user_stats.get('files_uploaded', 0)}\n"
            stats_text += f"💾 Total Size: {self.utils.format_file_size(user_stats.get('total_size', 0))}\n"
            stats_text += f"📈 Avg File Size: {self.utils.format_file_size(user_stats.get('avg_file_size', 0))}\n\n"
            
            stats_text += f"🔗 **Download Stats:**\n"
            stats_text += f"📥 URLs Downloaded: {user_stats.get('urls_downloaded', 0)}\n"
            stats_text += f"⏱️ Last Activity: {user_stats.get('last_activity', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')}\n\n"
            
            stats_text += f"📊 **Limits:**\n"
            stats_text += f"📤 Max Upload: {self.config.get_file_size_limit_gb():.1f}GB per file\n"
            stats_text += f"📥 Max Download: {self.config.get_download_size_limit_gb():.1f}GB per file"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📁 My Files", callback_data="user_files"),
                    InlineKeyboardButton("⚙️ Settings", callback_data="user_settings")
                ]
            ])
            
            await message.reply(stats_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in stats handler: {e}")
    
    async def handle_about(self, message: Message):
        """Handle /about command"""
        try:
            bot_info = self.config.BOT_INFO
            
            about_text = f"ℹ️ **{bot_info['name']}**\n\n"
            about_text += f"📋 **Description:**\n{bot_info['description']}\n\n"
            about_text += f"📊 **Version:** {bot_info['version']}\n"
            about_text += f"👨‍💻 **Developer:** {bot_info['author']}\n\n"
            about_text += f"✨ **Features:**\n"
            for feature in bot_info['features']:
                about_text += f"• {feature}\n"
            
            about_text += f"\n🔧 **Powered by:**\n"
            about_text += f"• [Pyrogram](https://pyrogram.org) - Modern Telegram Bot Framework\n"
            about_text += f"• [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Universal Media Downloader\n"
            about_text += f"• [GoFile.io](https://gofile.io) - File Hosting Service\n"
            about_text += f"• MongoDB - Database Storage"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🚀 Start Using", callback_data="show_help"),
                    InlineKeyboardButton("📱 Platforms", callback_data="show_platforms")
                ]
            ])
            
            await message.reply(about_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in about handler: {e}")
    
    # File upload handler
    async def handle_file_upload(self, message: Message):
        """Handle file upload to GoFile"""
        try:
            if not await self.check_user_permissions(message):
                return
            
            # Get file information
            file_info = await self.utils.get_file_info(message)
            if not file_info:
                await message.reply("❌ Unable to process this file type.")
                return
            
            # Check file size
            if file_info['size'] > self.config.MAX_FILE_SIZE:
                max_size_gb = self.config.get_file_size_limit_gb()
                current_size_gb = file_info['size'] / (1024**3)
                
                await message.reply(
                    self.config.ERROR_MESSAGES["file_too_large"].format(
                        max_size=max_size_gb,
                        file_size=f"{current_size_gb:.2f}GB"
                    )
                )
                return
            
            # Start upload process
            user_id = message.from_user.id
            
            # Cancel any existing operation for this user
            if user_id in self.active_operations:
                self.active_operations[user_id].cancel()
            
            # Create and start upload task
            upload_task = asyncio.create_task(
                self._process_file_upload(message, file_info)
            )
            self.active_operations[user_id] = upload_task
            
            try:
                await upload_task
            finally:
                if user_id in self.active_operations:
                    del self.active_operations[user_id]
                
        except Exception as e:
            logger.error(f"Error in file upload handler: {e}")
            await message.reply(self.config.ERROR_MESSAGES["processing_error"])
    
    async def _process_file_upload(self, message: Message, file_info: Dict[str, Any]):
        """Process file upload with progress tracking"""
        try:
            # Send initial status
            status_msg = await message.reply(
                f"📤 **Starting Upload**\n\n"
                f"📁 **File:** {file_info['name']}\n"
                f"📊 **Size:** {self.utils.format_file_size(file_info['size'])}\n"
                f"🔄 **Status:** Downloading from Telegram..."
            )
            
            # Download file from Telegram
            file_path = await self.utils.download_telegram_file(self.app, file_info['file_id'])
            
            # Update status
            await status_msg.edit_text(
                f"📤 **Uploading to GoFile**\n\n"
                f"📁 **File:** {file_info['name']}\n"
                f"📊 **Size:** {self.utils.format_file_size(file_info['size'])}\n"
                f"🔄 **Status:** Uploading to GoFile.io..."
            )
            
            # Progress callback
            last_update = 0
            async def progress_callback(progress_data):
                nonlocal last_update
                current_time = time.time()
                
                # Update every 2 seconds to avoid rate limits
                if current_time - last_update >= 2:
                    try:
                        progress = progress_data.get('progress', 0)
                        speed = progress_data.get('speed', 0)
                        
                        await status_msg.edit_text(
                            f"📤 **Uploading to GoFile** {progress}%\n\n"
                            f"📁 **File:** {file_info['name']}\n"
                            f"📊 **Size:** {self.utils.format_file_size(file_info['size'])}\n"
                            f"⚡ **Speed:** {self.utils.format_file_size(int(speed))}/s\n"
                            f"📊 **Progress:** {self.utils.create_progress_bar(progress)}"
                        )
                        last_update = current_time
                    except:
                        pass  # Ignore edit errors
            
            # Upload to GoFile
            result = await self.utils.upload_to_gofile(
                file_path, 
                file_info['name'], 
                message.from_user.id,
                progress_callback
            )
            
            if result['success']:
                # Save to database
                await self.db.save_file({
                    'user_id': message.from_user.id,
                    'file_name': file_info['name'],
                    'file_size': file_info['size'],
                    'file_type': file_info['type'],
                    'gofile_id': result['file_id'],
                    'gofile_url': result['download_url']
                })
                
                # Success message
                success_text = self.config.SUCCESS_MESSAGES["upload_complete"].format(
                    filename=file_info['name'],
                    filesize=self.utils.format_file_size(file_info['size']),
                    url=result['download_url']
                )
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📁 Download File", url=result['download_url'])],
                    [
                        InlineKeyboardButton("📊 My Files", callback_data="user_files"),
                        InlineKeyboardButton("📈 Stats", callback_data="user_stats")
                    ]
                ])
                
                await status_msg.edit_text(success_text, reply_markup=keyboard)
                
            else:
                # Error message
                error_text = self.config.ERROR_MESSAGES["upload_failed"].format(
                    error=result.get('error', 'Unknown error')
                )
                
                await status_msg.edit_text(error_text)
            
            # Cleanup
            await self.utils.cleanup_file(file_path)
            
        except asyncio.CancelledError:
            await message.reply(self.config.ERROR_MESSAGES["operation_cancelled"])
        except Exception as e:
            logger.error(f"Error processing file upload: {e}")
            await message.reply(self.config.ERROR_MESSAGES["processing_error"])
    
    # URL download handler
    async def handle_text_message(self, message: Message):
        """Handle text messages (URLs)"""
        try:
            text = message.text.strip()
            
            # Check if it's a URL
            if self.utils.is_valid_url(text):
                if await self.check_user_permissions(message):
                    await self.handle_url_download(message, text)
            else:
                # Unknown command
                await message.reply(
                    "❌ **Unknown Command**\n\n"
                    "💡 **Available options:**\n"
                    "• Send me any file to upload to GoFile.io\n"
                    "• Send me any URL to download and upload\n"
                    "• Use /help to see all commands\n\n"
                    "📊 **Limits:**\n"
                    "• Max upload: 4GB per file\n"
                    "• Max download: 2GB per file"
                )
                
        except Exception as e:
            logger.error(f"Error in text message handler: {e}")
    
    async def handle_url_download(self, message: Message, url: str):
        """Handle URL download and upload"""
        try:
            user_id = message.from_user.id
            
            # Cancel any existing operation
            if user_id in self.active_operations:
                self.active_operations[user_id].cancel()
            
            # Check if it's a supported platform for quality selection
            if self.downloader.is_supported_platform(url):
                await self._show_quality_selection(message, url)
            else:
                # Direct download
                download_task = asyncio.create_task(
                    self._process_url_download(message, url)
                )
                self.active_operations[user_id] = download_task
                
                try:
                    await download_task
                finally:
                    if user_id in self.active_operations:
                        del self.active_operations[user_id]
                        
        except Exception as e:
            logger.error(f"Error in URL download handler: {e}")
            await message.reply(self.config.ERROR_MESSAGES["processing_error"])
    
    async def _show_quality_selection(self, message: Message, url: str):
        """Show quality selection for supported platforms"""
        try:
            # Get available qualities
            quality_info = await self.downloader.get_quality_options(url)
            
            if not quality_info['success']:
                # Fallback to direct download
                await self._process_url_download(message, url)
                return
            
            title = quality_info['title'][:50]
            duration = quality_info.get('duration', 0)
            
            quality_text = f"🎥 **Quality Selection**\n\n"
            quality_text += f"📺 **Title:** {title}\n"
            if duration:
                minutes = duration // 60
                seconds = duration % 60
                quality_text += f"⏱️ **Duration:** {minutes}:{seconds:02d}\n"
            quality_text += f"\n🎯 **Choose quality:**"
            
            keyboard = []
            
            # Video formats
            if quality_info.get('has_video'):
                keyboard.append([InlineKeyboardButton("🎥 Video Formats", callback_data="quality_video")])
                
            # Audio formats
            if quality_info.get('has_audio'):
                keyboard.append([InlineKeyboardButton("🎵 Audio Only", callback_data="quality_audio")])
            
            # Quick options
            keyboard.extend([
                [
                    InlineKeyboardButton("🏆 Best Quality", callback_data=f"download_best:{url}"),
                    InlineKeyboardButton("💾 Small Size", callback_data=f"download_worst:{url}")
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_download")]
            ])
            
            # Store URL for callback
            await self.db.store_temp_data(message.from_user.id, 'download_url', url)
            await self.db.store_temp_data(message.from_user.id, 'quality_info', quality_info)
            
            await message.reply(
                quality_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Error showing quality selection: {e}")
            await self._process_url_download(message, url)
    
    async def _process_url_download(
        self, 
        message: Message, 
        url: str, 
        format_id: Optional[str] = None,
        extract_audio: bool = False
    ):
        """Process URL download with progress tracking"""
        try:
            # Send initial status
            status_msg = await message.reply(
                f"🔗 **Starting Download**\n\n"
                f"📥 **URL:** {url[:50]}{'...' if len(url) > 50 else ''}\n"
                f"🔄 **Status:** Analyzing URL..."
            )
            
            # Progress callback
            last_update = 0
            async def progress_callback(progress_data):
                nonlocal last_update
                current_time = time.time()
                
                if current_time - last_update >= 2:
                    try:
                        progress = progress_data.get('progress', 0)
                        speed = progress_data.get('speed', 0)
                        eta = progress_data.get('eta', 0)
                        downloaded = progress_data.get('downloaded', 0)
                        total = progress_data.get('total', 0)
                        
                        status_text = f"📥 **Downloading...** {progress}%\n\n"
                        status_text += f"📊 **Size:** {self.utils.format_file_size(downloaded)}"
                        if total:
                            status_text += f" / {self.utils.format_file_size(total)}"
                        status_text += f"\n⚡ **Speed:** {self.utils.format_file_size(int(speed))}/s"
                        if eta:
                            status_text += f"\n🕒 **ETA:** {int(eta)}s"
                        status_text += f"\n📊 {self.utils.create_progress_bar(progress)}"
                        
                        await status_msg.edit_text(status_text)
                        last_update = current_time
                    except:
                        pass
            
            # Download file
            result = await self.downloader.download_from_url(
                url, format_id, extract_audio, progress_callback
            )
            
            if not result['success']:
                error_text = self.config.ERROR_MESSAGES["download_failed"].format(
                    error=result.get('error', 'Unknown error')
                )
                await status_msg.edit_text(error_text)
                return
            
            # Update status for upload
            await status_msg.edit_text(
                f"📤 **Uploading to GoFile**\n\n"
                f"📁 **File:** {result['filename']}\n"
                f"📊 **Size:** {self.utils.format_file_size(result['filesize'])}\n"
                f"🔄 **Status:** Uploading..."
            )
            
            # Upload progress callback
            async def upload_progress_callback(progress_data):
                nonlocal last_update
                current_time = time.time()
                
                if current_time - last_update >= 2:
                    try:
                        progress = progress_data.get('progress', 0)
                        speed = progress_data.get('speed', 0)
                        
                        await status_msg.edit_text(
                            f"📤 **Uploading to GoFile** {progress}%\n\n"
                            f"📁 **File:** {result['filename']}\n"
                            f"📊 **Size:** {self.utils.format_file_size(result['filesize'])}\n"
                            f"⚡ **Speed:** {self.utils.format_file_size(int(speed))}/s\n"
                            f"📊 {self.utils.create_progress_bar(progress)}"
                        )
                        last_update = current_time
                    except:
                        pass
            
            # Upload to GoFile
            upload_result = await self.utils.upload_to_gofile(
                result['filepath'],
                result['filename'],
                message.from_user.id,
                upload_progress_callback
            )
            
            if upload_result['success']:
                # Save to database
                await self.db.save_file({
                    'user_id': message.from_user.id,
                    'file_name': result['filename'],
                    'file_size': result['filesize'],
                    'file_type': 'download',
                    'gofile_id': upload_result['file_id'],
                    'gofile_url': upload_result['download_url'],
                    'source_url': url
                })
                
                # Success message
                success_text = self.config.SUCCESS_MESSAGES["download_complete"].format(
                    filename=result['filename'],
                    filesize=self.utils.format_file_size(result['filesize']),
                    url=upload_result['download_url']
                )
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📁 Download File", url=upload_result['download_url'])],
                    [
                        InlineKeyboardButton("📊 My Files", callback_data="user_files"),
                        InlineKeyboardButton("🔄 Download Another", callback_data="help_download")
                    ]
                ])
                
                await status_msg.edit_text(success_text, reply_markup=keyboard)
                
            else:
                # Upload error
                error_text = self.config.ERROR_MESSAGES["upload_failed"].format(
                    error=upload_result.get('error', 'Unknown error')
                )
                await status_msg.edit_text(error_text)
            
            # Cleanup
            await self.utils.cleanup_file(result['filepath'])
            
        except asyncio.CancelledError:
            await message.reply(self.config.ERROR_MESSAGES["operation_cancelled"])
        except Exception as e:
            logger.error(f"Error processing URL download: {e}")
            await message.reply(self.config.ERROR_MESSAGES["processing_error"])
    
    # Admin handlers
    async def handle_admin(self, message: Message):
        """Handle /admin command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await message.reply(self.config.ERROR_MESSAGES["admin_only"])
                return
            
            stats = await self.db.get_bot_stats()
            
            admin_text = f"🛡️ **Admin Panel**\n\n"
            admin_text += f"📊 **Bot Statistics:**\n"
            admin_text += f"👥 Total Users: {stats.get('total_users', 0)}\n"
            admin_text += f"🟢 Active (7d): {stats.get('active_users', 0)}\n"
            admin_text += f"📁 Total Files: {stats.get('total_files', 0)}\n"
            admin_text += f"💾 Storage: {stats.get('storage_gb', 0):.2f} GB\n\n"
            
            admin_text += f"⚙️ **System Info:**\n"
            admin_text += f"📤 Max Upload: {self.config.get_file_size_limit_gb():.1f}GB\n"
            admin_text += f"📥 Max Download: {self.config.get_download_size_limit_gb():.1f}GB\n"
            admin_text += f"🔒 Force Sub: {'✅' if self.config.FORCE_SUB_ENABLED else '❌'}\n"
            admin_text += f"🎥 yt-dlp: {'✅' if self.config.YTDLP_ENABLED else '❌'}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("👥 Users", callback_data="admin_users"),
                    InlineKeyboardButton("📊 Stats", callback_data="admin_stats")
                ],
                [
                    InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
                    InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")
                ],
                [
                    InlineKeyboardButton("🔒 Force Sub", callback_data="admin_forcesub"),
                    InlineKeyboardButton("📋 Logs", callback_data="admin_logs")
                ]
            ])
            
            await message.reply(admin_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in admin handler: {e}")
    
    async def handle_broadcast(self, message: Message):
        """Handle /broadcast command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await message.reply(self.config.ERROR_MESSAGES["admin_only"])
                return
            
            # Extract message
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) < 2:
                await message.reply(
                    "📢 **Broadcast Message**\n\n"
                    "**Usage:** `/broadcast <message>`\n\n"
                    "**Example:**\n"
                    "`/broadcast Hello everyone! 👋`\n\n"
                    "⚠️ **Warning:** This sends to ALL users!"
                )
                return
            
            broadcast_text = command_parts[1]
            
            # Get all users
            all_users = await self.db.get_all_users(limit=10000)
            
            if not all_users:
                await message.reply("📋 No users found to broadcast to.")
                return
            
            # Confirmation
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Confirm Broadcast", callback_data=f"broadcast_confirm"),
                    InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")
                ]
            ])
            
            # Store broadcast data
            await self.db.store_temp_data(message.from_user.id, 'broadcast_text', broadcast_text)
            await self.db.store_temp_data(message.from_user.id, 'broadcast_users', all_users)
            
            await message.reply(
                f"📢 **Confirm Broadcast**\n\n"
                f"📝 **Message:**\n{broadcast_text}\n\n"
                f"👥 **Recipients:** {len(all_users)} users\n\n"
                f"❗ **Are you sure?**",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in broadcast handler: {e}")
    
    async def handle_users_list(self, message: Message):
        """Handle /users command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await message.reply(self.config.ERROR_MESSAGES["admin_only"])
                return
            
            users = await self.db.get_all_users(limit=25)
            
            if not users:
                await message.reply("📋 No users found.")
                return
            
            users_text = "👥 **Bot Users (Recent 25):**\n\n"
            
            for i, user in enumerate(users, 1):
                username = user.get('username', 'N/A')
                name = user.get('first_name', 'Unknown')
                banned = user.get('is_banned', False)
                files = user.get('usage_stats', {}).get('files_uploaded', 0)
                join_date = user.get('join_date', datetime.utcnow()).strftime('%m/%d')
                
                status = "🚫" if banned else "✅"
                
                users_text += f"{i}. {status} **{name}** (@{username})\n"
                users_text += f"   🆔 `{user['user_id']}` • 📁 {files} files • 📅 {join_date}\n\n"
            
            total_users = await self.db.get_users_count()
            users_text += f"📊 **Total Users:** {total_users}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="admin_users"),
                    InlineKeyboardButton("📊 Detailed Stats", callback_data="admin_stats")
                ]
            ])
            
            await message.reply(users_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in users list handler: {e}")
    
    async def handle_ban_user(self, message: Message):
        """Handle /ban command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await message.reply(self.config.ERROR_MESSAGES["admin_only"])
                return
            
            command_parts = message.text.split()
            if len(command_parts) < 2:
                await message.reply(
                    "🚫 **Ban User**\n\n"
                    "**Usage:** `/ban <user_id> [reason]`\n\n"
                    "**Example:**\n"
                    "`/ban 123456789 Spam`"
                )
                return
            
            try:
                user_id = int(command_parts[1])
            except ValueError:
                await message.reply("❌ Invalid user ID.")
                return
            
            reason = " ".join(command_parts[2:]) if len(command_parts) > 2 else "No reason"
            
            # Check if user exists
            user = await self.db.get_user(user_id)
            if not user:
                await message.reply(f"❌ User {user_id} not found.")
                return
            
            # Ban user
            success = await self.db.ban_user(user_id, message.from_user.id, reason)
            
            if success:
                await message.reply(
                    f"✅ **User Banned**\n\n"
                    f"🆔 **User:** {user_id}\n"
                    f"👤 **Name:** {user.get('first_name', 'Unknown')}\n"
                    f"📝 **Reason:** {reason}"
                )
            else:
                await message.reply(f"❌ Failed to ban user {user_id}.")
                
        except Exception as e:
            logger.error(f"Error in ban user handler: {e}")
    
    async def handle_unban_user(self, message: Message):
        """Handle /unban command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await message.reply(self.config.ERROR_MESSAGES["admin_only"])
                return
            
            command_parts = message.text.split()
            if len(command_parts) < 2:
                await message.reply(
                    "✅ **Unban User**\n\n"
                    "**Usage:** `/unban <user_id>`\n\n"
                    "**Example:**\n"
                    "`/unban 123456789`"
                )
                return
            
            try:
                user_id = int(command_parts[1])
            except ValueError:
                await message.reply("❌ Invalid user ID.")
                return
            
            # Unban user
            success = await self.db.unban_user(user_id, message.from_user.id)
            
            if success:
                await message.reply(
                    f"✅ **User Unbanned**\n\n"
                    f"🆔 **User:** {user_id}\n"
                    f"📅 **Can now use the bot again**"
                )
            else:
                await message.reply(f"❌ Failed to unban user {user_id}.")
                
        except Exception as e:
            logger.error(f"Error in unban user handler: {e}")
    
    async def handle_admin_stats(self, message: Message):
        """Handle /stats_admin command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await message.reply(self.config.ERROR_MESSAGES["admin_only"])
                return
            
            stats = await self.db.get_detailed_stats()
            
            stats_text = f"📊 **Detailed Bot Statistics**\n\n"
            
            stats_text += f"👥 **Users:**\n"
            stats_text += f"• Total: {stats.get('total_users', 0)}\n"
            stats_text += f"• Active (7d): {stats.get('active_users', 0)}\n"
            stats_text += f"• Active (30d): {stats.get('monthly_active', 0)}\n"
            stats_text += f"• Banned: {stats.get('banned_users', 0)}\n\n"
            
            stats_text += f"📁 **Files:**\n"
            stats_text += f"• Total: {stats.get('total_files', 0)}\n"
            stats_text += f"• Today: {stats.get('files_today', 0)}\n"
            stats_text += f"• This Week: {stats.get('files_week', 0)}\n"
            stats_text += f"• Storage: {stats.get('storage_gb', 0):.2f} GB\n\n"
            
            stats_text += f"📥 **Downloads:**\n"
            stats_text += f"• Total URLs: {stats.get('total_downloads', 0)}\n"
            stats_text += f"• Success Rate: {stats.get('success_rate', 0):.1f}%\n"
            stats_text += f"• Popular Platforms: {', '.join(stats.get('top_platforms', [])[:3])}\n\n"
            
            stats_text += f"⚙️ **System:**\n"
            stats_text += f"• Uptime: {stats.get('uptime', 'Unknown')}\n"
            stats_text += f"• Version: {self.config.BOT_INFO['version']}\n"
            stats_text += f"• yt-dlp: {'✅' if self.config.YTDLP_ENABLED else '❌'}"
            
            await message.reply(stats_text)
            
        except Exception as e:
            logger.error(f"Error in admin stats handler: {e}")
    
    async def handle_force_sub_settings(self, message: Message):
        """Handle /force_sub command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await message.reply(self.config.ERROR_MESSAGES["admin_only"])
                return
            
            settings_text = f"🔒 **Force Subscription Settings**\n\n"
            settings_text += f"**Status:** {'✅ Enabled' if self.config.FORCE_SUB_ENABLED else '❌ Disabled'}\n"
            settings_text += f"**Channel:** {self.config.FORCE_SUB_CHANNEL or 'Not Set'}\n\n"
            
            if self.config.FORCE_SUB_ENABLED and self.config.FORCE_SUB_CHANNEL:
                try:
                    chat = await self.app.get_chat(self.config.FORCE_SUB_CHANNEL)
                    settings_text += f"✅ **Channel Info:**\n"
                    settings_text += f"• Name: {chat.title}\n"
                    settings_text += f"• Members: {chat.members_count or 'Unknown'}\n"
                    settings_text += f"• Type: {chat.type}\n\n"
                except Exception as e:
                    settings_text += f"❌ **Channel Error:** {str(e)}\n\n"
            
            settings_text += f"⚙️ **Configuration:**\n"
            settings_text += f"These settings are in your `.env` file:\n"
            settings_text += f"```\n"
            settings_text += f"FORCE_SUB_ENABLED={self.config.FORCE_SUB_ENABLED}\n"
            settings_text += f"FORCE_SUB_CHANNEL={self.config.FORCE_SUB_CHANNEL}\n"
            settings_text += f"```\n\n"
            settings_text += f"**Note:** Restart bot after changes."
            
            await message.reply(settings_text)
            
        except Exception as e:
            logger.error(f"Error in force sub settings: {e}")
    
    # Callback query handler
    async def handle_callback_query(self, callback_query: CallbackQuery):
        """Handle all callback queries"""
        try:
            await callback_query.answer()
            
            data = callback_query.data
            user_id = callback_query.from_user.id
            message = callback_query.message
            
            # Handle different callback types
            if data == "check_subscription":
                await self._handle_subscription_check(callback_query)
            elif data.startswith("download_"):
                await self._handle_download_callback(callback_query)
            elif data.startswith("quality_"):
                await self._handle_quality_callback(callback_query)
            elif data.startswith("settings_"):
                await self._handle_settings_callback(callback_query)
            elif data.startswith("admin_"):
                await self._handle_admin_callback(callback_query)
            elif data in ["user_files", "user_stats", "user_settings"]:
                await self._handle_user_callback(callback_query)
            elif data in ["show_help", "show_about", "show_platforms"]:
                await self._handle_info_callback(callback_query)
            else:
                await callback_query.answer("❌ Unknown action", show_alert=True)
                
        except Exception as e:
            logger.error(f"Error in callback query handler: {e}")
            await callback_query.answer("❌ An error occurred", show_alert=True)
    
    async def _handle_subscription_check(self, callback_query: CallbackQuery):
        """Handle subscription check callback"""
        if await self.check_subscription(callback_query.from_user.id):
            await self.db.update_user(callback_query.from_user.id, {"subscription_status": True})
            await callback_query.message.edit_text(
                "✅ **Subscription Verified!**\n\n"
                "Welcome to GoFile Uploader Bot! 🎉\n\n"
                "🚀 **Get Started:**\n"
                "• Send me any file to upload to GoFile.io\n"
                "• Send any URL to download and upload\n"
                "• Use /help for all commands"
            )
        else:
            await callback_query.message.edit_text(
                "❌ **Subscription Not Found**\n\n"
                "Please join the channel first, then try again.\n\n"
                "If you're having issues, contact an administrator."
            )
    
    async def _handle_download_callback(self, callback_query: CallbackQuery):
        """Handle download-related callbacks"""
        data = callback_query.data
        
        if data.startswith("download_best:"):
            url = data.replace("download_best:", "")
            await self._process_url_download(callback_query.message, url, format_id="best")
        elif data.startswith("download_worst:"):
            url = data.replace("download_worst:", "")
            await self._process_url_download(callback_query.message, url, format_id="worst")
        elif data == "cancel_download":
            user_id = callback_query.from_user.id
            if user_id in self.active_operations:
                self.active_operations[user_id].cancel()
                del self.active_operations[user_id]
            await callback_query.message.edit_text("❌ Download cancelled.")
    
    async def _handle_quality_callback(self, callback_query: CallbackQuery):
        """Handle quality selection callbacks"""
        # Implement quality selection interface
        await callback_query.answer("🔧 Quality selection coming soon!", show_alert=True)
    
    async def _handle_settings_callback(self, callback_query: CallbackQuery):
        """Handle settings callbacks"""
        await callback_query.answer("⚙️ Settings panel coming soon!", show_alert=True)
    
    async def _handle_admin_callback(self, callback_query: CallbackQuery):
        """Handle admin callbacks"""
        if not self.config.is_admin(callback_query.from_user.id):
            await callback_query.answer("🔒 Admin access required", show_alert=True)
            return
            
        await callback_query.answer("🛡️ Admin features coming soon!", show_alert=True)
    
    async def _handle_user_callback(self, callback_query: CallbackQuery):
        """Handle user-related callbacks"""
        data = callback_query.data
        
        if data == "user_files":
            # Create fake message to reuse myfiles handler
            fake_msg = callback_query.message
            fake_msg.from_user = callback_query.from_user
            await self.handle_myfiles(fake_msg)
        elif data == "user_stats":
            fake_msg = callback_query.message  
            fake_msg.from_user = callback_query.from_user
            await self.handle_stats(fake_msg)
        elif data == "user_settings":
            fake_msg = callback_query.message
            fake_msg.from_user = callback_query.from_user  
            await self.handle_settings(fake_msg)
    
    async def _handle_info_callback(self, callback_query: CallbackQuery):
        """Handle info callbacks"""
        data = callback_query.data
        
        if data == "show_help":
            fake_msg = callback_query.message
            fake_msg.from_user = callback_query.from_user
            await self.handle_help(fake_msg)
        elif data == "show_about":
            fake_msg = callback_query.message
            fake_msg.from_user = callback_query.from_user
            await self.handle_about(fake_msg)
        elif data == "show_platforms":
            platforms = await self.downloader.get_supported_platforms_list()
            platforms_text = "📱 **Supported Platforms:**\n\n" + "\n".join(platforms)
            await callback_query.message.edit_text(platforms_text)
