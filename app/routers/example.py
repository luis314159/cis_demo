from fastapi import APIRouter, HTTPException
from app.models.example import Item
from app.services.example import ItemService
from app.db.prisma_client import prisma

router = APIRouter(
    prefix="/example",
    tags=["example"],
)

@router.post("/discount")
def calculate_discount(item: Item, discount: float):
    try:
        discounted_price = ItemService.calculate_discounted_price(item, discount)
        return {
            "original_price": item.price,
            "discounted_price": discounted_price,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/format")
def format_item(item: Item):
    formatted_data = ItemService.format_item_data(item)
    return {"formatted_item": formatted_data}


router = APIRouter()

@router.get("/users")
async def get_users():
    return await prisma.user.find_many()

@router.post("/users")
async def create_user(email: str, name: str):
    return await prisma.user.create(data={"email": email, "name": name})