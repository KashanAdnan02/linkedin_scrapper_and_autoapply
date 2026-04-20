import os
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from config import Config
import logging

# Setup basic logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

class JobDatabase:
    """
    Handles all interactions with MongoDB Atlas and local CSV backup.
    Provides methods to save, retrieve, and update job application records.
    """

    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.connect()

    def connect(self):
        """Establish connection to MongoDB Atlas."""
        if not Config.MONGO_URI:
            logger.error("MONGO_URI is not set in .env file.")
            raise ValueError("MONGO_URI is required but not found in environment variables.")

        try:
            self.client = MongoClient(
                Config.MONGO_URI,
                serverSelectionTimeoutMS=5000,
                retryWrites=True
            )
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[Config.MONGO_DB_NAME]
            self.collection = self.db["jobs"]
            
            # Create indexes for better performance
            self.collection.create_index("job_id", unique=False)
            self.collection.create_index("status")
            self.collection.create_index("timestamp", expireAfterSeconds=7776000)  # Auto-delete after 90 days (optional)

            logger.info("Successfully connected to MongoDB Atlas.")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while connecting to MongoDB: {e}")
            raise

    def save_job(self, job_data: dict):
        try:
            job_data.setdefault("status", "pending")
            job_data.setdefault("applied_date", None)
            job_data.setdefault("source", "unknown")
            job_data.setdefault("timestamp", datetime.utcnow())
            result = self.collection.update_one(
                {"job_id": job_data.get("job_id")},
                {"$set": job_data},
                upsert=True
            )

            if result.upserted_id:
                logger.info(f"New job saved: {job_data.get('title')} at {job_data.get('company')}")
            else:
                logger.info(f"Job updated: {job_data.get('title')}")
            self._save_to_csv(job_data)

        except Exception as e:
            logger.error(f"Error saving job to database: {e}")
            self._save_to_csv(job_data)

    def _save_to_csv(self, job_data: dict):
        """Append job data to local CSV file as backup."""
        try:
            df = pd.DataFrame([job_data])
            csv_path = Config.CSV_FILE

            if os.path.exists(csv_path):
                df.to_csv(csv_path, mode='a', header=False, index=False)
            else:
                df.to_csv(csv_path, index=False)
                logger.info(f"Created new CSV file at {csv_path}")
        except Exception as e:
            logger.error(f"Failed to save job to CSV: {e}")

    def get_all_jobs(self) -> pd.DataFrame:
        """Retrieve all jobs as a pandas DataFrame."""
        try:
            cursor = self.collection.find({})
            df = pd.DataFrame(list(cursor))
            
            if not df.empty:
                df = df.drop(columns=["_id"], errors="ignore")
            
            return df
        except Exception as e:
            logger.error(f"Error fetching jobs from MongoDB: {e}")
            return pd.DataFrame()
    def get_job_by_id(self, job_id: str) -> dict | None:
        """
        Retrieve a single job by its job_id.
        
        Args:
            job_id (str): The unique job identifier.
            
        Returns:
            dict | None: The job document if found, otherwise None.
        """
        if not job_id:
            logger.warning("get_job_by_id called with empty job_id.")
            return None

        try:
            job = self.collection.find_one(
                {"job_id": job_id},
                {"_id": 0}  # Exclude MongoDB's internal _id field
            )
            
            if job:
                logger.debug(f"Job found with job_id: {job_id}")
                return job
            else:
                logger.debug(f"No job found with job_id: {job_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving job with job_id {job_id}: {e}")
            return None
    def update_status(self, job_id: str, new_status: str, notes: str = None):
        """Update the status of a specific job application."""
        try:
            update_data = {"status": new_status, "last_updated": datetime.utcnow()}
            if notes:
                update_data["notes"] = notes

            result = self.collection.update_one(
                {"job_id": job_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Status updated to '{new_status}' for job_id: {job_id}")
            else:
                logger.warning(f"No job found with job_id: {job_id}")
        except Exception as e:
            logger.error(f"Error updating job status: {e}")

    def get_stats(self):
        """Return basic statistics for the dashboard."""
        try:
            pipeline = [
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            results = list(self.collection.aggregate(pipeline))
            
            stats = {item["_id"]: item["count"] for item in results}
            stats.setdefault("pending", 0)
            stats.setdefault("rejected", 0)
            stats.setdefault("approved", 0)
            stats.setdefault("interview", 0)
            
            return stats
        except Exception as e:
            logger.error(f"Error generating stats: {e}")
            return {}

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")