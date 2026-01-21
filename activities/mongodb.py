"""
MongoDB connection module for CRC Error workflow.
Provides connection to MongoDB for storing historical data and calculating deltas.
"""
from datetime import datetime
from typing import Optional

import pytz
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from .logger import get_logger
from props import MONGO_URI, MONGO_DB, TZ

logger = get_logger("mongodb")

# Default timezone: Asia/Riyadh (Saudi Arabia)
DEFAULT_TIMEZONE = "Asia/Riyadh"


def get_timezone() -> pytz.timezone:
    """
    Get timezone from props (loaded from TZ env var) or use default (Asia/Riyadh).

    Returns:
        pytz timezone object
    """
    tz_name = TZ if TZ else DEFAULT_TIMEZONE
    try:
        tz = pytz.timezone(tz_name)
        logger.debug(f"Using timezone: {tz_name}")
        return tz
    except pytz.exceptions.UnknownTimeZoneError:
        logger.warning(f"Unknown timezone '{tz_name}', falling back to {DEFAULT_TIMEZONE}")
        return pytz.timezone(DEFAULT_TIMEZONE)


def get_current_time() -> datetime:
    """
    Get current time in configured timezone.

    Returns:
        datetime object with timezone info
    """
    tz = get_timezone()
    return datetime.now(tz)


class MongoDBClient:
    """MongoDB client wrapper for CRC Error workflow."""

    _instance: Optional["MongoDBClient"] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> Database:
        """
        Connect to MongoDB using configuration from props.

        Returns:
            MongoDB database instance
        """
        if self._db is not None:
            return self._db

        if not MONGO_URI:
            logger.error("MONGO_URI is not configured")
            raise ValueError("MONGO_URI is required")

        if not MONGO_DB:
            logger.error("MONGO_DB is not configured")
            raise ValueError("MONGO_DB is required")

        logger.info(f"Connecting to MongoDB database: {MONGO_DB}")
        logger.debug(f"MongoDB URI: {MONGO_URI[:20]}...")  # Log only first 20 chars for security

        try:
            self._client = MongoClient(MONGO_URI)
            self._db = self._client[MONGO_DB]

            # Test connection
            self._client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")

            return self._db
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a collection from the database.

        Args:
            collection_name: Name of the collection

        Returns:
            MongoDB collection instance
        """
        db = self.connect()
        return db[collection_name]

    def close(self):
        """Close the MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")


# Singleton instance
mongodb_client = MongoDBClient()


def get_history_collection() -> Collection:
    """
    Get the CRC history collection.

    Returns:
        MongoDB collection for CRC history
    """
    return mongodb_client.get_collection("crc_history")
