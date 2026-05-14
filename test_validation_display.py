"""
Test script to diagnose validation display issue
Run this to check what data is actually being returned
"""

from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Update with your connection string
db = client["your_database_name"]  # Update with your database name

# Check ideas collection
print("=" * 80)
print("CHECKING IDEAS COLLECTION")
print("=" * 80)

ideas = list(db.ideas.find({"user_id": "9144cf27-6eac-4f87-927d-b760ef9f798d"}))
for idea in ideas:
    print(f"\nIdea: {idea.get('title')}")
    print(f"  ID: {idea.get('id')}")
    print(f"  Validation Count: {idea.get('validation_count')}")
    print(f"  Latest Validation ID: {idea.get('latest_validation_id')}")
    print(f"  Created: {idea.get('created_at')}")

# Check validation_results collection
print("\n" + "=" * 80)
print("CHECKING VALIDATION_RESULTS COLLECTION")
print("=" * 80)

validations = list(db.validation_results.find({"user_id": "9144cf27-6eac-4f87-927d-b760ef9f798d"}))
for validation in validations:
    print(f"\nValidation ID: {validation.get('validation_id')}")
    print(f"  Idea ID: {validation.get('idea_id')}")
    print(f"  Status: {validation.get('status')}")
    print(f"  Overall Score: {validation.get('overall_score')}")
    print(f"  Created: {validation.get('created_at')}")
    print(f"  Completed: {validation.get('completed_at')}")

# Check if latest_validation_id matches
print("\n" + "=" * 80)
print("CHECKING LINKAGE")
print("=" * 80)

for idea in ideas:
    latest_val_id = idea.get('latest_validation_id')
    if latest_val_id:
        validation = db.validation_results.find_one({"validation_id": latest_val_id})
        if validation:
            print(f"\n✓ Idea '{idea.get('title')}' is linked to validation")
            print(f"  Validation Status: {validation.get('status')}")
            print(f"  Overall Score: {validation.get('overall_score')}")
            print(f"  Score Type: {type(validation.get('overall_score'))}")
        else:
            print(f"\n✗ Idea '{idea.get('title')}' has latest_validation_id but validation not found!")
    else:
        print(f"\n✗ Idea '{idea.get('title')}' has no latest_validation_id")
