from fastapi import APIRouter

# Definimos el router
router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

# Dummy data
# dummy_data = ["WN675B", "WN675A", "WN675C"
# ]

dummy_data = [
  {
    "id": 1,
    "name": "WN675B"
  },
  {
    "id": 2,
    "name": "WN675A"
  },
  {
    "id": 3,
    "name": "WN675C"
  }
]

# Endpoint para devolver la dummy data
@router.get("/test_job")
async def get_dummy_data():
    """
    Devuelve la lista de datos dummy.
    """
    return dummy_data