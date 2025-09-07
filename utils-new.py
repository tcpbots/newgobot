"""
Utility functions for file operations, API calls, and helper methods
"""

import asyncio
import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from urllib.parse import urlparse

import aiofiles
import aiohttp
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from config import Config
from database import Database

logger = logging.getLogger(__name__)


class Utils:
    """Utility functions for the bot"""
    
    def __init__(self, config: Config, database: Database):
        self.config = config
        self.db = database
        
        # Create directories if they don't exist
        os.makedirs(self.config.DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(self.config.TEMP_DIR, exist_ok=True)
        
    def is_valid_url(self, url: str) -> bool:
        """Check if a string is a valid URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
            
    def get_file_info(self, message: types.Message) -> Optional[Dict[str, Any]]:
        """Extract file information from Telegram message"""
        try:
            file_info = None
            
            if message.document:
                file_info = {
                    'file_id': message.document.file_id,
                    'name': message.document.file_name or 'document',
                    'size': message.document.file_size or 0,
                    'type': 'document',
                    'mime_type': message.document.mime_type
                }
            elif message.photo:
                photo = message.photo[-1]  # Get highest resolution
                file_info = {
                    'file_id': photo.file_id,
                    'name': f'photo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg',
                    'size': photo.file_size or 0,
                    'type': 'photo',
                    'mime_type': 'image/jpeg'
                }
            elif message.video:
                file_info = {
                    'file_id': message.video.file_id,
                    'name': message.video.file_name or f'video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4',
                    'size': message.video.file_size or 0,
                    'type': 'video',
                    'mime_type': message.video.mime_type or 'video/mp4'
                }
            elif message.audio:
                file_info = {
                    'file_id': message.audio.file_id,
                    'name': message.audio.file_name or f'audio_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp3',
                    'size': message.audio.file_size or 0,
                    'type': 'audio',
                    'mime_type': message.audio.mime_type or 'audio/mpeg'
                }
            elif message.voice:
                file_info = {
                    'file_id': message.voice.file_id,
                    'name': f'voice_{datetime.now().strftime("%Y%m%d_%H%M%S")}.ogg',
                    'size': message.voice.file_size or 0,
                    'type': 'voice',
                    'mime_type': 'audio/ogg'
                }
            elif message.video_note:
                file_info = {
                    'file_id': message.video_note.file_id,
                    'name': f'video_note_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4',
                    'size': message.video_note.file_size or 0,
                    'type': 'video_note',
                    'mime_type': 'video/mp4'
                }
            elif message.animation:
                file_info = {
                    'file_id': message.animation.file_id,
                    'name': message.animation.file_name or f'animation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.gif',
                    'size': message.animation.file_size or 0,
                    'type': 'animation',
                    'mime_type': message.animation.mime_type or 'image/gif'
                }
                
            return file_info
            
        except Exception as e:
            logger.error(f"Error extracting file info: {e}")
            return None
            
    async def download_telegram_file(self, bot: AsyncTeleBot, file_id: str) -> str:
        """Download file from Telegram servers"""
        try:
            # Get file info
            file_info = await bot.get_file(file_id)
            
            # Create temporary file path
            temp_file = tempfile.mktemp(dir=self.config.TEMP_DIR)
            
            # Download file
            downloaded_file = await bot.download_file(file_info.file_path)
            
            # Save to temporary file
            async with aiofiles.open(temp_file, 'wb') as f:
                await f.write(downloaded_file)
                
            return temp_file
            
        except Exception as e:
            logger.error(f"Error downloading Telegram file: {e}")
            raise
            
    async def upload_to_gofile(
        self, 
        file_path: str, 
        file_name: str, 
        user_id: int,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Upload file to GoFile.io"""
        try:
            # Get user's GoFile token if available
            user = await self.db.get_user(user_id)
            gofile_token = None
            
            if user and user.get('gofile_account', {}).get('token'):
                gofile_token = user['gofile_account']['token']
                
            # Prepare upload data
            headers = {}
            if gofile_token:
                headers['Authorization'] = f'Bearer {gofile_token}'
                
            # Upload file
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                
                # Add file
                async with aiofiles.open(file_path, 'rb') as f:
                    file_content = await f.read()
                    data.add_field('file', file_content, filename=file_name)
                    
                # Make upload request
                async with session.post(
                    self.config.GOFILE_UPLOAD_URL,
                    data=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('status') == 'ok':
                            data = result.get('data', {})
                            return {
                                'success': True,
                                'file_id': data.get('code', ''),
                                'download_url': data.get('downloadPage', ''),
                                'direct_link': data.get('directLink', ''),
                                'parent_folder': data.get('parentFolder', '')
                            }
                        else:
                            return {
                                'success': False,
                                'error': result.get('message', 'Unknown error')
                            }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f'HTTP {response.status}: {error_text}'
                        }
                        
        except Exception as e:
            logger.error(f"Error uploading to GoFile: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def download_from_url(
        self, 
        url: str, 
        progress_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """Download file from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Get filename from URL or headers
                        filename = self.get_filename_from_url(url, response.headers)
                        file_path = os.path.join(self.config.DOWNLOAD_DIR, filename)
                        
                        # Get total size
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        # Download with progress
                        async with aiofiles.open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(self.config.CHUNK_SIZE):
                                await f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update progress
                                if progress_callback and total_size > 0:
                                    percent = int(downloaded / total_size * 100)
                                    await progress_callback(percent)
                                    
                        return file_path
                        
            return None
            
        except Exception as e:
            logger.error(f"Error downloading from URL: {e}")
            return None
            
    def get_filename_from_url(self, url: str, headers: Dict[str, str]) -> str:
        """Extract filename from URL or headers"""
        try:
            # Try to get from Content-Disposition header
            if 'content-disposition' in headers:
                import re
                content_disp = headers['content-disposition']
                filename_match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', content_disp)
                if filename_match:
                    return filename_match.group(1)
                    
            # Get from URL
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            if filename and '.' in filename:
                return filename
                
            # Default filename
            return f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        except Exception:
            return f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
            
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
            
        return f"{size_bytes:.1f} {size_names[i]}"
        
    async def cleanup_file(self, file_path: str) -> None:
        """Remove temporary file"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")
            
    def validate_file_type(self, file_info: Dict[str, Any]) -> bool:
        """Validate if file type is allowed"""
        return file_info.get('type') in self.config.ALLOWED_FILE_TYPES
        
    def validate_file_size(self, size: int) -> bool:
        """Validate if file size is within limits"""
        return size <= self.config.MAX_FILE_SIZE