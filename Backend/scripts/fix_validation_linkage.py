"""
Database Migration Script: Fix Validation Linkage
This script fixes ideas that have completed validations but aren't properly linked.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import ideas_collection, validation_results_collection
from app.core.logging import logger


def fix_validation_linkage():
    """
    Fix validation linkage for all ideas
    
    This script:
    1. Finds all ideas
    2. For each idea, finds the latest completed validation
    3. Updates the idea with the correct latest_validation_id and validation_count
    """
    
    logger.info("Starting validation linkage fix...")
    
    # Get all ideas
    ideas = list(ideas_collection.find({}))
    logger.info(f"Found {len(ideas)} ideas to process")
    
    fixed_count = 0
    skipped_count = 0
    error_count = 0
    
    for idea in ideas:
        idea_id = idea.get("id")
        user_id = idea.get("user_id")
        
        try:
            # Find all completed validations for this idea
            validations = list(validation_results_collection.find({
                "idea_id": idea_id,
                "user_id": user_id,
                "status": "completed"
            }).sort("created_at", -1))  # Sort by newest first
            
            validation_count = len(validations)
            
            # Get the latest validation
            latest_validation = validations[0] if validations else None
            latest_validation_id = latest_validation.get("validation_id") if latest_validation else None
            
            # Check if update is needed
            current_validation_id = idea.get("latest_validation_id")
            current_validation_count = idea.get("validation_count", 0)
            
            needs_update = (
                latest_validation_id != current_validation_id or
                validation_count != current_validation_count
            )
            
            if needs_update:
                # Update the idea
                update_data = {
                    "latest_validation_id": latest_validation_id,
                    "validation_count": validation_count,
                    "updated_at": datetime.utcnow()
                }
                
                result = ideas_collection.update_one(
                    {"id": idea_id},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    logger.info(
                        f"✓ Fixed idea '{idea.get('title')}': "
                        f"validation_count {current_validation_count} → {validation_count}, "
                        f"latest_validation_id {current_validation_id} → {latest_validation_id}"
                    )
                    fixed_count += 1
                else:
                    logger.warning(f"Failed to update idea '{idea.get('title')}'")
                    error_count += 1
            else:
                logger.debug(f"Skipped idea '{idea.get('title')}' (already correct)")
                skipped_count += 1
                
        except Exception as e:
            logger.error(f"Error processing idea '{idea.get('title')}': {str(e)}")
            error_count += 1
    
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION LINKAGE FIX COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total ideas processed: {len(ideas)}")
    logger.info(f"Ideas fixed: {fixed_count}")
    logger.info(f"Ideas skipped (already correct): {skipped_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("=" * 80)


def verify_linkage():
    """
    Verify that all ideas with validations are properly linked
    """
    logger.info("\nVerifying validation linkage...")
    
    # Find all ideas with validations
    ideas_with_validations = list(ideas_collection.find({
        "validation_count": {"$gt": 0}
    }))
    
    issues_found = 0
    
    for idea in ideas_with_validations:
        idea_id = idea.get("id")
        latest_validation_id = idea.get("latest_validation_id")
        
        if not latest_validation_id:
            logger.error(f"✗ Idea '{idea.get('title')}' has validation_count > 0 but no latest_validation_id")
            issues_found += 1
            continue
        
        # Check if the validation exists
        validation = validation_results_collection.find_one({
            "validation_id": latest_validation_id
        })
        
        if not validation:
            logger.error(f"✗ Idea '{idea.get('title')}' references non-existent validation {latest_validation_id}")
            issues_found += 1
            continue
        
        # Check if validation is completed
        if validation.get("status") != "completed":
            logger.warning(f"⚠ Idea '{idea.get('title')}' references non-completed validation (status: {validation.get('status')})")
        
        # Check if validation has overall_score
        if validation.get("overall_score") is None:
            logger.warning(f"⚠ Idea '{idea.get('title')}' references validation without overall_score")
    
    if issues_found == 0:
        logger.info("✓ All validations are properly linked!")
    else:
        logger.error(f"✗ Found {issues_found} linkage issues")
    
    return issues_found == 0


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("VALIDATION LINKAGE FIX SCRIPT")
    print("=" * 80)
    print("\nThis script will:")
    print("1. Find all ideas with completed validations")
    print("2. Update latest_validation_id and validation_count")
    print("3. Verify the linkage is correct")
    print("\n" + "=" * 80)
    
    response = input("\nProceed with fix? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        fix_validation_linkage()
        verify_linkage()
    else:
        print("Aborted.")
