"""
Database operations and models
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import motor.motor_asyncio
from pymongo import IndexModel
from pymongo.errors import DuplicateKeyError
from config import Config

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database operations"""
    
    def __init__(self):
        self.config = Config()
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        self.users = None
        self.files = None
        self.admin_logs = None
        self.settings = None
        
    async def initialize(self) -> None:
        """Initialize database connection"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.config.MONGO_URI,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Get database and collections
            self.db = self.client[self.config.DATABASE_NAME]
            self.users = self.db.users
            self.files = self.db.files
            self.admin_logs = self.db.admin_logs
            self.settings = self.db.settings
            
            # Create indexes
            await self._create_indexes()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
            
    async def close(self) -> None:
        """Close database connection"""
        if self.client:
            self.client.close()
            
    async def _create_indexes(self) -> None:
        """Create database indexes"""
        try:
            # Users collection indexes
            await self.users.create_indexes([
                IndexModel("user_id", unique=True),
                IndexModel("username"),
                IndexModel("is_banned"),
                IndexModel("join_date")
            ])
            
            # Files collection indexes
            await self.files.create_indexes([
                IndexModel("user_id"),
                IndexModel("upload_date"),
                IndexModel("gofile_id", unique=True)
            ])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            
    # User operations
    async def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create a new user"""
        try:
            user_doc = {
                "user_id": user_data["user_id"],
                "username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "join_date": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "is_banned": False,
                "gofile_account": {
                    "token": None,
                    "account_id": None
                },
                "subscription_status": False,
                "settings": self.config.DEFAULT_USER_SETTINGS.copy(),
                "usage_stats": {
                    "files_uploaded": 0,
                    "total_size": 0,
                    "downloads": 0,
                    "last_upload": None
                }
            }
            
            await self.users.insert_one(user_doc)
            logger.info(f"User {user_data['user_id']} created")
            return True
            
        except DuplicateKeyError:
            logger.info(f"User {user_data['user_id']} already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False
            
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user = await self.users.find_one({"user_id": user_id})
            return user
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
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
            logger.error(f"Failed to update user {user_id}: {e}")
            return False
            
    async def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        try:
            user = await self.users.find_one({"user_id": user_id, "is_banned": True})
            return user is not None
        except Exception as e:
            logger.error(f"Failed to check ban status: {e}")
            return False
            
    async def ban_user(self, user_id: int, admin_id: int, reason: str = None) -> bool:
        """Ban a user"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"is_banned": True, "ban_date": datetime.utcnow()}}
            )
            
            await self.log_admin_action(admin_id, "ban_user", {
                "target_user": user_id,
                "reason": reason
            })
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to ban user {user_id}: {e}")
            return False
            
    async def unban_user(self, user_id: int, admin_id: int) -> bool:
        """Unban a user"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"is_banned": False}, "$unset": {"ban_date": ""}}
            )
            
            await self.log_admin_action(admin_id, "unban_user", {
                "target_user": user_id
            })
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to unban user {user_id}: {e}")
            return False
            
    async def get_all_users(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Get all users with pagination"""
        try:
            cursor = self.users.find().skip(skip).limit(limit)
            users = await cursor.to_list(length=limit)
            return users
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            return []
            
    async def get_users_count(self) -> int:
        """Get total users count"""
        try:
            count = await self.users.count_documents({})
            return count
        except Exception as e:
            logger.error(f"Failed to get users count: {e}")
            return 0
            
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
                "is_public": file_data.get("is_public", True)
            }
            
            await self.files.insert_one(file_doc)
            
            # Update user stats
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
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            return False
            
    async def get_user_files(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's uploaded files"""
        try:
            cursor = self.files.find({"user_id": user_id}).sort("upload_date", -1).limit(limit)
            files = await cursor.to_list(length=limit)
            return files
        except Exception as e:
            logger.error(f"Failed to get user files: {e}")
            return []
            
    # Admin operations
    async def log_admin_action(self, admin_id: int, action: str, details: Dict[str, Any] = None) -> None:
        """Log admin action"""
        try:
            log_doc = {
                "admin_id": admin_id,
                "action": action,
                "details": details or {},
                "timestamp": datetime.utcnow()
            }
            
            await self.admin_logs.insert_one(log_doc)
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
            
    # Statistics
    async def get_bot_stats(self) -> Dict[str, Any]:
        """Get bot statistics"""
        try:
            total_users = await self.get_users_count()
            
            # Get active users (last 7 days)
            since_date = datetime.utcnow() - timedelta(days=7)
            active_users = await self.users.count_documents({
                "last_activity": {"$gte": since_date}
            })
            
            total_files = await self.files.count_documents({})
            
            # Get total storage used
            pipeline = [
                {"$group": {"_id": None, "total_size": {"$sum": "$file_size"}}}
            ]
            result = await self.files.aggregate(pipeline).to_list(1)
            total_storage = result[0]["total_size"] if result else 0
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_files": total_files,
                "total_storage": total_storage,
                "storage_gb": round(total_storage / (1024**3), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get bot stats: {e}")
            return {}
            
    # Settings operations
    async def get_bot_settings(self) -> Dict[str, Any]:
        """Get bot settings"""
        try:
            settings = await self.settings.find_one({"_id": "bot_settings"})
            if not settings:
                # Create default settings
                default_settings = {
                    "_id": "bot_settings",
                    "force_subscription": self.config.FORCE_SUB_ENABLED,
                    "channel": self.config.FORCE_SUB_CHANNEL,
                    "maintenance_mode": False,
                    "created_at": datetime.utcnow()
                }
                await self.settings.insert_one(default_settings)
                return default_settings
            return settings
        except Exception as e:
            logger.error(f"Failed to get bot settings: {e}")
            return {}
            
    async def update_bot_settings(self, settings: Dict[str, Any]) -> bool:
        """Update bot settings"""
        try:
            result = await self.settings.update_one(
                {"_id": "bot_settings"},
                {"$set": settings},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update bot settings: {e}")
            return False
