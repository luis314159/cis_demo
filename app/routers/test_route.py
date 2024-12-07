from fastapi import APIRouter

# Definimos el router
router = APIRouter(
    prefix="/object",
    tags=["Object"]
)

# Dummy data
dummy_data = [
    {
        "id": 1,
        "name": "Support Beam",
        "section": "CUTTING",
        "ocr": "SUP123",
        "quantity": 10,
        "scanned": False
    },
    {
        "id": 2,
        "name": "Gear Assembly",
        "section": "MACHINING",
        "ocr": "GEA456",
        "quantity": 5,
        "scanned": True
    },
    {
        "id": 3,
        "name": "Metal Panel",
        "section": "WAREHOUSE",
        "ocr": "MET789",
        "quantity": 20,
        "scanned": False
    },
    {
        "id": 4,
        "name": "Hydraulic Cylinder",
        "section": "BENT",
        "ocr": "HYD234",
        "quantity": 8,
        "scanned": True
    },
    {
        "id": 5,
        "name": "Steel Plate",
        "section": "CUTTING",
        "ocr": "STEEL001",
        "quantity": 15,
        "scanned": False
    },
    {
        "id": 6,
        "name": "Precision Screw",
        "section": "MACHINING",
        "ocr": "PRE678",
        "quantity": 50,
        "scanned": True
    },
    {
        "id": 7,
        "name": "Storage Rack",
        "section": "WAREHOUSE",
        "ocr": "STO890",
        "quantity": 12,
        "scanned": False
    },
    {
        "id": 8,
        "name": "Aluminum Tube",
        "section": "CUTTING",
        "ocr": "ALU345",
        "quantity": 7,
        "scanned": True
    },
    {
        "id": 9,
        "name": "Brass Rod",
        "section": "MACHINING",
        "ocr": "BRASS567",
        "quantity": 6,
        "scanned": False
    },
    {
        "id": 10,
        "name": "Plastic Cover",
        "section": "WAREHOUSE",
        "ocr": "PLAS789",
        "quantity": 30,
        "scanned": True
    },
    {
        "id": 11,
        "name": "Copper Wire",
        "section": "CUTTING",
        "ocr": "COP123",
        "quantity": 100,
        "scanned": False
    },
    {
        "id": 12,
        "name": "Motor Bracket",
        "section": "MACHINING",
        "ocr": "MOT678",
        "quantity": 4,
        "scanned": True
    },
    {
        "id": 13,
        "name": "Rubber Gasket",
        "section": "WAREHOUSE",
        "ocr": "RUB789",
        "quantity": 25,
        "scanned": False
    },
    {
        "id": 14,
        "name": "Steel Pipe",
        "section": "BENT",
        "ocr": "PIPE001",
        "quantity": 9,
        "scanned": True
    },
    {
        "id": 15,
        "name": "Metal Clamp",
        "section": "CUTTING",
        "ocr": "CLAMP345",
        "quantity": 18,
        "scanned": False
    }
]

# Endpoint para devolver la dummy data
@router.get("/data/{job_code}")
async def get_dummy_data(job_code: str):
    """
    Devuelve la lista de datos dummy independientemente del job_code.
    """
    return dummy_data
    return {"job_code": job_code, "data": dummy_data}
