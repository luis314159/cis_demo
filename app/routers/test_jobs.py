from fastapi import APIRouter

# Definimos el router
router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

# Dummy data
dummy_data = ["WN675B", "WN675A", "WN675C"
]

# Endpoint para devolver la dummy data
@router.get("/test_job")
async def get_dummy_data():
    """
    Devuelve la lista de datos dummy.
    """
    return dummy_data