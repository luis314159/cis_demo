from fastapi import APIRouter, HTTPException, status
from db import SessionDep
from sqlmodel import select
import logging
from models import Product, ProductCreate
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Definimos el router
router = APIRouter(
    prefix="/products",
    tags=["Product"]
)

@router.get('/',
            response_description="List all products",
            tags=["Product"],
            response_model=List[Product],
            status_code= status.HTTP_200_OK
            )
def list_products(
    session: SessionDep,
):
    statement = select(Product)
    products = session.exec(statement).all()
    return products

@router.post('/',
            response_description="Create a new product",
            tags=["Product"],
            response_model=Product,
            status_code=status.HTTP_201_CREATED
            )
def create_product(
    product: ProductCreate,
    session: SessionDep,
):
    try:
        # Crear instancia del modelo Product
        db_product = Product.model_validate(product)
        
        # Añadir a la base de datos
        session.add(db_product)
        session.commit()
        session.refresh(db_product)
        
        logger.info(f"Product created: {db_product.product_name}")
        return db_product
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating product: {str(e)}"
        )
    

@router.delete('/{product_id}',
              response_description="Delete a product",
              tags=["Product"],
              status_code=status.HTTP_204_NO_CONTENT
              )
def delete_product(
    product_id: int,
    session: SessionDep,
):
    try:
        # Buscar el producto en la base de datos
        statement = select(Product).where(Product.id == product_id)
        product = session.exec(statement).first()
        
        # Verificar si el producto existe
        if not product:
            logger.warning(f"Product with id {product_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )
        
        # Eliminar el producto
        session.delete(product)
        session.commit()
        
        logger.info(f"Product deleted: {product.product_name}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting product: {str(e)}"
        )