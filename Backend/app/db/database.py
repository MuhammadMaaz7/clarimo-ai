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

# Competitor Analysis Module collections
products_collection = db["products"]
competitor_analyses_collection = db["competitor_analyses"]

# Launch Planning Module collections
launch_plans_collection = db["launch_plans"]

# GTM Strategy Module collections
gtm_strategies_collection = db["gtm_strategies"]

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

# Products collection indexes
products_collection.create_index("id", unique=True)
products_collection.create_index([("user_id", 1), ("created_at", -1)])
products_collection.create_index([("user_id", 1), ("updated_at", -1)])

# Competitor analyses collection indexes
competitor_analyses_collection.create_index("analysis_id", unique=True)
competitor_analyses_collection.create_index([("product_id", 1), ("created_at", -1)])
competitor_analyses_collection.create_index([("user_id", 1), ("created_at", -1)])
competitor_analyses_collection.create_index([("status", 1), ("created_at", 1)])
competitor_analyses_collection.create_index([("product_id", 1), ("status", 1)])

# Launch plans collection indexes
launch_plans_collection.create_index("plan_id", unique=True)
launch_plans_collection.create_index([("user_id", 1), ("created_at", -1)])
launch_plans_collection.create_index([("status", 1), ("created_at", 1)])

# GTM strategies collection indexes
gtm_strategies_collection.create_index("gtm_id", unique=True)
gtm_strategies_collection.create_index([("user_id", 1), ("created_at", -1)])
