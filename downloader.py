"""
Complete Media Downloader with yt-dlp support
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from urllib.parse import urlparse

import yt_dlp
import aiofiles
import aiohttp

from config import Config
from utils import Utils

logger = logging.getLogger(__name__)


class MediaDownloader:
    """Advanced media downloader using yt-dlp"""
    
    def __init__(self, config: Config, utils: Utils):
        self.config = config
        self.utils = utils
        
        # yt-dlp configuration
        self.ytdl_opts = {
            'outtmpl': str(Path(self.config.DOWNLOAD_DIR) / '%(title)s.%(ext)s'),
            'format': self.config.YTDLP_VIDEO_FORMAT,
            'noplaylist': True,
            'extractaudio': self.config.YTDLP_EXTRACT_AUDIO,
            'audioformat': self.config.YTDLP_AUDIO_FORMAT,
            'audioquality': '0',  # Best quality
            'embed_subs': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': True,
            'no_warnings': False,
            'quiet': False,
            'no_color': True,
            'extract_flat': False,
            'writethumbnail': False,
            'writeinfojson': False,
            'max_filesize': self.config.MAX_DOWNLOAD_SIZE,
        }
        
        # Supported platforms
        self.supported_platforms = [
            'youtube.com', 'youtu.be', 'youtube-nocookie.com',
            'instagram.com', 'instagr.am',
            'tiktok.com', 'vm.tiktok.com',
            'twitter.com', 'x.com', 't.co',
            'facebook.com', 'fb.watch',
            'reddit.com', 'redd.it', 'v.redd.it',
            'vimeo.com',
            'dailymotion.com', 'dai.ly',
            'soundcloud.com',
            'twitch.tv', 'clips.twitch.tv',
            'streamable.com',
            'imgur.com',
            'pinterest.com', 'pin.it',
            'linkedin.com',
            'tumblr.com'
        ]
        
        # Direct download user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    def is_supported_platform(self, url: str) -> bool:
        """Check if URL is from a supported platform"""
        try:
            domain = urlparse(url).netloc.lower()
            return any(platform in domain for platform in self.supported_platforms)
        except Exception:
            return False
    
    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """Get video information without downloading"""
        try:
            opts = self.ytdl_opts.copy()
            opts.update({
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True,
                'dump_single_json': True
            })
            
            def extract_info():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, extract_info)
            
            if not info:
                return {'success': False, 'error': 'Could not extract video information'}
            
            # Extract relevant information
            result = {
                'success': True,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', ''),
                'description': info.get('description', '')[:200] + '...' if info.get('description') else '',
                'thumbnail': info.get('thumbnail', ''),
                'formats': []
            }
            
            # Extract format information
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('filesize') or fmt.get('filesize_approx'):
                        size = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                        if size <= self.config.MAX_DOWNLOAD_SIZE:
                            format_info = {
                                'format_id': fmt.get('format_id', ''),
                                'ext': fmt.get('ext', 'unknown'),
                                'quality': fmt.get('format_note', fmt.get('quality', 'Unknown')),
                                'filesize': size,
                                'width': fmt.get('width'),
                                'height': fmt.get('height'),
                                'fps': fmt.get('fps'),
                                'vcodec': fmt.get('vcodec'),
                                'acodec': fmt.get('acodec'),
                                'abr': fmt.get('abr'),
                                'vbr': fmt.get('vbr')
                            }
                            result['formats'].append(format_info)
            
            # Sort formats by quality
            result['formats'].sort(key=lambda x: (
                x.get('height', 0), 
                x.get('filesize', 0)
            ), reverse=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting video info: {e}")
            return {'success': False, 'error': str(e)}
    
    async def download_media(
        self, 
        url: str, 
        format_id: Optional[str] = None,
        extract_audio: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Download media using yt-dlp"""
        try:
            # Prepare download options
            opts = self.ytdl_opts.copy()
            
            if format_id:
                opts['format'] = format_id
            elif extract_audio:
                opts['format'] = 'bestaudio/best'
                opts['extractaudio'] = True
                opts['audioformat'] = self.config.YTDLP_AUDIO_FORMAT
            
            # Add progress hook
            downloaded_bytes = {'current': 0, 'total': 0}
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    downloaded_bytes['current'] = d.get('downloaded_bytes', 0)
                    downloaded_bytes['total'] = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                    
                    if progress_callback and downloaded_bytes['total'] > 0:
                        progress = int((downloaded_bytes['current'] / downloaded_bytes['total']) * 100)
                        asyncio.create_task(progress_callback({
                            'progress': progress,
                            'downloaded': downloaded_bytes['current'],
                            'total': downloaded_bytes['total'],
                            'speed': d.get('speed', 0),
                            'eta': d.get('eta', 0),
                            'status': 'downloading'
                        }))
            
            opts['progress_hooks'] = [progress_hook]
            
            # Download
            def download():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=True)
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, download)
            
            if not info:
                return {'success': False, 'error': 'Download failed'}
            
            # Find the downloaded file
            if 'requested_downloads' in info and info['requested_downloads']:
                filepath = info['requested_downloads'][0].get('filepath')
            else:
                # Fallback: construct filename
                filename = yt_dlp.YoutubeDL(opts).prepare_filename(info)
                filepath = filename
            
            if not filepath or not os.path.exists(filepath):
                return {'success': False, 'error': 'Downloaded file not found'}
            
            # Get file information
            file_size = os.path.getsize(filepath)
            filename = os.path.basename(filepath)
            
            return {
                'success': True,
                'filepath': filepath,
                'filename': filename,
                'filesize': file_size,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'format': info.get('ext', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return {'success': False, 'error': str(e)}
    
    async def download_direct(
        self, 
        url: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Download file directly from URL"""
        try:
            # Create session with timeout
            timeout = aiohttp.ClientTimeout(total=self.config.DOWNLOAD_TIMEOUT)
            headers = {'User-Agent': self.user_agents[0]}
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                # First, get file info with HEAD request
                async with session.head(url) as response:
                    if response.status != 200:
                        return {'success': False, 'error': f'HTTP {response.status}'}
                    
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > self.config.MAX_DOWNLOAD_SIZE:
                        return {
                            'success': False, 
                            'error': f'File too large: {self.utils.format_file_size(int(content_length))}'
                        }
                
                # Download the file
                async with session.get(url) as response:
                    if response.status != 200:
                        return {'success': False, 'error': f'HTTP {response.status}'}
                    
                    # Get filename
                    filename = self.utils.get_filename_from_url(url, response.headers)
                    filepath = os.path.join(self.config.DOWNLOAD_DIR, filename)
                    
                    # Ensure unique filename
                    counter = 1
                    original_path = filepath
                    while os.path.exists(filepath):
                        name, ext = os.path.splitext(original_path)
                        filepath = f"{name}_{counter}{ext}"
                        counter += 1
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    start_time = time.time()
                    
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.config.CHUNK_SIZE):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Check size limit
                            if downloaded > self.config.MAX_DOWNLOAD_SIZE:
                                await f.close()
                                os.remove(filepath)
                                return {'success': False, 'error': 'File size limit exceeded during download'}
                            
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
                                    'status': 'downloading'
                                })
                    
                    # Verify download
                    if not os.path.exists(filepath):
                        return {'success': False, 'error': 'Download verification failed'}
                    
                    file_size = os.path.getsize(filepath)
                    if file_size == 0:
                        os.remove(filepath)
                        return {'success': False, 'error': 'Downloaded file is empty'}
                    
                    return {
                        'success': True,
                        'filepath': filepath,
                        'filename': os.path.basename(filepath),
                        'filesize': file_size
                    }
                    
        except asyncio.TimeoutError:
            return {'success': False, 'error': 'Download timeout'}
        except aiohttp.ClientError as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            logger.error(f"Error in direct download: {e}")
            return {'success': False, 'error': str(e)}
    
    async def download_from_url(
        self, 
        url: str,
        format_id: Optional[str] = None,
        extract_audio: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Main download method that chooses appropriate downloader"""
        try:
            # Validate URL
            if not self.utils.is_valid_url(url):
                return {'success': False, 'error': 'Invalid URL'}
            
            # Choose download method
            if self.is_supported_platform(url) and self.config.YTDLP_ENABLED:
                logger.info(f"Using yt-dlp for supported platform: {url}")
                return await self.download_media(url, format_id, extract_audio, progress_callback)
            else:
                logger.info(f"Using direct download for: {url}")
                return await self.download_direct(url, progress_callback)
                
        except Exception as e:
            logger.error(f"Error in download_from_url: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_quality_options(self, url: str) -> Dict[str, Any]:
        """Get available quality options for a URL"""
        try:
            if not self.is_supported_platform(url):
                return {'success': False, 'error': 'Platform not supported for quality selection'}
            
            info = await self.get_video_info(url)
            if not info['success']:
                return info
            
            # Organize formats by type
            video_formats = []
            audio_formats = []
            
            for fmt in info['formats']:
                if fmt.get('vcodec') and fmt['vcodec'] != 'none':
                    # Video format
                    quality_text = f"{fmt['quality']} ({fmt['ext']}"
                    if fmt.get('filesize'):
                        quality_text += f", {self.utils.format_file_size(fmt['filesize'])}"
                    quality_text += ")"
                    
                    video_formats.append({
                        'format_id': fmt['format_id'],
                        'text': quality_text,
                        'filesize': fmt.get('filesize', 0),
                        'quality': fmt.get('height', 0)
                    })
                
                elif fmt.get('acodec') and fmt['acodec'] != 'none':
                    # Audio format
                    quality_text = f"{fmt['quality']} ({fmt['ext']}"
                    if fmt.get('abr'):
                        quality_text += f", {fmt['abr']}kbps"
                    if fmt.get('filesize'):
                        quality_text += f", {self.utils.format_file_size(fmt['filesize'])}"
                    quality_text += ")"
                    
                    audio_formats.append({
                        'format_id': fmt['format_id'],
                        'text': quality_text,
                        'filesize': fmt.get('filesize', 0),
                        'bitrate': fmt.get('abr', 0)
                    })
            
            # Sort formats
            video_formats.sort(key=lambda x: x['quality'], reverse=True)
            audio_formats.sort(key=lambda x: x['bitrate'], reverse=True)
            
            return {
                'success': True,
                'title': info['title'],
                'duration': info['duration'],
                'video_formats': video_formats[:10],  # Limit to 10 options
                'audio_formats': audio_formats[:5],   # Limit to 5 options
                'has_video': len(video_formats) > 0,
                'has_audio': len(audio_formats) > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting quality options: {e}")
            return {'success': False, 'error': str(e)}
    
    def cleanup_downloads(self):
        """Clean up old download files"""
        try:
            download_dir = Path(self.config.DOWNLOAD_DIR)
            if not download_dir.exists():
                return
                
            # Remove files older than 1 hour
            current_time = time.time()
            for file_path in download_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > 3600:  # 1 hour
                        try:
                            file_path.unlink()
                            logger.debug(f"Cleaned up old file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to clean up {file_path}: {e}")
                            
        except Exception as e:
            logger.error(f"Error in cleanup_downloads: {e}")
            
    async def get_supported_platforms_list(self) -> List[str]:
        """Get list of supported platforms"""
        return [
            "🎥 YouTube (youtube.com, youtu.be)",
            "📸 Instagram (instagram.com)",
            "🎵 TikTok (tiktok.com)",
            "🐦 Twitter/X (twitter.com, x.com)",
            "📘 Facebook (facebook.com)",
            "🔴 Reddit (reddit.com)",
            "🎬 Vimeo (vimeo.com)",
            "📹 Dailymotion (dailymotion.com)",
            "🎧 SoundCloud (soundcloud.com)",
            "🟣 Twitch (twitch.tv)",
            "🎯 Streamable (streamable.com)",
            "🖼️ Imgur (imgur.com)",
            "📌 Pinterest (pinterest.com)",
            "💼 LinkedIn (linkedin.com)",
            "📱 Tumblr (tumblr.com)",
            "🔗 Direct file links"
        ]
    
    def get_platform_emoji(self, url: str) -> str:
        """Get emoji for platform"""
        domain = urlparse(url).netloc.lower()
        
        if 'youtube.com' in domain or 'youtu.be' in domain:
            return '🎥'
        elif 'instagram.com' in domain:
            return '📸'
        elif 'tiktok.com' in domain:
            return '🎵'
        elif 'twitter.com' in domain or 'x.com' in domain:
            return '🐦'
        elif 'facebook.com' in domain:
            return '📘'
        elif 'reddit.com' in domain:
            return '🔴'
        elif 'vimeo.com' in domain:
            return '🎬'
        elif 'soundcloud.com' in domain:
            return '🎧'
        elif 'twitch.tv' in domain:
            return '🟣'
        else:
            return '🔗'
    
    async def extract_audio_from_video(self, video_path: str, audio_format: str = 'mp3') -> Optional[str]:
        """Extract audio from video file"""
        try:
            output_path = video_path.rsplit('.', 1)[0] + f'.{audio_format}'
            
            opts = {
                'format': 'bestaudio/best',
                'extractaudio': True,
                'audioformat': audio_format,
                'outtmpl': output_path,
                'quiet': True
            }
            
            def extract():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([video_path])
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, extract)
            
            if os.path.exists(output_path):
                return output_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return None
    
    def is_video_platform(self, url: str) -> bool:
        """Check if platform primarily hosts videos"""
        video_platforms = [
            'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
            'twitch.tv', 'tiktok.com', 'instagram.com/reel/', 'streamable.com'
        ]
        return any(platform in url.lower() for platform in video_platforms)
    
    def is_audio_platform(self, url: str) -> bool:
        """Check if platform primarily hosts audio"""
        audio_platforms = [
            'soundcloud.com', 'spotify.com', 'bandcamp.com', 'mixcloud.com'
        ]
        return any(platform in url.lower() for platform in audio_platforms)
    
    async def get_media_metadata(self, url: str) -> Dict[str, Any]:
        """Get detailed metadata for media"""
        try:
            info = await self.get_video_info(url)
            if not info['success']:
                return {}
                
            metadata = {
                'title': info.get('title', 'Unknown'),
                'uploader': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', ''),
                'description': info.get('description', ''),
                'thumbnail': info.get('thumbnail', ''),
                'platform': self.utils.get_platform_from_url(url),
                'url': url
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting media metadata: {e}")
            return {}
    
    async def download_playlist(self, url: str, max_videos: int = 5) -> List[Dict[str, Any]]:
        """Download playlist (limited number of videos)"""
        try:
            opts = self.ytdl_opts.copy()
            opts.update({
                'extract_flat': True,
                'playlistend': max_videos,
                'quiet': True
            })
            
            def extract_playlist():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            loop = asyncio.get_event_loop()
            playlist_info = await loop.run_in_executor(None, extract_playlist)
            
            if not playlist_info or 'entries' not in playlist_info:
                return []
            
            results = []
            for entry in playlist_info['entries'][:max_videos]:
                if entry:
                    video_url = entry.get('url') or entry.get('webpage_url')
                    if video_url:
                        results.append({
                            'title': entry.get('title', 'Unknown'),
                            'url': video_url,
                            'duration': entry.get('duration', 0)
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing playlist: {e}")
            return []
    
    def format_duration(self, seconds: int) -> str:
        """Format duration in human readable format"""
        if not seconds:
            return "Unknown"
            
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
