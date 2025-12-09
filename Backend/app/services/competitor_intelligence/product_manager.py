"""
Product Management Service
Handles CRUD operations for products
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.db.database import db, products_collection, competitor_analyses_collection
from app.db.models.product_model import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    LatestAnalysisSummary
)
from app.core.logging import logger


class ProductManager:
    """Service for managing products"""
    
    @staticmethod
    def create_product(user_id: str, product_data: ProductCreate) -> ProductResponse:
        """
        Create a new product
        
        Args:
            user_id: ID of the user creating the product
            product_data: Product creation data
            
        Returns:
            ProductResponse with created product
        """
        product_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        product_doc = {
            "id": product_id,
            "user_id": user_id,
            "product_name": product_data.product_name,
            "product_description": product_data.product_description,
            "key_features": product_data.key_features,
            "created_at": now,
            "updated_at": now
        }
        
        products_collection.insert_one(product_doc)
        
        logger.info(f"Created product {product_id} for user {user_id}")
        
        return ProductResponse(
            id=product_id,
            user_id=user_id,
            product_name=product_data.product_name,
            product_description=product_data.product_description,
            key_features=product_data.key_features,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            latest_analysis=None
        )
    
    @staticmethod
    def get_product(user_id: str, product_id: str) -> Optional[ProductResponse]:
        """
        Get a product by ID
        
        Args:
            user_id: ID of the user
            product_id: ID of the product
            
        Returns:
            ProductResponse or None if not found
        """
        product = products_collection.find_one({
            "id": product_id,
            "user_id": user_id
        })
        
        if not product:
            return None
        
        # Get latest analysis summary
        latest_analysis = None
        analysis = competitor_analyses_collection.find_one(
            {"product_id": product_id},
            sort=[("created_at", -1)]
        )
        
        if analysis:
            latest_analysis = LatestAnalysisSummary(
                analysis_id=analysis["analysis_id"],
                competitors_found=len(analysis.get("competitors", [])),
                status=analysis["status"],
                created_at=analysis["created_at"].isoformat()
            )
        
        return ProductResponse(
            id=product["id"],
            user_id=product["user_id"],
            product_name=product["product_name"],
            product_description=product["product_description"],
            key_features=product["key_features"],
            created_at=product["created_at"].isoformat(),
            updated_at=product["updated_at"].isoformat(),
            latest_analysis=latest_analysis
        )
    
    @staticmethod
    def get_all_products(user_id: str) -> List[ProductResponse]:
        """
        Get all products for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of ProductResponse
        """
        products = list(products_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1))
        
        result = []
        for product in products:
            # Get latest analysis summary
            latest_analysis = None
            analysis = competitor_analyses_collection.find_one(
                {"product_id": product["id"]},
                sort=[("created_at", -1)]
            )
            
            if analysis:
                latest_analysis = LatestAnalysisSummary(
                    analysis_id=analysis["analysis_id"],
                    competitors_found=len(analysis.get("competitors", [])),
                    status=analysis["status"],
                    created_at=analysis["created_at"].isoformat()
                )
            
            result.append(ProductResponse(
                id=product["id"],
                user_id=product["user_id"],
                product_name=product["product_name"],
                product_description=product["product_description"],
                key_features=product["key_features"],
                created_at=product["created_at"].isoformat(),
                updated_at=product["updated_at"].isoformat(),
                latest_analysis=latest_analysis
            ))
        
        return result
    
    @staticmethod
    def update_product(
        user_id: str,
        product_id: str,
        product_data: ProductUpdate
    ) -> Optional[ProductResponse]:
        """
        Update a product
        
        Args:
            user_id: ID of the user
            product_id: ID of the product
            product_data: Product update data
            
        Returns:
            Updated ProductResponse or None if not found
        """
        # Build update dict
        update_dict = {"updated_at": datetime.utcnow()}
        
        if product_data.product_name is not None:
            update_dict["product_name"] = product_data.product_name
        if product_data.product_description is not None:
            update_dict["product_description"] = product_data.product_description
        if product_data.key_features is not None:
            update_dict["key_features"] = product_data.key_features
        
        result = products_collection.find_one_and_update(
            {"id": product_id, "user_id": user_id},
            {"$set": update_dict},
            return_document=True
        )
        
        if not result:
            return None
        
        logger.info(f"Updated product {product_id}")
        
        return ProductManager.get_product(user_id, product_id)
    
    @staticmethod
    def delete_product(user_id: str, product_id: str) -> bool:
        """
        Delete a product and all its analyses
        
        Args:
            user_id: ID of the user
            product_id: ID of the product
            
        Returns:
            True if deleted, False if not found
        """
        result = products_collection.delete_one({
            "id": product_id,
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            return False
        
        # Delete all analyses for this product
        competitor_analyses_collection.delete_many({"product_id": product_id})
        
        logger.info(f"Deleted product {product_id} and its analyses")
        
        return True
