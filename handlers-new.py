"""
Bot command and message handlers
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_helper import ApiTelegramException

from config import Config
from database import Database
from utils import Utils

logger = logging.getLogger(__name__)


class BotHandlers:
    """Bot handlers for commands and messages"""
    
    def __init__(self, bot: AsyncTeleBot, database: Database, utils: Utils, config: Config):
        self.bot = bot
        self.db = database
        self.utils = utils
        self.config = config
        self.user_last_activity = {}
        
    def setup_handlers(self) -> None:
        """Set up all bot handlers"""
        # Command handlers
        self.bot.message_handler(commands=['start'])(self.start_command)
        self.bot.message_handler(commands=['help'])(self.help_command)
        self.bot.message_handler(commands=['upload'])(self.upload_command)
        self.bot.message_handler(commands=['download'])(self.download_command)
        self.bot.message_handler(commands=['settings'])(self.settings_command)
        self.bot.message_handler(commands=['myfiles'])(self.myfiles_command)
        self.bot.message_handler(commands=['account'])(self.account_command)
        self.bot.message_handler(commands=['stats'])(self.stats_command)
        
        # Admin commands
        self.bot.message_handler(commands=['admin'])(self.admin_command)
        self.bot.message_handler(commands=['broadcast'])(self.broadcast_command)
        self.bot.message_handler(commands=['stats_admin'])(self.admin_stats_command)
        self.bot.message_handler(commands=['users'])(self.users_command)
        self.bot.message_handler(commands=['ban'])(self.ban_command)
        self.bot.message_handler(commands=['unban'])(self.unban_command)
        self.bot.message_handler(commands=['force_sub'])(self.force_sub_command)
        
        # File handlers
        self.bot.message_handler(content_types=self.config.ALLOWED_FILE_TYPES)(self.file_handler)
        
        # Text message handler
        self.bot.message_handler(func=lambda message: True)(self.text_handler)
        
        # Callback query handlers
        self.bot.callback_query_handler(func=lambda call: True)(self.callback_handler)
        
        logger.info("Bot handlers set up successfully")
        
    async def check_subscription(self, user_id: int) -> bool:
        """Check if user is subscribed to the required channel"""
        if not self.config.FORCE_SUB_ENABLED or not self.config.FORCE_SUB_CHANNEL:
            return True
            
        try:
            member = await self.bot.get_chat_member(self.config.FORCE_SUB_CHANNEL, user_id)
            return member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            logger.error(f"Failed to check subscription for user {user_id}: {e}")
            return False
            
    async def check_user_permissions(self, message: types.Message) -> bool:
        """Check user permissions and rate limits"""
        user_id = message.from_user.id
        
        # Check if user is banned
        if await self.db.is_user_banned(user_id):
            await self.bot.reply_to(message, self.config.ERROR_MESSAGES["user_banned"])
            return False
            
        # Check subscription
        if not await self.check_subscription(user_id):
            await self.send_subscription_message(message)
            return False
            
        return True
        
    async def send_subscription_message(self, message: types.Message) -> None:
        """Send subscription required message"""
        markup = types.InlineKeyboardMarkup()
        
        join_btn = types.InlineKeyboardButton(
            "🔗 Join Channel",
            url=f"https://t.me/{self.config.FORCE_SUB_CHANNEL.lstrip('@')}"
        )
        
        check_btn = types.InlineKeyboardButton(
            "✅ I've Joined",
            callback_data="check_subscription"
        )
        
        markup.row(join_btn)
        markup.row(check_btn)
        
        await self.bot.reply_to(
            message,
            self.config.ERROR_MESSAGES["not_subscribed"],
            reply_markup=markup
        )
        
    # Command handlers
    async def start_command(self, message: types.Message) -> None:
        """Handle /start command"""
        try:
            user_id = message.from_user.id
            
            # Create user if doesn't exist
            user_data = {
                "user_id": user_id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name
            }
            
            await self.db.create_user(user_data)
            
            # Check permissions
            if not await self.check_user_permissions(message):
                return
                
            # Send welcome message
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("📁 Upload File", callback_data="help_upload"),
                types.InlineKeyboardButton("🔗 Download URL", callback_data="help_download")
            )
            markup.row(
                types.InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
                types.InlineKeyboardButton("📊 My Stats", callback_data="stats")
            )
            markup.row(
                types.InlineKeyboardButton("❓ Help", callback_data="help")
            )
            
            await self.bot.reply_to(
                message,
                self.config.WELCOME_MESSAGE,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await self.bot.reply_to(message, "❌ An error occurred. Please try again.")
            
    async def help_command(self, message: types.Message) -> None:
        """Handle /help command"""
        try:
            if not await self.check_user_permissions(message):
                return
                
            help_text = self.config.HELP_MESSAGE
            
            # Add admin help for admins
            if self.config.is_admin(message.from_user.id):
                help_text += f"\n\n{self.config.ADMIN_HELP_MESSAGE}"
                
            await self.bot.reply_to(message, help_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            
    async def upload_command(self, message: types.Message) -> None:
        """Handle /upload command"""
        try:
            if not await self.check_user_permissions(message):
                return
                
            # Check if replying to a file
            if message.reply_to_message:
                await self.process_file_upload(message.reply_to_message)
            else:
                await self.bot.reply_to(
                    message,
                    "📁 Please reply to a file with /upload command to upload it to GoFile.io"
                )
                
        except Exception as e:
            logger.error(f"Error in upload command: {e}")
            
    async def download_command(self, message: types.Message) -> None:
        """Handle /download command"""
        try:
            if not await self.check_user_permissions(message):
                return
                
            # Extract URL from command
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) < 2:
                await self.bot.reply_to(
                    message,
                    "🔗 Please provide a URL to download:\n\n`/download https://example.com/file.zip`",
                    parse_mode='Markdown'
                )
                return
                
            url = command_parts[1].strip()
            
            # Validate URL
            if not self.utils.is_valid_url(url):
                await self.bot.reply_to(message, self.config.ERROR_MESSAGES["invalid_url"])
                return
                
            # Start download process
            await self.download_and_upload(message, url)
            
        except Exception as e:
            logger.error(f"Error in download command: {e}")
            
    async def settings_command(self, message: types.Message) -> None:
        """Handle /settings command"""
        try:
            if not await self.check_user_permissions(message):
                return
                
            await self.bot.reply_to(
                message,
                "⚙️ **Settings**\n\nSettings panel coming soon!",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in settings command: {e}")
            
    async def myfiles_command(self, message: types.Message) -> None:
        """Handle /myfiles command"""
        try:
            if not await self.check_user_permissions(message):
                return
                
            files = await self.db.get_user_files(message.from_user.id, limit=10)
            
            if not files:
                await self.bot.reply_to(
                    message,
                    "📁 You haven't uploaded any files yet. Send me a file to get started!"
                )
                return
                
            files_text = "📁 **Your Recent Files:**\n\n"
            
            for i, file_doc in enumerate(files, 1):
                file_name = file_doc.get('file_name', 'Unknown')
                file_size = self.utils.format_file_size(file_doc.get('file_size', 0))
                upload_date = file_doc.get('upload_date', datetime.utcnow()).strftime('%Y-%m-%d')
                
                files_text += f"{i}. **{file_name}**\n"
                files_text += f"   📊 Size: {file_size}\n"
                files_text += f"   📅 Date: {upload_date}\n"
                files_text += f"   🔗 [Download](https://gofile.io/d/{file_doc.get('gofile_id', '')})\n\n"
                
            await self.bot.reply_to(
                message,
                files_text,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Error in myfiles command: {e}")
            
    async def account_command(self, message: types.Message) -> None:
        """Handle /account command"""
        try:
            if not await self.check_user_permissions(message):
                return
                
            await self.bot.reply_to(
                message,
                "🔗 **GoFile Account**\n\nAccount management coming soon!",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in account command: {e}")
            
    async def stats_command(self, message: types.Message) -> None:
        """Handle /stats command"""
        try:
            if not await self.check_user_permissions(message):
                return
                
            user = await self.db.get_user(message.from_user.id)
            if not user:
                await self.bot.reply_to(message, "❌ User not found. Please use /start first.")
                return
                
            stats = user.get('usage_stats', {})
            join_date = user.get('join_date', datetime.utcnow()).strftime('%Y-%m-%d')
            
            files_uploaded = stats.get('files_uploaded', 0)
            total_size = self.utils.format_file_size(stats.get('total_size', 0))
            
            stats_text = f"""
