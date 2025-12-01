from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.MONGODB_URL)
db = client[settings.DATABASE_NAME]

# Collections
users_collection = db["users"]
user_inputs_collection = db["user_inputs"]
generated_keywords_collection = db["generated_keywords"]

# Idea Validation Module collections
ideas_collection = db["ideas"]
validation_results_collection = db["validation_results"]

# User collection indexes
users_collection.create_index("email", unique=True)

# User inputs collection indexes
user_inputs_collection.create_index([("user_id", 1), ("created_at", -1)])  # user_id as string
user_inputs_collection.create_index("input_id", unique=True)
user_inputs_collection.create_index([("status", 1), ("created_at", 1)])

# Generated keywords collection indexes
generated_keywords_collection.create_index("input_id", unique=True)
generated_keywords_collection.create_index([("user_id", 1), ("created_at", -1)])

# Ideas collection indexes
ideas_collection.create_index("id", unique=True)
ideas_collection.create_index([("user_id", 1), ("created_at", -1)])
ideas_collection.create_index([("user_id", 1), ("updated_at", -1)])
ideas_collection.create_index([("user_id", 1), ("validation_count", -1)])

# Validation results collection indexes
validation_results_collection.create_index("validation_id", unique=True)
validation_results_collection.create_index([("idea_id", 1), ("created_at", -1)])
validation_results_collection.create_index([("user_id", 1), ("created_at", -1)])
validation_results_collection.create_index([("status", 1), ("created_at", 1)])
validation_results_collection.create_index([("idea_id", 1), ("status", 1)])
