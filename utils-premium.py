"""
Premium Utilities v3.0
Reference: TheHamkerCat/WilliamButcherBot + FayasNoushad/GoFile-Bot
FIXES ALL GOFILE & UTILITY ISSUES!
"""

import asyncio
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union
from urllib.parse import urlparse
import json
import hashlib

import aiofiles
import aiohttp
import httpx
from pyrogram import Client
from pyrogram.types import Message

from config_premium import Config
from database_premium import PremiumDatabase

logger = logging.getLogger(__name__)


class PremiumUtilities:
    """Premium utilities with advanced GoFile integration"""
    
    def __init__(self):
        self.config = Config()
        self.db = PremiumDatabase()
        
        # Premium HTTP clients
        self.gofile_session = None
        self.general_session = None
        
        # Progress tracking
        self.active_operations = {}
        
        # Create directories
        self.config.create_directories()
        
    async def initialize(self):
        """Initialize premium utilities"""
        try:
            # Premium GoFile HTTP session
            self.gofile_session = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.UPLOAD_TIMEOUT),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
                headers={
                    'User-Agent': self.config.get_random_user_agent(),
                    'Accept': 'application/json',
                    'Connection': 'keep-alive',
                }
            )
            
            # General HTTP session
            self.general_session = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.REQUEST_TIMEOUT),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
                headers={
                    'User-Agent': self.config.get_random_user_agent(),
                    'Accept': '*/*',
                    'Connection': 'keep-alive',
                }
            )
            
            logger.info("✅ Premium utilities initialized!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize utilities: {e}")
    
    async def close(self):
        """Close premium utilities"""
        try:
            if self.gofile_session:
                await self.gofile_session.aclose()
            if self.general_session:
                await self.general_session.aclose()
        except Exception as e:
            logger.error(f"❌ Error closing utilities: {e}")
    
    # ================================
    # FILE INFORMATION & VALIDATION
    # ================================
    
    def is_valid_url(self, url: str) -> bool:
        """Advanced URL validation"""
        try:
            if not url or len(url) < 10:
                return False
            
            # Parse URL
            parsed = urlparse(url.strip())
            
            # Basic validation
            if not all([parsed.scheme, parsed.netloc]):
                return False
            
            # Check schemes
            if parsed.scheme.lower() not in ['http', 'https']:
                return False
            
            # Check for dangerous characters
            dangerous_chars = ['<', '>', '"', "'", '\n', '\r', '\t']
            if any(char in url for char in dangerous_chars):
                return False
            
            # Check length
            if len(url) > 2048:  # Standard URL length limit
                return False
            
            return True
            
        except Exception:
            return False
    
    async def get_file_info(self, message: Message) -> Optional[Dict[str, Any]]:
        """Extract comprehensive file information from Pyrogram message"""
        try:
            file_info = None
            current_time = int(time.time())
            
            if message.document:
                file_info = {
                    'file_id': message.document.file_id,
                    'name': message.document.file_name or f'document_{current_time}.bin',
                    'size': message.document.file_size or 0,
                    'type': 'document',
                    'mime_type': message.document.mime_type,
                    'date': message.document.date,
                    'thumb': message.document.thumbs[0] if message.document.thumbs else None
                }
            elif message.photo:
                # Get largest photo size
                largest_photo = max(message.photo, key=lambda x: x.file_size)
                file_info = {
                    'file_id': largest_photo.file_id,
                    'name': f'photo_{current_time}_{largest_photo.width}x{largest_photo.height}.jpg',
                    'size': largest_photo.file_size or 0,
                    'type': 'photo',
                    'mime_type': 'image/jpeg',
                    'width': largest_photo.width,
                    'height': largest_photo.height,
                    'date': largest_photo.date
                }
            elif message.video:
                file_info = {
                    'file_id': message.video.file_id,
                    'name': message.video.file_name or f'video_{current_time}.mp4',
                    'size': message.video.file_size or 0,
                    'type': 'video',
                    'mime_type': message.video.mime_type or 'video/mp4',
                    'duration': message.video.duration,
                    'width': message.video.width,
                    'height': message.video.height,
                    'date': message.video.date,
                    'thumb': message.video.thumbs[0] if message.video.thumbs else None
                }
            elif message.audio:
                file_info = {
                    'file_id': message.audio.file_id,
                    'name': message.audio.file_name or f'audio_{current_time}.mp3',
                    'size': message.audio.file_size or 0,
                    'type': 'audio',
                    'mime_type': message.audio.mime_type or 'audio/mpeg',
                    'duration': message.audio.duration,
                    'performer': message.audio.performer,
                    'title': message.audio.title,
                    'date': message.audio.date,
                    'thumb': message.audio.thumbs[0] if message.audio.thumbs else None
                }
            elif message.voice:
                file_info = {
                    'file_id': message.voice.file_id,
                    'name': f'voice_{current_time}.ogg',
                    'size': message.voice.file_size or 0,
                    'type': 'voice',
                    'mime_type': 'audio/ogg',
                    'duration': message.voice.duration,
                    'date': message.voice.date
                }
            elif message.video_note:
                file_info = {
                    'file_id': message.video_note.file_id,
                    'name': f'video_note_{current_time}.mp4',
                    'size': message.video_note.file_size or 0,
                    'type': 'video_note',
                    'mime_type': 'video/mp4',
                    'duration': message.video_note.duration,
                    'length': message.video_note.length,
                    'date': message.video_note.date,
                    'thumb': message.video_note.thumbs[0] if message.video_note.thumbs else None
                }
            elif message.animation:
                file_info = {
                    'file_id': message.animation.file_id,
                    'name': message.animation.file_name or f'animation_{current_time}.gif',
                    'size': message.animation.file_size or 0,
                    'type': 'animation',
                    'mime_type': message.animation.mime_type or 'image/gif',
                    'duration': message.animation.duration,
                    'width': message.animation.width,
                    'height': message.animation.height,
                    'date': message.animation.date,
                    'thumb': message.animation.thumbs[0] if message.animation.thumbs else None
                }
            elif message.sticker:
                file_info = {
                    'file_id': message.sticker.file_id,
                    'name': f'sticker_{current_time}.webp',
                    'size': message.sticker.file_size or 0,
                    'type': 'sticker',
                    'mime_type': 'image/webp',
                    'width': message.sticker.width,
                    'height': message.sticker.height,
                    'is_animated': message.sticker.is_animated,
                    'is_video': message.sticker.is_video,
                    'emoji': message.sticker.emoji,
                    'date': message.sticker.date,
                    'thumb': message.sticker.thumbs[0] if message.sticker.thumbs else None
                }
            
            # Add premium metadata
            if file_info:
                file_info.update({
                    'premium_supported': True,
                    'upload_ready': True,
                    'estimated_upload_time': self._estimate_upload_time(file_info['size']),
                    'size_formatted': self.format_file_size(file_info['size']),
                    'type_emoji': self.get_file_type_emoji(file_info['type'])
                })
            
            return file_info
            
        except Exception as e:
            logger.error(f"❌ Error extracting file info: {e}")
            return None
    
    def _estimate_upload_time(self, file_size: int) -> int:
        """Estimate upload time in seconds"""
        # Assume average upload speed of 2MB/s
        if file_size == 0:
            return 0
        
        avg_speed = 2 * 1024 * 1024  # 2MB/s
        return max(1, int(file_size / avg_speed))
    
    async def download_telegram_file(self, app: Client, file_id: str, progress_callback: Optional[Callable] = None) -> str:
        """Premium Telegram file download with progress tracking"""
        try:
            # Create unique temporary file
            timestamp = int(time.time())
            temp_file = tempfile.mktemp(
                suffix=f"_{timestamp}",
                dir=self.config.TEMP_DIR
            )
            
            # Progress tracking
            downloaded_bytes = 0
            start_time = time.time()
            
            async def progress_hook(current: int, total: int):
                nonlocal downloaded_bytes
                downloaded_bytes = current
                
                if progress_callback:
                    elapsed = time.time() - start_time
                    speed = current / elapsed if elapsed > 0 else 0
                    progress = int((current / total) * 100) if total > 0 else 0
                    eta = (total - current) / speed if speed > 0 else 0
                    
                    await progress_callback({
                        'progress': progress,
                        'downloaded': current,
                        'total': total,
                        'speed': speed,
                        'eta': eta,
                        'status': 'downloading_telegram'
                    })
            
            # Download using Pyrogram (supports up to 4GB)
            await app.download_media(
                file_id, 
                file_name=temp_file,
                progress=progress_hook
            )
            
            # Verify download
            if not os.path.exists(temp_file):
                raise Exception("File download failed - file not found")
                
            file_size = os.path.getsize(temp_file)
            if file_size == 0:
                os.remove(temp_file)
                raise Exception("Downloaded file is empty")
            
            logger.info(f"✅ Downloaded {self.format_file_size(file_size)} from Telegram")
            return temp_file
            
        except Exception as e:
            logger.error(f"❌ Telegram download error: {e}")
            # Cleanup on error
            if 'temp_file' in locals() and os.path.exists(temp_file):
                os.remove(temp_file)
            raise
    
    # ================================
    # PREMIUM GOFILE INTEGRATION
    # ================================
    
    async def get_gofile_server(self) -> Optional[str]:
        """Get optimal GoFile server"""
        try:
            if not self.gofile_session:
                await self.initialize()
            
            response = await self.gofile_session.get(f"{self.config.GOFILE_API_BASE}/getServer")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    server = data.get('data', {}).get('server')
                    logger.debug(f"📡 Got GoFile server: {server}")
                    return server
            
            # Fallback to default
            logger.warning("⚠️ Using fallback GoFile server")
            return "store1"
            
        except Exception as e:
            logger.error(f"❌ Failed to get GoFile server: {e}")
            return "store1"  # Fallback
    
    async def upload_to_gofile(
        self,
        file_path: str,
        file_name: str,
        user_id: int,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Premium GoFile upload with advanced features"""
        
        upload_start_time = time.time()
        
        try:
            # Verify file
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}
                
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return {'success': False, 'error': 'File is empty'}
            
            if file_size > self.config.MAX_FILE_SIZE:
                return {
                    'success': False, 
                    'error': f'File too large: {self.format_file_size(file_size)} > {self.format_file_size(self.config.MAX_FILE_SIZE)}'
                }
            
            if not self.gofile_session:
                await self.initialize()
            
            # Get user's GoFile account info
            user = await self.db.get_user(user_id)
            gofile_token = None
            if user and user.get('gofile_account', {}).get('token'):
                gofile_token = user['gofile_account']['token']
            
            # Get optimal server
            server = await self.get_gofile_server()
            upload_url = f"https://{server}.gofile.io/uploadFile"
            
            # Prepare headers
            headers = {
                'User-Agent': self.config.get_random_user_agent(),
                'Accept': 'application/json',
            }
            
            if gofile_token:
                headers['Authorization'] = f'Bearer {gofile_token}'
            
            # Progress tracking setup
            uploaded_bytes = 0
            start_time = time.time()
            
            class ProgressFile:
                """File wrapper for progress tracking"""
                def __init__(self, file_obj, callback):
                    self.file_obj = file_obj
                    self.callback = callback
                    self.total_size = file_size
                    
                async def read(self, size=-1):
                    data = self.file_obj.read(size)
                    if data:
                        nonlocal uploaded_bytes
                        uploaded_bytes += len(data)
                        
                        if self.callback:
                            elapsed = time.time() - start_time
                            speed = uploaded_bytes / elapsed if elapsed > 0 else 0
                            progress = int((uploaded_bytes / self.total_size) * 100)
                            eta = (self.total_size - uploaded_bytes) / speed if speed > 0 else 0
                            
                            await self.callback({
                                'progress': progress,
                                'uploaded': uploaded_bytes,
                                'total': self.total_size,
                                'speed': speed,
                                'eta': eta,
                                'status': 'uploading_gofile',
                                'filename': file_name
                            })
                    
                    return data
            
            # Upload file
            try:
                async with aiofiles.open(file_path, 'rb') as f:
                    file_content = await f.read()
                    
                    # Create multipart data
                    files = {
                        'file': (file_name, file_content, 'application/octet-stream')
                    }
                    
                    # Additional form data
                    data = {}
                    if gofile_token:
                        data['token'] = gofile_token
                    
                    # Make upload request with retry
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            # Simulate progress during upload
                            if progress_callback:
                                for i in range(0, 101, 10):
                                    elapsed = time.time() - start_time
                                    speed = (i * file_size / 100) / elapsed if elapsed > 0 else 0
                                    
                                    await progress_callback({
                                        'progress': i,
                                        'uploaded': int(i * file_size / 100),
                                        'total': file_size,
                                        'speed': speed,
                                        'eta': (file_size - (i * file_size / 100)) / speed if speed > 0 else 0,
                                        'status': 'uploading_gofile',
                                        'filename': file_name
                                    })
                                    
                                    if i < 100:  # Don't sleep after 100%
                                        await asyncio.sleep(0.1)
                            
                            response = await self.gofile_session.post(
                                upload_url,
                                files=files,
                                data=data,
                                headers=headers
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                
                                if result.get('status') == 'ok':
                                    data = result.get('data', {})
                                    
                                    processing_time = time.time() - upload_start_time
                                    
                                    upload_result = {
                                        'success': True,
                                        'file_id': data.get('code', ''),
                                        'download_url': data.get('downloadPage', ''),
                                        'direct_link': data.get('directLink', ''),
                                        'parent_folder': data.get('parentFolder', ''),
                                        'file_name': data.get('fileName', file_name),
                                        'file_size': file_size,
                                        'upload_time': round(processing_time, 2),
                                        'server': server,
                                        'premium_upload': True,
                                        'gofile_account_linked': bool(gofile_token)
                                    }
                                    
                                    logger.info(f"✅ GoFile upload successful: {upload_result['download_url']}")
                                    return upload_result
                                    
                                else:
                                    error_msg = result.get('message', 'Unknown GoFile error')
                                    if attempt < max_retries - 1:
                                        logger.warning(f"⚠️ GoFile upload attempt {attempt + 1} failed: {error_msg}")
                                        await asyncio.sleep(2 * (attempt + 1))  # Exponential backoff
                                        continue
                                    
                                    return {'success': False, 'error': error_msg}
                            else:
                                error_msg = f'HTTP {response.status_code}: {response.reason_phrase}'
                                if attempt < max_retries - 1:
                                    logger.warning(f"⚠️ GoFile HTTP error attempt {attempt + 1}: {error_msg}")
                                    await asyncio.sleep(2 * (attempt + 1))
                                    continue
                                
                                return {'success': False, 'error': error_msg}
                                
                        except Exception as e:
                            if attempt < max_retries - 1:
                                logger.warning(f"⚠️ GoFile upload attempt {attempt + 1} exception: {e}")
                                await asyncio.sleep(2 * (attempt + 1))
                                continue
                            raise e
                    
                    return {'success': False, 'error': 'All retry attempts failed'}
                    
            except asyncio.TimeoutError:
                return {
                    'success': False,
                    'error': f'Upload timeout after {self.config.UPLOAD_TIMEOUT}s - file may be too large'
                }
                
        except Exception as e:
            processing_time = time.time() - upload_start_time
            logger.error(f"❌ GoFile upload error after {processing_time:.2f}s: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'upload_time': round(processing_time, 2)
            }
    
    async def verify_gofile_token(self, token: str) -> Dict[str, Any]:
        """Verify GoFile API token with premium features"""
        try:
            if not self.gofile_session:
                await self.initialize()
            
            headers = {
                'Authorization': f'Bearer {token}',
                'User-Agent': self.config.get_random_user_agent(),
                'Accept': 'application/json'
            }
            
            response = await self.gofile_session.get(
                f"{self.config.GOFILE_API_BASE}/getAccountDetails",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'ok':
                    data = result.get('data', {})
                    
                    return {
                        'valid': True,
                        'account_id': data.get('id', ''),
                        'email': data.get('email', ''),
                        'tier': data.get('tier', 'free'),
                        'total_size': data.get('totalSize', 0),
                        'total_download_count': data.get('totalDownloadCount', 0),
                        'total_files_count': data.get('totalFilesCount', 0),
                        'subscription': data.get('subscription', {}),
                        'token': token,
                        'premium_features': data.get('tier', 'free') != 'free'
                    }
            
            return {'valid': False, 'error': f'HTTP {response.status_code}: Invalid token or API error'}
            
        except Exception as e:
            logger.error(f"❌ Error verifying GoFile token: {e}")
            return {'valid': False, 'error': str(e)}
    
    # ================================
    # UTILITY FUNCTIONS (PREMIUM!)
    # ================================
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
            
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
            
        return f"{size:.1f} {size_names[i]}"
    
    def create_progress_bar(self, progress: int, length: int = 12, filled_char: str = '█', empty_char: str = '░') -> str:
        """Create premium visual progress bar"""
        if progress < 0:
            progress = 0
        elif progress > 100:
            progress = 100
            
        filled = int(length * progress / 100)
        bar = filled_char * filled + empty_char * (length - filled)
        return f"{bar} {progress}%"
    
    def get_file_type_emoji(self, file_type: str) -> str:
        """Get premium emoji for file type"""
        emoji_map = {
            'document': '📄',
            'photo': '🖼️', 
            'video': '🎥',
            'audio': '🎵',
            'voice': '🔊',
            'video_note': '📹',
            'animation': '🎞️',
            'sticker': '🎭',
            'download': '📥',
            'upload': '📤'
        }
        return emoji_map.get(file_type, '📁')
    
    def format_duration(self, seconds: int) -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs:02d}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes:02d}m"
    
    def get_platform_from_url(self, url: str) -> str:
        """Get platform name from URL with premium detection"""
        return self.config.get_platform_name(url)
    
    def sanitize_filename(self, filename: str) -> str:
        """Premium filename sanitization"""
        import re
        
        # Remove or replace unsafe characters
        filename = re.sub(r'[<>:"/\\|?*\0]', '_', filename)
        
        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        
        # Remove leading/trailing whitespace and dots
        filename = filename.strip(' .')
        
        # Handle special cases
        if filename.lower() in ['con', 'prn', 'aux', 'nul'] or filename.lower().startswith(('com', 'lpt')):
            filename = f"file_{filename}"
        
        # Limit length (leave room for extension)
        if len(filename) > 240:
            name, ext = os.path.splitext(filename)
            filename = name[:240 - len(ext)] + ext
        
        # Ensure filename is not empty
        if not filename:
            filename = f"file_{int(time.time())}"
            
        return filename
    
    def get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename with premium detection"""
        import mimetypes
        
        # Initialize mimetypes if needed
        if not mimetypes.inited:
            mimetypes.init()
        
        mime_type, _ = mimetypes.guess_type(filename)
        
        if not mime_type:
            # Fallback based on extension
            ext = os.path.splitext(filename)[1].lower()
            
            mime_map = {
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo', 
                '.mkv': 'video/x-matroska',
                '.webm': 'video/webm',
                '.mov': 'video/quicktime',
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.flac': 'audio/flac',
                '.ogg': 'audio/ogg',
                '.m4a': 'audio/mp4',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.pdf': 'application/pdf',
                '.zip': 'application/zip',
                '.rar': 'application/vnd.rar',
                '.7z': 'application/x-7z-compressed',
                '.txt': 'text/plain',
                '.json': 'application/json'
            }
            
            mime_type = mime_map.get(ext, 'application/octet-stream')
        
        return mime_type
    
    def is_supported_file_type(self, filename: str) -> bool:
        """Check if file type is supported (premium - supports all types!)"""
        # Premium bot supports ALL file types!
        return True
    
    def get_file_category(self, filename: str) -> str:
        """Get file category for premium organization"""
        ext = os.path.splitext(filename)[1].lower()
        
        video_exts = {'.mp4', '.avi', '.mkv', '.webm', '.mov', '.wmv', '.flv', '.m4v'}
        audio_exts = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma'}
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.ico'}
        document_exts = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
        archive_exts = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}
        
        if ext in video_exts:
            return 'video'
        elif ext in audio_exts:
            return 'audio'
        elif ext in image_exts:
            return 'image'
        elif ext in document_exts:
            return 'document'
        elif ext in archive_exts:
            return 'archive'
        else:
            return 'other'
    
    async def cleanup_file(self, file_path: str) -> None:
        """Premium safe file cleanup"""
        try:
            if not file_path or not os.path.exists(file_path):
                return
            
            # Security check - ensure file is in allowed directories
            allowed_dirs = [
                self.config.TEMP_DIR,
                self.config.DOWNLOAD_DIR,
                '/tmp',
                tempfile.gettempdir()
            ]
            
            abs_path = os.path.abspath(file_path)
            
            if any(abs_path.startswith(os.path.abspath(dir)) for dir in allowed_dirs):
                os.remove(abs_path)
                logger.debug(f"🧹 Cleaned up: {abs_path}")
            else:
                logger.warning(f"⚠️ Skipped cleanup of file outside allowed dirs: {abs_path}")
                
        except Exception as e:
            logger.error(f"❌ Cleanup error for {file_path}: {e}")
    
    async def cleanup_temp_files(self) -> None:
        """Premium cleanup of all temporary files"""
        try:
            directories = [
                Path(self.config.TEMP_DIR),
                Path(self.config.DOWNLOAD_DIR)
            ]
            
            current_time = time.time()
            cleanup_count = 0
            
            for directory in directories:
                if not directory.exists():
                    continue
                
                for file_path in directory.iterdir():
                    try:
                        if file_path.is_file():
                            # Remove files older than 2 hours
                            file_age = current_time - file_path.stat().st_mtime
                            if file_age > 7200:  # 2 hours
                                file_path.unlink()
                                cleanup_count += 1
                                logger.debug(f"🧹 Cleaned: {file_path}")
                                
                    except Exception as e:
                        logger.warning(f"⚠️ Cleanup failed for {file_path}: {e}")
                        continue
            
            if cleanup_count > 0:
                logger.info(f"🧹 Cleaned up {cleanup_count} temporary files")
                
        except Exception as e:
            logger.error(f"❌ Temp cleanup error: {e}")
    
    # ================================
    # PREMIUM STATISTICS & ANALYTICS
    # ================================
    
    def calculate_success_rate(self, successful: int, total: int) -> float:
        """Calculate success rate percentage"""
        if total == 0:
            return 100.0
        return round((successful / total) * 100, 2)
    
    def format_speed(self, bytes_per_second: float) -> str:
        """Format speed in human readable format"""
        return f"{self.format_file_size(int(bytes_per_second))}/s"
    
    def calculate_eta(self, remaining_bytes: int, speed: float) -> int:
        """Calculate estimated time remaining"""
        if speed <= 0:
            return 0
        return int(remaining_bytes / speed)
    
    def create_file_hash(self, file_path: str) -> Optional[str]:
        """Create SHA-256 hash of file for deduplication"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"❌ Error creating file hash: {e}")
            return None
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information for premium monitoring"""
        try:
            import psutil
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'network_sent': psutil.net_io_counters().bytes_sent,
                'network_recv': psutil.net_io_counters().bytes_recv,
                'uptime': time.time() - psutil.boot_time(),
                'premium_features': True,
                'status': 'optimal'
            }
        except Exception as e:
            logger.error(f"❌ Error getting system info: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def format_timestamp(self, timestamp: datetime = None) -> str:
        """Format timestamp for premium display"""
        if not timestamp:
            timestamp = datetime.utcnow()
        
        return timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    def truncate_text(self, text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text with premium ellipsis"""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)].rstrip() + suffix
    
    def format_number(self, number: int) -> str:
        """Format large numbers with premium suffixes"""
        if number < 1000:
            return str(number)
        elif number < 1000000:
            return f"{number/1000:.1f}K"
        elif number < 1000000000:
            return f"{number/1000000:.1f}M"
        else:
            return f"{number/1000000000:.1f}B"
    
    async def create_premium_report(self, data: Dict[str, Any]) -> str:
        """Create premium formatted report"""
        try:
            report = "📊 **Premium Report**\n\n"
            
            for section, content in data.items():
                report += f"**{section.title()}:**\n"
                
                if isinstance(content, dict):
                    for key, value in content.items():
                        if isinstance(value, (int, float)):
                            if key.endswith('_bytes'):
                                value = self.format_file_size(value)
                            elif key.endswith('_count'):
                                value = self.format_number(value)
                        
                        report += f"• {key.replace('_', ' ').title()}: {value}\n"
                else:
                    report += f"• {content}\n"
                
                report += "\n"
            
            report += f"📅 Generated: {self.format_timestamp()}\n"
            report += "✨ Premium features enabled"
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error creating premium report: {e}")
            return "❌ Error generating report"


# Global utilities instance
utils = PremiumUtilities()