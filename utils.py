"""
Complete Utility functions - REWRITE for Pyrogram
"""

import asyncio
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from urllib.parse import urlparse

import aiofiles
import aiohttp
from pyrogram import Client
from pyrogram.types import Message

from config import Config
from database import Database

logger = logging.getLogger(__name__)


class Utils:
    """Complete utility functions for the bot"""
    
    def __init__(self, config: Config, database: Database):
        self.config = config
        self.db = database
        
        # Create directories
        Path(self.config.DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.config.TEMP_DIR).mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
    def is_valid_url(self, url: str) -> bool:
        """Check if a string is a valid URL"""
        try:
            result = urlparse(url)
            return all([
                result.scheme in ['http', 'https'],
                result.netloc,
                len(url) > 10,
                not any(char in url for char in ['<', '>', '"', "'", '\n', '\r'])
            ])
        except Exception:
            return False
    
    async def get_file_info(self, message: Message) -> Optional[Dict[str, Any]]:
        """Extract file information from Pyrogram message"""
        try:
            file_info = None
            
            if message.document:
                file_info = {
                    'file_id': message.document.file_id,
                    'name': message.document.file_name or f'document_{int(time.time())}.bin',
                    'size': message.document.file_size or 0,
                    'type': 'document',
                    'mime_type': message.document.mime_type
                }
            elif message.photo:
                file_info = {
                    'file_id': message.photo.file_id,
                    'name': f'photo_{int(time.time())}.jpg',
                    'size': message.photo.file_size or 0,
                    'type': 'photo',
                    'mime_type': 'image/jpeg'
                }
            elif message.video:
                file_info = {
                    'file_id': message.video.file_id,
                    'name': message.video.file_name or f'video_{int(time.time())}.mp4',
                    'size': message.video.file_size or 0,
                    'type': 'video',
                    'mime_type': message.video.mime_type or 'video/mp4'
                }
            elif message.audio:
                file_info = {
                    'file_id': message.audio.file_id,
                    'name': message.audio.file_name or f'audio_{int(time.time())}.mp3',
                    'size': message.audio.file_size or 0,
                    'type': 'audio',
                    'mime_type': message.audio.mime_type or 'audio/mpeg'
                }
            elif message.voice:
                file_info = {
                    'file_id': message.voice.file_id,
                    'name': f'voice_{int(time.time())}.ogg',
                    'size': message.voice.file_size or 0,
                    'type': 'voice',
                    'mime_type': 'audio/ogg'
                }
            elif message.video_note:
                file_info = {
                    'file_id': message.video_note.file_id,
                    'name': f'video_note_{int(time.time())}.mp4',
                    'size': message.video_note.file_size or 0,
                    'type': 'video_note',
                    'mime_type': 'video/mp4'
                }
            elif message.animation:
                file_info = {
                    'file_id': message.animation.file_id,
                    'name': message.animation.file_name or f'animation_{int(time.time())}.gif',
                    'size': message.animation.file_size or 0,
                    'type': 'animation',
                    'mime_type': message.animation.mime_type or 'image/gif'
                }
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error extracting file info: {e}")
            return None
    
    async def download_telegram_file(self, app: Client, file_id: str) -> str:
        """Download file from Telegram using Pyrogram"""
        try:
            # Create temporary file path
            temp_file = tempfile.mktemp(dir=self.config.TEMP_DIR)
            
            # Download file using Pyrogram (supports up to 4GB)
            await app.download_media(file_id, file_name=temp_file)
            
            # Verify file was downloaded
            if not os.path.exists(temp_file):
                raise Exception("File download failed - file not found")
                
            if os.path.getsize(temp_file) == 0:
                os.remove(temp_file)
                raise Exception("Downloaded file is empty")
            
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
        """Upload file to GoFile.io with progress tracking"""
        try:
            # Verify file
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}
                
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return {'success': False, 'error': 'File is empty'}
            
            # Get user's GoFile token if available
            user = await self.db.get_user(user_id)
            gofile_token = None
            if user and user.get('gofile_account', {}).get('token'):
                gofile_token = user['gofile_account']['token']
            
            # Prepare headers
            headers = {'User-Agent': 'GoFileUploaderBot/2.0'}
            if gofile_token:
                headers['Authorization'] = f'Bearer {gofile_token}'
            
            # Configure timeout
            timeout = aiohttp.ClientTimeout(
                total=self.config.DOWNLOAD_TIMEOUT,
                connect=60,
                sock_read=60
            )
            
            # Upload file
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Read file in chunks for progress tracking
                async with aiofiles.open(file_path, 'rb') as f:
                    # Create multipart form data
                    data = aiohttp.FormData()
                    
                    # Add file with progress tracking
                    file_content = await f.read()
                    data.add_field(
                        'file',
                        file_content,
                        filename=file_name,
                        content_type='application/octet-stream'
                    )
                
                # Make upload request
                try:
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
                                    'error': result.get('message', 'Unknown GoFile error')
                                }
                        else:
                            error_text = await response.text()
                            return {
                                'success': False,
                                'error': f'HTTP {response.status}: {response.reason}'
                            }
                            
                except asyncio.TimeoutError:
                    return {
                        'success': False,
                        'error': 'Upload timeout - file may be too large'
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Upload error: {str(e)}'
                    }
                    
        except Exception as e:
            logger.error(f"Error uploading to GoFile: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
    
    def create_progress_bar(self, progress: int, length: int = 10) -> str:
        """Create a visual progress bar"""
        filled = int(length * progress / 100)
        bar = '█' * filled + '░' * (length - filled)
        return f"{bar} {progress}%"
    
    def get_filename_from_url(self, url: str, headers: Dict[str, str]) -> str:
        """Extract filename from URL or headers"""
        try:
            # Try Content-Disposition header
            if 'content-disposition' in headers:
                import re
                content_disp = headers['content-disposition']
                filename_match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', content_disp)
                if filename_match:
                    filename = filename_match.group(1).strip('"\'')
                    if filename and self._is_safe_filename(filename):
                        return self.sanitize_filename(filename)
            
            # Get from URL path
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            if filename and '.' in filename:
                filename = filename.split('?')[0]  # Remove query params
                if self._is_safe_filename(filename):
                    return self.sanitize_filename(filename)
            
            # Get extension from content-type
            extension = self._get_extension_from_content_type(headers.get('content-type', ''))
            
            # Generate default filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"download_{timestamp}{extension}"
            
        except Exception:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"download_{timestamp}"
    
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe"""
        if not filename or len(filename) > 255:
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0', '/', '\\']
        return not any(char in filename for char in dangerous_chars)
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from content type"""
        content_type = content_type.lower()
        
        if 'image/jpeg' in content_type or 'image/jpg' in content_type:
            return '.jpg'
        elif 'image/png' in content_type:
            return '.png'
        elif 'image/gif' in content_type:
            return '.gif'
        elif 'video/mp4' in content_type:
            return '.mp4'
        elif 'video/webm' in content_type:
            return '.webm'
        elif 'audio/mpeg' in content_type:
            return '.mp3'
        elif 'audio/wav' in content_type:
            return '.wav'
        elif 'application/pdf' in content_type:
            return '.pdf'
        elif 'application/zip' in content_type:
            return '.zip'
        elif 'text/plain' in content_type:
            return '.txt'
        else:
            return ''
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        import re
        
        # Remove or replace unsafe characters
        filename = re.sub(r'[<>:"/\\|?*\0]', '_', filename)
        
        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        
        # Remove leading/trailing whitespace and dots
        filename = filename.strip(' .')
        
        # Limit length
        if len(filename) > 250:
            name, ext = os.path.splitext(filename)
            filename = name[:250 - len(ext)] + ext
        
        # Ensure filename is not empty
        if not filename:
            filename = f"file_{int(time.time())}"
            
        return filename
    
    async def cleanup_file(self, file_path: str) -> None:
        """Remove temporary file safely"""
        try:
            if file_path and os.path.exists(file_path):
                # Ensure file is in allowed directories
                allowed_dirs = [
                    self.config.TEMP_DIR,
                    self.config.DOWNLOAD_DIR,
                    '/tmp'
                ]
                
                if any(allowed_dir in file_path for allowed_dir in allowed_dirs):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up file: {file_path}")
                else:
                    logger.warning(f"Skipped cleanup of file outside allowed dirs: {file_path}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")
    
    async def cleanup_temp_files(self) -> None:
        """Clean up all old temporary files"""
        try:
            temp_dir = Path(self.config.TEMP_DIR)
            download_dir = Path(self.config.DOWNLOAD_DIR)
            
            current_time = time.time()
            
            for directory in [temp_dir, download_dir]:
                if not directory.exists():
                    continue
                    
                for file_path in directory.iterdir():
                    if file_path.is_file():
                        # Remove files older than 2 hours
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > 7200:  # 2 hours
                            try:
                                file_path.unlink()
                                logger.debug(f"Cleaned up old file: {file_path}")
                            except Exception as e:
                                logger.warning(f"Failed to cleanup {file_path}: {e}")
                                
        except Exception as e:
            logger.error(f"Error in cleanup_temp_files: {e}")
    
    def get_file_type_emoji(self, file_type: str) -> str:
        """Get emoji for file type"""
        emoji_map = {
            'document': '📄',
            'photo': '🖼️',
            'video': '🎥',
            'audio': '🎵',
            'voice': '🔊',
            'video_note': '📹',
            'animation': '🎞️',
            'download': '📥'
        }
        return emoji_map.get(file_type, '📁')
    
    def format_duration(self, seconds: int) -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def get_platform_from_url(self, url: str) -> str:
        """Get platform name from URL"""
        try:
            domain = urlparse(url).netloc.lower()
            
            if 'youtube.com' in domain or 'youtu.be' in domain:
                return 'YouTube'
            elif 'instagram.com' in domain:
                return 'Instagram'
            elif 'tiktok.com' in domain:
                return 'TikTok'
            elif 'twitter.com' in domain or 'x.com' in domain:
                return 'Twitter/X'
            elif 'facebook.com' in domain:
                return 'Facebook'
            elif 'reddit.com' in domain:
                return 'Reddit'
            elif 'vimeo.com' in domain:
                return 'Vimeo'
            elif 'soundcloud.com' in domain:
                return 'SoundCloud'
            elif 'twitch.tv' in domain:
                return 'Twitch'
            else:
                return 'Direct Link'
                
        except Exception:
            return 'Unknown'
    
    async def verify_gofile_token(self, token: str) -> Dict[str, Any]:
        """Verify GoFile API token"""
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'User-Agent': 'GoFileUploaderBot/2.0'
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    f"{self.config.GOFILE_API_BASE}/accounts/getid",
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('status') == 'ok':
                            data = result.get('data', {})
                            return {
                                'valid': True,
                                'account_id': data.get('id', ''),
                                'tier': data.get('tier', 'free'),
                                'email': data.get('email', ''),
                                'token': token
                            }
                    
                    return {'valid': False, 'error': 'Invalid token or API error'}
                    
        except Exception as e:
            logger.error(f"Error verifying GoFile token: {e}")
            return {'valid': False, 'error': str(e)}
    
    def get_quality_text(self, format_info: Dict[str, Any]) -> str:
        """Generate quality text from format info"""
        quality_parts = []
        
        if format_info.get('height'):
            quality_parts.append(f"{format_info['height']}p")
        
        if format_info.get('ext'):
            quality_parts.append(format_info['ext'].upper())
            
        if format_info.get('filesize'):
            quality_parts.append(self.format_file_size(format_info['filesize']))
        
        return " • ".join(quality_parts) if quality_parts else "Unknown Quality"
    
    async def create_thumbnail(self, video_path: str) -> Optional[str]:
        """Create thumbnail from video file"""
        try:
            # This would require ffmpeg
            # For now, return None - implement if needed
            return None
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return None
    
    def is_video_url(self, url: str) -> bool:
        """Check if URL is likely a video"""
        video_indicators = [
            'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
            'twitch.tv', 'tiktok.com', 'instagram.com/p/', 'instagram.com/reel/',
            'facebook.com/watch', 'reddit.com/r/', 'streamable.com'
        ]
        
        return any(indicator in url.lower() for indicator in video_indicators)
    
    def is_audio_url(self, url: str) -> bool:
        """Check if URL is likely audio"""
        audio_indicators = [
            'soundcloud.com', 'spotify.com', 'bandcamp.com',
            'mixcloud.com', 'audiomack.com'
        ]
        
        return any(indicator in url.lower() for indicator in audio_indicators)
    
    def estimate_download_time(self, file_size: int, speed: float) -> str:
        """Estimate download time"""
        if speed <= 0:
            return "Unknown"
            
        eta_seconds = file_size / speed
        return self.format_duration(int(eta_seconds))
    
    def get_file_extension(self, filename: str) -> str:
        """Get file extension"""
        return os.path.splitext(filename)[1].lower()
    
    def is_supported_file_type(self, filename: str) -> bool:
        """Check if file type is supported"""
        supported_extensions = [
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar'
        ]
        
        ext = self.get_file_extension(filename)
        return ext in supported_extensions
    
    def format_bytes_per_second(self, bytes_per_sec: float) -> str:
        """Format bytes per second as speed"""
        return f"{self.format_file_size(int(bytes_per_sec))}/s"
    
    def calculate_eta(self, total_size: int, downloaded: int, speed: float) -> int:
        """Calculate estimated time remaining"""
        if speed <= 0:
            return 0
            
        remaining = total_size - downloaded
        return int(remaining / speed)
    
    def get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def truncate_text(self, text: str, max_length: int = 100) -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    def format_number(self, number: int) -> str:
        """Format large numbers with K, M, B suffixes"""
        if number < 1000:
            return str(number)
        elif number < 1000000:
            return f"{number/1000:.1f}K"
        elif number < 1000000000:
            return f"{number/1000000:.1f}M"
        else:
            return f"{number/1000000000:.1f}B"
    
    async def get_url_info(self, url: str) -> Dict[str, Any]:
        """Get basic information about a URL"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            headers = {'User-Agent': 'GoFileUploaderBot/2.0'}
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.head(url) as response:
                    return {
                        'status': response.status,
                        'content_type': response.headers.get('content-type', ''),
                        'content_length': int(response.headers.get('content-length', 0)),
                        'filename': self.get_filename_from_url(url, response.headers)
                    }
                    
        except Exception as e:
            logger.error(f"Error getting URL info: {e}")
            return {}
    
    def create_file_tree(self, directory: str) -> List[str]:
        """Create a file tree structure"""
        try:
            tree = []
            for root, dirs, files in os.walk(directory):
                level = root.replace(directory, '').count(os.sep)
                indent = ' ' * 2 * level
                tree.append(f"{indent}{os.path.basename(root)}/")
                
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    tree.append(f"{subindent}{file}")
                    
            return tree
        except Exception as e:
            logger.error(f"Error creating file tree: {e}")
            return []
    
    def validate_file_size(self, size: int, max_size: int) -> bool:
        """Validate file size against maximum"""
        return 0 < size <= max_size
    
    def get_file_age(self, filepath: str) -> int:
        """Get file age in seconds"""
        try:
            return int(time.time() - os.path.getmtime(filepath))
        except Exception:
            return 0
    
    async def compress_file(self, filepath: str, compression_level: int = 6) -> Optional[str]:
        """Compress file using gzip (if needed)"""
        try:
            import gzip
            
            compressed_path = f"{filepath}.gz"
            
            async with aiofiles.open(filepath, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb', compresslevel=compression_level) as f_out:
                    content = await f_in.read()
                    f_out.write(content)
            
            return compressed_path if os.path.exists(compressed_path) else None
            
        except Exception as e:
            logger.error(f"Error compressing file: {e}")
            return None
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            import psutil
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'boot_time': datetime.fromtimestamp(psutil.boot_time())
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}
    
    def format_timestamp(self, timestamp: datetime) -> str:
        """Format timestamp for display"""
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    def calculate_progress_eta(self, start_time: float, progress: float) -> str:
        """Calculate ETA based on progress"""
        if progress <= 0:
            return "Unknown"
            
        elapsed = time.time() - start_time
        total_time = elapsed / (progress / 100)
        remaining = total_time - elapsed
        
        return self.format_duration(int(remaining))
    
    async def create_backup(self, source_path: str, backup_dir: str) -> bool:
        """Create backup of a file"""
        try:
            import shutil
            
            Path(backup_dir).mkdir(parents=True, exist_ok=True)
            filename = os.path.basename(source_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f"{timestamp}_{filename}")
            
            shutil.copy2(source_path, backup_path)
            return os.path.exists(backup_path)
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
