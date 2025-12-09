"""
API routes for Product Management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.db.models.product_model import (
    ProductCreate,
    ProductUpdate,
    ProductResponse
)
from app.services.competitor_intelligence.product_manager import ProductManager
from app.core.dependencies import get_current_user
from app.core.logging import logger

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new product for competitor analysis
    
    - **product_name**: Name of your product
    - **product_description**: Detailed description of what your product does
    - **key_features**: List of key features that make your product unique
    """
    try:
        user_id = current_user.id
        product = ProductManager.create_product(user_id, product_data)
        return product
    except Exception as e:
        logger.error(f"Failed to create product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}"
        )


@router.get("/", response_model=List[ProductResponse])
async def get_all_products(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all products for the current user
    """
    try:
        user_id = current_user.id
        products = ProductManager.get_all_products(user_id)
        return products
    except Exception as e:
        logger.error(f"Failed to get products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get products: {str(e)}"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific product by ID
    """
    try:
        user_id = current_user.id
        product = ProductManager.get_product(user_id, product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get product: {str(e)}"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a product
    """
    try:
        user_id = current_user.id
        product = ProductManager.update_product(user_id, product_id, product_data)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}"
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a product and all its analyses
    """
    try:
        user_id = current_user.id
        deleted = ProductManager.delete_product(user_id, product_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete product: {str(e)}"
        )
