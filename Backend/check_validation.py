"""
Quick script to check validation data in database
"""
from app.db.database import validation_results_collection
import json

validation_id = "3e34541e-60a6-4240-9955-2393c3d8b31f"

# Find the validation
validation = validation_results_collection.find_one({"validation_id": validation_id})

if validation:
    print("✅ Validation found!")
    print(f"Status: {validation.get('status')}")
    print(f"Overall Score: {validation.get('overall_score')}")
    print(f"Has report_data: {'YES' if validation.get('report_data') else 'NO'}")
    print(f"Has individual_scores: {'YES' if validation.get('individual_scores') else 'NO'}")
    
    if validation.get('report_data'):
        report = validation['report_data']
        print(f"\nReport Data Keys: {list(report.keys())}")
        print(f"Report overall_score: {report.get('overall_score')}")
    else:
        print("\n❌ report_data is NULL or empty!")
        
    if validation.get('individual_scores'):
        print(f"\nIndividual Scores: {list(validation['individual_scores'].keys())}")
    else:
        print("\n❌ individual_scores is NULL or empty!")
        
    print(f"\nCreated: {validation.get('created_at')}")
    print(f"Completed: {validation.get('completed_at')}")
    print(f"Error: {validation.get('error_message')}")
else:
    print("❌ Validation NOT FOUND in database!")
