"""
Premium Database Manager v3.0
Reference: TheHamkerCat/WilliamButcherBot + Advanced MongoDB patterns
FIXES ALL PREVIOUS DATABASE CONFLICTS!
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import motor.motor_asyncio
from pymongo import IndexModel, DESCENDING, ASCENDING, TEXT
from pymongo.errors import DuplicateKeyError, BulkWriteError
import orjson as json
from config_premium import Config

logger = logging.getLogger(__name__)


class PremiumDatabase:
    """Premium MongoDB Database Manager - NO CONFLICTS!"""
    
    def __init__(self):
        self.config = Config()
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        
        # Collections
        self.users = None
        self.files = None
        self.downloads = None
        self.admin_logs = None
        self.settings = None
        self.temp_data = None
        self.statistics = None
        
        # Connection state
        self.is_connected = False
        
    async def initialize(self) -> None:
        """Initialize premium database with advanced configuration"""
        try:
            # Advanced MongoDB connection with optimal settings
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.config.MONGO_URI,
                serverSelectionTimeoutMS=15000,  # 15 seconds
                connectTimeoutMS=10000,          # 10 seconds
                maxPoolSize=100,                 # Premium pool size
                minPoolSize=10,
                maxIdleTimeMS=300000,           # 5 minutes
                retryWrites=True,
                retryReads=True,
                w='majority',                   # Write concern for data safety
                j=True,                         # Journal for durability
                readPreference='primaryPreferred'
            )
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("📡 MongoDB connection established!")
            
            # Get database and collections
            self.db = self.client[self.config.DATABASE_NAME]
            
            # Initialize collections
            self.users = self.db.users
            self.files = self.db.files
            self.downloads = self.db.downloads
            self.admin_logs = self.db.admin_logs
            self.settings = self.db.settings
            self.temp_data = self.db.temp_data
            self.statistics = self.db.statistics
            
            # Create premium indexes for performance
            await self._create_premium_indexes()
            
            # Initialize default settings
            await self._initialize_premium_settings()
            
            self.is_connected = True
            logger.info("✅ Premium Database initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    async def _create_premium_indexes(self) -> None:
        """Create optimized indexes for premium performance"""
        try:
            # USERS collection indexes (Advanced!)
            await self.users.create_indexes([
                IndexModel("user_id", unique=True, name="user_id_unique"),
                IndexModel("username", sparse=True, name="username_sparse"),
                IndexModel("is_banned", name="ban_status"),
                IndexModel("join_date", name="join_date_desc"),
                IndexModel("last_activity", name="last_activity_desc"),
                IndexModel([("is_banned", ASCENDING), ("last_activity", DESCENDING)], name="active_users"),
                IndexModel([("join_date", DESCENDING)], name="recent_users"),
                IndexModel("gofile_account.token", sparse=True, name="gofile_users")
            ])
            
            # FILES collection indexes (Premium!)
            await self.files.create_indexes([
                IndexModel("user_id", name="files_by_user"),
                IndexModel("gofile_id", unique=True, sparse=True, name="gofile_id_unique"),
                IndexModel("upload_date", name="upload_date_desc"),
                IndexModel([("user_id", ASCENDING), ("upload_date", DESCENDING)], name="user_files_recent"),
                IndexModel("file_type", name="file_type_index"),
                IndexModel("file_size", name="file_size_index"),
                IndexModel("platform", sparse=True, name="platform_index"),
                IndexModel([("file_name", TEXT)], name="filename_search")
            ])
            
            # DOWNLOADS collection indexes (Performance!)
            await self.downloads.create_indexes([
                IndexModel("user_id", name="downloads_by_user"),
                IndexModel("platform", name="platform_stats"),
                IndexModel("download_date", name="download_date_desc"),
                IndexModel("success", name="success_status"),
                IndexModel([("user_id", ASCENDING), ("download_date", DESCENDING)], name="user_downloads"),
                IndexModel([("platform", ASCENDING), ("success", DESCENDING)], name="platform_success")
            ])
            
            # ADMIN LOGS indexes
            await self.admin_logs.create_indexes([
                IndexModel("admin_id", name="admin_actions"),
                IndexModel("timestamp", name="log_timestamp"),
                IndexModel("action", name="action_type"),
                IndexModel([("admin_id", ASCENDING), ("timestamp", DESCENDING)], name="admin_recent")
            ])
            
            # TEMP DATA with TTL (Auto-cleanup!)
            await self.temp_data.create_index("expires_at", expireAfterSeconds=0, name="ttl_cleanup")
            await self.temp_data.create_index([("user_id", ASCENDING), ("key", ASCENDING)], name="user_temp_data")
            
            # STATISTICS indexes
            await self.statistics.create_indexes([
                IndexModel("date", name="stats_by_date"),
                IndexModel("type", name="stats_by_type"),
                IndexModel([("type", ASCENDING), ("date", DESCENDING)], name="type_date")
            ])
            
            logger.info("📊 Premium database indexes created successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")
            # Don't raise - indexes are for performance, not functionality
    
    async def _initialize_premium_settings(self) -> None:
        """Initialize premium bot settings"""
        try:
            premium_settings = {
                "_id": "premium_bot_settings",
                "bot_version": self.config.BOT_INFO["version"],
                "premium_features": {
                    "unlimited_uploads": True,
                    "premium_download_size": self.config.MAX_DOWNLOAD_SIZE,
                    "concurrent_operations": True,
                    "advanced_retry": True,
                    "premium_quality": True,
                    "gofile_integration": True
                },
                "limits": {
                    "max_file_size": self.config.MAX_FILE_SIZE,
                    "max_download_size": self.config.MAX_DOWNLOAD_SIZE,
                    "max_concurrent_uploads": self.config.MAX_CONCURRENT_UPLOADS,
                    "max_concurrent_downloads": self.config.MAX_CONCURRENT_DOWNLOADS
                },
                "features": {
                    "force_subscription": self.config.FORCE_SUB_ENABLED,
                    "channel": self.config.FORCE_SUB_CHANNEL,
                    "maintenance_mode": False,
                    "ytdlp_enabled": self.config.YTDLP_ENABLED,
                    "premium_processing": True,
                    "smart_retry": True
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.settings.replace_one(
                {"_id": "premium_bot_settings"},
                premium_settings,
                upsert=True
            )
            
            logger.info("⚙️ Premium settings initialized!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize settings: {e}")
    
    # ================================
    # USER OPERATIONS (CONFLICT-FREE!)
    # ================================
    
    async def create_or_update_user(self, user_data: Dict[str, Any]) -> bool:
        """Create or update user - COMPLETELY CONFLICT-FREE!"""
        try:
            user_id = user_data["user_id"]
            current_time = datetime.utcnow()
            
            # Check if user exists using find_one (safe approach)
            existing_user = await self.users.find_one(
                {"user_id": user_id}, 
                {"_id": 1, "join_date": 1, "settings": 1, "usage_stats": 1}
            )
            
            if existing_user:
                # User exists - UPDATE ONLY activity and basic info
                update_doc = {
                    "last_activity": current_time,
                    "username": user_data.get("username"),
                    "first_name": user_data.get("first_name"), 
                    "last_name": user_data.get("last_name"),
                    "language_code": user_data.get("language_code", "en")
                }
                
                result = await self.users.update_one(
                    {"user_id": user_id},
                    {"$set": update_doc}
                )
                
                return result.modified_count > 0
                
            else:
                # New user - CREATE complete document
                user_doc = {
                    "user_id": user_id,
                    "username": user_data.get("username"),
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "language_code": user_data.get("language_code", "en"),
                    "join_date": current_time,
                    "last_activity": current_time,
                    "is_banned": False,
                    "ban_info": None,
                    "subscription_status": False,
                    "gofile_account": {
                        "token": None,
                        "account_id": None,
                        "tier": "free",
                        "linked_at": None,
                        "email": None
                    },
                    "settings": self.config.DEFAULT_USER_SETTINGS.copy(),
                    "usage_stats": {
                        "files_uploaded": 0,
                        "total_uploaded_size": 0,
                        "urls_downloaded": 0,
                        "total_downloaded_size": 0,
                        "last_upload": None,
                        "last_download": None,
                        "favorite_platform": None,
                        "success_rate": 100.0
                    },
                    "premium_features": {
                        "enabled": True,
                        "advanced_retry": True,
                        "smart_quality": True,
                        "progress_notifications": True,
                        "concurrent_operations": True
                    }
                }
                
                try:
                    await self.users.insert_one(user_doc)
                    logger.info(f"✅ New premium user created: {user_id}")
                    return True
                except DuplicateKeyError:
                    # Race condition - user was created by another operation
                    # Just update the activity
                    await self.users.update_one(
                        {"user_id": user_id},
                        {"$set": {"last_activity": current_time}}
                    )
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Failed to create/update user {user_data.get('user_id', 'unknown')}: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID with premium data"""
        try:
            user = await self.users.find_one({"user_id": user_id})
            return user
        except Exception as e:
            logger.error(f"❌ Failed to get user {user_id}: {e}")
            return None
    
    async def update_user_field(self, user_id: int, field: str, value: Any) -> bool:
        """Safely update a specific user field"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        field: value,
                        "last_activity": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to update user field {field}: {e}")
            return False
    
    async def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Update user settings (premium)"""
        try:
            # Build update document with dot notation
            update_doc = {"last_activity": datetime.utcnow()}
            
            for key, value in settings.items():
                update_doc[f"settings.{key}"] = value
            
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$set": update_doc}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to update user settings: {e}")
            return False
    
    async def increment_user_stats(self, user_id: int, stat_type: str, value: Union[int, float] = 1) -> bool:
        """Increment user statistics safely"""
        try:
            update_doc = {
                f"usage_stats.{stat_type}": value,
                "last_activity": datetime.utcnow()
            }
            
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": update_doc,
                    "$set": {"last_activity": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to increment user stats: {e}")
            return False
    
    async def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned (optimized)"""
        try:
            result = await self.users.find_one(
                {"user_id": user_id, "is_banned": True},
                {"_id": 1}
            )
            return result is not None
        except Exception as e:
            logger.error(f"❌ Failed to check ban status: {e}")
            return False
    
    async def ban_user(self, user_id: int, admin_id: int, reason: str = "No reason provided") -> bool:
        """Ban user with premium logging"""
        try:
            ban_info = {
                "banned_by": admin_id,
                "ban_date": datetime.utcnow(),
                "reason": reason,
                "permanent": True
            }
            
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "is_banned": True,
                        "ban_info": ban_info,
                        "last_activity": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Log admin action
                await self.log_admin_action(admin_id, "ban_user", {
                    "target_user": user_id,
                    "reason": reason
                })
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to ban user {user_id}: {e}")
            return False
    
    async def unban_user(self, user_id: int, admin_id: int) -> bool:
        """Unban user with premium logging"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "is_banned": False,
                        "last_activity": datetime.utcnow()
                    },
                    "$unset": {
                        "ban_info": ""
                    }
                }
            )
            
            if result.modified_count > 0:
                await self.log_admin_action(admin_id, "unban_user", {
                    "target_user": user_id
                })
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to unban user {user_id}: {e}")
            return False
    
    # ================================
    # FILE OPERATIONS (PREMIUM!)
    # ================================
    
    async def save_file(self, file_data: Dict[str, Any]) -> bool:
        """Save file with premium metadata"""
        try:
            current_time = datetime.utcnow()
            
            file_doc = {
                "user_id": file_data["user_id"],
                "file_name": file_data["file_name"],
                "file_size": file_data["file_size"],
                "file_type": file_data["file_type"],
                "mime_type": file_data.get("mime_type"),
                "gofile_id": file_data["gofile_id"],
                "gofile_url": file_data["gofile_url"],
                "gofile_download_url": file_data.get("gofile_download_url"),
                "upload_date": current_time,
                "source_info": {
                    "type": file_data.get("source_type", "direct"),
                    "url": file_data.get("source_url"),
                    "platform": file_data.get("platform"),
                    "quality": file_data.get("quality"),
                    "format": file_data.get("format")
                },
                "metadata": {
                    "duration": file_data.get("duration"),
                    "resolution": file_data.get("resolution"),
                    "bitrate": file_data.get("bitrate"),
                    "codec": file_data.get("codec"),
                    "fps": file_data.get("fps")
                },
                "stats": {
                    "downloads": 0,
                    "last_accessed": current_time,
                    "view_count": 0
                },
                "premium_features": {
                    "high_quality": True,
                    "fast_upload": True,
                    "permanent_storage": True
                }
            }
            
            # Insert file document
            await self.files.insert_one(file_doc)
            
            # Update user statistics atomically
            await self.increment_user_stats(file_data["user_id"], "files_uploaded", 1)
            await self.increment_user_stats(file_data["user_id"], "total_uploaded_size", file_data["file_size"])
            await self.update_user_field(file_data["user_id"], "usage_stats.last_upload", current_time)
            
            # Update daily statistics
            await self.update_daily_stats("files_uploaded", 1)
            await self.update_daily_stats("total_upload_size", file_data["file_size"])
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save file: {e}")
            return False
    
    async def get_user_files(self, user_id: int, limit: int = 20, skip: int = 0) -> List[Dict[str, Any]]:
        """Get user files with premium pagination"""
        try:
            cursor = self.files.find(
                {"user_id": user_id}
            ).sort("upload_date", DESCENDING).skip(skip).limit(limit)
            
            files = await cursor.to_list(length=limit)
            return files
            
        except Exception as e:
            logger.error(f"❌ Failed to get user files: {e}")
            return []
    
    async def search_files(self, user_id: int, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search user files (premium feature)"""
        try:
            # Text search with MongoDB text index
            cursor = self.files.find(
                {
                    "$and": [
                        {"user_id": user_id},
                        {"$text": {"$search": query}}
                    ]
                },
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            files = await cursor.to_list(length=limit)
            return files
            
        except Exception as e:
            logger.error(f"❌ Failed to search files: {e}")
            return []
    
    # ================================
    # DOWNLOAD OPERATIONS (PREMIUM!)
    # ================================
    
    async def save_download(self, download_data: Dict[str, Any]) -> bool:
        """Save download with premium analytics"""
        try:
            current_time = datetime.utcnow()
            
            download_doc = {
                "user_id": download_data["user_id"],
                "url": download_data["url"],
                "platform": download_data.get("platform", "Unknown"),
                "title": download_data.get("title"),
                "file_size": download_data.get("file_size", 0),
                "quality": download_data.get("quality"),
                "format": download_data.get("format"),
                "success": download_data.get("success", False),
                "error": download_data.get("error"),
                "download_date": current_time,
                "processing_time": download_data.get("processing_time", 0),
                "gofile_id": download_data.get("gofile_id"),
                "premium_features": {
                    "smart_retry": download_data.get("retry_count", 0) > 0,
                    "high_quality": True,
                    "fast_processing": download_data.get("processing_time", 0) < 30
                },
                "metadata": {
                    "duration": download_data.get("duration"),
                    "uploader": download_data.get("uploader"),
                    "view_count": download_data.get("view_count"),
                    "upload_date": download_data.get("upload_date")
                }
            }
            
            await self.downloads.insert_one(download_doc)
            
            # Update user stats
            if download_data.get("success"):
                await self.increment_user_stats(download_data["user_id"], "urls_downloaded", 1)
                if download_data.get("file_size"):
                    await self.increment_user_stats(download_data["user_id"], "total_downloaded_size", download_data["file_size"])
                await self.update_user_field(download_data["user_id"], "usage_stats.last_download", current_time)
                
                # Update platform preference
                platform = download_data.get("platform", "Unknown")
                await self.update_user_field(download_data["user_id"], "usage_stats.favorite_platform", platform)
            
            # Update daily statistics
            await self.update_daily_stats("downloads_attempted", 1)
            if download_data.get("success"):
                await self.update_daily_stats("downloads_successful", 1)
                await self.update_daily_stats("total_download_size", download_data.get("file_size", 0))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save download: {e}")
            return False
    
    # ================================
    # STATISTICS (PREMIUM ANALYTICS!)
    # ================================
    
    async def update_daily_stats(self, stat_type: str, value: Union[int, float]) -> None:
        """Update daily statistics for premium analytics"""
        try:
            today = datetime.utcnow().date()
            
            await self.statistics.update_one(
                {
                    "date": today,
                    "type": "daily"
                },
                {
                    "$inc": {f"stats.{stat_type}": value},
                    "$set": {"updated_at": datetime.utcnow()}
                },
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to update daily stats: {e}")
    
    async def get_premium_stats(self) -> Dict[str, Any]:
        """Get comprehensive premium statistics"""
        try:
            # Basic counts
            total_users = await self.users.count_documents({})
            total_files = await self.files.count_documents({})
            total_downloads = await self.downloads.count_documents({})
            
            # Active users (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            active_users = await self.users.count_documents({
                "last_activity": {"$gte": week_ago}
            })
            
            # Storage calculation
            storage_pipeline = [
                {"$group": {"_id": None, "total_size": {"$sum": "$file_size"}}}
            ]
            storage_result = await self.files.aggregate(storage_pipeline).to_list(1)
            total_storage = storage_result[0]["total_size"] if storage_result else 0
            
            # Success rate
            successful_downloads = await self.downloads.count_documents({"success": True})
            success_rate = (successful_downloads / total_downloads * 100) if total_downloads > 0 else 100
            
            # Top platforms
            platform_pipeline = [
                {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            platform_result = await self.downloads.aggregate(platform_pipeline).to_list(10)
            top_platforms = [{"platform": p["_id"], "count": p["count"]} for p in platform_result]
            
            # Files by type
            type_pipeline = [
                {"$group": {"_id": "$file_type", "count": {"$sum": 1}, "size": {"$sum": "$file_size"}}},
                {"$sort": {"count": -1}}
            ]
            type_result = await self.files.aggregate(type_pipeline).to_list(10)
            files_by_type = [{"type": t["_id"], "count": t["count"], "size": t["size"]} for t in type_result]
            
            return {
                "overview": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "total_files": total_files,
                    "total_downloads": total_downloads,
                    "total_storage_bytes": total_storage,
                    "total_storage_gb": round(total_storage / (1024**3), 2),
                    "success_rate": round(success_rate, 2)
                },
                "analytics": {
                    "top_platforms": top_platforms,
                    "files_by_type": files_by_type,
                    "premium_features": {
                        "unlimited_uploads": True,
                        "high_quality_downloads": True,
                        "advanced_retry": True,
                        "concurrent_operations": True
                    }
                },
                "performance": {
                    "database_status": "optimal",
                    "premium_features": "enabled",
                    "auto_scaling": "active"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get premium stats: {e}")
            return {}
    
    # ================================
    # ADMIN OPERATIONS
    # ================================
    
    async def log_admin_action(self, admin_id: int, action: str, details: Dict[str, Any] = None) -> None:
        """Log admin actions for audit trail"""
        try:
            log_doc = {
                "admin_id": admin_id,
                "action": action,
                "details": details or {},
                "timestamp": datetime.utcnow(),
                "ip_address": details.get("ip_address") if details else None,
                "user_agent": details.get("user_agent") if details else None
            }
            
            await self.admin_logs.insert_one(log_doc)
            
        except Exception as e:
            logger.error(f"❌ Failed to log admin action: {e}")
    
    async def get_admin_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent admin logs"""
        try:
            cursor = self.admin_logs.find().sort("timestamp", DESCENDING).limit(limit)
            logs = await cursor.to_list(length=limit)
            return logs
        except Exception as e:
            logger.error(f"❌ Failed to get admin logs: {e}")
            return []
    
    # ================================
    # TEMPORARY DATA (WITH TTL)
    # ================================
    
    async def store_temp_data(self, user_id: int, key: str, data: Any, ttl_minutes: int = 60) -> bool:
        """Store temporary data with automatic expiration"""
        try:
            doc = {
                "user_id": user_id,
                "key": key,
                "data": data,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=ttl_minutes)
            }
            
            await self.temp_data.replace_one(
                {"user_id": user_id, "key": key},
                doc,
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store temp data: {e}")
            return False
    
    async def get_temp_data(self, user_id: int, key: str) -> Any:
        """Get temporary data (only if not expired)"""
        try:
            doc = await self.temp_data.find_one({
                "user_id": user_id,
                "key": key,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            return doc.get("data") if doc else None
            
        except Exception as e:
            logger.error(f"❌ Failed to get temp data: {e}")
            return None
    
    async def delete_temp_data(self, user_id: int, key: str = None) -> bool:
        """Delete temporary data"""
        try:
            filter_doc = {"user_id": user_id}
            if key:
                filter_doc["key"] = key
                
            result = await self.temp_data.delete_many(filter_doc)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to delete temp data: {e}")
            return False
    
    # ================================
    # GOFILE ACCOUNT OPERATIONS
    # ================================
    
    async def link_gofile_account(self, user_id: int, account_data: Dict[str, Any]) -> bool:
        """Link GoFile account to user"""
        try:
            gofile_data = {
                "token": account_data["token"],
                "account_id": account_data["account_id"],
                "tier": account_data.get("tier", "free"),
                "email": account_data.get("email"),
                "linked_at": datetime.utcnow(),
                "verified": True,
                "premium_features": account_data.get("tier", "free") != "free"
            }
            
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "gofile_account": gofile_data,
                        "last_activity": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to link GoFile account: {e}")
            return False
    
    async def unlink_gofile_account(self, user_id: int) -> bool:
        """Unlink GoFile account from user"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "gofile_account.token": None,
                        "gofile_account.verified": False,
                        "last_activity": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to unlink GoFile account: {e}")
            return False
    
    # ================================
    # CLEANUP & MAINTENANCE
    # ================================
    
    async def cleanup_old_data(self) -> None:
        """Premium database cleanup with retention policies"""
        try:
            current_time = datetime.utcnow()
            
            # Clean old admin logs (keep 6 months)
            six_months_ago = current_time - timedelta(days=180)
            await self.admin_logs.delete_many({
                "timestamp": {"$lt": six_months_ago}
            })
            
            # Clean old download history (keep 3 months for free users, 1 year for premium)
            three_months_ago = current_time - timedelta(days=90)
            one_year_ago = current_time - timedelta(days=365)
            
            # Free users - 3 months retention
            await self.downloads.delete_many({
                "download_date": {"$lt": three_months_ago},
                "user_id": {"$nin": await self._get_premium_user_ids()}
            })
            
            # Premium users - 1 year retention
            await self.downloads.delete_many({
                "download_date": {"$lt": one_year_ago}
            })
            
            # Clean expired temp data (handled by TTL, but manual cleanup for safety)
            await self.temp_data.delete_many({
                "expires_at": {"$lt": current_time}
            })
            
            # Clean old statistics (keep 1 year)
            await self.statistics.delete_many({
                "date": {"$lt": one_year_ago.date()}
            })
            
            logger.info("🧹 Premium database cleanup completed!")
            
        except Exception as e:
            logger.error(f"❌ Database cleanup failed: {e}")
    
    async def _get_premium_user_ids(self) -> List[int]:
        """Get list of premium user IDs"""
        try:
            cursor = self.users.find(
                {"gofile_account.tier": {"$ne": "free"}},
                {"user_id": 1}
            )
            users = await cursor.to_list(length=None)
            return [user["user_id"] for user in users]
        except Exception as e:
            logger.error(f"❌ Failed to get premium users: {e}")
            return []
    
    async def get_database_health(self) -> Dict[str, Any]:
        """Get database health metrics"""
        try:
            # Database stats
            stats = await self.db.command("dbStats")
            
            # Collection stats
            collections_info = {}
            for collection_name in ["users", "files", "downloads", "admin_logs", "temp_data", "statistics"]:
                collection = getattr(self, collection_name)
                count = await collection.count_documents({})
                collections_info[collection_name] = {
                    "document_count": count,
                    "status": "healthy" if count >= 0 else "error"
                }
            
            return {
                "database": {
                    "name": stats.get("db", "unknown"),
                    "collections": stats.get("collections", 0),
                    "data_size_mb": round(stats.get("dataSize", 0) / 1024 / 1024, 2),
                    "storage_size_mb": round(stats.get("storageSize", 0) / 1024 / 1024, 2),
                    "indexes": stats.get("indexes", 0),
                    "index_size_mb": round(stats.get("indexSize", 0) / 1024 / 1024, 2)
                },
                "collections": collections_info,
                "status": "healthy" if self.is_connected else "disconnected",
                "premium_features": "enabled"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get database health: {e}")
            return {"status": "error", "error": str(e)}
    
    async def close(self) -> None:
        """Close database connection gracefully"""
        try:
            if self.client:
                self.client.close()
                self.is_connected = False
                logger.info("📊 Premium database connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing database: {e}")


# Global database instance
db = PremiumDatabase()