📊 **Your Statistics**

👤 **User Info:**
🆔 ID: `{user['user_id']}`
📅 Joined: {join_date}

📁 **Upload Stats:**
📄 Files Uploaded: {files_uploaded}
💾 Total Size: {total_size}
"""
            
            await self.bot.reply_to(
                message,
                stats_text,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in stats command: {e}")
            
    # Admin commands
    async def admin_command(self, message: types.Message) -> None:
        """Handle /admin command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await self.bot.reply_to(message, self.config.ERROR_MESSAGES["admin_only"])
                return
                
            bot_stats = await self.db.get_bot_stats()
            
            admin_text = f"""
🛡️ **Admin Panel**

📊 **Bot Statistics:**
👥 Total Users: {bot_stats.get('total_users', 0)}
📁 Total Files: {bot_stats.get('total_files', 0)}
💾 Storage Used: {bot_stats.get('storage_gb', 0)} GB

⚙️ **Available Commands:**
/stats_admin - Detailed bot statistics
/users - List all users
/broadcast <message> - Broadcast to all users
/ban <user_id> - Ban a user
/unban <user_id> - Unban a user
"""
            
            await self.bot.reply_to(
                message,
                admin_text,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in admin command: {e}")
            
    async def broadcast_command(self, message: types.Message) -> None:
        """Handle /broadcast command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await self.bot.reply_to(message, self.config.ERROR_MESSAGES["admin_only"])
                return
                
            # Extract broadcast message
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) < 2:
                await self.bot.reply_to(
                    message,
                    "📢 Please provide a message to broadcast:\n\n`/broadcast Your message here`",
                    parse_mode='Markdown'
                )
                return
                
            broadcast_text = command_parts[1]
            
            # Get all users
            all_users = await self.db.get_all_users(limit=1000)
            
            success_count = 0
            
            # Send status message
            status_msg = await self.bot.reply_to(
                message,
                f"📢 Starting broadcast to {len(all_users)} users..."
            )
            
            # Broadcast to all users
            for user in all_users:
                try:
                    await self.bot.send_message(user['user_id'], broadcast_text)
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send broadcast to user {user['user_id']}: {e}")
                    
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
                
            # Final status
            final_text = self.config.SUCCESS_MESSAGES["broadcast_sent"].format(count=success_count)
            
            await self.bot.edit_message_text(
                final_text,
                chat_id=status_msg.chat.id,
                message_id=status_msg.message_id
            )
            
        except Exception as e:
            logger.error(f"Error in broadcast command: {e}")
            
    async def admin_stats_command(self, message: types.Message) -> None:
        """Handle /stats_admin command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await self.bot.reply_to(message, self.config.ERROR_MESSAGES["admin_only"])
                return
                
            stats = await self.db.get_bot_stats()
            
            stats_text = f"""
📊 **Bot Statistics**

👥 **Users:**
• Total Users: {stats.get('total_users', 0)}
• Active Users (7d): {stats.get('active_users', 0)}

📁 **Files:**
• Total Files: {stats.get('total_files', 0)}
• Total Storage: {stats.get('storage_gb', 0)} GB

⚙️ **System:**
• Force Subscription: {"Enabled" if self.config.FORCE_SUB_ENABLED else "Disabled"}
• Max File Size: {self.config.MAX_FILE_SIZE // 1024**2} MB
"""
            
            await self.bot.reply_to(
                message,
                stats_text,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in admin stats command: {e}")
            
    async def users_command(self, message: types.Message) -> None:
        """Handle /users command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await self.bot.reply_to(message, self.config.ERROR_MESSAGES["admin_only"])
                return
                
            users = await self.db.get_all_users(limit=20)
            
            if not users:
                await self.bot.reply_to(message, "📋 No users found.")
                return
                
            users_text = "👥 **Bot Users (First 20):**\n\n"
            
            for i, user in enumerate(users, 1):
                username = user.get('username', 'N/A')
                first_name = user.get('first_name', 'Unknown')
                is_banned = user.get('is_banned', False)
                join_date = user.get('join_date', datetime.utcnow()).strftime('%Y-%m-%d')
                
                status = "🚫 Banned" if is_banned else "✅ Active"
                
                users_text += f"{i}. **{first_name}** (@{username})\n"
                users_text += f"   🆔 ID: `{user['user_id']}`\n"
                users_text += f"   📅 Joined: {join_date}\n"
                users_text += f"   📊 Status: {status}\n\n"
                
            await self.bot.reply_to(
                message,
                users_text,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in users command: {e}")
            
    async def ban_command(self, message: types.Message) -> None:
        """Handle /ban command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await self.bot.reply_to(message, self.config.ERROR_MESSAGES["admin_only"])
                return
                
            # Extract user ID from command
            command_parts = message.text.split()
            if len(command_parts) < 2:
                await self.bot.reply_to(
                    message,
                    "🚫 Please provide a user ID to ban:\n\n`/ban 123456789`",
                    parse_mode='Markdown'
                )
                return
                
            try:
                user_id = int(command_parts[1])
            except ValueError:
                await self.bot.reply_to(message, "❌ Invalid user ID provided.")
                return
                
            # Ban user
            success = await self.db.ban_user(user_id, message.from_user.id)
            
            if success:
                success_text = self.config.SUCCESS_MESSAGES["user_banned"].format(user_id=user_id)
                await self.bot.reply_to(message, success_text)
            else:
                await self.bot.reply_to(message, f"❌ Failed to ban user {user_id}.")
                
        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            
    async def unban_command(self, message: types.Message) -> None:
        """Handle /unban command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await self.bot.reply_to(message, self.config.ERROR_MESSAGES["admin_only"])
                return
                
            # Extract user ID from command
            command_parts = message.text.split()
            if len(command_parts) < 2:
                await self.bot.reply_to(
                    message,
                    "✅ Please provide a user ID to unban:\n\n`/unban 123456789`",
                    parse_mode='Markdown'
                )
                return
                
            try:
                user_id = int(command_parts[1])
            except ValueError:
                await self.bot.reply_to(message, "❌ Invalid user ID provided.")
                return
                
            # Unban user
            success = await self.db.unban_user(user_id, message.from_user.id)
            
            if success:
                success_text = self.config.SUCCESS_MESSAGES["user_unbanned"].format(user_id=user_id)
                await self.bot.reply_to(message, success_text)
            else:
                await self.bot.reply_to(message, f"❌ Failed to unban user {user_id}.")
                
        except Exception as e:
            logger.error(f"Error in unban command: {e}")
            
    async def force_sub_command(self, message: types.Message) -> None:
        """Handle /force_sub command"""
        try:
            if not self.config.is_admin(message.from_user.id):
                await self.bot.reply_to(message, self.config.ERROR_MESSAGES["admin_only"])
                return
                
            settings_text = f"""
⚙️ **Force Subscription Settings**

🔒 **Status:** {"✅ Enabled" if self.config.FORCE_SUB_ENABLED else "❌ Disabled"}
📢 **Channel:** {self.config.FORCE_SUB_CHANNEL or "Not Set"}

Configure these settings in your .env file:
- FORCE_SUB_ENABLED=true/false
- FORCE_SUB_CHANNEL=@your_channel
"""
            
            await self.bot.reply_to(
                message,
                settings_text,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in force_sub command: {e}")
            
    # File handling
    async def file_handler(self, message: types.Message) -> None:
        """Handle file uploads"""
        try:
            if not await self.check_user_permissions(message):
                return
                
            await self.process_file_upload(message)
            
        except Exception as e:
            logger.error(f"Error in file handler: {e}")
            
    async def process_file_upload(self, message: types.Message) -> None:
        """Process file upload to GoFile.io"""
        try:
            # Get file info
            file_info = self.utils.get_file_info(message)
            if not file_info:
                await self.bot.reply_to(message, "❌ Unable to process this file type.")
                return
                
            # Check file size
            if file_info['size'] > self.config.MAX_FILE_SIZE:
                max_size_mb = self.config.MAX_FILE_SIZE // 1024**2
                await self.bot.reply_to(
                    message,
                    self.config.ERROR_MESSAGES["file_too_large"].format(max_size=max_size_mb)
                )
                return
                
            # Start upload process
            status_msg = await self.bot.reply_to(
                message,
                f"📤 Uploading {file_info['name']} ({self.utils.format_file_size(file_info['size'])})..."
            )
            
            # Download file from Telegram
            file_path = await self.utils.download_telegram_file(self.bot, file_info['file_id'])
            
            # Upload to GoFile
            result = await self.utils.upload_to_gofile(file_path, file_info['name'], message.from_user.id)
            
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
                    url=result['download_url']
                )
                
                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton("📁 Download", url=result['download_url'])
                )
                
                await self.bot.edit_message_text(
                    success_text,
                    chat_id=status_msg.chat.id,
                    message_id=status_msg.message_id,
                    reply_markup=markup
                )
                
            else:
                error_msg = self.config.ERROR_MESSAGES["upload_failed"].format(
                    error=result.get('error', 'Unknown error')
                )
                await self.bot.edit_message_text(
                    error_msg,
                    chat_id=status_msg.chat.id,
                    message_id=status_msg.message_id
                )
                
            # Cleanup temp file
            await self.utils.cleanup_file(file_path)
            
        except Exception as e:
            logger.error(f"Error processing file upload: {e}")
            await self.bot.reply_to(message, "❌ An error occurred during upload.")
            
    async def download_and_upload(self, message: types.Message, url: str) -> None:
        """Download file from URL and upload to GoFile"""
        try:
            status_msg = await self.bot.reply_to(
                message,
                f"🔗 Downloading from URL...\n`{url[:50]}...`",
                parse_mode='Markdown'
            )
            
            # Download file
            downloaded_file = await self.utils.download_from_url(url)
            
            if not downloaded_file:
                await self.bot.edit_message_text(
                    self.config.ERROR_MESSAGES["download_failed"].format(error="Failed to download file"),
                    chat_id=status_msg.chat.id,
                    message_id=status_msg.message_id
                )
                return
                
            # Upload to GoFile
            await self.bot.edit_message_text(
                "📤 Uploading to GoFile.io...",
                chat_id=status_msg.chat.id,
                message_id=status_msg.message_id
            )
            
            filename = os.path.basename(downloaded_file)
            result = await self.utils.upload_to_gofile(downloaded_file, filename, message.from_user.id)
            
            if result['success']:
                # Save to database
                file_size = os.path.getsize(downloaded_file)
                await self.db.save_file({
                    'user_id': message.from_user.id,
                    'file_name': filename,
                    'file_size': file_size,
                    'file_type': 'download',
                    'gofile_id': result['file_id'],
                    'gofile_url': result['download_url']
                })
                
                # Success message
                success_text = self.config.SUCCESS_MESSAGES["download_complete"].format(
                    url=result['download_url']
                )
                
                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton("📁 Download", url=result['download_url'])
                )
                
                await self.bot.edit_message_text(
                    success_text,
                    chat_id=status_msg.chat.id,
                    message_id=status_msg.message_id,
                    reply_markup=markup
                )
                
            else:
                error_msg = self.config.ERROR_MESSAGES["upload_failed"].format(
                    error=result.get('error', 'Unknown error')
                )
                await self.bot.edit_message_text(
                    error_msg,
                    chat_id=status_msg.chat.id,
                    message_id=status_msg.message_id
                )
                
            # Cleanup
            await self.utils.cleanup_file(downloaded_file)
            
        except Exception as e:
            logger.error(f"Error in download and upload: {e}")
            await self.bot.reply_to(message, "❌ An error occurred during download and upload.")
            
    # Callback query handler
    async def callback_handler(self, call: types.CallbackQuery) -> None:
        """Handle callback queries from inline keyboards"""
        try:
            await self.bot.answer_callback_query(call.id)
            
            data = call.data
            
            if data == "check_subscription":
                if await self.check_subscription(call.from_user.id):
                    await self.db.update_user(call.from_user.id, {"subscription_status": True})
                    await self.bot.edit_message_text(
                        "✅ Subscription verified! You can now use the bot.",
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id
                    )
                else:
                    await self.bot.edit_message_text(
                        "❌ Please join the channel first and then click 'I've Joined'.",
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id
                    )
                    
            elif data == "settings":
                await self.settings_command(call.message)
                
            elif data == "stats":
                await self.stats_command(call.message)
                
            elif data == "help":
                await self.help_command(call.message)
                
        except Exception as e:
            logger.error(f"Error in callback handler: {e}")
            
    async def text_handler(self, message: types.Message) -> None:
        """Handle text messages"""
        try:
            # Check if it's a URL
            if self.utils.is_valid_url(message.text):
                if await self.check_user_permissions(message):
                    await self.download_and_upload(message, message.text.strip())
            else:
                # Unknown command
                await self.bot.reply_to(
                    message,
                    self.config.ERROR_MESSAGES["invalid_command"]
                )
                
        except Exception as e:
            logger.error(f"Error in text handler: {e}")