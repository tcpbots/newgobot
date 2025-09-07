"""
Database operations - COMPLETE REWRITE with Enhanced Features
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import motor.motor_asyncio
from pymongo import IndexModel, DESCENDING, ASCENDING
from pymongo.errors import DuplicateKeyError
from config import Config

logger = logging.getLogger(__name__)


class Database:
    """Enhanced MongoDB database operations"""
    
    def __init__(self):
        self.config = Config()
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        
        # Collections
        self.users = None
        self.files = None
        self.admin_logs = None
        self.settings = None
        self.temp_data = None
        self.download_history = None
        
    async def initialize(self) -> None:
        """Initialize database connection with enhanced setup"""
        try:
            # Connect to MongoDB
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.config.MONGO_URI,
                serverSelectionTimeoutMS=10000,
                maxPoolSize=50,
                minPoolSize=5
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Get database and collections
            self.db = self.client[self.config.DATABASE_NAME]
            self.users = self.db.users
            self.files = self.db.files
            self.admin_logs = self.db.admin_logs
            self.settings = self.db.settings
            self.temp_data = self.db.temp_data
            self.download_history = self.db.download_history
            
            # Create indexes for performance
            await self._create_indexes()
            
            # Initialize default settings
            await self._initialize_default_settings()
            
            logger.info("✅ Database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    async def _create_indexes(self) -> None:
        """Create optimized database indexes"""
        try:
            # Users collection indexes
            await self.users.create_indexes([
                IndexModel("user_id", unique=True),
                IndexModel("username"),
                IndexModel("is_banned"),
                IndexModel("join_date", background=True),
                IndexModel("last_activity", background=True),
                IndexModel([("is_banned", ASCENDING), ("last_activity", DESCENDING)])
            ])
            
            # Files collection indexes
            await self.files.create_indexes([
                IndexModel("user_id", background=True),
                IndexModel("gofile_id", unique=True),
                IndexModel("upload_date", background=True),
                IndexModel([("user_id", ASCENDING), ("upload_date", DESCENDING)]),
                IndexModel("file_type"),
                IndexModel("file_size")
            ])
            
            # Admin logs indexes
            await self.admin_logs.create_indexes([
                IndexModel("admin_id"),
                IndexModel("timestamp", background=True),
                IndexModel("action")
            ])
            
            # Temp data indexes (with TTL)
            await self.temp_data.create_index("expires_at", expireAfterSeconds=0)
            await self.temp_data.create_index("user_id")
            
            # Download history indexes
            await self.download_history.create_indexes([
                IndexModel("user_id", background=True),
                IndexModel("platform"),
                IndexModel("download_date", background=True),
                IndexModel([("user_id", ASCENDING), ("download_date", DESCENDING)])
            ])
            
            logger.info("✅ Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")
    
    async def _initialize_default_settings(self) -> None:
        """Initialize default bot settings"""
        try:
            default_settings = {
                "_id": "bot_settings",
                "force_subscription": self.config.FORCE_SUB_ENABLED,
                "channel": self.config.FORCE_SUB_CHANNEL,
                "maintenance_mode": False,
                "max_file_size": self.config.MAX_FILE_SIZE,
                "max_download_size": self.config.MAX_DOWNLOAD_SIZE,
                "ytdlp_enabled": self.config.YTDLP_ENABLED,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.settings.update_one(
                {"_id": "bot_settings"},
                {"$setOnInsert": default_settings},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error initializing default settings: {e}")
    
    # User operations
    async def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create or update user"""
        try:
            user_doc = {
                "user_id": user_data["user_id"],
                "username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "language_code": user_data.get("language_code", "en"),
                "join_date": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "is_banned": False,
                "ban_date": None,
                "ban_reason": None,
                "subscription_status": False,
                "gofile_account": {
                    "token": None,
                    "account_id": None,
                    "tier": None,
                    "linked_at": None
                },
                "settings": self.config.DEFAULT_USER_SETTINGS.copy(),
                "usage_stats": {
                    "files_uploaded": 0,
                    "total_size": 0,
                    "urls_downloaded": 0,
                    "last_upload": None,
                    "last_download": None,
                    "avg_file_size": 0,
                    "favorite_platform": None
                },
                "preferences": {
                    "default_quality": "best[height<=720]",
                    "auto_extract_audio": False,
                    "notifications": True,
                    "delete_after_upload": False
                }
            }
            
            # Upsert user (create if not exists, update last_activity if exists)
            result = await self.users.update_one(
                {"user_id": user_data["user_id"]},
                {
                    "$setOnInsert": user_doc,
                    "$set": {
                        "last_activity": datetime.utcnow(),
                        "username": user_data.get("username"),
                        "first_name": user_data.get("first_name"),
                        "last_name": user_data.get("last_name")
                    }
                },
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"✅ New user created: {user_data['user_id']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create/update user: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user = await self.users.find_one({"user_id": user_id})
            return user
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            update_data["last_activity"] = datetime.utcnow()
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False
    
    async def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        try:
            user = await self.users.find_one(
                {"user_id": user_id, "is_banned": True},
                {"_id": 1}
            )
            return user is not None
        except Exception as e:
            logger.error(f"Error checking ban status: {e}")
            return False
    
    async def ban_user(self, user_id: int, admin_id: int, reason: str = None) -> bool:
        """Ban a user"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "is_banned": True,
                        "ban_date": datetime.utcnow(),
                        "ban_reason": reason or "No reason provided",
                        "banned_by": admin_id
                    }
                }
            )
            
            if result.modified_count > 0:
                await self.log_admin_action(admin_id, "ban_user", {
                    "target_user": user_id,
                    "reason": reason
                })
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error banning user {user_id}: {e}")
            return False
    
    async def unban_user(self, user_id: int, admin_id: int) -> bool:
        """Unban a user"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {"is_banned": False},
                    "$unset": {
                        "ban_date": "",
                        "ban_reason": "",
                        "banned_by": ""
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
            logger.error(f"Error unbanning user {user_id}: {e}")
            return False
    
    async def get_all_users(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Get all users with pagination"""
        try:
            cursor = self.users.find().sort("join_date", DESCENDING).skip(skip).limit(limit)
            users = await cursor.to_list(length=limit)
            return users
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    async def get_users_count(self) -> int:
        """Get total users count"""
        try:
            count = await self.users.count_documents({})
            return count
        except Exception as e:
            logger.error(f"Error getting users count: {e}")
            return 0
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get detailed user statistics"""
        try:
            user = await self.users.find_one({"user_id": user_id})
            if not user:
                return {}
            
            # Get file statistics
            files_cursor = self.files.aggregate([
                {"$match": {"user_id": user_id}},
                {
                    "$group": {
                        "_id": None,
                        "total_files": {"$sum": 1},
                        "total_size": {"$sum": "$file_size"},
                        "avg_size": {"$avg": "$file_size"}
                    }
                }
            ])
            
            files_stats = await files_cursor.to_list(1)
            file_info = files_stats[0] if files_stats else {}
            
            # Get download statistics
            downloads_count = await self.download_history.count_documents({"user_id": user_id})
            
            return {
                "user_id": user_id,
                "join_date": user.get("join_date", datetime.utcnow()),
                "last_activity": user.get("last_activity", datetime.utcnow()),
                "files_uploaded": file_info.get("total_files", 0),
                "total_size": file_info.get("total_size", 0),
                "avg_file_size": file_info.get("avg_size", 0),
                "urls_downloaded": downloads_count,
                "is_banned": user.get("is_banned", False),
                "gofile_linked": bool(user.get("gofile_account", {}).get("token"))
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    # File operations
    async def save_file(self, file_data: Dict[str, Any]) -> bool:
        """Save uploaded file information"""
        try:
            file_doc = {
                "user_id": file_data["user_id"],
                "file_name": file_data["file_name"],
                "file_size": file_data["file_size"],
                "file_type": file_data["file_type"],
                "gofile_id": file_data["gofile_id"],
                "gofile_url": file_data["gofile_url"],
                "upload_date": datetime.utcnow(),
                "download_count": 0,
                "is_public": file_data.get("is_public", True),
                "source_url": file_data.get("source_url"),
                "platform": file_data.get("platform"),
                "quality": file_data.get("quality"),
                "duration": file_data.get("duration"),
                "metadata": file_data.get("metadata", {})
            }
            
            await self.files.insert_one(file_doc)
            
            # Update user statistics
            await self.users.update_one(
                {"user_id": file_data["user_id"]},
                {
                    "$inc": {
                        "usage_stats.files_uploaded": 1,
                        "usage_stats.total_size": file_data["file_size"]
                    },
                    "$set": {
                        "usage_stats.last_upload": datetime.utcnow()
                    }
                }
            )
            
            # Update average file size
            user_stats = await self.get_user_stats(file_data["user_id"])
            if user_stats.get("files_uploaded", 0) > 0:
                avg_size = user_stats.get("total_size", 0) / user_stats["files_uploaded"]
                await self.users.update_one(
                    {"user_id": file_data["user_id"]},
                    {"$set": {"usage_stats.avg_file_size": avg_size}}
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return False
    
    async def get_user_files(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's uploaded files"""
        try:
            cursor = self.files.find(
                {"user_id": user_id}
            ).sort("upload_date", DESCENDING).limit(limit)
            
            files = await cursor.to_list(length=limit)
            return files
            
        except Exception as e:
            logger.error(f"Error getting user files: {e}")
            return []
    
    async def get_file_by_gofile_id(self, gofile_id: str) -> Optional[Dict[str, Any]]:
        """Get file by GoFile ID"""
        try:
            file_doc = await self.files.find_one({"gofile_id": gofile_id})
            return file_doc
        except Exception as e:
            logger.error(f"Error getting file by GoFile ID: {e}")
            return None
    
    # Download history
    async def save_download_history(self, download_data: Dict[str, Any]) -> bool:
        """Save download history"""
        try:
            history_doc = {
                "user_id": download_data["user_id"],
                "url": download_data["url"],
                "platform": download_data.get("platform", "Unknown"),
                "title": download_data.get("title"),
                "file_size": download_data.get("file_size"),
                "quality": download_data.get("quality"),
                "success": download_data.get("success", True),
                "error": download_data.get("error"),
                "download_date": datetime.utcnow(),
                "gofile_id": download_data.get("gofile_id"),
                "duration": download_data.get("duration")
            }
            
            await self.download_history.insert_one(history_doc)
            
            # Update user download count
            await self.users.update_one(
                {"user_id": download_data["user_id"]},
                {
                    "$inc": {"usage_stats.urls_downloaded": 1},
                    "$set": {"usage_stats.last_download": datetime.utcnow()}
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving download history: {e}")
            return False
    
    # Temporary data storage
    async def store_temp_data(self, user_id: int, key: str, data: Any, ttl_minutes: int = 60) -> bool:
        """Store temporary data with TTL"""
        try:
            doc = {
                "user_id": user_id,
                "key": key,
                "data": data,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=ttl_minutes)
            }
            
            await self.temp_data.update_one(
                {"user_id": user_id, "key": key},
                {"$set": doc},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing temp data: {e}")
            return False
    
    async def get_temp_data(self, user_id: int, key: str) -> Any:
        """Get temporary data"""
        try:
            doc = await self.temp_data.find_one({
                "user_id": user_id,
                "key": key,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            return doc.get("data") if doc else None
            
        except Exception as e:
            logger.error(f"Error getting temp data: {e}")
            return None
    
    async def delete_temp_data(self, user_id: int, key: str) -> bool:
        """Delete temporary data"""
        try:
            result = await self.temp_data.delete_one({
                "user_id": user_id,
                "key": key
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting temp data: {e}")
            return False
    
    # Admin operations
    async def log_admin_action(self, admin_id: int, action: str, details: Dict[str, Any] = None) -> None:
        """Log admin action"""
        try:
            log_doc = {
                "admin_id": admin_id,
                "action": action,
                "details": details or {},
                "timestamp": datetime.utcnow(),
                "ip_address": details.get("ip_address") if details else None
            }
            
            await self.admin_logs.insert_one(log_doc)
            
        except Exception as e:
            logger.error(f"Error logging admin action: {e}")
    
    async def get_admin_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent admin logs"""
        try:
            cursor = self.admin_logs.find().sort("timestamp", DESCENDING).limit(limit)
            logs = await cursor.to_list(length=limit)
            return logs
        except Exception as e:
            logger.error(f"Error getting admin logs: {e}")
            return []
    
    # Statistics
    async def get_bot_stats(self) -> Dict[str, Any]:
        """Get basic bot statistics"""
        try:
            # Get user stats
            total_users = await self.get_users_count()
            
            # Active users in last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)
            active_users = await self.users.count_documents({
                "last_activity": {"$gte": week_ago}
            })
            
            # File stats
            total_files = await self.files.count_documents({})
            
            # Total storage
            pipeline = [
                {"$group": {"_id": None, "total_size": {"$sum": "$file_size"}}}
            ]
            result = await self.files.aggregate(pipeline).to_list(1)
            total_storage = result[0]["total_size"] if result else 0
            storage_gb = total_storage / (1024**3)
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_files": total_files,
                "total_storage": total_storage,
                "storage_gb": round(storage_gb, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting bot stats: {e}")
            return {}
    
    async def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed bot statistics"""
        try:
            basic_stats = await self.get_bot_stats()
            
            # Monthly active users
            month_ago = datetime.utcnow() - timedelta(days=30)
            monthly_active = await self.users.count_documents({
                "last_activity": {"$gte": month_ago}
            })
            
            # Banned users
            banned_users = await self.users.count_documents({"is_banned": True})
            
            # Files today
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            files_today = await self.files.count_documents({
                "upload_date": {"$gte": today}
            })
            
            # Files this week
            week_ago = datetime.utcnow() - timedelta(days=7)
            files_week = await self.files.count_documents({
                "upload_date": {"$gte": week_ago}
            })
            
            # Download statistics
            total_downloads = await self.download_history.count_documents({})
            successful_downloads = await self.download_history.count_documents({"success": True})
            success_rate = (successful_downloads / total_downloads * 100) if total_downloads > 0 else 0
            
            # Top platforms
            platform_pipeline = [
                {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            platform_result = await self.download_history.aggregate(platform_pipeline).to_list(5)
            top_platforms = [p["_id"] for p in platform_result if p["_id"]]
            
            basic_stats.update({
                "monthly_active": monthly_active,
                "banned_users": banned_users,
                "files_today": files_today,
                "files_week": files_week,
                "total_downloads": total_downloads,
                "success_rate": round(success_rate, 1),
                "top_platforms": top_platforms
            })
            
            return basic_stats
            
        except Exception as e:
            logger.error(f"Error getting detailed stats: {e}")
            return await self.get_bot_stats()  # Fallback to basic stats
    
    # Settings operations
    async def get_bot_settings(self) -> Dict[str, Any]:
        """Get bot settings"""
        try:
            settings = await self.settings.find_one({"_id": "bot_settings"})
            return settings or {}
        except Exception as e:
            logger.error(f"Error getting bot settings: {e}")
            return {}
    
    async def update_bot_settings(self, settings: Dict[str, Any]) -> bool:
        """Update bot settings"""
        try:
            settings["updated_at"] = datetime.utcnow()
            
            result = await self.settings.update_one(
                {"_id": "bot_settings"},
                {"$set": settings},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating bot settings: {e}")
            return False
    
    # User preferences
    async def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Update user settings"""
        try:
            update_dict = {}
            for key, value in settings.items():
                update_dict[f"settings.{key}"] = value
            
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$set": update_dict}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating user settings: {e}")
            return False
    
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings"""
        try:
            user = await self.users.find_one(
                {"user_id": user_id},
                {"settings": 1}
            )
            
            if user and "settings" in user:
                return user["settings"]
            else:
                return self.config.DEFAULT_USER_SETTINGS.copy()
                
        except Exception as e:
            logger.error(f"Error getting user settings: {e}")
            return self.config.DEFAULT_USER_SETTINGS.copy()
    
    # GoFile account operations
    async def link_gofile_account(self, user_id: int, account_data: Dict[str, Any]) -> bool:
        """Link GoFile account to user"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "gofile_account": {
                            "token": account_data["token"],
                            "account_id": account_data["account_id"],
                            "tier": account_data.get("tier", "free"),
                            "email": account_data.get("email"),
                            "linked_at": datetime.utcnow()
                        }
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error linking GoFile account: {e}")
            return False
    
    async def unlink_gofile_account(self, user_id: int) -> bool:
        """Unlink GoFile account from user"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "gofile_account": {
                            "token": None,
                            "account_id": None,
                            "tier": None,
                            "linked_at": None
                        }
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error unlinking GoFile account: {e}")
            return False
    
    # Cleanup operations
    async def cleanup_old_data(self) -> None:
        """Cleanup old data (run periodically)"""
        try:
            # Remove old temp data (should be handled by TTL, but just in case)
            await self.temp_data.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            # Remove old admin logs (keep only last 6 months)
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            await self.admin_logs.delete_many({
                "timestamp": {"$lt": six_months_ago}
            })
            
            # Remove old download history (keep only last 3 months)
            three_months_ago = datetime.utcnow() - timedelta(days=90)
            await self.download_history.delete_many({
                "download_date": {"$lt": three_months_ago}
            })
            
            logger.info("✅ Database cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during database cleanup: {e}")
    
    async def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        try:
            stats = await self.db.command("dbStats")
            
            return {
                "database_name": stats.get("db", "unknown"),
                "collections": stats.get("collections", 0),
                "data_size": stats.get("dataSize", 0),
                "storage_size": stats.get("storageSize", 0),
                "indexes": stats.get("indexes", 0),
                "index_size": stats.get("indexSize", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {}
