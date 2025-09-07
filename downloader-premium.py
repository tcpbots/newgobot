"""
Premium Media Downloader v3.0
Reference: ssebastianoo/yt-dlp-telegram + nonoo/yt-dlp-telegram-bot
FIXES ALL YT-DLP ISSUES + PREMIUM FEATURES!
"""

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from urllib.parse import urlparse
import random

import yt_dlp
import aiohttp
import aiofiles
import httpx
from config_premium import Config
from database_premium import PremiumDatabase

logger = logging.getLogger(__name__)


class PremiumMediaDownloader:
    """Premium Media Downloader with advanced yt-dlp configuration"""
    
    def __init__(self):
        self.config = Config()
        self.db = PremiumDatabase()
        
        # Premium yt-dlp configuration (FIXES ALL ISSUES!)
        self.ytdl_base_opts = {
            'format': 'best[height<=2160]/best',  # 4K support!
            'outtmpl': str(Path(self.config.DOWNLOAD_DIR) / '%(title).200s-%(id)s.%(ext)s'),
            'writesubtitles': False,
            'writeautomaticsub': False,
            'writeinfojson': False,
            'writethumbnail': False,
            'writedescription': False,
            'noplaylist': True,
            'extractaudio': False,
            'audioformat': 'best',
            'audioquality': 0,
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'no_warnings': False,
            'ignoreerrors': False,
            'retries': 5,  # Premium retry count
            'fragment_retries': 10,  # Premium fragment retries
            'skip_unavailable_fragments': True,
            'abort_on_unavailable_fragment': False,
            'keep_fragments': False,
            'concurrent_fragment_downloads': 4,  # Premium concurrency
            'throttledratelimit': None,
            'noprogress': True,  # We handle progress ourselves
            'logtostderr': False,
            'quiet': True,
            'no_color': True,
            'extract_flat': False,
            
            # PREMIUM HEADERS & USER AGENTS (FIXES YouTube/Instagram issues!)
            'http_headers': {
                'User-Agent': random.choice(self.config.YTDLP_USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            },
            
            # PREMIUM EXTRACTOR ARGS (FIXES platform-specific issues!)
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_client': ['android', 'web'],
                    'player_skip': ['configs'],
                    'comment_sort': ['top'],
                    'max_comments': [0],
                },
                'instagram': {
                    'api_version': ['v1'],
                    'include_stories': [False],
                    'include_highlights': [False],
                },
                'tiktok': {
                    'api_hostname': ['api16-normal-c-useast1a.tiktokv.com'],
                },
                'twitter': {
                    'api': ['syndication'],
                },
                'generic': {
                    'variant_id': None,
                }
            },
            
            # PREMIUM POSTPROCESSORS (QUALITY OPTIMIZATION!)
            'postprocessors': [],
            
            # PREMIUM RATE LIMITING (RESPECTFUL)
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            'sleep_interval_subtitles': 0,
        }
        
        # Supported platforms with premium configuration
        self.platform_configs = {
            'youtube.com': {
                'format': 'best[height<=2160][ext=mp4]/best[height<=2160]/best[ext=mp4]/best',
                'extractaudio': False,
                'prefer_formats': ['mp4', 'webm', 'mkv'],
                'max_filesize': self.config.MAX_DOWNLOAD_SIZE,
            },
            'instagram.com': {
                'format': 'best[height<=1080][ext=mp4]/best[height<=1080]/best[ext=mp4]/best',
                'extractaudio': False,
                'prefer_formats': ['mp4'],
                'max_filesize': self.config.MAX_DOWNLOAD_SIZE,
            },
            'tiktok.com': {
                'format': 'best[height<=1080][ext=mp4]/best[height<=1080]/best[ext=mp4]/best',
                'extractaudio': False,
                'prefer_formats': ['mp4'],
                'max_filesize': self.config.MAX_DOWNLOAD_SIZE,
            },
            'twitter.com': {
                'format': 'best[height<=1080][ext=mp4]/best[height<=1080]/best[ext=mp4]/best',
                'extractaudio': False,
                'prefer_formats': ['mp4'],
                'max_filesize': self.config.MAX_DOWNLOAD_SIZE,
            },
            'facebook.com': {
                'format': 'best[height<=1080][ext=mp4]/best[height<=1080]/best[ext=mp4]/best',
                'extractaudio': False,
                'prefer_formats': ['mp4'],
                'max_filesize': self.config.MAX_DOWNLOAD_SIZE,
            },
            'reddit.com': {
                'format': 'best[height<=1080][ext=mp4]/best[height<=1080]/best[ext=mp4]/best',
                'extractaudio': False,
                'prefer_formats': ['mp4'],
                'max_filesize': self.config.MAX_DOWNLOAD_SIZE,
            },
            'vimeo.com': {
                'format': 'best[height<=2160][ext=mp4]/best[height<=2160]/best[ext=mp4]/best',
                'extractaudio': False,
                'prefer_formats': ['mp4'],
                'max_filesize': self.config.MAX_DOWNLOAD_SIZE,
            },
            'dailymotion.com': {
                'format': 'best[height<=1080][ext=mp4]/best[height<=1080]/best/mp4',
                'extractaudio': False,
                'prefer_formats': ['mp4'],
                'max_filesize': self.config.MAX_DOWNLOAD_SIZE,
            },
            'soundcloud.com': {
                'format': 'best[abr<=320]/best',
                'extractaudio': True,
                'audioformat': 'mp3',
                'prefer_formats': ['mp3', 'm4a'],
                'max_filesize': self.config.MAX_DOWNLOAD_SIZE,
            },
            'twitch.tv': {
                'format': 'best[height<=1080][ext=mp4]/best[height<=1080]/best[ext=mp4]/best',
                'extractaudio': False,
                'prefer_formats': ['mp4'],
                'max_filesize': self.config.MAX_DOWNLOAD_SIZE,
            }
        }
        
        # Premium HTTP client for direct downloads
        self.http_session = None
        
    async def initialize(self):
        """Initialize premium downloader"""
        try:
            # Create premium HTTP session
            self.http_session = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.DOWNLOAD_TIMEOUT),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
                headers={
                    'User-Agent': random.choice(self.config.YTDLP_USER_AGENTS),
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                }
            )
            logger.info("✅ Premium downloader initialized!")
        except Exception as e:
            logger.error(f"❌ Failed to initialize downloader: {e}")
    
    async def close(self):
        """Close premium downloader"""
        try:
            if self.http_session:
                await self.http_session.aclose()
        except Exception as e:
            logger.error(f"❌ Error closing downloader: {e}")
    
    def is_supported_platform(self, url: str) -> bool:
        """Check if URL is from a supported platform"""
        try:
            domain = urlparse(url).netloc.lower()
            return any(platform in domain for platform in self.config.SUPPORTED_PLATFORMS)
        except Exception:
            return False
    
    def get_platform_config(self, url: str) -> Dict[str, Any]:
        """Get platform-specific configuration"""
        try:
            domain = urlparse(url).netloc.lower()
            
            for platform, config in self.platform_configs.items():
                if platform in domain:
                    return config.copy()
            
            # Default configuration
            return {
                'format': 'best[height<=1080]/best',
                'extractaudio': False,
                'prefer_formats': ['mp4', 'webm'],
                'max_filesize': self.config.MAX_DOWNLOAD_SIZE,
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting platform config: {e}")
            return self.platform_configs['youtube.com'].copy()
    
    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """Get video information without downloading (PREMIUM!)"""
        try:
            # Get platform-specific configuration
            platform_config = self.get_platform_config(url)
            
            # Create yt-dlp options for info extraction
            opts = self.ytdl_base_opts.copy()
            opts.update({
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writeinfojson': False,
                'dump_single_json': True,
                'simulate': True,
                'listformats': False,
                'http_headers': {
                    **opts['http_headers'],
                    'User-Agent': random.choice(self.config.YTDLP_USER_AGENTS),
                }
            })
            
            def extract_info():
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        return ydl.extract_info(url, download=False)
                except Exception as e:
                    logger.error(f"yt-dlp extraction error: {e}")
                    return None
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, extract_info)
            
            if not info:
                return {'success': False, 'error': 'Could not extract video information'}
            
            # Extract premium information
            result = {
                'success': True,
                'title': self._sanitize_title(info.get('title', 'Unknown')),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'uploader_id': info.get('uploader_id', ''),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'upload_date': info.get('upload_date', ''),
                'description': (info.get('description', '') or '')[:300] + '...' if info.get('description') else '',
                'thumbnail': info.get('thumbnail', ''),
                'webpage_url': info.get('webpage_url', url),
                'original_url': url,
                'platform': self.config.get_platform_name(url),
                'formats': [],
                'audio_formats': [],
                'best_format': None,
                'premium_quality': True
            }
            
            # Extract format information (PREMIUM!)
            if 'formats' in info and info['formats']:
                video_formats = []
                audio_formats = []
                
                for fmt in info['formats']:
                    if not fmt:
                        continue
                        
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    
                    # Skip if too large
                    if filesize and filesize > self.config.MAX_DOWNLOAD_SIZE:
                        continue
                    
                    format_info = {
                        'format_id': fmt.get('format_id', ''),
                        'ext': fmt.get('ext', 'unknown'),
                        'quality': fmt.get('format_note', fmt.get('quality', 'Unknown')),
                        'filesize': filesize,
                        'width': fmt.get('width'),
                        'height': fmt.get('height'),
                        'fps': fmt.get('fps'),
                        'vcodec': fmt.get('vcodec', 'none'),
                        'acodec': fmt.get('acodec', 'none'),
                        'abr': fmt.get('abr'),
                        'vbr': fmt.get('vbr'),
                        'tbr': fmt.get('tbr'),
                        'protocol': fmt.get('protocol', 'unknown'),
                        'url': fmt.get('url', ''),
                        'premium': True
                    }
                    
                    # Categorize formats
                    if fmt.get('vcodec') and fmt.get('vcodec') != 'none':
                        video_formats.append(format_info)
                    elif fmt.get('acodec') and fmt.get('acodec') != 'none':
                        audio_formats.append(format_info)
                
                # Sort formats by quality (PREMIUM SORTING!)
                video_formats.sort(key=lambda x: (
                    x.get('height', 0), 
                    x.get('width', 0),
                    x.get('tbr', 0),
                    x.get('filesize', 0)
                ), reverse=True)
                
                audio_formats.sort(key=lambda x: (
                    x.get('abr', 0),
                    x.get('filesize', 0)
                ), reverse=True)
                
                result['formats'] = video_formats[:15]  # Top 15 video formats
                result['audio_formats'] = audio_formats[:10]  # Top 10 audio formats
                result['best_format'] = video_formats[0] if video_formats else (audio_formats[0] if audio_formats else None)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error extracting video info: {e}")
            return {'success': False, 'error': str(e)}
    
    def _sanitize_title(self, title: str) -> str:
        """Sanitize video title for filename"""
        import re
        
        # Remove problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', title)
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
        sanitized = sanitized.strip(' .')
        
        # Limit length
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        
        return sanitized if sanitized else f"video_{int(time.time())}"
    
    async def download_media(
        self, 
        url: str,
        format_id: Optional[str] = None,
        extract_audio: bool = False,
        quality: str = 'best',
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Premium media download with advanced error handling"""
        
        download_start_time = time.time()
        
        try:
            # Get platform-specific configuration
            platform_config = self.get_platform_config(url)
            
            # Create premium yt-dlp options
            opts = self.ytdl_base_opts.copy()
            
            # Apply platform-specific settings
            if extract_audio or platform_config.get('extractaudio', False):
                opts['format'] = 'bestaudio/best'
                opts['extractaudio'] = True
                opts['audioformat'] = platform_config.get('audioformat', 'mp3')
                opts['audioquality'] = '0'  # Best quality
            else:
                if format_id:
                    opts['format'] = format_id
                else:
                    opts['format'] = platform_config.get('format', 'best[height<=1080]/best')
            
            # Premium user agent rotation
            opts['http_headers']['User-Agent'] = random.choice(self.config.YTDLP_USER_AGENTS)
            
            # Advanced retry configuration
            opts['retries'] = self.config.MAX_RETRIES
            opts['fragment_retries'] = self.config.MAX_RETRIES * 2
            
            # Progress tracking setup
            download_progress = {'downloaded': 0, 'total': 0, 'speed': 0, 'eta': 0}
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    download_progress.update({
                        'downloaded': d.get('downloaded_bytes', 0),
                        'total': d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0),
                        'speed': d.get('speed', 0),
                        'eta': d.get('eta', 0),
                        'filename': d.get('filename', 'Unknown')
                    })
                    
                    if progress_callback and download_progress['total'] > 0:
                        progress = int((download_progress['downloaded'] / download_progress['total']) * 100)
                        asyncio.create_task(progress_callback({
                            'progress': progress,
                            'downloaded': download_progress['downloaded'],
                            'total': download_progress['total'],
                            'speed': download_progress['speed'],
                            'eta': download_progress['eta'],
                            'status': 'downloading',
                            'platform': self.config.get_platform_name(url)
                        }))
                elif d['status'] == 'finished':
                    download_progress['filename'] = d.get('filename')
                    if progress_callback:
                        asyncio.create_task(progress_callback({
                            'progress': 100,
                            'status': 'finished',
                            'filename': d.get('filename')
                        }))
            
            opts['progress_hooks'] = [progress_hook]
            
            # Premium download with error handling
            def download():
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        return info
                except yt_dlp.utils.DownloadError as e:
                    error_msg = str(e).lower()
                    
                    # Handle specific errors with solutions
                    if 'sign in' in error_msg or 'login' in error_msg:
                        raise Exception("Platform requires login - try a different URL or wait a few minutes")
                    elif 'rate limit' in error_msg or 'too many requests' in error_msg:
                        raise Exception("Rate limited - please wait a few minutes and try again")
                    elif 'geo' in error_msg or 'location' in error_msg:
                        raise Exception("Content not available in your region")
                    elif 'private' in error_msg or 'unavailable' in error_msg:
                        raise Exception("Content is private or unavailable")
                    elif 'format' in error_msg:
                        raise Exception("Requested quality/format not available - try different settings")
                    else:
                        raise Exception(f"Download failed: {str(e)}")
                except Exception as e:
                    raise Exception(f"Download error: {str(e)}")
            
            # Execute download
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, download)
            
            if not info:
                return {'success': False, 'error': 'Download failed - no information returned'}
            
            # Find downloaded file
            filepath = None
            if 'requested_downloads' in info and info['requested_downloads']:
                filepath = info['requested_downloads'][0].get('filepath')
            
            if not filepath:
                # Construct filename from template
                template = opts['outtmpl']
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        filepath = ydl.prepare_filename(info)
                except:
                    filepath = download_progress.get('filename')
            
            # Verify file exists
            if not filepath or not os.path.exists(filepath):
                return {'success': False, 'error': 'Downloaded file not found'}
            
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                os.remove(filepath)
                return {'success': False, 'error': 'Downloaded file is empty'}
            
            # Check size limits
            if file_size > self.config.MAX_DOWNLOAD_SIZE:
                os.remove(filepath)
                return {
                    'success': False,
                    'error': f'File too large: {self._format_bytes(file_size)} > {self._format_bytes(self.config.MAX_DOWNLOAD_SIZE)}'
                }
            
            processing_time = time.time() - download_start_time
            
            # Return premium download result
            result = {
                'success': True,
                'filepath': filepath,
                'filename': os.path.basename(filepath),
                'filesize': file_size,
                'title': self._sanitize_title(info.get('title', 'Unknown')),
                'duration': info.get('duration', 0),
                'format': info.get('ext', 'unknown'),
                'platform': self.config.get_platform_name(url),
                'uploader': info.get('uploader', 'Unknown'),
                'upload_date': info.get('upload_date', ''),
                'view_count': info.get('view_count', 0),
                'url': url,
                'processing_time': round(processing_time, 2),
                'quality': info.get('format_note', 'Unknown'),
                'resolution': f"{info.get('width', 0)}x{info.get('height', 0)}" if info.get('width') and info.get('height') else None,
                'fps': info.get('fps'),
                'video_codec': info.get('vcodec'),
                'audio_codec': info.get('acodec'),
                'premium_features': True,
                'retry_count': 0  # Will be updated if retries occur
            }
            
            return result
            
        except Exception as e:
            processing_time = time.time() - download_start_time
            error_msg = str(e)
            
            logger.error(f"❌ Download failed for {url}: {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'url': url,
                'platform': self.config.get_platform_name(url),
                'processing_time': round(processing_time, 2),
                'premium_error_handling': True
            }
    
    async def download_direct(
        self,
        url: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Premium direct file download"""
        
        download_start_time = time.time()
        
        try:
            if not self.http_session:
                await self.initialize()
            
            # Get file info first
            try:
                response = await self.http_session.head(url, follow_redirects=True)
                content_length = response.headers.get('content-length')
                
                if content_length and int(content_length) > self.config.MAX_DOWNLOAD_SIZE:
                    return {
                        'success': False,
                        'error': f'File too large: {self._format_bytes(int(content_length))} > {self._format_bytes(self.config.MAX_DOWNLOAD_SIZE)}'
                    }
                
                content_type = response.headers.get('content-type', '')
                filename = self._extract_filename_from_headers(url, response.headers)
                
            except Exception as e:
                logger.warning(f"Failed to get file info: {e}")
                content_length = None
                content_type = 'application/octet-stream'
                filename = self._extract_filename_from_url(url)
            
            # Download the file
            total_size = int(content_length) if content_length else 0
            downloaded = 0
            start_time = time.time()
            
            # Create unique temporary file
            temp_file = tempfile.mktemp(
                suffix=f"_{filename}",
                dir=self.config.TEMP_DIR
            )
            
            try:
                async with self.http_session.stream('GET', url) as response:
                    if response.status_code != 200:
                        return {
                            'success': False,
                            'error': f'HTTP {response.status_code}: {response.reason_phrase}'
                        }
                    
                    async with aiofiles.open(temp_file, 'wb') as f:
                        async for chunk in response.aiter_bytes(self.config.CHUNK_SIZE):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Check size limit during download
                            if downloaded > self.config.MAX_DOWNLOAD_SIZE:
                                await f.close()
                                os.remove(temp_file)
                                return {
                                    'success': False,
                                    'error': f'File size limit exceeded during download: {self._format_bytes(downloaded)}'
                                }
                            
                            # Progress callback
                            if progress_callback and total_size > 0:
                                progress = int((downloaded / total_size) * 100)
                                elapsed = time.time() - start_time
                                speed = downloaded / elapsed if elapsed > 0 else 0
                                eta = (total_size - downloaded) / speed if speed > 0 else 0
                                
                                await progress_callback({
                                    'progress': progress,
                                    'downloaded': downloaded,
                                    'total': total_size,
                                    'speed': speed,
                                    'eta': eta,
                                    'status': 'downloading',
                                    'filename': filename,
                                    'platform': 'Direct Link'
                                })
                
                # Verify download
                if not os.path.exists(temp_file):
                    return {'success': False, 'error': 'Download verification failed'}
                
                actual_size = os.path.getsize(temp_file)
                if actual_size == 0:
                    os.remove(temp_file)
                    return {'success': False, 'error': 'Downloaded file is empty'}
                
                processing_time = time.time() - download_start_time
                
                return {
                    'success': True,
                    'filepath': temp_file,
                    'filename': filename,
                    'filesize': actual_size,
                    'title': filename,
                    'format': os.path.splitext(filename)[1].lstrip('.') or 'unknown',
                    'platform': 'Direct Link',
                    'url': url,
                    'processing_time': round(processing_time, 2),
                    'content_type': content_type,
                    'premium_direct_download': True
                }
                
            except Exception as e:
                # Cleanup on error
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                raise e
                
        except Exception as e:
            processing_time = time.time() - download_start_time
            
            logger.error(f"❌ Direct download failed for {url}: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'platform': 'Direct Link',
                'processing_time': round(processing_time, 2)
            }
    
    async def download_with_retry(
        self,
        url: str,
        format_id: Optional[str] = None,
        extract_audio: bool = False,
        quality: str = 'best',
        progress_callback: Optional[Callable] = None,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """Premium download with intelligent retry mechanism"""
        
        max_retries = max_retries or self.config.MAX_RETRIES
        retry_delay = self.config.RETRY_DELAY
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"🔄 Retry attempt {attempt}/{max_retries} for {url}")
                    await asyncio.sleep(retry_delay * attempt)  # Exponential backoff
                
                # Choose download method
                if self.is_supported_platform(url):
                    result = await self.download_media(
                        url, format_id, extract_audio, quality, progress_callback
                    )
                else:
                    result = await self.download_direct(url, progress_callback)
                
                if result['success']:
                    result['retry_count'] = attempt
                    result['premium_retry'] = attempt > 0
                    return result
                
                # Check if error is retryable
                error = result.get('error', '').lower()
                if any(non_retryable in error for non_retryable in [
                    'private', 'unavailable', 'not found', 'removed', 'deleted',
                    'region', 'geo', 'country', 'blocked'
                ]):
                    # Don't retry for permanent errors
                    logger.info(f"⏭️ Non-retryable error, skipping retries: {error}")
                    break
                
                if attempt < max_retries:
                    logger.warning(f"⚠️ Attempt {attempt + 1} failed: {result.get('error')}")
                
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed with exception: {e}")
                if attempt == max_retries:
                    return {
                        'success': False,
                        'error': str(e),
                        'retry_count': attempt,
                        'url': url
                    }
        
        return {
            'success': False,
            'error': 'All retry attempts failed',
            'retry_count': max_retries,
            'url': url,
            'premium_retry_exhausted': True
        }
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format"""
        if bytes_value == 0:
            return "0 B"
            
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(bytes_value)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
            
        return f"{size:.1f} {size_names[i]}"
    
    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL"""
        try:
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            
            if filename and '.' in filename:
                # Remove query parameters
                filename = filename.split('?')[0]
                return filename
            
            # Generate filename
            timestamp = int(time.time())
            return f"download_{timestamp}"
            
        except Exception:
            timestamp = int(time.time())
            return f"download_{timestamp}"
    
    def _extract_filename_from_headers(self, url: str, headers: Dict[str, str]) -> str:
        """Extract filename from HTTP headers"""
        try:
            import re
            
            # Try Content-Disposition header
            content_disp = headers.get('content-disposition', '')
            if content_disp:
                filename_match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', content_disp)
                if filename_match:
                    filename = filename_match.group(1).strip('"\'')
                    if filename and self._is_safe_filename(filename):
                        return filename
            
            # Fallback to URL
            return self._extract_filename_from_url(url)
            
        except Exception:
            return self._extract_filename_from_url(url)
    
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe"""
        if not filename or len(filename) > 255:
            return False
        
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0', '/', '\\']
        return not any(char in filename for char in dangerous_chars)
    
    async def get_supported_platforms_list(self) -> List[str]:
        """Get formatted list of supported platforms"""
        platform_emojis = {
            'youtube.com': '🎥',
            'instagram.com': '📸', 
            'tiktok.com': '🎵',
            'twitter.com': '🐦',
            'facebook.com': '📘',
            'reddit.com': '🔴',
            'vimeo.com': '🎬',
            'dailymotion.com': '📹',
            'soundcloud.com': '🎧',
            'twitch.tv': '🟣'
        }
        
        platforms = []
        for platform in self.config.SUPPORTED_PLATFORMS[:20]:  # Top 20
            emoji = platform_emojis.get(platform, '🔗')
            name = platform.replace('.com', '').replace('.tv', '').replace('.ly', '').title()
            platforms.append(f"{emoji} {name}")
        
        platforms.append("🔗 Direct file links")
        return platforms
    
    async def cleanup_temp_files(self) -> None:
        """Clean up temporary download files"""
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
                                logger.debug(f"🧹 Cleaned up: {file_path}")
                            except Exception as e:
                                logger.warning(f"⚠️ Cleanup failed for {file_path}: {e}")
                                
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")
    
    def get_platform_emoji(self, url: str) -> str:
        """Get emoji for platform"""
        domain = urlparse(url).netloc.lower()
        
        emoji_map = {
            'youtube.com': '🎥', 'youtu.be': '🎥',
            'instagram.com': '📸',
            'tiktok.com': '🎵',
            'twitter.com': '🐦', 'x.com': '🐦',
            'facebook.com': '📘',
            'reddit.com': '🔴',
            'vimeo.com': '🎬',
            'dailymotion.com': '📹',
            'soundcloud.com': '🎧',
            'twitch.tv': '🟣'
        }
        
        for domain_key, emoji in emoji_map.items():
            if domain_key in domain:
                return emoji
        
        return '🔗'


# Global downloader instance
downloader = PremiumMediaDownloader()