from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.MONGODB_URL)
db = client[settings.DATABASE_NAME]
users_collection = db["users"]

# Ensure email is unique
users_collection.create_index("email", unique=True)
